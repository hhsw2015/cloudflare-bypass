# Cloudflare 人机验证自动绕过工具

这是一个简单的工具，用于自动检测和绕过 Cloudflare 人机验证。它会持续监控 VNC 屏幕，当检测到 Cloudflare 验证界面时，自动发送点击命令到容器中。

## 核心功能

1. **持续监控** - 循环检测 VNC 界面
2. **自动识别** - 检测 Cloudflare 人机验证
3. **自动点击** - 向容器发送点击命令
4. **验证结果** - 检查是否通过验证
5. **谷歌语音验证** - Cloudflare验证通过后自动检测并点击谷歌语音验证按钮

## 文件结构

- `cloudflare_monitor.py` - 核心监控和点击功能
- `images/` - 包含用于检测的模板图像
  - `cf_logo.png` - Cloudflare logo 图像 (亮色模式)
  - `cf_logo_dark.png` - Cloudflare logo 图像 (暗色模式)
  - `voice_button.png` - 谷歌语音验证按钮图像

## 使用方法

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 确保容器中已安装 xdotool
docker exec firefox2 sh -c 'apk update && apk add xdotool'
```

### 2. 运行监控

基本用法：
```bash
python cloudflare_monitor.py
```

命令行参数：
```bash
# 验证通过后自动退出程序
python cloudflare_monitor.py --exit

# 自定义检测间隔（秒）
python cloudflare_monitor.py --interval 5

# 自定义点击后等待验证的时间（秒）
python cloudflare_monitor.py --wait 10

# 自定义谷歌语音验证检测超时时间（秒）
python cloudflare_monitor.py --voice-timeout 60

# 启用调试模式（保存截图并显示详细检测信息）
python cloudflare_monitor.py --debug

# 仅检测谷歌语音按钮（调试模式）
python cloudflare_monitor.py --voice-only --debug

# 调整语音按钮点击位置（向左偏移20像素，向上偏移10像素）
python cloudflare_monitor.py --voice-only --debug --voice-offset-x -20 --voice-offset-y -10

# 组合使用
python cloudflare_monitor.py --exit --interval 2 --wait 8 --voice-timeout 45 --debug
```

### 3. 配置选项

可以通过环境变量自定义配置：

```bash
# 设置 VNC 主机地址
export VNC_HOST=192.168.1.100
# 设置容器名称
export CONTAINER_NAME=firefox2
# 运行监控
python cloudflare_monitor.py
```

## 工作原理

1. 每隔几秒捕获一次 VNC 屏幕截图
2. 使用模板匹配检测 Cloudflare 验证界面
3. 如果检测到验证界面，计算点击位置（logo 左侧 430 像素处）
4. 向容器发送点击命令
5. 等待几秒后再次检测，确认 Cloudflare 验证是否通过
6. **Cloudflare 验证通过后，自动检测谷歌语音验证按钮（30秒超时）**
7. **如果检测到语音按钮，点击按钮中心位置**
8. **完成所有验证后程序退出，或根据设置继续监控**

## 日志输出

程序会输出详细的日志信息，包括：
- 检测状态和置信度
- 点击位置和操作结果
- 验证结果
- 错误信息

## 自定义

如果需要调整点击位置或检测阈值，可以直接修改 `cloudflare_monitor.py` 文件中的相关参数：

- `self.threshold = 0.6` - 模板匹配阈值
- `click_x = 430` - 点击位置的 X 坐标
- `check_interval=3` - 检测间隔（秒）
- `verification_wait=5` - 点击后等待验证的时间（秒）