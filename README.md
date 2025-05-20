[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/mcp-server-summary/biliscribe)

---

# biliscribe

A MCP Server that extracts and formats Bilibili video content into structured text, optimized for LLM processing and analysis.

一个 MCP Server，将 B站视频转成文字，给大模型总结。

I have only completed testing on macOS. Before running this MCP Server, you need to ensure that ffmpeg can be called from your shell environment.

我只在 macOS 上完成了测试。在运行此 MCP 服务器之前，您需要确保可以从命令行环境调用 ffmpeg。

## Installation 安装

You can install the `mcp-server-biliscribe` package using `uvx`:<br/>
您可以使用 `uvx` 安装 `mcp-server-biliscribe` 包：

```bash
uvx mcp-server-biliscribe
```

## Prerequisites 前置条件

Before using this service, you need to prepare:<br/>
在使用此服务之前，您需要准备：

1. Cloudflare R2 access credentials - for storing audio data<br/>
   Cloudflare R2 访问凭据 - 用于存储音频数据

2. Replicate API Key - for whisperx calling<br/>
   Replicate API Key - 用于 whisperx 调用

## Environment Variables 环境变量

You need to set the following environment variables:<br>
您需要设置以下环境变量：

```
REPLICATE_API_TOKEN=r8_THIS_IS_REPLICATE_API_KEY
S3_API_ENDPOINT=https://this_is_s3_api_endpoint.r2.cloudflarestorage.com
BUCKET_NAME=this_is_your_bucket_name
ACCESS_KEY=THIS_IS_YOUR_S3_AK
SECRET_KEY=THIS_IS_YOUR_S3_SK
```

## Communication Protocols 通信协议

This server supports two communication protocols:<br/>
该服务器支持两种通信协议：

- Standard I/O (stdio) - default<br/>
  标准输入/输出 (stdio) - 默认

- Server-Sent Events (SSE)<br/>
  服务器发送事件 (SSE)

You can control the protocol using the environment variable `BILISCRIBE_SERVER_SSE`. Set it to `true` to enable SSE mode.<br/>
您可以使用环境变量 `BILISCRIBE_SERVER_SSE` 控制协议。将其设置为 `true` 以启用 SSE 模式。
