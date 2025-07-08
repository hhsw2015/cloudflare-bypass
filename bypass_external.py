from cloudflare_bypass import bypass
import time
import os

def main():
    target_url = os.getenv("TARGET_URL", "https://your-target-website.com")
    print(f"正在监控 VNC 画面: {target_url}")

    while True:
        bypassed = bypass(
            mode='light',
            warmup_time=5,
            timeout=30,
            interval=0.5,
            threshold=0.8
        )
        if bypassed:
            print("Cloudflare CAPTCHA 绕过成功！")
            with open("bypass_log.txt", "a") as log_file:
                log_file.write(f"{time.ctime()}: CAPTCHA 绕过成功\n")
            break
        else:
            print("未检测到 CAPTCHA 或绕过失败，继续监控...")
            with open("bypass_log.txt", "a") as log_file:
                log_file.write(f"{time.ctime()}: CAPTCHA 未检测到或绕过失败\n")
        time.sleep(5)

if __name__ == "__main__":
    main()
