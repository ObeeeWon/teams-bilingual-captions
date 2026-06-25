#!/usr/bin/env bash
# 检查新用户环境是否就绪；start.sh 会自动调用
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0

echo "[check] Python …"
if ! command -v python3 &>/dev/null; then
  echo "  ✗ 未找到 python3 → xcode-select --install"
  FAIL=1
else
  echo "  ✓ $(python3 --version)"
fi

echo "[check] keys.env …"
KEYS="$ROOT/keys.env"
if [[ ! -f "$KEYS" ]]; then
  echo "  ✗ 不存在 → 运行 ./scripts/setup.sh 或 cp keys.env.example keys.env"
  FAIL=1
else
  # shellcheck disable=SC1090
  source "$KEYS" 2>/dev/null || true
  if [[ -z "${AZURE_SPEECH_KEY:-}" ]] || [[ "$AZURE_SPEECH_KEY" == *"粘贴"* ]] || [[ "$AZURE_SPEECH_KEY" == *"PASTE"* ]]; then
    echo "  ✗ AZURE_SPEECH_KEY 未填写"
    echo "    → python3 scripts/setup_keys.py"
    echo "    → 或阅读 docs/GETTING_STARTED.zh.md"
    FAIL=1
  elif [[ -z "${AZURE_SPEECH_REGION:-}" ]]; then
    echo "  ✗ AZURE_SPEECH_REGION 未填写（例如 canadacentral）"
    FAIL=1
  else
    echo "  ✓ Azure Speech Key 已配置"
  fi
fi

if [[ $FAIL -eq 0 ]]; then
  echo "[check] Azure SDK …"
  if python3 -m src.main --check-keys 2>&1 | grep -q "Azure Speech 密钥: OK"; then
    echo "  ✓ 密钥与 SDK 验证通过"
  else
    python3 -m src.main --check-keys || true
    FAIL=1
  fi
fi

if [[ $FAIL -ne 0 ]]; then
  echo ""
  echo "=========================================="
  echo "  环境未就绪 — 新用户请看:"
  echo "  docs/GETTING_STARTED.zh.md"
  echo "=========================================="
  exit 1
fi

echo ""
echo "[check] 全部通过，可以 ./start.sh 启动"
exit 0
