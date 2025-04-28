from mcp.server import FastMCP
from typing import Tuple

app = FastMCP("biliscribe",
                "A MCP Server that extracts and formats Bilibili video content into structured text, optimized for LLM processing and analysis.")

def exec_command(command: str) -> Tuple[str, int]:
    import subprocess

    try:
        # Create and execute the shell command with zsh
        cmd = f"source ~/.zshrc &&  {command}"
        # Run the command using zsh as the shell
        result = subprocess.run(['zsh', '-c', cmd], 
                                capture_output=True, 
                                text=True, 
                                check=True)
        return (result.stdout.strip(), result.returncode)
    
    except Exception as e:
        return (f"Unexpected error during audio processing: {str(e)}", -1)
    
async def get_bili_video_meta(video_url: str) -> str:
    """
    Retrieves metadata of a Bilibili video.
    
    Args:
        video_url (str): The URL(can also be av|bv|BV|ep|ss) of the Bilibili video to process.
    
    Returns:
        str: The metadata of the video.
    """
    import re

    bbdown_output, code = exec_command(f"BBDown '{video_url}' -info")
    if code != 0:
        return bbdown_output
    
    # 查找视频标题
    title_match = re.search(r"视频标题: (.+)$", bbdown_output, re.MULTILINE)
    title = title_match.group(1) if title_match else None
    
    # 查找发布时间
    time_match = re.search(r"发布时间: (.+)$", bbdown_output, re.MULTILINE)
    publish_time = time_match.group(1) if time_match else None
    
    return f"""
===视频元数据===
标题: {title}
发布时间: {publish_time}
    """

def get_audio_transcription(video_url: str) -> Tuple[str, int]:
    """
    Transcribes the audio of a Bilibili video using WhisperX.
    
    Args:
        video_url (str): The URL(can also be av|bv|BV|ep|ss) of the Bilibili video to process.
    
    Returns:
        str: The transcribed text from the audio.
    """

    import random
    import os

    # 1. Download audio from the Bilibili video and save it to a temporary folder
    # 2. Generate a random folder name
    random_folder = f"/tmp/audio_{random.randint(1000, 9999)}"
    # 3. Create the folder
    os.makedirs(random_folder, exist_ok=True)
    # 4. Download the audio
    out, code = exec_command(f"BBDown '{video_url}' --audio-only --work-dir {random_folder} -F raw")
    if code != 0:
        return (out, code)

    # 5. Get the audio file name, assuming it's the first one in the folder
    audio_file = os.path.join(f'{random_folder}', os.listdir(f'{random_folder}')[0])

    # 6. Transcribe the audio to .wav using ffmpeg
    out, code = exec_command(f"ffmpeg -i '{audio_file}' '{random_folder}/out.wav'")
    if code != 0:
        return (out, code)

    # 7. using whisperx to transcribe the audio
    out, code = exec_command(f"pyenv shell 3.11.12 && whisperx --output_format=srt --output_dir={random_folder} --compute_type=int8 {random_folder}/out.wav --verbose=False")
    if code != 0:
        return (out, code)
    
    # 8. Read the transcription from the .srt file
    srt_file = f"{random_folder}/out.srt"
    with open(srt_file, 'r', encoding='utf-8') as f:
        transcription = f.read()

    # 9. Delete everything in the folder
    for file in os.listdir(random_folder):
        file_path = os.path.join(random_folder, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    
    # 10. Delete the folder
    os.rmdir(random_folder)

    return (transcription, 0)

def get_bili_video_sub(video_url: str) -> Tuple[str, int]:
    """
    Retrieves subtitles of a Bilibili video.
    
    Args:
        video_url (str): The URL(can also be av|bv|BV|ep|ss) of the Bilibili video to process.
    
    Returns:
        str: The subtitles of the video.
    """

    # 1. Make random folder
    import random
    import os
    random_folder = f"/tmp/sub_{random.randint(1000, 9999)}"
    os.makedirs(random_folder, exist_ok=True)

    # 1. Get the subtitles using BBDown
    out, code = exec_command(f"BBDown '{video_url}' --sub-only --work-dir {random_folder} -F raw")
    if code != 0:
        return (out, code)

    # 2. Get the subtitle file name, assuming it's the first one in the folder
    sub_file = os.path.join(f'{random_folder}', os.listdir(f'{random_folder}')[0])
    # 3. Read the subtitle file
    with open(sub_file, 'r', encoding='utf-8') as f:
        sub = f.read()
    # 4. Delete everything in the folder
    for file in os.listdir(random_folder):
        file_path = os.path.join(random_folder, file)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    # 5. Delete the folder
    os.rmdir(random_folder)
    return (sub, 0)
            

@app.tool()
async def bili_scribe(video_url: str, use_audio: bool = True) -> str:
    """
    Extracts and formats Bilibili video content into structured text, optimized for LLM processing and analysis.
    
    Args:
        video_url (str): The URL(can also be av|bv|BV|ep|ss) of the Bilibili video to process.
        use_audio (bool): Whether to use audio for transcription. If False, only use subtitles generated by Bilibili.
    
    Returns:
        str: The formatted text content of the video.
    """

    # 1. Get Metadata of the Bilibili video
    metadata = await get_bili_video_meta(video_url)
    sub = '===内容转录===\n'

    if use_audio:
        # 2. Get audio transcription
        transcription, code = get_audio_transcription(video_url)
        if code != 0:
            return transcription
        sub += transcription
    else:
        # 3. Get subtitles
        videosub, code = get_bili_video_sub(video_url)
        if code != 0:
            return videosub
        sub += videosub

    return f"""
{metadata}

{sub}
"""

def serve():
    app.run(transport="stdio")