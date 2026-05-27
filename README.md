# Claude Usage Monitor

Real-time Claude Code usage monitor. Shows the same data as the Claude app — current 5-hour session usage and weekly limit — directly below the input prompt while you chat.

**Works on:** macOS · Linux · WSL

> For Windows native (non-WSL), see [Claude-Code-Usage-Monitor](https://github.com/CodeZeno/Claude-Code-Usage-Monitor) which has a taskbar tray icon.

---

## What it looks like

**statusLine** — shown below the input prompt while chatting with Claude Code:

```
Claude: session 42% (in 3h 44m) · week 3% (in 6d 22h)
```

**Full live monitor** (optional, run manually in a separate terminal):

```
╭──────────────────────────── Claude Usage ─────────────────────────────╮
│                                                                        │
│   Current session           [████████░░░░░░░░░░░░]   42%  in 3h 44m  │
│   All models weekly limit   [█░░░░░░░░░░░░░░░░░░░]    3%  in 6d 22h  │
│                                                                        │
╰──────────────────────────── 15:02:37 · refreshes every 60s ───────────╯
```

---

## Install

```bash
git clone https://github.com/monfeecapital/claude-usage-monitor
cd claude-usage-monitor
chmod +x install.sh
./install.sh
```

Restart Claude Code — the statusLine appears automatically.

### Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (preferred) or `pip`
- Claude Code logged in (uses your existing auth token — no separate API key needed)

---

## How it works

Calls `https://api.anthropic.com/api/oauth/usage` using the OAuth token that Claude Code already stores in `~/.claude/.credentials.json`. No separate credentials needed.

The statusLine reads from a local cache file so it responds instantly without making a network request on every keypress. The cache refreshes every 5 minutes automatically.

---

## Running the live monitor manually

```bash
~/.claude/scripts/venv/bin/python3 ~/.claude/scripts/usage-monitor.py          # live, refreshes every 60s
~/.claude/scripts/venv/bin/python3 ~/.claude/scripts/usage-monitor.py --once   # print once and exit
~/.claude/scripts/venv/bin/python3 ~/.claude/scripts/usage-monitor.py --compact # one-line output (tmux etc.)
```

### tmux status bar

```tmux
set -g status-right "#($HOME/.claude/scripts/venv/bin/python3 $HOME/.claude/scripts/usage-monitor.py --compact)"
set -g status-interval 60
```

---

## Files installed

| File | Purpose |
|------|---------|
| `~/.claude/scripts/usage-monitor.py` | Main script |
| `~/.claude/scripts/venv/` | Python virtualenv (rich + requests) |
| `~/.claude/scripts/usage-cache.json` | Cache file (auto-created) |
| `~/.claude/statusline-command.sh` | Claude Code statusLine hook |

The installer also adds `statusLine` to `~/.claude/settings.json`.
