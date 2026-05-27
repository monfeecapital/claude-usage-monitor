#!/bin/sh
# Claude Usage Monitor — installer
# Works on macOS, Linux, and WSL

set -e

SCRIPTS_DIR="$HOME/.claude/scripts"
VENV="$SCRIPTS_DIR/venv"
MONITOR="$SCRIPTS_DIR/usage-monitor.py"
STATUSLINE="$HOME/.claude/statusline-command.sh"
SETTINGS="$HOME/.claude/settings.json"

# ── Python ─────────────────────────────────────────────────────────────────────
if command -v uv > /dev/null 2>&1; then
    echo "→ Creating venv with uv..."
    uv venv "$VENV" --quiet
    uv pip install --python "$VENV/bin/python3" rich requests --quiet
elif command -v python3 > /dev/null 2>&1; then
    echo "→ Creating venv with python3..."
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet rich requests
else
    echo "Error: python3 not found. Install Python 3.10+ first." >&2
    exit 1
fi

# ── Copy monitor script ────────────────────────────────────────────────────────
mkdir -p "$SCRIPTS_DIR"
cp monitor.py "$MONITOR"
chmod +x "$MONITOR"

# ── statusLine script ──────────────────────────────────────────────────────────
cat > "$STATUSLINE" << EOF
#!/bin/sh
$VENV/bin/python3 $MONITOR --statusline 2>/dev/null
EOF
chmod +x "$STATUSLINE"

# ── settings.json — add statusLine ────────────────────────────────────────────
if [ -f "$SETTINGS" ]; then
    if grep -q '"statusLine"' "$SETTINGS"; then
        echo "→ statusLine already configured in settings.json, skipping."
    else
        python3 - "$SETTINGS" "$STATUSLINE" << 'PYEOF'
import json, sys
path, statusline_path = sys.argv[1], sys.argv[2]
with open(path) as f:
    cfg = json.load(f)
cfg["statusLine"] = {"type": "command", "command": statusline_path}
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
print("→ statusLine added to settings.json")
PYEOF
    fi
else
    echo "→ ~/.claude/settings.json not found, skipping statusLine setup."
fi

echo ""
echo "Done! Restart Claude Code to activate the statusLine."
echo ""
echo "The usage info will appear below the input prompt automatically."
echo ""
echo "To run the full live monitor manually:"
echo "  $VENV/bin/python3 $MONITOR"
