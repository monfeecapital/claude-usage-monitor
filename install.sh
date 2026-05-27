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
cat > "$STATUSLINE" << 'EOF'
#!/bin/sh
"$HOME/.claude/scripts/venv/bin/python3" "$HOME/.claude/scripts/usage-monitor.py" --statusline 2>/dev/null
EOF
# expand $HOME at write time
sed -i "s|\$HOME|$HOME|g" "$STATUSLINE"
chmod +x "$STATUSLINE"

# ── settings.json — add statusLine ────────────────────────────────────────────
if [ -f "$SETTINGS" ]; then
    if grep -q '"statusLine"' "$SETTINGS"; then
        echo "→ statusLine already configured in settings.json, skipping."
    else
        python3 - "$SETTINGS" << 'PYEOF'
import json, sys
path = sys.argv[1]
with open(path) as f:
    cfg = json.load(f)
cfg["statusLine"] = {"type": "command", "command": f"{__import__('pathlib').Path.home()}/.claude/statusline-command.sh"}
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
print("→ statusLine added to settings.json")
PYEOF
    fi
else
    echo "→ ~/.claude/settings.json not found, skipping statusLine setup."
fi

# ── shell alias ────────────────────────────────────────────────────────────────
ALIAS_LINE="alias ccmon='$VENV/bin/python3 $MONITOR'"

for RC in "$HOME/.zshrc" "$HOME/.bashrc"; do
    if [ -f "$RC" ] && ! grep -q "alias ccmon=" "$RC"; then
        printf "\n# Claude Usage Monitor\n%s\n" "$ALIAS_LINE" >> "$RC"
        echo "→ alias 'ccmon' added to $RC"
    fi
done

echo ""
echo "Done! Restart your terminal (or run: source ~/.zshrc / source ~/.bashrc)"
echo ""
echo "  ccmon          — live monitor"
echo "  ccmon --once   — print once and exit"
echo "  ccmon --compact — one-line output (tmux etc.)"
echo ""
echo "Restart Claude Code to activate the statusLine."
