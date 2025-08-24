#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描器模组主入口文件
负责启动和管理扫描器服务
"""

import sys
import os
import asyncio
import signal
from pathlib import Path
from typing import Optional
import structlog
import click

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scanner.core import ScannerController
from scanner.utils import ConfigManager, setup_logging

# 配置日志
logger = structlog.get_logger(__name__)


class ScannerService:
    """扫描器服务管理类"""

    def __init__(
        self, config_path: Optional[str] = None, environment: str = "development"
    ):
        self.config_path = config_path
        self.environment = environment
        self.controller: Optional[ScannerController] = None
        self.running = False

        # 设置信号处理
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """设置信号处理器"""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Windows特定信号
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, signal_handler)

    async def start(self) -> bool:
        """启动扫描器服务

        Returns:
            启动是否成功
        """
        try:
            logger.info("Starting Scanner Service", environment=self.environment)

            # 加载配置
            config_manager = ConfigManager()
            if self.config_path:
                config = config_manager.load_config(self.config_path)
            else:
                config = config_manager.load_environment_config(self.environment)

            # 设置日志
            setup_logging(config.get("logging", {}))

            # 创建控制器
            self.controller = ScannerController(config)

            # 启动控制器
            success = await self.controller.start()
            if not success:
                logger.error("Failed to start scanner controller")
                return False

            self.running = True
            logger.info("Scanner Service started successfully")

            # 保持运行
            await self._run_forever()

            return True

        except Exception as e:
            logger.error("Error starting scanner service", error=str(e))
            return False

    async def _run_forever(self):
        """保持服务运行"""
        try:
            while self.running and self.controller:
                # 检查控制器状态
                if not await self.controller.is_healthy():
                    logger.warning("Controller health check failed")
                    
                # 等待一段时间
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info("Service loop cancelled")
        except Exception as e:
            logger.error("Error in service loop", error=str(e))
            self.running = False

    def stop(self):
        """停止扫描器服务"""
        logger.info("Stopping Scanner Service")
        self.running = False
        
        if self.controller:
            asyncio.create_task(self.controller.stop())

    async def restart(self) -> bool:
        """重启扫描器服务"""
        logger.info("Restarting Scanner Service")
        
        # 停止当前服务
        self.stop()
        await asyncio.sleep(2)
        
        # 重新启动
        return await self.start()


# CLI命令定义
@click.group()
@click.option('--debug/--no-debug', default=False, help='Enable debug mode')
@click.pass_context
def cli(ctx, debug):
    """扫描器模组命令行工具"""
    ctx.ensure_object(dict)
    ctx.obj['DEBUG'] = debug
    
    if debug:
        os.environ['LOG_LEVEL'] = 'DEBUG'


@cli.command()
@click.option('--environment', '-e', default='development', 
              type=click.Choice(['development', 'staging', 'production']),
              help='运行环境')
@click.option('--config', '-c', help='配置文件路径')
@click.pass_context
def start(ctx, environment, config):
    """启动扫描器服务"""
    service = ScannerService(config_path=config, environment=environment)
    
    try:
        asyncio.run(service.start())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error("Service failed", error=str(e))
        sys.exit(1)


@cli.command()
@click.option('--environment', '-e', default='development',
              type=click.Choice(['development', 'staging', 'production']),
              help='运行环境')
def status(environment):
    """检查扫描器服务状态"""
    # 这里可以实现状态检查逻辑
    click.echo(f"Checking scanner status for environment: {environment}")
    # TODO: 实现实际的状态检查


@cli.command()
@click.option('--environment', '-e', default='development',
              type=click.Choice(['development', 'staging', 'production']),
              help='运行环境')
def stop(environment):
    """停止扫描器服务"""
    # 这里可以实现停止逻辑
    click.echo(f"Stopping scanner for environment: {environment}")
    # TODO: 实现实际的停止逻辑


@cli.command()
@click.option('--environment', '-e', default='development',
              type=click.Choice(['development', 'staging', 'production']),
              help='运行环境')
def restart(environment):
    """重启扫描器服务"""
    click.echo(f"Restarting scanner for environment: {environment}")
    # TODO: 实现实际的重启逻辑


@cli.command()
@click.option('--environment', '-e', default='development',
              type=click.Choice(['development', 'staging', 'production']),
              help='运行环境')
def health(environment):
    """健康检查"""
    click.echo(f"Health check for environment: {environment}")
    # TODO: 实现健康检查逻辑


if __name__ == '__main__':
    # 设置环境变量
    os.environ.setdefault('SCANNER_ENV', 'development')
    
    # 启动CLI
    cli()