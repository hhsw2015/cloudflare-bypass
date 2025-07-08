"""
VNC连接管理器 - 单例模式管理VNC连接，避免重复连接
"""
import logging
import time
import os
from vncdotool import api
from twisted.internet.error import ConnectionRefusedError

logger = logging.getLogger(__name__)

class VNCManager:
    """VNC连接管理器，使用单例模式"""
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VNCManager, cls).__new__(cls)
            cls._instance.vnc_host = os.getenv("VNC_HOST", "127.0.0.1")
            cls._instance.vnc_port = 5900
            cls._instance.vnc_password = None
        return cls._instance
    
    def get_client(self):
        """获取VNC客户端，如果连接断开则重新连接"""
        if self._client is None or not self._is_connected():
            self._connect()
        return self._client
    
    def _is_connected(self):
        """检查VNC连接是否有效"""
        try:
            if self._client and hasattr(self._client, 'transport'):
                return self._client.transport and self._client.transport.connected
        except:
            pass
        return False
    
    def _connect(self):
        """建立VNC连接"""
        if self._client and self._is_connected():
            logger.info("VNC连接已存在且有效")
            return
        
        # 断开现有连接
        if self._client:
            try:
                self._client.disconnect()
            except:
                pass
            self._client = None
        
        max_retries = 5
        retry_interval = 1
        
        for attempt in range(max_retries):
            try:
                logger.info(f"VNC连接尝试 {attempt + 1}/{max_retries}: {self.vnc_host}:{self.vnc_port}")
                self._client = api.connect(f"{self.vnc_host}:{self.vnc_port}", 
                                         password=self.vnc_password, timeout=10)
                logger.info("VNC连接成功")
                return
            except ConnectionRefusedError as e:
                logger.warning(f"VNC连接被拒绝 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
            except Exception as e:
                logger.error(f"VNC连接失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
        
        logger.error("无法建立VNC连接")
        raise RuntimeError(f"无法连接到VNC服务器 {self.vnc_host}:{self.vnc_port}")
    
    def disconnect(self):
        """断开VNC连接"""
        if self._client:
            try:
                self._client.disconnect()
            except:
                pass
            self._client = None
            logger.info("VNC连接已断开")

# 全局VNC管理器实例
vnc_manager = VNCManager()