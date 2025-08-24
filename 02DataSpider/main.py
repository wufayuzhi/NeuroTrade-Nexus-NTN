#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroTrade Nexus (NTN) - 信息源爬虫模组主入口
模组二：Info Crawler Module

启动方式：
  python main.py --env development
  python main.py --env staging  
  python main.py --env production
"""

import sys
import os
import argparse
from pathlib import Path

# 添加依赖库路径
sys.path.insert(0, r"D:\yilai\core_lib")

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import ConfigManager
from app.utils import Logger
from app.api import create_app
from app.crawlers import ScrapyCrawler, TelegramCrawler
from app.zmq_client import ZMQPublisher


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="NeuroTrade Nexus 信息源爬虫模组")
    parser.add_argument(
        "--env",
        choices=["development", "staging", "production"],
        default="development",
        help="运行环境 (默认: development)",
    )
    parser.add_argument(
        "--mode",
        choices=["crawler", "api", "all"],
        default="all",
        help="运行模式 (默认: all)",
    )
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    return parser.parse_args()


def setup_environment(env: str):
    """设置环境变量"""
    os.environ["NTN_ENV"] = env
    os.environ["APP_ENV"] = env
    
    # 设置日志级别
    if env == "development":
        os.environ["LOG_LEVEL"] = "DEBUG"
    else:
        os.environ["LOG_LEVEL"] = "INFO"


def start_crawler_service(config, logger):
    """启动爬虫服务"""
    logger.info("启动爬虫服务...")
    
    try:
        # 初始化ZMQ发布者
        zmq_publisher = ZMQPublisher(config)
        
        # 启动Scrapy爬虫
        scrapy_crawler = ScrapyCrawler(config, zmq_publisher)
        scrapy_crawler.start()
        
        # 启动Telegram爬虫
        telegram_crawler = TelegramCrawler(config, zmq_publisher)
        telegram_crawler.start()
        
        logger.info("爬虫服务启动成功")
        
        # 保持服务运行
        import time
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"爬虫服务启动失败: {e}")
        raise


def start_api_service(config, logger):
    """启动API服务"""
    logger.info("启动API服务...")
    
    try:
        app = create_app(config)
        
        import uvicorn
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=config.get("api.port", 5000),
            log_level=config.get("logging.level", "info").lower(),
        )
        
    except Exception as e:
        logger.error(f"API服务启动失败: {e}")
        raise


def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置环境
    setup_environment(args.env)
    
    # 初始化配置
    config = ConfigManager(args.env)
    
    # 初始化日志
    logger = Logger(config).get_logger()
    
    logger.info(f"NeuroTrade Nexus 信息源爬虫模组启动 - 环境: {args.env}, 模式: {args.mode}")
    
    try:
        if args.mode == "crawler":
            start_crawler_service(config, logger)
        elif args.mode == "api":
            start_api_service(config, logger)
        elif args.mode == "all":
            # 在生产环境中，通常使用进程管理器来分别启动不同服务
            # 这里为了简化，使用多线程
            import threading
            
            # 启动爬虫服务线程
            crawler_thread = threading.Thread(
                target=start_crawler_service, args=(config, logger)
            )
            crawler_thread.daemon = True
            crawler_thread.start()
            
            # 启动API服务（主线程）
            start_api_service(config, logger)
            
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务运行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()