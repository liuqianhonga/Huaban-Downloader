import os
import httpx
import time
from pathlib import Path
import random
import json

class HuabanDownloader:
    def __init__(self):
        self.base_url = "https://huaban.com/v3"
        self.img_base_url = "https://gd-hbimg.huaban.com"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.client = httpx.Client(verify=False, timeout=30)
        
    def _get_headers(self, cookie=None):
        """获取请求头"""
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": self.user_agent,
            "Referer": "https://huaban.com/",
            "Origin": "https://huaban.com"
        }
        if cookie:
            headers["Cookie"] = cookie
        return headers
        
    def get_board_info(self, board_id, cookie):
        """获取画板信息"""
        try:
            url = f"{self.base_url}/boards/{board_id}?fields=board:BOARD_DETAIL"
            resp = self.client.get(url, headers=self._get_headers(cookie))
            resp.raise_for_status()
            
            data = resp.json()
            if "board" not in data:
                raise Exception(f"API返回错误: {json.dumps(data, ensure_ascii=False)}")
                
            return data["board"]
        except Exception as e:
            raise Exception(f"获取画板信息失败: {str(e)}")
    
    def get_board_pins(self, board_id, cookie):
        """获取画板中的所有图片列表"""
        try:
            all_pins = []
            page_size = 100
            last_pin = None
            
            while True:
                url = f"{self.base_url}/boards/{board_id}/pins?limit={page_size}&fields=pins:PIN|board:BOARD_DETAIL|check"
                if last_pin:
                    url += f"&max={last_pin['pin_id']}"
                
                resp = self.client.get(url, headers=self._get_headers(cookie))
                resp.raise_for_status()
                
                data = resp.json()
                if "pins" not in data:
                    raise Exception(f"API返回错误: {json.dumps(data, ensure_ascii=False)}")
                    
                pins = data["pins"]
                if not pins:
                    break
                    
                all_pins.extend(pins)
                if len(pins) < page_size:
                    break
                    
                last_pin = pins[-1]
                time.sleep(0.5)  # 固定延迟
            
            return all_pins
            
        except Exception as e:
            raise Exception(f"获取图片列表失败: {str(e)}")
    
    def download_image(self, pin, save_dir):
        """下载单张图片"""
        try:
            file_info = pin["file"]
            key = file_info["key"]
            img_url = f"{self.img_base_url}/{key}"
            file_type = file_info["type"].split('/')[-1]
            
            # 创建保存目录
            os.makedirs(save_dir, exist_ok=True)
            
            # 构建文件名
            file_name = pin.get('raw_text', key)[:50]  # 限制文件名长度
            file_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_'))  # 移除非法字符
            save_path = os.path.join(save_dir, f"{file_name}_{key}.{file_type}")
            
            # 如果文件已存在，直接返回
            if os.path.exists(save_path):
                return save_path
                
            # 下载文件
            with self.client.stream("GET", img_url, headers=self._get_headers()) as resp:
                resp.raise_for_status()
                with open(save_path, 'wb') as f:
                    for chunk in resp.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                    
            return save_path
            
        except Exception as e:
            raise Exception(f"下载图片失败 [{img_url}]: {str(e)}")
            
    def __del__(self):
        """确保关闭客户端连接"""
        if hasattr(self, 'client'):
            self.client.close()