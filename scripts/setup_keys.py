"""Interactive helper: paste API keys into keys.env.

    python3 scripts/setup_keys.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = ROOT / "keys.env"


def main() -> None:
    print("=== Teams Bilingual Captions — 密钥配置 ===\n")
    print(f"配置文件: {KEYS}\n")
    print("从 Azure portal 打开 teams-speech → Keys and Endpoint")
    print("复制 KEY 1 和 Region，粘贴到下面。\n")

    speech_key = input("AZURE_SPEECH_KEY (KEY 1): ").strip()
    region = input("AZURE_SPEECH_REGION [canadacentral]: ").strip() or "canadacentral"
    translator_key = input("AZURE_TRANSLATOR_KEY (可回车跳过): ").strip()
    deepgram_key = input("DEEPGRAM_API_KEY (可回车跳过): ").strip()

    content = f"""# 由 scripts/setup_keys.py 生成 — 请勿提交到 git

AZURE_SPEECH_KEY={speech_key}
AZURE_SPEECH_REGION={region}

AZURE_TRANSLATOR_KEY={translator_key}
AZURE_TRANSLATOR_REGION={region}

DEEPGRAM_API_KEY={deepgram_key}
DEEPGRAM_AUTOLOAD_DISABLED=1
"""
    KEYS.write_text(content, encoding="utf-8")
    print(f"\n已保存到 {KEYS}")
    print("验证: python3 -m src.main --check-keys")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
