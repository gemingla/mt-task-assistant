# 贡献指南

感谢你考虑为 MT Task Assistant 做出贡献！

## 如何贡献

### 报告 Bug

如果你发现了 bug，请在 [Issues](https://github.com/gemingla/mt-task-assistant/issues) 页面创建一个新的 issue，包含：

- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 系统环境（Windows 版本、Python 版本）

### 提交功能建议

欢迎提出新功能建议！请创建 issue 并描述：

- 功能描述
- 使用场景
- 实现思路（可选）

### 提交代码

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature-name`
3. 进行修改
4. 确保代码风格一致
5. 提交更改：`git commit -m "描述你的更改"`
6. 推送到分支：`git push origin feature/your-feature-name`
7. 创建 Pull Request

## 代码规范

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 编码规范
- 使用类型注解
- 添加必要的注释和文档字符串
- 保持代码简洁

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/gemingla/mt-task-assistant.git
cd mt-task-assistant

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

## 许可证

提交代码即表示你同意你的贡献将按照 MIT 许可证授权。
