# 免费 API Key 申请链接（已验证）

> 最后检测：2026-06-19 · 运行 `scripts/check_links.sh` 可重新验证

**说明：** 带 🔐 的链接需在浏览器中**登录 Microsoft 账号**后使用；命令行检测可能显示 403，属正常现象。

---

## 必填（主方案）

| 步骤 | 链接 | 检测 | 免费额度 |
|------|------|------|----------|
| 1. 注册 Azure 账号 | https://azure.microsoft.com/free/ | ✅ 200 | 含 $200 试用额度（30 天） |
| 1b. 直接注册页（备用） | https://signup.azure.com/signup?offer=ms-azr-0044p | ✅ 200 | 同上 |
| 2. 创建 **Speech** 资源 (F0) | https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices | 🔐 浏览器 | **5 小时/月** 语音识别+翻译 |
| 3. 复制 Key | 创建后 → 资源页 → **Keys and Endpoint** | — | KEY 1 + Region |
| 定价说明（F0 免费层） | https://azure.microsoft.com/pricing/details/cognitive-services/speech-services/ | ✅ 200 | 确认选 Free F0 |

### 创建 Speech 资源时注意

- **Pricing tier** 必须选 **Free F0**（不是 Standard S0）
- **Region** 记下，填到 `keys.env` 的 `AZURE_SPEECH_REGION`（如 `canadacentral`）

---

## 可选（备用方案，第一版可不填）

| 服务 | 链接 | 检测 | 免费额度 |
|------|------|------|----------|
| Azure Translator (F0) | https://portal.azure.com/#create/Microsoft.CognitiveServicesTextTranslation | 🔐 浏览器 | **200 万字符/月** |
| Deepgram STT | https://console.deepgram.com/signup | ✅ 200 | **$200 赠金**（一次性，无需信用卡） |
| DeepL 翻译 API | https://www.deepl.com/pro-api | ✅ 200 | **50 万字符/月**（API Free） |
| DeepL 开发者文档 | https://developers.deepl.com/docs | ✅ 200 | — |

---

## 可选（Teams 系统音频）

| 工具 | 链接 / 命令 | 说明 |
|------|-------------|------|
| BlackHole 2ch | `brew install blackhole-2ch` | macOS 虚拟声卡，采 Teams 输出 |
| Homebrew | https://brew.sh | 未安装 brew 时先装 |

---

## 官方文档（排错参考）

| 文档 | 链接 | 检测 |
|------|------|------|
| Azure Speech 语音翻译快速入门 | https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-speech-translation | ✅ 200 |

---

## 填 Key 到项目

```bash
python3 scripts/setup_keys.py    # 交互填写
# 或编辑 keys.env
python3 -m src.main --check-keys # 验证
./start.sh                       # 启动
```

---

## 给朋友的一句话

> 克隆仓库 → `./scripts/setup.sh` → 按 [GETTING_STARTED.zh.md](GETTING_STARTED.zh.md) 用上面链接**自己**申请 Azure Speech 免费 Key → `./start.sh`

**切勿共用 Key，切勿把 `keys.env` 提交到 Git。**
