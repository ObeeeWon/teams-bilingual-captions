#!/usr/bin/env bash
# 验证文档中的免费 API 申请链接是否可访问
# Usage: ./scripts/check_links.sh
set -uo pipefail

echo "=== 免费 API 链接可用性检测 ==="
echo ""

# name|url|expect_pattern (optional, grep in body)
LINKS=(
  "Azure 免费注册|https://azure.microsoft.com/free/|"
  "Azure 注册直达|https://signup.azure.com/signup?offer=ms-azr-0044p|"
  "Azure Speech 定价|https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/|Free"
  "Azure Speech 创建|https://portal.azure.com/|"
  "Deepgram 注册|https://console.deepgram.com/signup|Deepgram"
  "DeepL API|https://www.deepl.com/pro-api|"
  "DeepL 文档|https://developers.deepl.com/docs|"
  "Microsoft 语音翻译文档|https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-speech-translation|Speech"
)

OK=0
WARN=0
FAIL=0

check_one() {
  local name="$1" url="$2" pattern="${3:-}"
  local code tmp
  tmp=$(mktemp)
  code=$(curl -sL -o "$tmp" -w "%{http_code}" --max-time 20 "$url" 2>/dev/null || echo "000")
  local status="FAIL"
  local note=""

  if [[ "$code" == "200" ]]; then
    if [[ -n "$pattern" ]] && ! grep -qi "$pattern" "$tmp" 2>/dev/null; then
      status="WARN"
      note="HTTP 200 但未匹配关键字: $pattern"
      ((WARN++)) || true
    else
      status="OK"
      ((OK++)) || true
    fi
  elif [[ "$code" == "403" ]] && [[ "$url" == *"portal.azure.com"* ]]; then
    status="OK"
    note="Portal 需浏览器登录（403 对脚本正常）"
    ((OK++)) || true
  elif [[ "$code" =~ ^[23] ]]; then
    status="WARN"
    note="HTTP $code"
    ((WARN++)) || true
  else
    status="FAIL"
    note="HTTP $code 或超时"
    ((FAIL++)) || true
  fi

  printf "  %-24s [%s] %s\n" "$status" "$code" "$name"
  [[ -n "$note" ]] && printf "      %s\n" "$note"
  rm -f "$tmp"
}

for entry in "${LINKS[@]}"; do
  IFS='|' read -r name url pattern <<< "$entry"
  check_one "$name" "$url" "$pattern"
done

echo ""
echo "结果: OK=$OK  WARN=$WARN  FAIL=$FAIL"
echo "完整链接列表: docs/FREE_API_LINKS.zh.md"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
exit 0
