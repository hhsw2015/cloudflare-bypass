# Firefox Container CAPTCHA Bypass

这个项目专门为在Docker容器中运行的Firefox浏览器设计，用于自动绕过CloudFlare CAPTCHA验证。

## 🐳 容器设置

### 1. 启动Firefox容器

```bash
docker run -d \
    --name firefox \
    -p 5800:5800 \
    -p 5900:5900 \
    -v /root/firefox-data:/config:rw \
    -e TZ=Asia/Shanghai \
    -e LANG=zh_CN.UTF-8 \
    -e ENABLE_CJK_FONT=1 \
    --restart unless-stopped \
    jlesage/firefox
```

### 2. 设置容器工具

运行设置脚本（只需要运行一次）：
```bash
chmod +x setup_firefox_container.sh
./setup_firefox_container.sh
```

或者手动安装：
```bash
docker exec firefox sh -c "apk update && apk add xdotool xwininfo"
```

### 3. 测试设置

```bash
python3 test_firefox_container.py
```

## 🎯 使用方法

### 基本使用

```bash
python bypass_external.py
```

### 高级配置

如果需要自定义容器名称：
```python
from firefox_container_click import firefox_container_click
firefox_container_click.container_name = "your_container_name"
```

## 🔧 工作原理

1. **检测CloudFlare Logo**：使用模板匹配检测验证界面
2. **自适应定位**：根据屏幕分辨率计算最佳点击位置
3. **容器内点击**：通过docker exec在容器内执行xdotool命令
4. **验证结果**：检查Logo是否消失来确认验证成功

## 📊 技术特性

- ✅ **自适应屏幕分辨率**：自动适配不同分辨率
- ✅ **多种点击方法**：4种不同的点击策略
- ✅ **自动工具安装**：自动检测和安装必要工具
- ✅ **完整错误处理**：详细的日志和异常处理
- ✅ **容器专用**：专门为Docker环境优化

## 🛠️ 故障排除

### 容器未运行
```bash
docker ps --filter name=firefox
```

### xdotool未安装
```bash
docker exec firefox which xdotool
```

### 显示问题
```bash
docker exec -e DISPLAY=:0 firefox xwininfo -root
```

### 权限问题
确保Docker有足够权限访问容器。

## 📝 日志示例

```
2025-01-08 10:00:00,000 - INFO - xdotool is available in Firefox container
2025-01-08 10:00:01,000 - INFO - Logo detected at (596, 374)-(695, 431)
2025-01-08 10:00:02,000 - INFO - Using optimal position: (430, 376)
2025-01-08 10:00:03,000 - INFO - Clicking at position (430, 376) in Firefox container
2025-01-08 10:00:04,000 - INFO - Click executed successfully in Firefox container
2025-01-08 10:00:09,000 - INFO - SUCCESS! Verification passed!
```

## 🎯 成功率优化

- 确保Firefox窗口处于活动状态
- 确保网页完全加载
- 检查网络连接稳定性
- 验证容器内工具正常工作