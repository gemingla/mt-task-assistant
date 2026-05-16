# MT Task Assistant

<p align="center">
  <img src="images/mt520.png" alt="MT Task Assistant Logo" width="120">
</p>

<p align="center">
  <strong>🚀 智能任务管理桌面应用 - AI 驱动的高效时间管理助手</strong>
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#安装">安装</a> •
  <a href="#使用指南">使用指南</a> •
  <a href="#开发">开发</a> •
  <a href="#贡献">贡献</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/PyQt5-5.15+-green.svg" alt="PyQt5">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## 简介

MT Task Assistant 是一款基于人工智能的桌面任务管理应用，融合了自然语言处理、智能优先级排序、AI 对话助手等功能。通过直观的界面和强大的 AI 能力，帮助你高效管理日常任务、提升工作效率。

## ✨ 功能特性

### 📋 任务管理
- 任务创建、编辑、删除、状态追踪
- 支持截止时间、预估时长、优先级、标签
- 拖拽排序、搜索筛选

### 🧠 自然语言解析
- 智能识别 `明天下午3点开会 #工作 重要`
- 自动提取时间、优先级、标签

### 🤖 AI 智能助手
- 兼容 DeepSeek / OpenAI API
- 流式输出、上下文记忆
- 任务分析、周报生成

### ⏱️ 番茄钟
- 25分钟专注 + 5分钟休息
- 专注统计、任务关联

### 📅 日历视图
- 月历显示、任务标记
- 快速查看当日任务

### 🔔 提醒系统
- 定时提醒、重复提醒
- Windows 原生通知

### 🏆 成就系统
- 任务成就、连续打卡
- 积分累计、趣味成就

### 💾 数据管理
- 自动备份、数据恢复
- 本地存储、隐私安全

### 🎨 个性化
- 毛玻璃风格 UI
- 深色/浅色主题

## 📥 安装

### 方式一：直接下载（推荐）

前往 [Releases](https://github.com/your-username/mt-task-assistant/releases) 页面下载最新版本的安装包。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/your-username/mt-task-assistant.git
cd mt-task-assistant

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

### 依赖说明

| 依赖 | 用途 | 必需 |
|------|------|------|
| PyQt5 | GUI 框架 | ✅ |
| requests | HTTP 请求 | ✅ |
| winotify | Windows 通知 | 可选 |
| vosk | 语音输入 | 可选 |

## 📖 使用指南

### 首次运行

1. 启动程序后，按照欢迎向导完成初始配置
2. 在设置中配置 AI API（支持 DeepSeek、OpenAI 等兼容接口）

### 自然语言创建任务

开启"智能模式"后输入：

```
明天下午3点开会 #工作 重要
周五晚上看电影 #生活
后天早上8点跑步 半小时
紧急！今天下午5点前提交报告
```

### 快捷操作

- **双击任务名称** - 编辑任务
- **双击截止时间** - 修改时间
- **点击标签** - 修改/删除标签

### AI 助手

在 AI 对话框中：
- 询问任务建议
- 生成周报
- 分析任务优先级

## 🔧 开发

### 项目结构

```
mt-task-assistant/
├── main.py                 # 主程序入口
├── glass_style.py          # UI 样式系统
├── ai_client.py            # AI 客户端
├── task_manager.py         # 任务管理
├── memory_manager.py       # AI 记忆管理
├── achievement_manager.py  # 成就系统
├── reminder_manager.py     # 提醒管理
├── calendar_widget.py      # 日历组件
├── pomodoro_widget.py      # 番茄钟组件
├── nlp_task_parser.py      # 自然语言解析
├── backup_manager.py       # 数据备份
├── config.py               # 配置管理
├── utils.py                # 工具函数
└── requirements.txt        # 依赖列表
```

### 打包发布

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller mt_task_assistant.spec
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范

- 遵循 PEP 8
- 使用类型注解
- 添加必要的注释

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - GUI 框架
- [DeepSeek](https://deepseek.com/) - AI 模型支持
- 所有贡献者

---

<p align="center">
  如果这个项目对你有帮助，请给一个 ⭐️ Star！
</p>
