#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroTrade Nexus (NTN) - 14模组集成测试脚本
AI智能体驱动交易系统V1.2 - 全局集成测试专用

功能说明：
1. 基础服务层测试 (01-03模组)
2. 数据信息层测试 (04-06模组)
3. 决策执行层测试 (07-10模组)
4. 指令支撑层测试 (11-14模组)
5. ZeroMQ通信测试
6. 性能监控
7. 报告生成
"""

import os
import sys
import json
import time
import logging
import subprocess
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import requests
import zmq
import psutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ntn_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class NTNTestSession:
    """NTN测试会话管理器"""
    
    def __init__(self):
        self.session_id = f"ntn_test_{int(time.time())}"
        self.start_time = datetime.now()
        self.results = {}
        self.performance_data = []
        self.errors = []
        
    def log_result(self, module: str, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        if module not in self.results:
            self.results[module] = []
        
        self.results[module].append({
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        status = "PASS" if success else "FAIL"
        logger.info(f"[{module}] {test_name}: {status} - {details}")
    
    def log_performance(self, metric: str, value: float, unit: str = ""):
        """记录性能数据"""
        self.performance_data.append({
            'metric': metric,
            'value': value,
            'unit': unit,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_error(self, error: str, context: str = ""):
        """记录错误"""
        self.errors.append({
            'error': error,
            'context': context,
            'timestamp': datetime.now().isoformat()
        })
        logger.error(f"Error in {context}: {error}")

class NTNModuleTester:
    """NTN模组测试器"""
    
    def __init__(self, session: NTNTestSession):
        self.session = session
        self.base_path = Path.cwd()
        self.modules = {
            '01APIForge': {'port': 8000, 'path': '01APIForge'},
            '02DataSpider': {'port': 5000, 'path': '02DataSpider'},
            '03ScanPulse': {'port': 8000, 'path': '03ScanPulse'},
            '04OptiCore': {'port': 8000, 'path': '04OptiCore'},
            '05-07TradeGuard': {'port': 8000, 'path': '05-07TradeGuard'},
            '08NeuroHub': {'port': 8000, 'path': '08NeuroHub'},
            '09MMS': {'port': 8000, 'path': '09MMS'},
            '10ReviewGuard': {'port': 8000, 'path': '10ReviewGuard'},
            '11ASTSConsole': {'port': 80, 'path': '11ASTSConsole'},
            '12TACoreService': {'port': 8000, 'path': '12TACoreService'},
            '13AIStrategyAssistant': {'port': 8000, 'path': '13AIStrategyAssistant'},
            '14ObservabilityCenter': {'port': 80, 'path': '14ObservabilityCenter'}
        }
    
    def test_basic_functionality(self) -> bool:
        """测试基础功能"""
        logger.info("开始基础功能测试...")
        all_passed = True
        
        for module_name, config in self.modules.items():
            try:
                # 检查模组目录
                module_path = self.base_path / config['path']
                if not module_path.exists():
                    self.session.log_result(module_name, "目录检查", False, f"目录不存在: {module_path}")
                    all_passed = False
                    continue
                
                self.session.log_result(module_name, "目录检查", True, "目录存在")
                
                # 检查Dockerfile
                dockerfile_path = module_path / "Dockerfile"
                if dockerfile_path.exists():
                    self.session.log_result(module_name, "Dockerfile检查", True, "Dockerfile存在")
                else:
                    self.session.log_result(module_name, "Dockerfile检查", False, "Dockerfile不存在")
                    all_passed = False
                
                # 检查主要源文件
                source_files = list(module_path.rglob("*.py")) + list(module_path.rglob("*.ts")) + list(module_path.rglob("*.tsx"))
                if source_files:
                    self.session.log_result(module_name, "源文件检查", True, f"找到{len(source_files)}个源文件")
                else:
                    self.session.log_result(module_name, "源文件检查", False, "未找到源文件")
                    all_passed = False
                
            except Exception as e:
                self.session.log_error(str(e), f"{module_name}基础功能测试")
                self.session.log_result(module_name, "基础功能测试", False, f"异常: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_docker_build(self, module_name: str) -> bool:
        """测试Docker构建"""
        try:
            module_config = self.modules[module_name]
            module_path = self.base_path / module_config['path']
            
            if not (module_path / "Dockerfile").exists():
                self.session.log_result(module_name, "Docker构建", False, "Dockerfile不存在")
                return False
            
            # 构建Docker镜像
            build_cmd = f"docker build -t ntn-{module_name.lower()} {module_path}"
            result = subprocess.run(build_cmd, shell=True, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.session.log_result(module_name, "Docker构建", True, "构建成功")
                return True
            else:
                self.session.log_result(module_name, "Docker构建", False, f"构建失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.session.log_result(module_name, "Docker构建", False, "构建超时")
            return False
        except Exception as e:
            self.session.log_error(str(e), f"{module_name} Docker构建")
            self.session.log_result(module_name, "Docker构建", False, f"异常: {str(e)}")
            return False
    
    def test_service_health(self, module_name: str, port: int) -> bool:
        """测试服务健康状态"""
        try:
            # 尝试连接健康检查端点
            health_urls = [
                f"http://localhost:{port}/health",
                f"http://localhost:{port}/api/health",
                f"http://localhost:{port}/"
            ]
            
            for url in health_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        self.session.log_result(module_name, "健康检查", True, f"服务正常 ({url})")
                        return True
                except requests.exceptions.RequestException:
                    continue
            
            self.session.log_result(module_name, "健康检查", False, "所有健康检查端点均无响应")
            return False
            
        except Exception as e:
            self.session.log_error(str(e), f"{module_name}健康检查")
            self.session.log_result(module_name, "健康检查", False, f"异常: {str(e)}")
            return False
    
    def test_zeromq_communication(self) -> bool:
        """测试ZeroMQ通信"""
        logger.info("开始ZeroMQ通信测试...")
        
        try:
            context = zmq.Context()
            
            # 测试REQ/REP模式
            socket = context.socket(zmq.REQ)
            socket.setsockopt(zmq.RCVTIMEO, 5000)  # 5秒超时
            socket.connect("tcp://localhost:5555")
            
            test_message = {
                "type": "test",
                "timestamp": datetime.now().isoformat(),
                "data": "ZeroMQ通信测试"
            }
            
            socket.send_json(test_message)
            response = socket.recv_json()
            
            socket.close()
            context.term()
            
            self.session.log_result("ZeroMQ", "REQ/REP通信", True, f"收到响应: {response}")
            return True
            
        except zmq.error.Again:
            self.session.log_result("ZeroMQ", "REQ/REP通信", False, "连接超时")
            return False
        except Exception as e:
            self.session.log_error(str(e), "ZeroMQ通信测试")
            self.session.log_result("ZeroMQ", "REQ/REP通信", False, f"异常: {str(e)}")
            return False

class NTNPerformanceMonitor:
    """NTN性能监控器"""
    
    def __init__(self, session: NTNTestSession):
        self.session = session
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """开始性能监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        logger.info("性能监控已启动")
    
    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("性能监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.session.log_performance("CPU使用率", cpu_percent, "%")
                
                # 内存使用率
                memory = psutil.virtual_memory()
                self.session.log_performance("内存使用率", memory.percent, "%")
                
                # 磁盘使用率
                disk = psutil.disk_usage('/')
                self.session.log_performance("磁盘使用率", disk.percent, "%")
                
                # 网络IO
                net_io = psutil.net_io_counters()
                self.session.log_performance("网络发送字节", net_io.bytes_sent, "bytes")
                self.session.log_performance("网络接收字节", net_io.bytes_recv, "bytes")
                
                time.sleep(10)  # 每10秒采集一次
                
            except Exception as e:
                self.session.log_error(str(e), "性能监控")
                time.sleep(5)

class NTNReportGenerator:
    """NTN报告生成器"""
    
    def __init__(self, session: NTNTestSession):
        self.session = session
    
    def generate_comprehensive_report(self) -> str:
        """生成综合报告"""
        report = []
        report.append("# NeuroTrade Nexus (NTN) 测试报告")
        report.append(f"\n**会话ID**: {self.session.session_id}")
        report.append(f"**开始时间**: {self.session.start_time.isoformat()}")
        report.append(f"**结束时间**: {datetime.now().isoformat()}")
        
        # 测试结果汇总
        report.append("\n## 测试结果汇总")
        total_tests = 0
        passed_tests = 0
        
        for module, tests in self.session.results.items():
            module_passed = sum(1 for test in tests if test['success'])
            module_total = len(tests)
            total_tests += module_total
            passed_tests += module_passed
            
            status = "✅" if module_passed == module_total else "❌"
            report.append(f"- {status} **{module}**: {module_passed}/{module_total} 通过")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        report.append(f"\n**总体通过率**: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        # 详细测试结果
        report.append("\n## 详细测试结果")
        for module, tests in self.session.results.items():
            report.append(f"\n### {module}")
            for test in tests:
                status = "✅" if test['success'] else "❌"
                report.append(f"- {status} {test['test_name']}: {test['details']}")
        
        # 性能数据
        if self.session.performance_data:
            report.append("\n## 性能数据")
            metrics = {}
            for data in self.session.performance_data:
                metric = data['metric']
                if metric not in metrics:
                    metrics[metric] = []
                metrics[metric].append(data['value'])
            
            for metric, values in metrics.items():
                avg_value = sum(values) / len(values)
                max_value = max(values)
                min_value = min(values)
                report.append(f"- **{metric}**: 平均 {avg_value:.2f}, 最大 {max_value:.2f}, 最小 {min_value:.2f}")
        
        # 错误汇总
        if self.session.errors:
            report.append("\n## 错误汇总")
            for error in self.session.errors:
                report.append(f"- **{error['context']}**: {error['error']}")
        
        return "\n".join(report)
    
    def generate_markdown_report(self, filename: str = None) -> str:
        """生成Markdown报告文件"""
        if filename is None:
            filename = f"ntn_test_report_{self.session.session_id}.md"
        
        report_content = self.generate_comprehensive_report()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"测试报告已生成: {filename}")
        return filename

def run_group_tests(test_type: str = "basic") -> NTNTestSession:
    """运行分组测试"""
    session = NTNTestSession()
    tester = NTNModuleTester(session)
    monitor = NTNPerformanceMonitor(session)
    
    logger.info(f"开始运行 {test_type} 测试组...")
    
    # 启动性能监控
    monitor.start_monitoring()
    
    try:
        if test_type == "basic":
            # 基础功能测试
            tester.test_basic_functionality()
            
        elif test_type == "zeromq":
            # ZeroMQ通信测试
            tester.test_zeromq_communication()
            
        elif test_type == "full":
            # 完整测试
            tester.test_basic_functionality()
            tester.test_zeromq_communication()
            
            # Docker构建测试（可选）
            for module_name in tester.modules.keys():
                tester.test_docker_build(module_name)
        
    finally:
        # 停止性能监控
        monitor.stop_monitoring()
    
    logger.info(f"{test_type} 测试组完成")
    return session

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NeuroTrade Nexus (NTN) 集成测试")
    parser.add_argument("--type", choices=["basic", "zeromq", "full"], default="basic",
                       help="测试类型 (默认: basic)")
    parser.add_argument("--report", action="store_true", help="生成测试报告")
    parser.add_argument("--output", help="报告输出文件名")
    
    args = parser.parse_args()
    
    # 运行测试
    session = run_group_tests(args.type)
    
    # 生成报告
    if args.report:
        generator = NTNReportGenerator(session)
        report_file = generator.generate_markdown_report(args.output)
        print(f"\n测试报告已生成: {report_file}")
    
    # 输出简要结果
    total_tests = sum(len(tests) for tests in session.results.values())
    passed_tests = sum(sum(1 for test in tests if test['success']) for tests in session.results.values())
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n测试完成: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")
    
    if session.errors:
        print(f"发现 {len(session.errors)} 个错误")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())