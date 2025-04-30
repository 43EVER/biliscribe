import re
import os
from .utils import exec_command, TempDir

def get_video_meta(video_url: str) -> str:
    out, code = exec_command(f"BBDown '{video_url}' -info")
    if code != 0:
        return f"[Error] 获取视频元数据失败：{out}"
    def find(pattern: str) -> str:
        m = re.search(pattern, out, re.MULTILINE)
        return m.group(1).strip() if m else "N/A"

    title = find(r"视频标题:\s*(.+)")
    pubtime = find(r"发布时间:\s*(.+)")
    return (
        "=== 视频元数据 ===\n"
        f"标题：{title}\n"
        f"发布时间：{pubtime}\n"
    )

def transcribe_audio(video_url: str) -> str:
    with TempDir(prefix="audio_") as workdir:
        # 1. 下载纯音频
        cmd1 = f"BBDown '{video_url}' --audio-only --work-dir {workdir} -F raw"
        out, code = exec_command(cmd1)
        if code != 0:
            return f"[Error] 下载音频失败：{out}"

        # 2. 找到文件并转成 wav
        src = os.path.join(workdir, os.listdir(workdir)[0])
        wav = os.path.join(workdir, "out.wav")
        out, code = exec_command(f"ffmpeg -y -i '{src}' '{wav}'")
        if code != 0:
            return f"[Error] ffmpeg 转码失败：{out}"

        # 3. whisperx 转写
        cmd3 = (
            "whisperx "
            f"--output_format=srt --output_dir={workdir} "
            f"--compute_type=int8 {wav} --verbose=False"
        )
        out, code = exec_command(cmd3)
        if code != 0:
            return f"[Error] WhisperX 转写失败：{out}"

        # 4. 读取 .srt
        srt = os.path.join(workdir, "out.srt")
        try:
            return open(srt, encoding="utf-8", errors="ignore").read()
        except Exception as e:
            return f"[Error] 读取转写结果失败：{e}"

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
