# Cloudflare 绕过工具 - 简化版

## 核心功能
这是一个简化版的 Cloudflare 人机验证绕过工具，只保留核心逻辑：

1. **循环检测** - 持续监控 VNC 界面
2. **识别验证** - 检测 Cloudflare 人机验证界面
3. **自动点击** - 向容器发送点击命令
4. **验证结果** - 检查是否通过验证

## 文件结构

### 核心文件
- `bypass_core.py` - 主入口文件，包含核心绕过逻辑
- `cloudflare_bypass_simplified.py` - 简化的检测和点击功能
- `cloudflare_bypass/cloudflare_detector.py` - Cloudflare 检测器类
- `cloudflare_bypass/images/` - 模板图像文件

### 已删除的文件
- `bypass_external.py` - 原始复杂版本
- `simple_container_click.py` - 独立的点击功能
- `cloudflare_bypass/auto.py` - 复杂的自动化逻辑
- `cloudflare_bypass/base_detector.py` - 基础检测器类
- `cloudflare_bypass/vnc_manager.py` - VNC 管理器

## 使用方法

### 1. 持续监控模式
```bash
python bypass_core.py
```

### 2. 单次绕过
```python
from bypass_core import bypass_cloudflare

success = bypass_cloudflare(max_attempts=5, timeout=30)
if success:
    print("绕过成功！")
```

### 3. 自定义检测
```python
from cloudflare_bypass_simplified import CloudflareDetector, send_click_to_container

detector = CloudflareDetector()
if detector.detect_cloudflare():
    x, y = calculate_click_position(detector.matched_bbox)
    send_click_to_container(x, y)
```

## 核心逻辑流程

```
开始监控
    ↓
检测 Cloudflare 验证
    ↓
计算点击位置
    ↓
发送点击命令到容器
    ↓
等待 5 秒
    ↓
检查验证是否通过
    ↓
成功 → 继续监控
失败 → 重新尝试
```

## 环境要求

- Python 3.6+
- OpenCV (`cv2`)
- Docker (用于容器点击)
- vncdo (用于 VNC 截图)
- xdotool (容器内点击工具)

## 配置

- VNC 主机: 通过环境变量 `VNC_HOST` 设置 (默认: 127.0.0.1)
- VNC 端口: 5900
- 容器名称: firefox (可在函数中修改)
- 检测阈值: 0.6 (可调整)

## 日志

程序会输出详细的日志信息，包括：
- 检测状态
- 点击操作
- 验证结果
- 错误信息