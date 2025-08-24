#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
12TACoreService - AI智能体驱动交易系统核心服务
负载均衡代理，统一处理所有TradingAgents-CN相关请求
"""

import os
import json
import zmq
import logging
import multiprocessing
import threading
import time
from multiprocessing import Process
from worker import TACoreWorker


class TACoreService:
    def __init__(self, frontend_port=5555, backend_port=5556, health_port=5557, num_workers=4):
        self.frontend_port = frontend_port
        self.backend_port = backend_port
        self.health_port = health_port
        self.num_workers = num_workers
        self.context = zmq.Context()
        self.workers = []
        self.running = False
        self.health_thread = None

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger("TACoreService")

    def start_workers(self):
        """启动工作进程池"""
        for i in range(self.num_workers):
            worker = TACoreWorker(worker_id=i, backend_port=self.backend_port)
            process = Process(target=worker.run)
            process.start()
            self.workers.append(process)
            self.logger.info(f"启动工作进程 {i}")

    def start_proxy(self):
        """启动ZMQ代理，连接前端客户端和后端工作进程"""
        try:
            # 前端套接字 - 接收客户端请求
            frontend = self.context.socket(zmq.ROUTER)
            frontend.bind(f"tcp://*:{self.frontend_port}")

            # 后端套接字 - 连接工作进程
            backend = self.context.socket(zmq.DEALER)
            backend.bind(f"tcp://*:{self.backend_port}")

            self.logger.info("TACoreService 代理启动")
            self.logger.info(f"前端端口: {self.frontend_port}")
            self.logger.info(f"后端端口: {self.backend_port}")
            self.logger.info(f"工作进程数: {self.num_workers}")

            # 启动代理
            zmq.proxy(frontend, backend)

        except Exception as e:
            self.logger.error(f"代理启动失败: {e}")
        finally:
            frontend.close()
            backend.close()

    def start_health_server(self):
        """启动健康检查服务器"""
        def health_server():
            health_context = zmq.Context()
            health_socket = health_context.socket(zmq.REP)
            health_socket.bind(f"tcp://*:{self.health_port}")
            
            self.logger.info(f"健康检查服务器启动在端口 {self.health_port}")
            
            while self.running:
                try:
                    # 设置超时，避免阻塞
                    health_socket.setsockopt(zmq.RCVTIMEO, 1000)
                    request = health_socket.recv_json()
                    
                    # 检查是否为健康检查请求
                    if request.get('method') == 'system.health':
                        response = {
                            'id': request.get('id', 1),
                            'result': {
                                'status': 'healthy',
                                'timestamp': time.time(),
                                'workers': len(self.workers)
                            }
                        }
                    else:
                        response = {
                            'id': request.get('id', 1),
                            'error': {'code': -32601, 'message': 'Method not found'}
                        }
                    
                    health_socket.send_json(response)
                    
                except zmq.Again:
                    # 超时，继续循环
                    continue
                except Exception as e:
                    self.logger.error(f"健康检查服务器错误: {e}")
                    break
            
            health_socket.close()
            health_context.term()
        
        self.health_thread = threading.Thread(target=health_server)
        self.health_thread.daemon = True
        self.health_thread.start()

    def start(self):
        """启动服务"""
        self.running = True
        
        # 启动健康检查服务器
        self.start_health_server()
        
        # 启动工作进程
        self.start_workers()
        
        try:
            # 启动代理（这会阻塞主线程）
            self.start_proxy()
        except KeyboardInterrupt:
            self.logger.info("接收到中断信号，正在关闭服务...")
        finally:
            self.stop()

    def stop(self):
        """停止服务"""
        self.running = False
        
        # 停止所有工作进程
        for worker in self.workers:
            if worker.is_alive():
                worker.terminate()
                worker.join(timeout=5)
        
        # 关闭ZMQ上下文
        self.context.term()
        
        self.logger.info("TACoreService 已停止")


def main():
    """主函数"""
    # 从环境变量读取配置
    frontend_port = int(os.getenv('TACORE_FRONTEND_PORT', 5555))
    backend_port = int(os.getenv('TACORE_BACKEND_PORT', 5556))
    health_port = int(os.getenv('TACORE_HEALTH_PORT', 5557))
    num_workers = int(os.getenv('TACORE_NUM_WORKERS', 4))
    
    # 创建并启动服务
    service = TACoreService(
        frontend_port=frontend_port,
        backend_port=backend_port,
        health_port=health_port,
        num_workers=num_workers
    )
    
    service.start()


if __name__ == "__main__":
    main()