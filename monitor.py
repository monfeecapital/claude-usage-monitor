#!/usr/bin/env python3
"""
Claude Code Usage Monitor
Real data from https://api.anthropic.com/api/oauth/usage
Format mirrors the Claude app usage panel.
"""

import json, os, sys, time, argparse
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

CREDS_FILE  = Path.home() / ".claude" / ".credentials.json"
CACHE_FILE  = Path.home() / ".claude" / "scripts" / "usage-cache.json"
API_URL     = "https://api.anthropic.com/api/oauth/usage"
BETA_HEADER = "oauth-2025-04-20"

# ── credentials ────────────────────────────────────────────────────────────────

def load_token() -> str:
    try:
        with open(CREDS_FILE) as f:
            creds = json.load(f)
        return creds.get("claudeAiOauth", {}).get("accessToken", "")
    except (OSError, json.JSONDecodeError, KeyError):
        return ""

# ── API ────────────────────────────────────────────────────────────────────────

def fetch_usage(token: str) -> dict | None:
    if not HAS_REQUESTS or not token:
        return None
    try:
        r = requests.get(
            API_URL,
            headers={"Authorization": f"Bearer {token}", "anthropic-beta": BETA_HEADER},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            write_cache(data)
            return data
        return None
    except Exception:
        return None

def write_cache(data: dict) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({"ts": time.time(), "data": data}))
    except OSError:
        pass

def read_cache() -> dict | None:
    """Return cached data if fresher than 5 minutes."""
    try:
        obj = json.loads(CACHE_FILE.read_text())
        if time.time() - obj["ts"] < 120:
            return obj["data"]
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    return None

# ── helpers ────────────────────────────────────────────────────────────────────

def parse_resets_at(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except ValueError:
        return None

def time_until(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    total = int((dt - now).total_seconds())
    if total <= 0:
        return "soon"
    d, r = divmod(total, 86400)
    h, r = divmod(r, 3600)
    m    = r // 60
    parts = []
    if d: parts.append(f"{d}d")
    if h: parts.append(f"{h}h")
    parts.append(f"{m}m")
    return "in " + " ".join(parts)

def make_bar(pct: float, width: int = 20) -> tuple[str, str]:
    pct   = max(0.0, min(100.0, pct))
    color = "green" if pct < 60 else ("yellow" if pct < 85 else "red")
    n     = round(width * pct / 100)
    return "█" * n + "░" * (width - n), color

# ── rendering ──────────────────────────────────────────────────────────────────

def metric_row(label: str, pct: float, reset_dt) -> "Text":
    b, c = make_bar(pct)
    line = Text()
    line.append(f"  {label:<26}", style="dim")
    line.append(f"[{b}]", style=c)
    line.append(f"  {pct:>3.0f}%  ", style=f"bold {c}")
    line.append(time_until(reset_dt), style="dim")
    return line

def render_rich(data: dict) -> "Panel":
    from rich.console import Group

    five  = data.get("five_hour") or {}
    seven = data.get("seven_day") or {}

    rows = [
        Text(""),
        metric_row("Current session",         float(five.get("utilization", 0)),  parse_resets_at(five.get("resets_at"))),
        metric_row("All models weekly limit",  float(seven.get("utilization", 0)), parse_resets_at(seven.get("resets_at"))),
        Text(""),
    ]

    now_str = datetime.now().strftime("%H:%M:%S")
    return Panel(
        Group(*rows),
        title="[bold cyan]Claude Usage[/bold cyan]",
        subtitle=f"[dim]{now_str}  ·  refreshes every 60s[/dim]",
        border_style="cyan",
        padding=(0, 1),
    )

def render_compact(data: dict) -> str:
    five  = data.get("five_hour") or {}
    seven = data.get("seven_day") or {}
    f_pct = float(five.get("utilization", 0))
    s_pct = float(seven.get("utilization", 0))
    f_rst = time_until(parse_resets_at(five.get("resets_at")))
    s_rst = time_until(parse_resets_at(seven.get("resets_at")))
    return f"Claude: session {f_pct:.0f}% ({f_rst}) · week {s_pct:.0f}% ({s_rst})"

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Claude Code Usage Monitor")
    ap.add_argument("--compact",    action="store_true", help="One-line output (for tmux etc.)")
    ap.add_argument("--once",       action="store_true", help="Print once and exit")
    ap.add_argument("--statusline", action="store_true", help="Fast output for Claude Code statusLine (reads cache)")
    ap.add_argument("--daemon",     action="store_true", help="Background cache poller")
    ap.add_argument("--interval",   type=int, default=60, help="Refresh interval in seconds (default: 60)")
    args = ap.parse_args()

    if args.statusline:
        data = read_cache() or fetch_usage(load_token())
        print(render_compact(data) if data else "")
        return

    if args.daemon:
        token = load_token()
        if not token:
            sys.exit(1)
        while True:
            fetch_usage(token)
            time.sleep(args.interval)

    token = load_token()
    if not token:
        print("Error: token not found in ~/.claude/.credentials.json", file=sys.stderr)
        sys.exit(1)

    def get_and_print():
        data = fetch_usage(token)
        if not data:
            print("Claude: no data" if args.compact else "Failed to fetch usage data", file=sys.stderr)
            return False
        if args.compact:
            print(render_compact(data))
        elif HAS_RICH:
            Console().print(render_rich(data))
        else:
            print(render_compact(data))
        return True

    if args.compact or args.once:
        get_and_print()
        return

    if not HAS_RICH:
        print("Install 'rich' to use live mode: pip install rich", file=sys.stderr)
        sys.exit(1)

    with Live(Console(), refresh_per_second=1, screen=False) as live:
        while True:
            data = fetch_usage(token)
            if data:
                live.update(render_rich(data))
            time.sleep(args.interval)

if __name__ == "__main__":
    main()
