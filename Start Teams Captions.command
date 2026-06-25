#!/bin/bash
# 双击此文件启动 — Teams 会议模式（需已安装 BlackHole）
cd "$(dirname "$0")"
chmod +x start.sh 2>/dev/null || true
./start.sh teams
