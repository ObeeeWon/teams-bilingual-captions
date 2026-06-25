# Teams Bilingual Captions

Real-time **EN → ZH** subtitles for Microsoft Teams on macOS.

## Quick start (any Mac)

```bash
git clone <your-repo-url> teams-bilingual-captions
cd teams-bilingual-captions
./scripts/setup.sh          # first time only
# edit keys.env — paste Azure keys (NOT synced via git)
./start.sh                  # one-click start (microphone)
```

Or **double-click** in Finder:
- `Start Captions.command` — microphone test
- `Start Teams Captions.command` — Teams system audio (BlackHole)

Running `python3 -m src.main` or `./run.sh` also works; `start.sh` is the simplest entry.

## Mac mini → MacBook workflow

| Step | Mac mini (dev) | MacBook (test) |
|------|----------------|----------------|
| Code | `git push` | `git clone` / `git pull` |
| Secrets | stays in local `keys.env` | copy `keys.env` manually (AirDrop / 1Password) |
| Setup | once: `./scripts/setup.sh` | once: `./scripts/setup.sh` |
| Run | `./run.sh --audio mic` | same |

**`keys.env` is gitignored** — never commit API keys. Use `keys.env.example` as template.

## Commands

| Command | Purpose |
|---------|---------|
| **`./start.sh`** | **One-click start (mic, recommended)** |
| `./start.sh teams` | Start with BlackHole system audio |
| `./scripts/setup.sh` | Full first-time install (venv, pip, keys template) |
| `./run.sh` | Bootstrap + run (pass any `src.main` flags) |
| `python3 -m src.main --check-keys` | Verify Azure keys & SDK |
| `python3 -m src.main --audio mic` | Live captions from microphone |
| `python3 -m src.main --audio blackhole` | Captions from Teams system audio |
| `python3 -m src.main --simulate --fast` | Demo without keys/audio |

## macOS prerequisites (Teams meetings)

1. **BlackHole** (virtual audio cable):
   ```bash
   brew install blackhole-2ch
   ```
2. **Audio MIDI Setup** → create Multi-Output Device (Speakers + BlackHole)
3. Set system output to Multi-Output Device
4. Run: `./run.sh --audio blackhole`

## Provider chain (free tiers)

1. Azure Speech Translation — 5 h/month
2. Deepgram + Azure Translator — backup
3. Deepgram + DeepL — backup
4. Hard stop before any paid usage

Configure keys in `keys.env`. See `config.yaml` for failover settings.

## Project layout

```
run.sh                 ← recommended entry
scripts/setup.sh       ← first-time machine setup
scripts/setup_keys.py  ← interactive key wizard
keys.env.example       ← committed template (safe)
keys.env               ← local secrets (gitignored)
src/bootstrap.py       ← auto-runs on app start
```

## Tests

```bash
python3 -m pytest -q
```
