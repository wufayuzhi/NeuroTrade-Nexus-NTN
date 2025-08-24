#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略优化模组主入口文件
NeuroTrade Nexus (NTN) - Strategy Optimization Module

核心职责：
1. 订阅扫描器发布的潜在交易机会
2. 执行策略回测和参数优化
3. 进行压力测试和风险评估
4. 发布经过验证的策略参数包
"""

import asyncio
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.logging_config import setup_logging
from config.settings import get_settings
from optimizer.backtester.engine import BacktestEngine
from optimizer.communication.zmq_client import (
    StrategyPackage,
    TradingOpportunity,
    create_zmq_client,
)
from optimizer.decision.engine import DecisionEngine
from optimizer.optimization.genetic_optimizer import GeneticOptimizer
from optimizer.strategies.manager import StrategyManager


@dataclass
class OptimizerComponents:
    """优化器核心组件"""

    backtest_engine: Optional[Any] = None
    genetic_optimizer: Optional[Any] = None
    decision_engine: Optional[Any] = None
    strategy_manager: Optional[Any] = None
    risk_manager: Optional[Any] = None
    data_validator: Optional[Any] = None


@dataclass
class OptimizerCommunication:
    """优化器通信组件"""

    zmq_client: Optional[Any] = None
    zmq_context: Optional[Any] = None


@dataclass
class OptimizerState:
    """优化器运行状态"""

    is_running: bool = False


@dataclass
class OptimizerStats:
    """优化器统计信息"""

    opportunities_processed: int = 0
    strategies_published: int = 0
    last_activity: Optional[datetime] = None


class StrategyOptimizationModule:
    """
    策略优化模组主类

    实现NeuroTrade Nexus核心设计理念：
    - 微服务架构设计
    - ZeroMQ消息总线通信
    - 三环境隔离(development/staging/production)
    - 数据隔离与环境管理规范
    """

    def __init__(self, config=None):
        # 如果传入了配置，先验证它
        if config is not None:
            self._validate_config(config)
            self.config = config
        else:
            self.config = get_settings()

        self.logger = logging.getLogger(__name__)

        # 使用数据类管理组件和状态
        self.components = OptimizerComponents()
        self.communication = OptimizerCommunication()
        self.state = OptimizerState()
        self.stats = OptimizerStats()

        # 初始化标志
        self._initialized = False

    def _validate_config(self, config):
        """验证配置对象"""
        required_attrs = [
            "zmq_subscriber_port",
            "zmq_publisher_port",
            "redis_host",
            "redis_port",
            "database_path",
            "environment",
        ]

        for attr in required_attrs:
            if not hasattr(config, attr):
                raise ValueError(f"配置对象缺少必需属性: {attr}")

        # 验证环境值
        valid_environments = ["development", "staging", "production"]
        if config.environment not in valid_environments:
            raise ValueError(
                f"无效的环境配置: {config.environment}. "
                f"有效值: {valid_environments}"
            )

        # 验证端口范围
        if not (1024 <= config.zmq_subscriber_port <= 65535):
            raise ValueError(
                f"ZMQ订阅端口超出有效范围: {config.zmq_subscriber_port}"
            )

        if not (1024 <= config.zmq_publisher_port <= 65535):
            raise ValueError(
                f"ZMQ发布端口超出有效范围: {config.zmq_publisher_port}"
            )

        if config.zmq_subscriber_port == config.zmq_publisher_port:
            raise ValueError("ZMQ订阅端口和发布端口不能相同")

        # 验证Redis配置
        if not (1 <= config.redis_port <= 65535):
            raise ValueError(f"Redis端口超出有效范围: {config.redis_port}")

        # 验证数据库路径
        if not config.database_path:
            raise ValueError("数据库路径不能为空")

        self.logger.info(f"配置验证通过: 环境={config.environment}")

    async def initialize(self):
        """初始化优化器组件"""
        if self._initialized:
            self.logger.warning("优化器已经初始化，跳过重复初始化")
            return

        try:
            self.logger.info("开始初始化策略优化模组...")

            # 初始化核心组件
            await self._initialize_components()

            # 初始化通信组件
            await self._initialize_communication()

            self._initialized = True
            self.logger.info("策略优化模组初始化完成")

        except Exception as e:
            self.logger.error(f"初始化失败: {e}")
            await self.cleanup()
            raise

    async def _initialize_components(self):
        """初始化核心组件"""
        try:
            # 初始化回测引擎
            self.components.backtest_engine = BacktestEngine(
                config={
                    "database_path": self.config.database_path,
                    "cache_size": getattr(self.config, "cache_size", 1000),
                    "max_workers": getattr(self.config, "max_workers", 4),
                }
            )

            # 初始化遗传算法优化器
            self.components.genetic_optimizer = GeneticOptimizer(
                config={
                    "population_size": getattr(self.config, "population_size", 50),
                    "generations": getattr(self.config, "generations", 100),
                    "mutation_rate": getattr(self.config, "mutation_rate", 0.1),
                    "crossover_rate": getattr(self.config, "crossover_rate", 0.8),
                }
            )

            # 初始化决策引擎
            self.components.decision_engine = DecisionEngine(
                config={
                    "risk_threshold": getattr(self.config, "risk_threshold", 0.02),
                    "min_sharpe_ratio": getattr(self.config, "min_sharpe_ratio", 1.0),
                    "max_drawdown": getattr(self.config, "max_drawdown", 0.1),
                }
            )

            # 初始化策略管理器
            self.components.strategy_manager = StrategyManager(
                config={
                    "strategy_path": getattr(
                        self.config, "strategy_path", "./strategies"
                    ),
                    "max_strategies": getattr(self.config, "max_strategies", 100),
                }
            )

            self.logger.info("核心组件初始化完成")

        except Exception as e:
            self.logger.error(f"核心组件初始化失败: {e}")
            raise

    async def _initialize_communication(self):
        """初始化通信组件"""
        try:
            await self._initialize_zmq_client()
            self.logger.info("通信组件初始化完成")

        except Exception as e:
            self.logger.error(f"通信组件初始化失败: {e}")
            raise

    async def _initialize_zmq_client(self):
        """初始化ZMQ客户端"""
        try:
            self.communication.zmq_client = await create_zmq_client(
                subscriber_port=self.config.zmq_subscriber_port,
                publisher_port=self.config.zmq_publisher_port,
                subscriber_topics=["trading_opportunity"],
            )

            # 设置消息处理回调
            self.communication.zmq_client.set_message_handler(
                "trading_opportunity", self._handle_trading_opportunity
            )

            self.logger.info(
                f"ZMQ客户端初始化完成 - "
                f"订阅端口: {self.config.zmq_subscriber_port}, "
                f"发布端口: {self.config.zmq_publisher_port}"
            )

        except Exception as e:
            self.logger.error(f"ZMQ客户端初始化失败: {e}")
            raise

    async def start(self):
        """启动优化器"""
        if not self._initialized:
            await self.initialize()

        if self.state.is_running:
            self.logger.warning("优化器已在运行中")
            return

        try:
            self.state.is_running = True
            self.logger.info("策略优化模组启动")

            # 启动ZMQ客户端
            if self.communication.zmq_client:
                await self.communication.zmq_client.start()

            # 启动主运行循环
            await self.run()

        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            self.state.is_running = False
            raise

    async def stop(self):
        """停止优化器"""
        if not self.state.is_running:
            self.logger.warning("优化器未在运行")
            return

        try:
            self.state.is_running = False
            self.logger.info("正在停止策略优化模组...")

            # 停止ZMQ客户端
            if self.communication.zmq_client:
                await self.communication.zmq_client.stop()

            self.logger.info("策略优化模组已停止")

        except Exception as e:
            self.logger.error(f"停止过程中发生错误: {e}")
            raise

    async def run(self):
        """主运行循环"""
        self.logger.info("进入主运行循环")

        try:
            while self.state.is_running:
                # 处理消息队列
                if self.communication.zmq_client:
                    await self.communication.zmq_client.process_messages()

                # 短暂休眠避免CPU占用过高
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            self.logger.info("主运行循环被取消")
        except Exception as e:
            self.logger.error(f"主运行循环异常: {e}")
            raise
        finally:
            self.logger.info("退出主运行循环")

    async def _handle_trading_opportunity(self, opportunity: TradingOpportunity):
        """
        处理交易机会

        Args:
            opportunity: 扫描器发布的交易机会
        """
        try:
            self.logger.info(
                f"收到交易机会: {opportunity.symbol} - {opportunity.strategy_type}"
            )

            # 更新统计信息
            self.stats.opportunities_processed += 1
            self.stats.last_activity = datetime.now()

            # 准备策略配置
            strategy_configs = await self._prepare_strategy_configs(opportunity)

            # 执行回测和优化
            optimization_results = []
            for config in strategy_configs:
                # 回测
                backtest_result = await self.components.backtest_engine.run_backtest(
                    symbol=opportunity.symbol,
                    strategy_config=config,
                    start_date=opportunity.analysis_period["start"],
                    end_date=opportunity.analysis_period["end"],
                )

                # 参数优化
                if backtest_result.is_profitable:
                    optimized_params = (
                        await self.components.genetic_optimizer.optimize(
                            strategy_config=config,
                            backtest_engine=self.components.backtest_engine,
                            symbol=opportunity.symbol,
                        )
                    )

                    optimization_results.append(
                        {
                            "config": config,
                            "backtest_result": backtest_result,
                            "optimized_params": optimized_params,
                        }
                    )

            # 决策引擎评估
            if optimization_results:
                decision = await self.components.decision_engine.evaluate(
                    optimization_results, opportunity
                )

                # 发布策略包
                if decision.should_publish:
                    await self._publish_strategy_package(decision, opportunity)

        except Exception as e:
            self.logger.error(f"处理交易机会时发生错误: {e}")

    async def _prepare_strategy_configs(self, opportunity: TradingOpportunity) -> list:
        """
        根据交易机会准备策略配置

        Args:
            opportunity: 交易机会

        Returns:
            策略配置列表
        """
        configs = []

        # 基于机会类型选择策略
        if opportunity.strategy_type == "momentum":
            configs.append(
                {
                    "name": "momentum_strategy",
                    "type": "momentum",
                    "parameters": {
                        "lookback_period": 20,
                        "momentum_threshold": 0.02,
                        "stop_loss": 0.05,
                        "take_profit": 0.10,
                    },
                }
            )

        elif opportunity.strategy_type == "mean_reversion":
            configs.append(
                {
                    "name": "mean_reversion_strategy",
                    "type": "mean_reversion",
                    "parameters": {
                        "lookback_period": 50,
                        "deviation_threshold": 2.0,
                        "stop_loss": 0.03,
                        "take_profit": 0.06,
                    },
                }
            )

        elif opportunity.strategy_type == "breakout":
            configs.append(
                {
                    "name": "breakout_strategy",
                    "type": "breakout",
                    "parameters": {
                        "lookback_period": 30,
                        "breakout_threshold": 0.015,
                        "stop_loss": 0.04,
                        "take_profit": 0.08,
                    },
                }
            )

        return configs

    async def _publish_strategy_package(
        self, decision, opportunity: TradingOpportunity
    ):
        """
        发布策略包

        Args:
            decision: 决策结果
            opportunity: 交易机会
        """
        try:
            strategy_package = StrategyPackage(
                package_id=f"pkg_{opportunity.symbol}_{int(datetime.now().timestamp())}",
                symbol=opportunity.symbol,
                strategy_type=opportunity.strategy_type,
                parameters=decision.recommended_params,
                risk_metrics={
                    "max_drawdown": decision.risk_assessment["max_drawdown"],
                    "sharpe_ratio": decision.risk_assessment["sharpe_ratio"],
                    "var_95": decision.risk_assessment["var_95"],
                    "expected_return": decision.risk_assessment["expected_return"],
                },
                backtest_results={
                    "total_return": decision.performance_metrics["total_return"],
                    "win_rate": decision.performance_metrics["win_rate"],
                    "profit_factor": decision.performance_metrics["profit_factor"],
                    "max_consecutive_losses": decision.performance_metrics[
                        "max_consecutive_losses"
                    ],
                },
                confidence_score=decision.confidence_score,
                valid_until=decision.expiry_time,
                created_at=datetime.now(),
                metadata={
                    "optimization_method": "genetic_algorithm",
                    "backtest_period": opportunity.analysis_period,
                    "market_conditions": opportunity.market_context,
                    "data_quality_score": opportunity.confidence_score,
                },
            )

            # 通过ZMQ发布策略包
            if self.communication.zmq_client:
                await self.communication.zmq_client.publish(
                    "strategy_package", strategy_package
                )

            # 更新统计信息
            self.stats.strategies_published += 1

            self.logger.info(
                f"策略包已发布: {strategy_package.package_id} - "
                f"置信度: {strategy_package.confidence_score:.2f}"
            )

        except Exception as e:
            self.logger.error(f"发布策略包时发生错误: {e}")

    async def cleanup(self):
        """
        清理资源
        """
        try:
            self.logger.info("开始清理资源...")

            # 停止运行
            if self.state.is_running:
                await self.stop()

            # 清理通信组件
            if self.communication.zmq_client:
                await self.communication.zmq_client.cleanup()
                self.communication.zmq_client = None

            # 清理核心组件
            if self.components.backtest_engine:
                await self.components.backtest_engine.cleanup()
                self.components.backtest_engine = None

            if self.components.genetic_optimizer:
                await self.components.genetic_optimizer.cleanup()
                self.components.genetic_optimizer = None

            if self.components.decision_engine:
                await self.components.decision_engine.cleanup()
                self.components.decision_engine = None

            if self.components.strategy_manager:
                await self.components.strategy_manager.cleanup()
                self.components.strategy_manager = None

            self._initialized = False
            self.logger.info("资源清理完成")

        except Exception as e:
            self.logger.error(f"清理资源时发生错误: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取运行统计信息

        Returns:
            统计信息字典
        """
        return {
            "opportunities_processed": self.stats.opportunities_processed,
            "strategies_published": self.stats.strategies_published,
            "last_activity": self.stats.last_activity.isoformat()
            if self.stats.last_activity
            else None,
            "is_running": self.state.is_running,
            "is_initialized": self._initialized,
            "uptime": (datetime.now() - self.stats.last_activity).total_seconds()
            if self.stats.last_activity
            else 0,
        }

    # 属性访问器
    @property
    def backtest_engine(self):
        return self.components.backtest_engine

    @property
    def genetic_optimizer(self):
        return self.components.genetic_optimizer

    @property
    def decision_engine(self):
        return self.components.decision_engine

    @property
    def strategy_manager(self):
        return self.components.strategy_manager

    @property
    def risk_manager(self):
        return self.components.risk_manager

    @property
    def data_validator(self):
        return self.components.data_validator

    @property
    def is_initialized(self):
        return self._initialized

    async def get_system_metrics(self):
        """获取系统指标"""
        return {
            "memory_usage": self._get_memory_usage(),
            "cpu_usage": self._get_cpu_usage(),
            "disk_usage": self._get_disk_usage(),
            "network_stats": self._get_network_stats(),
        }

    @property
    def is_running(self):
        return self.state.is_running

    async def pause(self):
        """暂停优化器"""
        self.state.is_running = False
        self.logger.info("优化器已暂停")

    async def resume(self):
        """恢复优化器"""
        self.state.is_running = True
        self.logger.info("优化器已恢复")

    async def get_business_metrics(self):
        """获取业务指标"""
        return {
            "total_opportunities": self.stats.opportunities_processed,
            "total_strategies": self.stats.strategies_published,
            "success_rate": self._calculate_success_rate(),
            "average_confidence": self._calculate_average_confidence(),
        }


async def main():
    """主函数"""
    # 设置日志
    setup_logging()
    logger = logging.getLogger(__name__)

    # 创建优化器实例
    optimizer = StrategyOptimizationModule()

    try:
        # 启动优化器
        await optimizer.start()
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"运行时发生错误: {e}")
    finally:
        # 清理资源
        await optimizer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())