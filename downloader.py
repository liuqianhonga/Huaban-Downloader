import os
import requests
import time
from pathlib import Path
import random
import json

class HuabanDownloader:
    def __init__(self):
        self.base_url = "https://huaban.com/v3"
        self.img_base_url = "https://gd-hbimg.huaban.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
    def _get_headers(self, cookie):
        """获取请求头"""
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cookie": cookie,
            "User-Agent": random.choice(self.user_agents),
            "Referer": "https://huaban.com/",
            "Origin": "https://huaban.com",
            "X-Requested-With": "XMLHttpRequest",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        
    def get_board_info(self, board_id, cookie):
        """获取画板信息"""
        try:
            headers = self._get_headers(cookie)
            url = f"{self.base_url}/boards/{board_id}?fields=board:BOARD_DETAIL"
            
            # 先发送一个 OPTIONS 请求
            requests.options(url, headers=headers, timeout=10)
            
            # 然后发送 GET 请求
            resp = requests.get(url, headers=headers, timeout=10)
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
            headers = self._get_headers(cookie)
            all_pins = []
            page_size = 100
            last_pin = None
            
            while True:
                url = f"{self.base_url}/boards/{board_id}/pins?limit={page_size}&fields=pins:PIN|board:BOARD_DETAIL|check"
                if last_pin:
                    url += f"&max={last_pin['pin_id']}"
                
                # 先发送 OPTIONS 请求
                requests.options(url, headers=headers, timeout=10)
                
                # 然后发送 GET 请求
                resp = requests.get(url, headers=headers, timeout=10)
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
                time.sleep(random.uniform(0.5, 1.0))  # 随机延迟
            
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
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Referer": "https://huaban.com/"
            }
            resp = requests.get(img_url, headers=headers, stream=True, timeout=10)
            resp.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for data in resp.iter_content(1024):
                    f.write(data)
                    
            return save_path
            
        except Exception as e:
            raise Exception(f"下载图片失败 [{img_url}]: {str(e)}")