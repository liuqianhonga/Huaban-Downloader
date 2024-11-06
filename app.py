import gradio as gr
from downloader import HuabanDownloader
import time
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_board(board_id, cookie, save_dir=None, progress=gr.Progress()):
    """Gradio界面的下载函数"""
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
            # 构建图片标题
            desc = pin.get('raw_text', '无描述')
            source = f"[{pin['source']}]" if pin.get('source') else ''
            title = f"{desc} {source}"
            # 将图片URL和标题一起添加到预览列表
            preview_list.append((img_url, title))
            
            progress((i/total) * 0.9 + 0.1, f"下载图片 {i}/{total}...")
            
            try:
                save_path = downloader.download_image(pin, save_dir)
                status = "✅"
            except Exception as e:
                logger.error(f"下载失败: {str(e)}")
                status = "❌"
                
            # 更新标题以包含下载状态
            preview_list[-1] = (img_url, f"{title} {status}")
            time.sleep(0.1)  # 避免请求过快
            
        progress(1.0, desc="下载完成!")
        
        return (
            preview_list, 
            board_info,  # 只返回画板基本信息
            f"画板 [{board['title']}] 下载完成! 共下载 {len(pins)} 张图片，保存在 {save_dir}"
        )
        
    except Exception as e:
        error_msg = f"下载失败: {str(e)}"
        logger.error(error_msg)
        return [], error_msg, error_msg

def create_ui():
    with gr.Blocks(title="花瓣网画板下载器") as ui:
        gr.Markdown("# 花瓣网画板下载器")
        
        with gr.Row():
            board_id = gr.Textbox(
                label="画板ID",
                placeholder="请输入画板ID，例如: 94146939",
                info="可以从画板URL中获取"
            )
            cookie = gr.Textbox(
                label="Cookie",
                lines=3,
                placeholder="请输入Cookie",
                info="从浏览器开发者工具中复制"
            )
            save_dir = gr.Textbox(
                label="保存路径(可选)",
                placeholder="默认保存到 huaban/{board_id}",
                info="留空则使用默认路径"
            )
            
        download_btn = gr.Button("开始下载", variant="primary")
        
        with gr.Row():
            # 修改 Gallery 组件配置
            with gr.Column(scale=2):
                gallery = gr.Gallery(
                    label="图片预览",
                    columns=4,
                    rows=3,  # 设置每页显示的行数
                    height="600px",  # 增加高度
                    allow_preview=True,  # 允许点击预览大图
                    show_download_button=True,  # 显示下载按钮
                    object_fit="contain",  # 保持图片比例
                    show_label=True,  # 显示标题
                    elem_id="gallery"  # 添加元素ID
                )
            
            # 右侧只显示画板信息和状态
            with gr.Column(scale=1):
                board_info = gr.Markdown(label="画板信息", value="等待开始下载...")
                status = gr.Textbox(label="状态")
        
        download_btn.click(
            fn=download_board,
            inputs=[board_id, cookie, save_dir],
            outputs=[gallery, board_info, status]
        )
    
    return ui

if __name__ == "__main__":
    ui = create_ui()
    ui.launch(
        server_name="127.0.0.1",
        share=True,
        show_error=True
    )