#!/usr/bin/env bash
# Teams 双语字幕 — 一键启动
#
# 用法:
#   ./start.sh              麦克风模式（默认）
#   ./start.sh teams        Teams 系统音频（需 BlackHole）
#   ./start.sh setup        新用户：安装环境 + 检查配置
#
# macOS 双击: Start Captions.command
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "======================================"
echo "  Teams Bilingual Captions"
echo "======================================"

# 新用户引导模式
if [[ "${1:-}" == "setup" ]]; then
  chmod +x scripts/setup.sh scripts/check_setup.sh 2>/dev/null || true
  ./scripts/setup.sh
  echo ""
  echo "下一步: python3 scripts/setup_keys.py  填写 Azure Key"
  echo "然后:    ./start.sh"
  exit 0
fi

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

# 首次创建 keys.env
if [[ ! -f "keys.env" ]]; then
  if [[ -f "keys.env.example" ]]; then
    cp keys.env.example keys.env
  fi
  echo ""
  echo "[!] 新用户请先配置 Azure Key："
  echo "    1. 阅读 docs/GETTING_STARTED.zh.md"
  echo "    2. 申请链接 docs/FREE_API_LINKS.zh.md"
  echo "    3. 运行 python3 scripts/setup_keys.py"
  echo "    或编辑 $ROOT/keys.env"
  exit 1
fi

python3 -m src.bootstrap

# 密钥检查（占位符 / 空值会拦截并提示）
chmod +x scripts/check_setup.sh 2>/dev/null || true
if ! ./scripts/check_setup.sh; then
  exit 1
fi

MODE="${1:-mic}"
shift || true
case "$MODE" in
  teams|blackhole|system)
    AUDIO="blackhole"
    echo "[→] Teams 系统音频模式（需 BlackHole）· Ctrl+C 停止"
    ;;
  mic|microphone|*)
    AUDIO="mic"
    echo "[→] 麦克风模式 · 说英文测试 · Ctrl+C 停止"
    ;;
esac

echo ""
exec python3 -m src.main --audio "$AUDIO" "$@"
