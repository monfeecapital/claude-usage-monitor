# Claude Usage Monitor

Real-time Claude Code usage monitor for the terminal. Shows the same data as the Claude app — current 5-hour session usage and weekly limit — directly in your terminal.

**Works on:** macOS · Linux · WSL

> For Windows native (non-WSL), see [Claude-Code-Usage-Monitor](https://github.com/CodeZeno/Claude-Code-Usage-Monitor) which has a taskbar tray icon.

---

## What it looks like

**Live monitor** (`ccmon`):

```
╭──────────────────────────── Claude Usage ─────────────────────────────╮
│                                                                        │
│   Current session           [████████░░░░░░░░░░░░]   42%  in 3h 44m  │
│   All models weekly limit   [█░░░░░░░░░░░░░░░░░░░]    3%  in 6d 22h  │
│                                                                        │
╰──────────────────────────── 15:02:37 · refreshes every 60s ───────────╯
```

**Claude Code statusLine** (shown below the input prompt while chatting):

```
Claude: session 42% (in 3h 44m) · week 3% (in 6d 22h)
```

---

## Install

```bash
git clone https://github.com/monfeecapital/claude-usage-monitor
cd claude-usage-monitor
chmod +x install.sh
./install.sh
```

Then restart your terminal.

### Requirements

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) (preferred) or `pip`
- Claude Code logged in (the monitor reads your existing auth token — no separate API key needed)

---

## Usage

```bash
ccmon                  # live monitor, refreshes every 60s
ccmon --once           # print once and exit
ccmon --compact        # one-line output
ccmon --daemon         # background cache poller (for statusLine without ccmon running)
ccmon --interval 30    # custom refresh interval
```

### tmux status bar

Add to `~/.tmux.conf`:

```tmux
set -g status-right "#($HOME/.claude/scripts/venv/bin/python3 $HOME/.claude/scripts/usage-monitor.py --compact)"
set -g status-interval 60
```

---

## How it works

The monitor calls `https://api.anthropic.com/api/oauth/usage` using the OAuth token that Claude Code already stores in `~/.claude/.credentials.json`. No separate credentials needed.

The **statusLine** integration reads from a local cache file (`~/.claude/scripts/usage-cache.json`) so it responds instantly without making a network request on every keypress. The cache is refreshed whenever you run `ccmon` or every 5 minutes automatically.

---

## Files installed

| File | Purpose |
|------|---------|
| `~/.claude/scripts/usage-monitor.py` | Main script |
| `~/.claude/scripts/venv/` | Python virtualenv (rich + requests) |
| `~/.claude/scripts/usage-cache.json` | Cache file (auto-created) |
| `~/.claude/statusline-command.sh` | Claude Code statusLine hook |

The installer also adds `statusLine` to `~/.claude/settings.json` and an alias `ccmon` to your shell rc file.
