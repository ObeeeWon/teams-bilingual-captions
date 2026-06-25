#!/usr/bin/env bash
# Teams 双语字幕 — 一键启动
#
# 用法:
#   ./start.sh              麦克风模式（默认，测试用）
#   ./start.sh teams        Teams 系统音频（需 BlackHole）
#   ./start.sh mic          同上，显式指定麦克风
#
# macOS 也可双击: Start Captions.command
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "======================================"
echo "  Teams Bilingual Captions"
echo "  项目: $ROOT"
echo "======================================"

# 虚拟环境（setup.sh 创建后自动启用）
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

# 检查密钥
if [[ ! -f "keys.env" ]]; then
  if [[ -f "keys.env.example" ]]; then
    cp keys.env.example keys.env
    echo ""
    echo "[!] 已创建 keys.env，请先填入 Azure Key 后再启动。"
    echo "    文件: $ROOT/keys.env"
    exit 1
  fi
fi

# 安装缺失依赖
python3 -m src.bootstrap

# 音频模式
MODE="${1:-mic}"
shift || true
case "$MODE" in
  teams|blackhole|system)
    AUDIO="blackhole"
    echo ""
    echo "[→] 模式: Teams 系统音频 (BlackHole)"
    echo "    按 Ctrl+C 停止"
    ;;
  mic|microphone|*)
    AUDIO="mic"
    echo ""
    echo "[→] 模式: 麦克风"
    echo "    对着麦克风说英文，按 Ctrl+C 停止"
    ;;
esac

echo ""
exec python3 -m src.main --audio "$AUDIO" "$@"
