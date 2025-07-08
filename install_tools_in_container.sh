#!/bin/bash
# 在Firefox容器中安装必要工具

echo "在Firefox容器中安装xdotool..."
docker exec firefox sh -c "apk update && apk add xdotool"
echo "工具安装完成！"