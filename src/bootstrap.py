"""First-run bootstrap: deps, directories, keys template, macOS hints.

Called automatically when you run `python3 -m src.main` (unless --skip-bootstrap).
"""
from __future__ import annotations

import hashlib
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
KEYS_FILE = PROJECT_ROOT / "keys.env"
KEYS_EXAMPLE = PROJECT_ROOT / "keys.env.example"
STATE_DIR = PROJECT_ROOT / ".state"
DEPS_STAMP = STATE_DIR / ".deps_stamp"
HINT_STAMP = STATE_DIR / ".setup_hinted"

# Minimum packages needed for real (non-simulate) runs.
CORE_IMPORTS = [
    ("yaml", "pyyaml"),
    ("numpy", "numpy"),
    ("sounddevice", "sounddevice"),
    ("azure.cognitiveservices.speech", "azure-cognitiveservices-speech"),
]


def _run(cmd: List[str], quiet: bool = False) -> int:
    print(f"[setup] {' '.join(cmd)}", flush=True)
    return subprocess.call(
        cmd,
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.DEVNULL if quiet else None,
        stderr=subprocess.STDOUT if quiet else None,
    )


def _requirements_hash() -> str:
    if not REQUIREMENTS.exists():
        return ""
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()[:16]


def _missing_packages() -> List[Tuple[str, str]]:
    missing = []
    for module, pip_name in CORE_IMPORTS:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append((module, pip_name))
    return missing


def _ensure_directories() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_keys_file() -> None:
    if KEYS_FILE.exists():
        return
    if KEYS_EXAMPLE.exists():
        KEYS_FILE.write_text(KEYS_EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[setup] 已从模板创建 {KEYS_FILE.name}，请填入 API Key。", flush=True)
    else:
        KEYS_FILE.write_text(
            "AZURE_SPEECH_KEY=\nAZURE_SPEECH_REGION=canadacentral\n",
            encoding="utf-8",
        )
        print(f"[setup] 已创建空的 {KEYS_FILE.name}，请填入 API Key。", flush=True)


def _pip_install(requirements: bool = True) -> bool:
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
    _run(cmd, quiet=True)
    if requirements and REQUIREMENTS.exists():
        rc = _run([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)])
        if rc != 0:
            print("[setup] pip install 失败，请手动运行: pip install -r requirements.txt",
                  flush=True)
            return False
    return True


def _ensure_dependencies(force: bool = False) -> bool:
    stamp = _requirements_hash()
    if not force and DEPS_STAMP.exists():
        if DEPS_STAMP.read_text(encoding="utf-8").strip() == stamp:
            missing = _missing_packages()
            if not missing:
                return True

    missing = _missing_packages()
    if not missing and not force:
        DEPS_STAMP.write_text(stamp, encoding="utf-8")
        return True

    if missing:
        names = ", ".join(p for _, p in missing)
        print(f"[setup] 缺少依赖: {names}", flush=True)

    if not _pip_install():
        return False

    missing = _missing_packages()
    if missing:
        names = ", ".join(p for _, p in missing)
        print(f"[setup] 安装后仍缺少: {names}", flush=True)
        return False

    DEPS_STAMP.write_text(stamp, encoding="utf-8")
    print("[setup] Python 依赖已就绪。", flush=True)
    return True


def _macos_hints() -> None:
    if sys.platform != "darwin" or HINT_STAMP.exists():
        return
    print("[setup] macOS 提示:", flush=True)
    print("  · 麦克风测试: python3 -m src.main --audio mic", flush=True)
    print("  · Teams 系统音频: brew install blackhole-2ch → --audio blackhole", flush=True)
    print("  · 密钥: 编辑 keys.env（不随 git 同步，每台机器单独配置）", flush=True)
    HINT_STAMP.touch()


def ensure_ready(project_root: Optional[Path] = None, force_deps: bool = False,
                 quiet_hints: bool = False) -> bool:
    """Run all bootstrap steps. Returns False if setup failed critically."""
    root = project_root or PROJECT_ROOT
    os.chdir(root)
    _ensure_directories()
    _ensure_keys_file()
    ok = _ensure_dependencies(force=force_deps)
    if not quiet_hints:
        _macos_hints()
    return ok


def main() -> None:
    import argparse
    p = argparse.ArgumentParser(description="Bootstrap dependencies and config")
    p.add_argument("--force-deps", action="store_true", help="reinstall all requirements")
    args = p.parse_args()
    ok = ensure_ready(force_deps=args.force_deps)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
