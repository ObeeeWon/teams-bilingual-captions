#!/bin/bash
# 双击此文件在 macOS 终端中启动字幕程序（麦克风模式）
cd "$(dirname "$0")"
chmod +x start.sh 2>/dev/null || true
./start.sh mic
