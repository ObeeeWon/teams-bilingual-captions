# 新用户指南（5 分钟上手）

把本仓库分享给朋友时，请让他们阅读本文。**代码可以免费克隆，但 API 密钥必须每人自己申请**（不能共用你的 `keys.env`）。

---

## 你需要准备什么

| 项目 | 是否必须 | 说明 |
|------|----------|------|
| **macOS 电脑** | ✅ | 目前仅支持 Mac（Sequoia / Sonoma 等） |
| **Microsoft Teams** | ✅ | 桌面版 |
| **Azure 账号 + Speech 免费资源** | ✅ | 每月 5 小时免费，需个人邮箱注册 |
| **Deepgram / DeepL** | ❌ | 可选备用方案，第一版可不填 |
| **BlackHole** | ⚠️ | 仅 Teams 会议采系统音频时需要；麦克风测试不需要 |

---

## 第一步：克隆项目

```bash
git clone https://github.com/ObeeeWon/teams-bilingual-captions.git
cd teams-bilingual-captions
```

---

## 第二步：一键安装环境

```bash
chmod +x start.sh scripts/setup.sh
./scripts/setup.sh
```

会自动：创建 Python 虚拟环境、安装依赖、生成 `keys.env` 模板。

> 若提示没有 `python3`，先安装 Xcode 命令行工具：`xcode-select --install`

---

## 第三步：申请 Azure Speech（每人独立账号）

**不能共用朋友的 Key**，否则额度算在他账上，且存在安全风险。

1. 注册 Azure（个人 Outlook/Gmail 即可）：  
   https://azure.microsoft.com/free/

2. 创建 **Speech** 资源（必须选 **Free F0**）：  
   https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices  
   - Region 建议：`canadacentral` 或离你最近的区域  
   - Resource group 随意新建，例如 `my-captions`

3. 进入资源 → **Keys and Endpoint**，复制：
   - `KEY 1` → 填入 `keys.env` 的 `AZURE_SPEECH_KEY`
   - `Location/Region` → 填入 `AZURE_SPEECH_REGION`（如 `canadacentral`）

4. （可选）创建 **Translator** 备用资源（Free F0）：  
   https://portal.azure.com/#create/Microsoft.CognitiveServicesTextTranslation

### 填写密钥（二选一）

**方式 A — 交互向导：**
```bash
python3 scripts/setup_keys.py
```

**方式 B — 手动编辑：**
```bash
open keys.env    # 或用 Cursor / 文本编辑器打开
```

---

## 第四步：验证配置

```bash
python3 -m src.main --check-keys
```

应看到：
```
Azure Speech 密钥: OK
Azure Speech SDK: 已安装
```

---

## 第五步：启动

### 麦克风测试（推荐第一次）

```bash
./start.sh
```

或双击 **`Start Captions.command`**

对着麦克风说英文，终端会出现：
```
EN  Hello everyone...
ZH  大家好……
```

按 **Ctrl+C** 停止。

### Teams 开会使用

1. 安装 BlackHole：`brew install blackhole-2ch`
2. 打开 **音频 MIDI 设置** → 创建「多输出设备」（扬声器 + BlackHole）
3. 系统输出选「多输出设备」
4. 启动：
   ```bash
   ./start.sh teams
   ```
   或双击 **`Start Teams Captions.command`**

---

## 常见问题

### Q: 启动后约 2 分钟就退出？
更新到最新代码：`git pull`。旧版有 120 秒限时；新版会一直运行直到 Ctrl+C。

### Q: 报错 `Invalid 'language'` / Error 1007？
`git pull` 获取最新代码（已修复语言码 `en-US` / `zh`）。

### Q: 报错 `keys.env` / 缺少密钥？
每人必须自己填 Azure Key，见第三步。

### Q: 会自动扣费吗？
默认 **不会**。免费额度用尽会弹窗并停止，不会静默扣费。Azure 创建资源时务必选 **F0 Free**。

### Q: Windows 能用吗？
目前不行，仅 macOS。

---

## 推荐给朋友时你可以这样说

> 1. 克隆：https://github.com/ObeeeWon/teams-bilingual-captions  
> 2. 运行 `./scripts/setup.sh`  
> 3. 自己注册 Azure Speech 免费层，把 Key 填进 `keys.env`  
> 4. `./start.sh` 测试  
> 详细步骤看仓库里的 `docs/GETTING_STARTED.zh.md`

---

## 相关链接

| 服务 | 注册 / 创建 |
|------|-------------|
| Azure 免费账号 | https://azure.microsoft.com/free/ |
| Azure Speech (F0) | https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices |
| Azure Translator (F0，可选) | https://portal.azure.com/#create/Microsoft.CognitiveServicesTextTranslation |
| Deepgram $200 赠金（可选） | https://console.deepgram.com/signup |
| BlackHole | `brew install blackhole-2ch` |
