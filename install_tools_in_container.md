# 容器内工具安装

在Firefox容器内安装必要的点击工具：

```bash
# 安装xdotool到Firefox容器
docker exec firefox sh -c "apk update && apk add xdotool"

# 验证安装
docker exec firefox which xdotool
```

安装完成后，Python程序就可以通过docker exec发送点击命令了。