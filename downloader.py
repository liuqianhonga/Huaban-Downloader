import os
import requests
import time
from pathlib import Path

class HuabanDownloader:
    def __init__(self):
        self.base_url = "https://huaban.com/v3"
        self.img_base_url = "https://gd-hbimg.huaban.com"
        
    def get_board_info(self, board_id, cookie):
        """获取画板信息"""
        try:
            headers = {
                "accept": "application/json",
                "cookie": cookie,
                "accept-language": "zh-CN,zh;q=0.9",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }
            
            url = f"{self.base_url}/boards/{board_id}?fields=board:BOARD_DETAIL"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            return resp.json()["board"]
        except Exception as e:
            raise Exception(f"获取画板信息失败: {str(e)}")
    
    def get_board_pins(self, board_id, cookie):
        """获取画板中的所有图片列表"""
        try:
            headers = {
                "accept": "application/json",
                "cookie": cookie,
                "accept-language": "zh-CN,zh;q=0.9",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }
            
            all_pins = []
            page_size = 100
            last_pin = None
            
            while True:
                # 构建URL，如果有last_pin则添加max参数
                url = f"{self.base_url}/boards/{board_id}/pins?limit={page_size}&fields=pins:PIN|board:BOARD_DETAIL|check"
                if last_pin:
                    url += f"&max={last_pin['pin_id']}"
                
                resp = requests.get(url, headers=headers, timeout=10)
                resp.raise_for_status()
                pins = resp.json()["pins"]
                
                if not pins:
                    break
                    
                all_pins.extend(pins)
                
                # 如果返回的数量小于page_size，说明已经是最后一页
                if len(pins) < page_size:
                    break
                    
                # 记录最后一个pin的ID，用于下一页请求
                last_pin = pins[-1]
                
                # 避免请求过快
                time.sleep(0.5)
            
            return all_pins
            
        except Exception as e:
            raise Exception(f"获取图片列表失败: {str(e)}")
    
    def download_image(self, file_info, save_dir):
        """下载单张图片"""
        try:
            key = file_info["file"]["key"]
            img_url = f"{self.img_base_url}/{key}"
            file_type = file_info["file"]["type"].split('/')[-1]
            
            # 创建保存目录
            os.makedirs(save_dir, exist_ok=True)
            
            # 构建文件名
            file_name = file_info.get('raw_text', key)[:50]  # 限制文件名长度
            file_name = "".join(c for c in file_name if c.isalnum() or c in (' ', '-', '_'))  # 移除非法字符
            save_path = os.path.join(save_dir, f"{file_name}_{key}.{file_type}")
            
            # 如果文件已存在，直接返回
            if os.path.exists(save_path):
                return save_path
                
            # 下载文件
            resp = requests.get(img_url, stream=True, timeout=10)
            resp.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for data in resp.iter_content(1024):
                    f.write(data)
                    
            return save_path
        except Exception as e:
            raise Exception(f"下载图片失败 {key}: {str(e)}")