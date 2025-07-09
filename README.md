# Cloudflare 人机验证自动绕过工具

这是一个智能的工具，用于自动检测和绕过 Cloudflare 人机验证。它会持续监控 VNC 界面，使用 OCR 文字识别技术智能判断验证状态，并自动执行相应的操作。

## 核心功能

1. **智能检测** - 使用 OCR 识别验证状态和类型
2. **自动识别** - 检测 Cloudflare 和 Google reCAPTCHA 验证
3. **智能点击** - 根据验证类型执行不同的点击策略
4. **状态判断** - 准确判断验证成功、失败或进行中
5. **语音验证** - 使用固定坐标自动点击语音按钮并处理重试逻辑

## 系统要求

- **操作系统**: Linux (Ubuntu/Debian/CentOS 等)
- **Python**: 3.6 或更高版本
- **Docker**: 用于运行浏览器容器
- **VNC**: 用于屏幕截图和控制

## 完整安装指南

### 1. 系统依赖安装

#### Ubuntu/Debian 系统
```bash
# 更新系统包
sudo apt-get update

# 安装 Python 和 pip
sudo apt-get install python3 python3-pip

# 安装 OCR 引擎 (必需)
sudo apt-get install tesseract-ocr

# 安装 VNC 工具
sudo apt-get install vncdotool

# 验证安装
tesseract --version
vncdo --help
```

#### CentOS/RHEL 系统
```bash
# 安装 EPEL 仓库
sudo yum install epel-release

# 安装 Python 和 pip
sudo yum install python3 python3-pip

# 安装 OCR 引擎
sudo yum install tesseract

# 安装 VNC 工具
pip3 install vncdotool
```

### 2. Python 依赖安装

```bash
# 克隆或下载项目
cd cloudflare-bypass

# 创建虚拟环境 (推荐)
python3 -m venv myenv
source myenv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. Docker 容器配置

```bash
# 确保 Docker 容器正在运行 (假设容器名为 firefox2)
docker ps | grep firefox2

# 在容器中安装点击工具
docker exec firefox2 sh -c 'apk update && apk add xdotool'

# 验证容器中的工具
docker exec firefox2 xdotool --version
```

### 4. 验证安装

```bash
# 测试 OCR 功能
echo "Hello World" | tesseract stdin stdout

# 测试程序导入
python3 -c "
import cv2
import numpy as np
import pytesseract
print('✓ 所有依赖安装成功')
"
```

## 文件结构

- `cloudflare_monitor.py` - 主程序文件，包含所有功能
- `images/` - 检测模板图像目录
  - `cf_logo.png` - Cloudflare logo (亮色模式)
  - `cf_logo_dark.png` - Cloudflare logo (暗色模式)  
- `requirements.txt` - Python 依赖列表
- `README.md` - 使用说明

## 使用方法

### 基本用法

```bash
# 完整验证流程（验证完成后自动退出）
python3 cloudflare_monitor.py --exit

# 持续监控模式（验证完成后继续监控）
python3 cloudflare_monitor.py
```

### 调试模式

```bash
# 仅测试语音验证（使用固定坐标）
python3 cloudflare_monitor.py --voice-only --debug

# 坐标调试（移动鼠标到指定位置，不点击）
python3 cloudflare_monitor.py --move-to 735,985
```

### 高级参数

```bash
# 自定义检测间隔（秒）
python3 cloudflare_monitor.py --interval 5

# 自定义点击后等待时间（秒）
python3 cloudflare_monitor.py --wait 10

# 自定义语音验证检测超时时间（秒）
python3 cloudflare_monitor.py --voice-timeout 60

# 启用调试模式（保存截图并显示详细信息）
python3 cloudflare_monitor.py --debug

# 组合使用
python3 cloudflare_monitor.py --exit --interval 2 --wait 8 --voice-timeout 45 --debug
```

## 工作原理

### 验证检测顺序
1. **Cloudflare 验证** - 检测并点击 Cloudflare 人机验证
2. **等待界面加载** - 等待5秒让谷歌验证界面出现
3. **OCR 状态检测** - 使用文字识别判断当前验证状态
4. **智能响应** - 根据检测结果采取相应行动

### OCR 智能识别
程序使用 OCR 技术识别以下关键词：

#### 成功关键词
- `verification complete`, `verification successful`, `success`

#### 失败关键词  
- `multiple correct solutions required`, `please try again`, `incorrect`

#### 挑战关键词
- `select all squares`, `press play to listen`, `enter what you hear`

#### 验证对象
- `crosswalks`, `bicycles`, `motorcycles`, `traffic lights` 等

### 智能点击策略

#### 图像验证 → 语音验证
- 检测到 "Select all squares" 等图像验证
- 使用固定坐标 (735, 985) 自动点击语音按钮切换到语音验证

#### 语音验证失败 → 重新开始
- 检测到 "Press PLAY to listen" 但验证失败
- 自动点击重新开始按钮

#### 验证成功 → 停止
- 检测到成功关键词或无验证界面
- 自动停止验证流程

## 环境变量配置

```bash
# 设置 VNC 主机地址
export VNC_HOST=192.168.1.100

# 设置容器名称
export CONTAINER_NAME=firefox2

# 运行程序
python3 cloudflare_monitor.py --exit
```

## 故障排除

### 常见问题

#### 1. OCR 识别失败
```bash
# 检查 tesseract 是否安装
tesseract --version

# 重新安装 tesseract
sudo apt-get install --reinstall tesseract-ocr
```

#### 2. VNC 连接失败
```bash
# 检查 VNC 服务是否运行
vncdo -s 127.0.0.1::5900 capture test.png

# 检查防火墙设置
sudo ufw status
```

#### 3. 容器点击失败
```bash
# 检查容器是否运行
docker ps | grep firefox2

# 重新安装 xdotool
docker exec firefox2 sh -c 'apk update && apk add xdotool'
```

#### 4. 语音验证坐标调整
```bash
# 使用坐标调试功能确认语音按钮位置
python3 cloudflare_monitor.py --move-to 735,985

# 使用调试模式查看语音验证过程
python3 cloudflare_monitor.py --voice-only --debug
```

### 调试技巧

#### 查看 OCR 识别结果
```bash
# 启用调试模式查看 OCR 识别的文字
python3 cloudflare_monitor.py --debug
```

#### 测试点击位置
```bash
# 移动鼠标到指定位置确认坐标
python3 cloudflare_monitor.py --move-to 735,985
```

#### 查看语音验证调试
```bash
# 查看语音验证的详细过程和OCR识别结果
python3 cloudflare_monitor.py --voice-only --debug
```

## 性能优化

### 提高识别准确率
- 确保 VNC 分辨率足够高
- 使用稳定的网络连接
- 根据实际界面调整语音按钮坐标

### 减少资源消耗
- 适当增加检测间隔 `--interval`
- 在无验证时降低检测频率
- 使用 `--exit` 参数在完成后自动退出

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 免责声明

本工具仅供学习和研究目的使用，请遵守相关网站的服务条款和法律法规。