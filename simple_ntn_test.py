#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroTrade Nexus (NTN) - 简化测试脚本
AI智能体驱动交易系统V1.2 - 快速验证专用

功能说明：
1. 基础文件系统检查
2. Docker配置验证
3. 模组状态检查
4. 简化报告生成
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class SimpleNTNTester:
    """简化NTN测试器"""
    
    def __init__(self):
        self.base_path = Path.cwd()
        self.results = {}
        self.modules = [
            '01APIForge',
            '02DataSpider', 
            '03ScanPulse',
            '04OptiCore',
            '05-07TradeGuard',
            '08NeuroHub',
            '09MMS',
            '10ReviewGuard',
            '11ASTSConsole',
            '12TACoreService',
            '13AIStrategyAssistant',
            '14ObservabilityCenter'
        ]
    
    def check_module_existence(self) -> Dict[str, bool]:
        """检查模组目录是否存在"""
        print("检查模组目录...")
        results = {}
        
        for module in self.modules:
            module_path = self.base_path / module
            exists = module_path.exists() and module_path.is_dir()
            results[module] = exists
            status = "✅" if exists else "❌"
            print(f"  {status} {module}: {'存在' if exists else '不存在'}")
        
        return results
    
    def check_docker_files(self) -> Dict[str, Dict[str, bool]]:
        """检查Docker相关文件"""
        print("\n检查Docker文件...")
        results = {}
        
        for module in self.modules:
            module_path = self.base_path / module
            if not module_path.exists():
                results[module] = {'dockerfile': False, 'compose': False}
                continue
            
            dockerfile_exists = (module_path / "Dockerfile").exists()
            compose_exists = (module_path / "docker-compose.yml").exists()
            
            results[module] = {
                'dockerfile': dockerfile_exists,
                'compose': compose_exists
            }
            
            docker_status = "✅" if dockerfile_exists else "❌"
            compose_status = "✅" if compose_exists else "❌"
            print(f"  {module}:")
            print(f"    {docker_status} Dockerfile")
            print(f"    {compose_status} docker-compose.yml")
        
        return results
    
    def check_source_files(self) -> Dict[str, Dict[str, int]]:
        """检查源文件"""
        print("\n检查源文件...")
        results = {}
        
        for module in self.modules:
            module_path = self.base_path / module
            if not module_path.exists():
                results[module] = {'python': 0, 'typescript': 0, 'other': 0}
                continue
            
            python_files = len(list(module_path.rglob("*.py")))
            ts_files = len(list(module_path.rglob("*.ts"))) + len(list(module_path.rglob("*.tsx")))
            other_files = len(list(module_path.rglob("*.*"))) - python_files - ts_files
            
            results[module] = {
                'python': python_files,
                'typescript': ts_files,
                'other': other_files
            }
            
            total = python_files + ts_files + other_files
            status = "✅" if total > 0 else "❌"
            print(f"  {status} {module}: {python_files} Python, {ts_files} TypeScript, {other_files} 其他 (总计: {total})")
        
        return results
    
    def check_global_files(self) -> Dict[str, bool]:
        """检查全局文件"""
        print("\n检查全局文件...")
        
        global_files = {
            'docker-compose.yml': self.base_path / 'docker-compose.yml',
            '.gitignore': self.base_path / '.gitignore',
            'README.md': self.base_path / 'README.md',
            'run_ntn_tests.py': self.base_path / 'run_ntn_tests.py',
            'nginx.conf': self.base_path / 'config' / 'nginx.conf',
            'redis.conf': self.base_path / 'config' / 'redis.conf'
        }
        
        results = {}
        for name, path in global_files.items():
            exists = path.exists()
            results[name] = exists
            status = "✅" if exists else "❌"
            print(f"  {status} {name}")
        
        return results
    
    def generate_summary(self, module_results: Dict, docker_results: Dict, 
                        source_results: Dict, global_results: Dict) -> str:
        """生成测试摘要"""
        print("\n" + "="*50)
        print("测试摘要")
        print("="*50)
        
        # 模组存在性统计
        existing_modules = sum(1 for exists in module_results.values() if exists)
        total_modules = len(module_results)
        print(f"模组目录: {existing_modules}/{total_modules} 存在")
        
        # Docker文件统计
        dockerfile_count = sum(1 for module_data in docker_results.values() if module_data['dockerfile'])
        compose_count = sum(1 for module_data in docker_results.values() if module_data['compose'])
        print(f"Dockerfile: {dockerfile_count}/{total_modules} 存在")
        print(f"docker-compose.yml: {compose_count}/{total_modules} 存在")
        
        # 源文件统计
        total_python = sum(data['python'] for data in source_results.values())
        total_typescript = sum(data['typescript'] for data in source_results.values())
        total_other = sum(data['other'] for data in source_results.values())
        print(f"源文件: {total_python} Python, {total_typescript} TypeScript, {total_other} 其他")
        
        # 全局文件统计
        global_existing = sum(1 for exists in global_results.values() if exists)
        total_global = len(global_results)
        print(f"全局文件: {global_existing}/{total_global} 存在")
        
        # 总体健康度
        health_score = (
            (existing_modules / total_modules) * 0.3 +
            (dockerfile_count / total_modules) * 0.3 +
            (global_existing / total_global) * 0.2 +
            (min(total_python + total_typescript, total_modules) / total_modules) * 0.2
        ) * 100
        
        print(f"\n总体健康度: {health_score:.1f}%")
        
        if health_score >= 80:
            print("状态: 良好 ✅")
        elif health_score >= 60:
            print("状态: 一般 ⚠️")
        else:
            print("状态: 需要修复 ❌")
        
        return f"{health_score:.1f}%"
    
    def generate_report(self, filename: str = None) -> str:
        """生成详细报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simple_ntn_test_report_{timestamp}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'simple_filesystem_check',
            'results': self.results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存: {filename}")
        return filename
    
    def run_all_checks(self) -> str:
        """运行所有检查"""
        print("NeuroTrade Nexus (NTN) - 简化测试")
        print("="*50)
        
        # 执行各项检查
        module_results = self.check_module_existence()
        docker_results = self.check_docker_files()
        source_results = self.check_source_files()
        global_results = self.check_global_files()
        
        # 保存结果
        self.results = {
            'modules': module_results,
            'docker_files': docker_results,
            'source_files': source_results,
            'global_files': global_results
        }
        
        # 生成摘要
        health_score = self.generate_summary(module_results, docker_results, source_results, global_results)
        
        return health_score

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NeuroTrade Nexus (NTN) 简化测试")
    parser.add_argument("--report", action="store_true", help="生成详细报告")
    parser.add_argument("--output", help="报告输出文件名")
    
    args = parser.parse_args()
    
    # 创建测试器并运行
    tester = SimpleNTNTester()
    health_score = tester.run_all_checks()
    
    # 生成报告
    if args.report:
        report_file = tester.generate_report(args.output)
        print(f"详细报告: {report_file}")
    
    # 根据健康度返回退出码
    health_value = float(health_score.rstrip('%'))
    if health_value >= 80:
        return 0  # 成功
    elif health_value >= 60:
        return 1  # 警告
    else:
        return 2  # 错误

if __name__ == "__main__":
    sys.exit(main())