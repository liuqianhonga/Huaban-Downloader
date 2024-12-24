import gradio as gr
from downloader import HuabanDownloader
import time
import os
import logging
from typing import Optional, Tuple, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_board(
    board_id: str,
    cookie: str,
    save_dir: Optional[str] = None,
    progress: gr.Progress = gr.Progress()
) -> Tuple[List[str], str, str]:
    """Gradio界面的下载函数
    
    Args:
        board_id: 画板ID
        cookie: Cookie字符串
        save_dir: 保存目录
        progress: 进度条对象
        
    Returns:
        tuple: (预览列表, 画板信息, 状态信息)
    """
    try:
        downloader = HuabanDownloader()
        
        # 获取画板信息
        progress(0, desc="获取画板信息...")
        board = downloader.get_board_info(board_id, cookie)
        
        # 显示画板基本信息
        board_info = f"""
### 画板信息
- 名称: {board['title']}
- 描述: {board['description'] or '无'}
- 图片数量: {board['pin_count']}
- 创建者: {board['user']['username']}
- 关注数: {board.get('follow_count', 0)}
- 更新时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(board['updated_at']))}
        """
        
        # 获取图片列表
        progress(0.1, desc="获取图片列表...")
        pins = downloader.get_board_pins(board_id, cookie)
        
        if not pins:
            raise ValueError("未找到任何图片")
            
        # 设置默认保存路径
        if not save_dir:
            save_dir = os.path.join("huaban", str(board_id))
            
        # 构建图片预览列表
        preview_list = []
        
        # 开始下载图片
        total = len(pins)
        for i, pin in enumerate(pins, 1):
            img_url = f"{downloader.img_base_url}/{pin['file']['key']}"
            progress((i/total) * 0.9 + 0.1, desc=f"下载图片 {i}/{total}...")
            
            try:
                save_path = downloader.download_image(pin, save_dir)
                # 将本地文件路径添加到预览列表
                preview_list.append(save_path)
            except Exception as e:
                logger.error(f"下载失败: {str(e)}")
            
            time.sleep(0.1)  # 避免请求过快
            
        progress(1.0, desc="下载完成!")
        
        return (
            preview_list,  # 返回本地文件路径列表
            board_info,
            f"画板 [{board['title']}] 下载完成! 共下载 {len(preview_list)}/{total} 张图片，保存在 {save_dir}"
        )
        
    except Exception as e:
        error_msg = f"下载失败: {str(e)}"
        logger.error(error_msg)
        return [], error_msg, error_msg

def create_ui() -> gr.Blocks:
    """创建Gradio界面"""
    with gr.Blocks(
        title="花瓣网画板下载器",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="blue",
        ),
    ) as ui:
        gr.Markdown(
            """
            # 花瓣网画板下载器
            轻松下载花瓣网画板中的所有图片。
            """
        )
        
        with gr.Row():
            board_id = gr.Textbox(
                label="画板ID",
                placeholder="请输入画板ID，例如: 94146939",
                info="可以从画板URL中获取",
                scale=1
            )
            cookie = gr.Textbox(
                label="Cookie",
                placeholder="请输入Cookie",
                info="从浏览器开发者工具中复制",
                lines=3,
                scale=2
            )
            save_dir = gr.Textbox(
                label="保存路径(可选)",
                placeholder="默认保存到 huaban/{board_id}",
                info="留空则使用默认路径",
                scale=1
            )
            
        download_btn = gr.Button(
            "开始下载",
            variant="primary",
            scale=1
        )
        
        with gr.Row(equal_height=True):
            with gr.Column(scale=2):
                gallery = gr.Gallery(
                    label="图片预览",
                    columns=4,
                    rows=None,  # 自动调整行数
                    height=600,
                    preview=True,
                    show_label=True,
                    show_share_button=False,
                    show_download_button=True,
                    elem_id="gallery"
                )
            
            with gr.Column(scale=1):
                board_info = gr.Markdown(
                    value="等待开始下载...",
                    elem_id="board-info"
                )
                status = gr.Textbox(
                    label="状态",
                    interactive=False,
                    elem_id="status"
                )
        
        download_btn.click(
            fn=download_board,
            inputs=[board_id, cookie, save_dir],
            outputs=[gallery, board_info, status],
            show_progress=True
        )
        
        # 添加使用说明
        gr.Markdown(
            """
            ### 使用说明
            1. 从花瓣网画板URL中获取画板ID
            2. 从浏览器开发者工具中复制Cookie
            3. 点击"开始下载"按钮
            4. 等待下载完成
            
            ### 注意事项
            - Cookie需要登录后获取
            - 下载速度取决于网络状况
            - 图片会按原始分辨率下载
            """
        )
    
    return ui

if __name__ == "__main__":
    ui = create_ui()
    ui.queue().launch(
        server_name="127.0.0.1",
        share=True,
        show_error=True,
        show_api=False,
        favicon_path="./screenshot/favicon.ico" if os.path.exists("./screenshot/favicon.ico") else None
    )