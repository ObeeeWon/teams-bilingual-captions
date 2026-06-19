#!/usr/bin/env bash
# One-time / manual full setup on a new Mac (Mac mini or MacBook).
# Usage: ./scripts/setup.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "=== Teams Bilingual Captions — 环境安装 ==="
echo "项目目录: $ROOT"
echo ""

# 1. Python
if ! command -v python3 &>/dev/null; then
  echo "错误: 未找到 python3。请先安装 Xcode Command Line Tools:"
  echo "  xcode-select --install"
  exit 1
fi
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[1/5] Python $PY_VER"

# 2. Virtual env (recommended)
if [[ ! -d ".venv" ]]; then
  echo "[2/5] 创建虚拟环境 .venv …"
  python3 -m venv .venv
else
  echo "[2/5] 虚拟环境 .venv 已存在"
fi
# shellcheck disable=SC1091
source .venv/bin/activate

# 3. Python deps via bootstrap
echo "[3/5] 安装 Python 依赖 …"
python3 -m src.bootstrap --force-deps

# 4. keys.env
if [[ ! -f keys.env ]]; then
  echo "[4/5] 从模板创建 keys.env …"
  cp keys.env.example keys.env
  echo "      请编辑 keys.env 填入 Azure Key（MacBook 上需重新配置或手动复制）"
else
  echo "[4/5] keys.env 已存在，跳过"
fi

# 5. macOS extras
echo "[5/5] macOS 可选组件 …"
if [[ "$(uname)" == "Darwin" ]]; then
  if command -v brew &>/dev/null; then
    if ! brew list blackhole-2ch &>/dev/null 2>&1; then
      echo "      BlackHole 未安装。Teams 系统音频采集需要它:"
      echo "        brew install blackhole-2ch"
      echo "      安装后需在「音频 MIDI 设置」配置多输出设备。"
    else
      echo "      BlackHole 已安装 ✓"
    fi
  else
    echo "      未检测到 Homebrew。可选安装: https://brew.sh"
  fi
fi

echo ""
echo "=== 安装完成 ==="
echo ""
echo "验证密钥:  python3 -m src.main --check-keys"
echo "麦克风测试: python3 -m src.main --audio mic"
echo "或直接运行: ./run.sh --audio mic"
echo ""
