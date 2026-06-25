# Teams Bilingual Captions

macOS 上 Microsoft Teams 会议的 **实时英→中双语字幕**工具。

**GitHub:** https://github.com/ObeeeWon/teams-bilingual-captions

---

## 新用户（朋友推荐来的）→ 从这里开始

**完整图文步骤：** [`docs/GETTING_STARTED.zh.md`](docs/GETTING_STARTED.zh.md)

```bash
git clone https://github.com/ObeeeWon/teams-bilingual-captions.git
cd teams-bilingual-captions
chmod +x start.sh scripts/setup.sh
./scripts/setup.sh                 # 第一次：安装环境
python3 scripts/setup_keys.py      # 填入你自己申请的 Azure Key
./start.sh                         # 启动（麦克风测试）
```

> **重要：** 每人需**自己注册 Azure 免费 Speech 资源**，不能共用 Key。  
> Azure 注册：https://azure.microsoft.com/free/  
> 创建 Speech (F0)：https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices

---

## 一键启动

| 方式 | 命令 |
|------|------|
| 终端 | `./start.sh` |
| Teams 会议 | `./start.sh teams`（需 BlackHole） |
| 双击 | `Start Captions.command` / `Start Teams Captions.command` |

按 **Ctrl+C** 停止。程序会一直运行，不会自动退出。

---

## 命令参考

| 命令 | 用途 |
|------|------|
| `./scripts/setup.sh` | 新机完整安装（venv + 依赖） |
| `./scripts/check_setup.sh` | 检查环境是否就绪 |
| `python3 scripts/setup_keys.py` | 交互式填写密钥 |
| `python3 -m src.main --check-keys` | 验证 Azure 配置 |
| `./start.sh teams` | Teams 系统音频（BlackHole） |
| `python3 -m src.main --simulate --fast` | 无密钥演示 |

---

## Teams 会议前置（BlackHole）

```bash
brew install blackhole-2ch
```

音频 MIDI 设置 → 多输出设备（扬声器 + BlackHole）→ 系统输出选多输出 → `./start.sh teams`

---

## 免费额度与安全

- Azure Speech F0：**5 小时/月**（主方案）
- Deepgram：**$200 一次性赠金**（可选备用）
- 额度用尽 → **弹窗并停止**，不会自动扣费
- `keys.env` **不会**随 Git 同步，请勿提交密钥

---

## 开发 / 测试

```bash
python3 -m pytest -q
```

---

## 推荐给朋友

直接发仓库链接 + 一句话：

> 克隆后运行 `./scripts/setup.sh`，按 `docs/GETTING_STARTED.zh.md` 申请 Azure 免费 Key，然后 `./start.sh` 即可。

English quick start: same flow; Azure Speech F0 free tier required per user.
