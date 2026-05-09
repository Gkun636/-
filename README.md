# 番茄钟 (Pomodoro Timer)

一个桌面番茄钟应用，基于 Python + tkinter 构建。

## 功能

- 🍅 工作时间倒计时（默认 25 分钟）
- ☕ 短休 / 🌴 长休自动切换
- 🔔 计时结束铃声 + 弹窗提醒
- ⚙ 自定义工作时长、休息时长、长休间隔
- 📌 窗口置顶
- 💾 配置自动保存到本地 JSON

## 运行

```bash
python pomodoro.py
```

或双击桌面 `番茄钟.bat`。

## 依赖

- Python 3（无需额外安装库，仅使用标准库 tkinter、threading、winsound、json）
- Windows 系统（winsound 为 Windows 专属）

## 分支

- `main` — Python tkinter 原版
- `webV` — 网页版（HTML/CSS/JS）
