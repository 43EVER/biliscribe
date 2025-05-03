import re
import os
from mcp_server_biliscribe.utils import exec_command, TempDir, float_sec_to_hhmmss
import aiohttp
import asyncio
import hashlib
import boto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError
from yt_dlp import YoutubeDL
import json

def get_yt_dlp_config() -> dict:
    return {
        "verbose": False,
        "quiet": True,
        "format": "mp3/bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        }],
        "allow_multiple_audio_streams": True,
    }

async def get_video_meta(video_url: str) -> str:
    """
    从视频 URL 中提取出 meta

    >>> from mcp_server_biliscribe.process import get_video_meta
    >>> import asyncio
    >>> video_url = "https://www.bilibili.com/video/BV1giGzzLEZr"
    >>> result = asyncio.run(get_video_meta(video_url))
    >>> "[Error]" not in result
    True
    """
    
    with YoutubeDL(get_yt_dlp_config()) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            json_info = ydl.sanitize_info(info)
            title = json_info.get("title", "未知标题")
            uploader = json_info.get("uploader", "未知上传者")
            description = json_info.get("description", "未知描述")
            tags = json_info.get("tags", "未知标签")
            tags = ", ".join(tags) if isinstance(tags, list) else tags
        except Exception as e:
            return f"[Error] 获取视频元数据失败：{e}"
    
    return f"""
    === 视频元数据 ===
    标题：{title}
    上传者：{uploader}
    视频简介：{description}
    标签：{tags}
    """

async def transcribe_audio(video_url: str) -> str:
    """
    使用 yt-dlp 下载音频并转写为文本

    >>> from mcp_server_biliscribe.process import transcribe_audio_by_ytdlp
    >>> import asyncio
    >>> video_url = "https://www.bilibili.com/video/BV1giGzzLEZr"
    >>> "Error" not in asyncio.run(transcribe_audio_by_ytdlp(video_url))
    True
    """

    # 下载纯音频
    with TempDir(prefix="audio_") as workdir:
        ydl_opts = get_yt_dlp_config()
        ydl_opts["outtmpl"] = os.path.join(workdir, "raw")
        with YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([video_url])
            except Exception as e:
                return f"[Error] 下载音频失败：{e}"
        
        # upload to R2 storage
        dst = os.path.join(workdir, "raw.mp3")
        public_url = upload_file_to_s3(dst)
        if "[Error]" in public_url:
            return public_url

        # 4. whisperx 转写
        text = await audio_to_text(public_url)
        if "[Error]" in text:
            return text
        
        return f"=========\n音频转写结果：\n{text}\n=========\n\n\n"

def upload_file_to_s3(file_path: str) -> str:
    """
    上传文件到 S3，并返回预签名 URL

    >>> from mcp_server_biliscribe.process import upload_file_to_s3
    >>> import asyncio
    >>> file_path = "/Users/r3v334/Desktop/output.mp3"
    >>> "[Error]" not in upload_file_to_s3(file_path)
    True
    """

    S3_API_URL = os.getenv("S3_API_ENDPOINT")
    BUKKET_NAME = os.getenv("BUCKET_NAME")
    ACCESS_KEY = os.getenv("ACCESS_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    # 1. 检查环境变量
    if not all([S3_API_URL, BUKKET_NAME, ACCESS_KEY, SECRET_KEY]):
        return "[Error] S3 环境变量未设置"

    config = Config(
        signature_version='s3v4',  # 使用S3v4签名版本，更好地支持安全令牌
        s3={'addressing_style': 'path'}  # 使用路径风格的URL
    )
    s3_client = boto3.client(
        's3',
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        endpoint_url=S3_API_URL,
        region_name="us-east-1",
        config=config,
    )

    # file content md5 as fileid
    with open(file_path, "rb") as f:
        file_content = f.read()
        file_md5 = hashlib.md5(file_content).hexdigest()
        file_id = f"audio_trans_{file_md5}.mp3"

    try:
        s3_client.upload_file(
            file_path,
            BUKKET_NAME,
            file_id,
            ExtraArgs={
                "ContentType": "audio/mpeg",
            }
        )

        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": BUKKET_NAME,
                "Key": file_id
            },
            ExpiresIn=1800 # 30 minutes
        )

    except FileNotFoundError:
        return f"[Error] 文件未找到：{file_path}"
    except NoCredentialsError:
        return "[Error] AWS 凭证错误"
    except Exception as e:
        return f"[Error] 上传文件失败：{e}"

    return presigned_url

async def audio_to_text(audio_file_url: str) -> str:
    """
    使用 WhisperX 将音频文件转写为文本

    >>> from mcp_server_biliscribe.process import audio_to_text
    >>> import asyncio
    >>> audio_file_url = "https://pub-ccdd0b3fa98d499aaab6051235856797.r2.dev/output.mp3"
    >>> "[Error]" not in asyncio.run(audio_to_text(audio_file_url))
    True
    """
    url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Bearer {os.getenv('REPLICATE_API_TOKEN')}",
        "Content-Type": "application/json",
    }
    data = {
        "version": "84d2ad2d6194fe98a17d2b60bef1c7f910c46b2f6fd38996ca457afd9c8abfcb",
        "input": {
            "debug": False,
            "vad_onset": 0.5,
            "audio_file": audio_file_url,
            "batch_size": 64,
            "vad_offset": 0.363,
            "diarization": False,
            "temperature": 0,
            "align_output": False,
            "language_detection_min_prob": 0,
            "language_detection_max_tries": 5
        }
    }

    try:
        # 发送请求
        async with aiohttp.ClientSession() as session:
            create_response = await session.post(url, headers=headers, json=data)
            if create_response.status == 201:
                tmp = await create_response.json()
                succ_url = tmp["urls"]["get"]
            else:
                return f"[Error] Replicate API 请求失败：{create_response.status} {await create_response.text()}"
            
            # 等待结果，最多 10 分钟
            for _ in range(600):
                reuslt_response = await session.get(succ_url, headers=headers)
                if reuslt_response.status != 200:
                    return f"[Error] Replicate API 请求失败：{reuslt_response.status} {await reuslt_response.text()}"
                result = await reuslt_response.json()
                if result["status"] == "succeeded":
                    break
                elif result["status"] in ["failed", "canceled"]:           
                    return f"[Error] Replicate API 请求失败：{result['error']}"
                await asyncio.sleep(1)

    except Exception as e:
        return f"[Error] Replicate API 请求失败：{e}"
        
    # 处理结果
    subs = []
    try:
        for seg in result["output"]["segments"]:
            # 秒转小时:分:秒
            start = int(seg["start"])
            end = int(seg["end"])
            text = seg["text"]

            start_time = float_sec_to_hhmmss(start)
            end_time = float_sec_to_hhmmss(end)
            subs.append(f"{start_time} --> {end_time}\n{text}\n")
    except Exception as e:
        return f"[Error] 处理转写结果失败：{e}"

    return "\n".join(subs)

def get_subtitles(video_url: str) -> str:
    with TempDir(prefix="sub_") as workdir:
        out, code = exec_command(
            f"BBDown '{video_url}' --sub-only --work-dir {workdir} -F raw"
        )
        if code != 0:
            return f"[Error] 获取字幕失败：{out}"
        subfile = os.path.join(workdir, os.listdir(workdir)[0])
        try:
            return open(subfile, encoding="utf-8", errors="ignore").read()
        except Exception as e:
            return f"[Error] 读取字幕文件失败：{e}"
