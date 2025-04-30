"""
mcp_server_biliscribe 包的初始化文件。
只做最轻量的 API 暴露，不做启动逻辑。
"""

try:
    from importlib.metadata import version
    __version__ = version("mcp-server-biliscribe")
except Exception:
    __version__ = "0.0.0"

from .server import serve

def main():
    serve()

# 对外暴露的 API
from .process import get_subtitles, get_video_meta, transcribe_audio

# 控制 `from mcp_server_biliscribe import *` 时，哪些名字会被导入
__all__ = ["get_subtitles", "get_video_meta", "transcribe_audio", "__version__"]
