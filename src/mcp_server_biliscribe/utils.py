import subprocess
from typing import Tuple
import tempfile
import shutil

def exec_command(cmd: str, shell: str = "zsh") -> Tuple[str, int]:
    """
    统一命令执行函数，返回 stdout 和 returncode
    """
    try:
        res = subprocess.run(
            [shell, "-c", f"source ~/.{shell}rc && {cmd}"],
            capture_output=True, text=True, check=False
        )
        out, code = res.stdout.strip() or res.stderr.strip(), res.returncode
        return out, code
    except Exception as e:
        return str(e), -1

class TempDir:
    """
    上下文管理器：创建临时目录，退出自动删除
    """
    def __init__(self, prefix=""):
        self._tmp = tempfile.mkdtemp(prefix=prefix)

    def __enter__(self):
        return self._tmp

    def __exit__(self, exc_type, exc, tb):
        shutil.rmtree(self._tmp, ignore_errors=True)

def float_sec_to_hhmmss(seconds: float) -> str:
    """
    秒转小时:分:秒
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"