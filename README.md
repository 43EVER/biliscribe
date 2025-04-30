# biliscribe

A MCP Server that extracts and formats Bilibili video content into structured text, optimized for LLM processing and analysis.

一个 MCP Server，将 B站视频转成文字，给大模型总结。

I have only completed testing on macOS. Before running this MCP Server, you need to ensure that BBDown, ffmpeg, and whisperx can be called from zsh.

我只在 macOS 上完成了测试。在运行此 MCP 服务器之前，您需要确保可以从 zsh 调用 BBDown、ffmpeg 和 whisperx。

## Installation

You can install the `mcp-server-biliscribe` package using `uvx`:
您可以使用 `uvx` 安装 `mcp-server-biliscribe` 包：

```bash
uvx mcp-server-biliscribe
```
