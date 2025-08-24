# 贡献指南

感谢您对 NeuroTrade Nexus (NTN) 项目的关注！我们欢迎所有形式的贡献，包括但不限于代码、文档、测试、问题报告和功能建议。

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)
- [问题报告](#问题报告)
- [功能请求](#功能请求)
- [测试指南](#测试指南)
- [文档贡献](#文档贡献)

## 行为准则

本项目采用 [Contributor Covenant](https://www.contributor-covenant.org/) 行为准则。参与本项目即表示您同意遵守其条款。

### 我们的承诺

- 使用友好和包容的语言
- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

## 如何贡献

### 贡献类型

1. **代码贡献**
   - 修复 bug
   - 实现新功能
   - 性能优化
   - 代码重构

2. **文档贡献**
   - 改进现有文档
   - 添加缺失的文档
   - 翻译文档
   - 示例代码

3. **测试贡献**
   - 编写单元测试
   - 编写集成测试
   - 改进测试覆盖率
   - 性能测试

4. **其他贡献**
   - 报告 bug
   - 提出功能请求
   - 代码审查
   - 社区支持

## 开发环境设置

### 前置要求

- **操作系统**: Ubuntu 20.04+ / macOS 10.15+ / Windows 10+
- **Python**: 3.8+
- **Node.js**: 16+
- **Docker**: 20.10+
- **Git**: 2.25+

### 环境配置

1. **Fork 并克隆仓库**
```bash
# Fork 仓库到您的 GitHub 账户
# 然后克隆您的 fork
git clone https://github.com/YOUR_USERNAME/NeuroTrade-Nexus-NTN.git
cd NeuroTrade-Nexus-NTN

# 添加上游仓库
git remote add upstream https://github.com/wufayuzhi/NeuroTrade-Nexus-NTN.git
```

2. **创建开发分支**
```bash
git checkout -b feature/your-feature-name
```

3. **安装依赖**
```bash
# Python 依赖
pip install -r requirements-dev.txt

# Node.js 依赖（如果需要）
npm install

# 安装 pre-commit hooks
pre-commit install
```

4. **环境变量配置**
```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的环境变量
```

5. **验证环境**
```bash
# 运行测试确保环境正常
python -m pytest tests/

# 启动开发服务器
docker-compose up -d
```

## 代码规范

### Python 代码规范

- **风格指南**: 严格遵循 [PEP 8](https://pep8.org/)
- **类型注解**: 使用 Python 3.8+ 类型注解
- **文档字符串**: 使用 Google 风格的 docstring
- **导入顺序**: 使用 `isort` 自动排序
- **代码格式化**: 使用 `black` 自动格式化

```python
# 示例代码
from typing import Dict, List, Optional

def process_market_data(
    data: List[Dict[str, float]], 
    symbol: str,
    timeframe: Optional[str] = None
) -> Dict[str, float]:
    """处理市场数据。
    
    Args:
        data: 市场数据列表
        symbol: 交易品种代码
        timeframe: 时间周期，可选
        
    Returns:
        处理后的数据字典
        
    Raises:
        ValueError: 当数据格式不正确时
    """
    if not data:
        raise ValueError("数据不能为空")
    
    # 处理逻辑
    result = {"symbol": symbol, "count": len(data)}
    return result
```

### TypeScript 代码规范

- **严格模式**: 启用 TypeScript 严格模式
- **ESLint**: 使用项目配置的 ESLint 规则
- **Prettier**: 使用 Prettier 格式化代码
- **命名规范**: 使用 camelCase 命名变量和函数，PascalCase 命名组件

```typescript
// 示例代码
interface MarketData {
  symbol: string;
  price: number;
  timestamp: Date;
}

const processMarketData = (data: MarketData[]): number => {
  return data.reduce((sum, item) => sum + item.price, 0);
};

export const MarketDataComponent: React.FC<{ data: MarketData[] }> = ({ data }) => {
  const totalValue = processMarketData(data);
  
  return (
    <div className="market-data">
      <h2>市场数据</h2>
      <p>总价值: {totalValue}</p>
    </div>
  );
};
```

### 代码质量工具

```bash
# Python 代码检查
flake8 src/
mypy src/
black --check src/
isort --check-only src/

# TypeScript 代码检查
npm run lint
npm run type-check
npm run format:check
```

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交格式

```
type(scope): description

[optional body]

[optional footer(s)]
```

### 提交类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整（不影响功能）
- `refactor`: 代码重构（既不是新功能也不是修复）
- `perf`: 性能优化
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动
- `ci`: CI/CD 相关变更
- `build`: 构建系统或外部依赖变更

### 作用域（可选）

- `api`: API 相关
- `ui`: 用户界面
- `core`: 核心功能
- `config`: 配置相关
- `docs`: 文档
- `test`: 测试
- 模组名称：如 `apiforge`, `dataspider` 等

### 示例

```bash
# 好的提交信息
feat(apiforge): add rate limiting middleware
fix(dataspider): resolve memory leak in data processing
docs: update installation guide
test(core): add unit tests for risk management

# 不好的提交信息
update code
fix bug
add feature
```

## Pull Request 流程

### 1. 准备工作

```bash
# 确保您的分支是最新的
git checkout main
git pull upstream main
git checkout your-feature-branch
git rebase main
```

### 2. 代码检查

```bash
# 运行所有检查
make lint
make test
make type-check

# 或者使用 pre-commit
pre-commit run --all-files
```

### 3. 提交更改

```bash
git add .
git commit -m "feat(scope): your commit message"
git push origin your-feature-branch
```

### 4. 创建 Pull Request

1. 访问 GitHub 仓库页面
2. 点击 "New Pull Request"
3. 选择您的分支
4. 填写 PR 模板

### 5. PR 模板

```markdown
## 变更描述

简要描述此 PR 的变更内容。

## 变更类型

- [ ] Bug 修复
- [ ] 新功能
- [ ] 代码重构
- [ ] 文档更新
- [ ] 性能优化
- [ ] 测试改进

## 测试

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试完成
- [ ] 代码覆盖率满足要求

## 检查清单

- [ ] 代码遵循项目规范
- [ ] 提交信息符合规范
- [ ] 文档已更新（如需要）
- [ ] 测试已添加/更新
- [ ] 无破坏性变更（或已在描述中说明）

## 相关 Issue

Closes #issue_number

## 截图（如适用）

<!-- 添加截图或 GIF 展示变更效果 -->

## 额外说明

<!-- 任何需要审查者注意的额外信息 -->
```

### 6. 代码审查

- 至少需要一名维护者的批准
- 解决所有审查意见
- 确保 CI/CD 检查通过

## 问题报告

### 报告 Bug

使用 [Bug 报告模板](https://github.com/wufayuzhi/NeuroTrade-Nexus-NTN/issues/new?template=bug_report.md)：

1. **环境信息**
   - 操作系统
   - Python/Node.js 版本
   - 项目版本

2. **重现步骤**
   - 详细的操作步骤
   - 预期行为
   - 实际行为

3. **错误信息**
   - 完整的错误日志
   - 堆栈跟踪
   - 相关配置

4. **附加信息**
   - 截图或录屏
   - 相关代码片段
   - 可能的解决方案

## 功能请求

使用 [功能请求模板](https://github.com/wufayuzhi/NeuroTrade-Nexus-NTN/issues/new?template=feature_request.md)：

1. **功能描述**
   - 清晰的功能说明
   - 使用场景
   - 预期收益

2. **实现建议**
   - 可能的实现方案
   - 技术考虑
   - 兼容性影响

3. **替代方案**
   - 其他可能的解决方案
   - 现有的变通方法

## 测试指南

### 测试类型

1. **单元测试**
```bash
# 运行所有单元测试
pytest tests/unit/

# 运行特定模组测试
pytest tests/unit/test_apiforge.py

# 生成覆盖率报告
pytest --cov=src tests/
```

2. **集成测试**
```bash
# 运行集成测试
pytest tests/integration/

# 运行 Docker 集成测试
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

3. **端到端测试**
```bash
# 运行 E2E 测试
python run_ntn_tests.py

# 运行简化测试
python simple_ntn_test.py
```

### 测试要求

- **覆盖率**: 新代码至少 80% 测试覆盖率
- **测试命名**: 使用描述性的测试名称
- **测试隔离**: 每个测试应该独立运行
- **Mock 使用**: 适当使用 mock 隔离外部依赖

### 测试示例

```python
import pytest
from unittest.mock import Mock, patch

from src.apiforge.rate_limiter import RateLimiter

class TestRateLimiter:
    """速率限制器测试类。"""
    
    def test_should_allow_request_within_limit(self):
        """测试在限制范围内应该允许请求。"""
        # Given
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        
        # When
        result = limiter.is_allowed("user123")
        
        # Then
        assert result is True
    
    def test_should_deny_request_exceeding_limit(self):
        """测试超出限制应该拒绝请求。"""
        # Given
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("user123")  # 第一次请求
        
        # When
        result = limiter.is_allowed("user123")  # 第二次请求
        
        # Then
        assert result is False
    
    @patch('time.time')
    def test_should_reset_after_window_expires(self, mock_time):
        """测试时间窗口过期后应该重置。"""
        # Given
        mock_time.return_value = 1000
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        limiter.is_allowed("user123")
        
        # When
        mock_time.return_value = 1070  # 70秒后
        result = limiter.is_allowed("user123")
        
        # Then
        assert result is True
```

## 文档贡献

### 文档类型

1. **API 文档**: 使用 docstring 和 Sphinx
2. **用户指南**: Markdown 格式
3. **开发文档**: 技术设计和架构说明
4. **示例代码**: 实用的代码示例

### 文档规范

- 使用清晰、简洁的语言
- 提供实际的代码示例
- 包含必要的截图或图表
- 保持文档与代码同步

### 文档结构

```
docs/
├── api/                 # API 文档
├── guides/              # 用户指南
├── development/         # 开发文档
├── examples/            # 示例代码
└── assets/              # 图片和其他资源
```

## 发布流程

### 版本管理

我们使用 [语义化版本](https://semver.org/)：

- **主版本号**: 不兼容的 API 修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 发布步骤

1. 更新 `CHANGELOG.md`
2. 更新版本号
3. 创建 release 分支
4. 运行完整测试套件
5. 创建 Git tag
6. 发布到 GitHub Releases

## 社区支持

### 获取帮助

- **GitHub Issues**: 报告问题和请求功能
- **GitHub Discussions**: 社区讨论和问答
- **邮件**: [your-email@example.com]

### 贡献认可

我们会在以下地方认可贡献者：

- `CONTRIBUTORS.md` 文件
- 发布说明
- 项目 README
- 年度贡献者报告

## 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下授权。

---

再次感谢您的贡献！如果您有任何问题，请随时通过 GitHub Issues 或邮件联系我们。