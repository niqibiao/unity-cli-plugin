#!/usr/bin/env bash
set -euo pipefail

PLUGIN_NAME="unity-cli-plugin"
PLUGIN_REPO="https://github.com/niqibiao/unity-cli-plugin.git"
PLUGIN_BRANCH="codex-plugin"

die()  { echo "ERROR: $*" >&2; exit 1; }
info() { echo "  [*] $*"; }
ok()   { echo "  [OK] $*"; }

# Detect working python (python3 may be a Windows Store stub)
PY=""
for cmd in python3 python; do
  if "$cmd" -c "import sys; sys.exit(0)" 2>/dev/null; then PY="$cmd"; break; fi
done
[ -n "$PY" ] || die "Python 3 is required but not found."

if [ $# -lt 1 ]; then
  echo "Usage: bash install.sh <workspace-dir>"
  echo ""
  echo "  Installs ${PLUGIN_NAME} into the given workspace."
  echo ""
  echo "  <workspace-dir>  Root of your project/repo."
  echo "                   Plugin  -> <dir>/plugins/${PLUGIN_NAME}/"
  echo "                   Market  -> <dir>/.agents/plugins/marketplace.json"
  exit 1
fi

TARGET_DIR="$(cd "$1" && pwd)" || die "Directory '$1' does not exist."
PLUGIN_DIR="${TARGET_DIR}/plugins/${PLUGIN_NAME}"
MARKETPLACE_DIR="${TARGET_DIR}/.agents/plugins"
MARKETPLACE_FILE="${MARKETPLACE_DIR}/marketplace.json"

echo ""
echo "=== Installing ${PLUGIN_NAME} into ${TARGET_DIR} ==="
echo ""

# ── 1. Clone or update plugin ──────────────────────────────
PLUGIN_TMP="${PLUGIN_DIR}.tmp.$$"
if [ -d "${PLUGIN_DIR}/.codex-plugin" ]; then
  info "Plugin already exists, updating..."
  mkdir -p "$(dirname "${PLUGIN_DIR}")"
  git clone --depth=1 --branch "${PLUGIN_BRANCH}" --single-branch \
    "${PLUGIN_REPO}" "${PLUGIN_TMP}" --quiet \
    || { rm -rf "${PLUGIN_TMP}"; die "Clone failed — existing plugin left intact."; }
  rm -rf "${PLUGIN_TMP}/.git"
  rm -rf "${PLUGIN_DIR}"
  mv "${PLUGIN_TMP}" "${PLUGIN_DIR}"
  ok "Updated ${PLUGIN_DIR}"
elif [ ! -d "${PLUGIN_DIR}" ]; then
  info "Cloning ${PLUGIN_REPO} (branch: ${PLUGIN_BRANCH})..."
  mkdir -p "$(dirname "${PLUGIN_DIR}")"
  git clone --depth=1 --branch "${PLUGIN_BRANCH}" --single-branch \
    "${PLUGIN_REPO}" "${PLUGIN_DIR}" --quiet
  rm -rf "${PLUGIN_DIR}/.git"
  ok "Cloned into ${PLUGIN_DIR}"
fi

# ── 2. Create or update marketplace.json ───────────────────
mkdir -p "${MARKETPLACE_DIR}"

export MARKETPLACE_FILE
$PY << 'PYEOF'
import json, os

plugin_name = "unity-cli-plugin"
mf = os.environ["MARKETPLACE_FILE"]
entry = {
    "name": plugin_name,
    "source": {"source": "local", "path": f"./plugins/{plugin_name}"},
    "policy": {"installation": "INSTALLED_BY_DEFAULT", "authentication": "ON_INSTALL"},
    "category": "Productivity"
}

if os.path.isfile(mf):
    with open(mf) as f:
        data = json.load(f)
    plugins = data.setdefault("plugins", [])
    idx = next((i for i, p in enumerate(plugins) if p.get("name") == plugin_name), None)
    if idx is not None:
        plugins[idx] = entry
        print(f"  [OK] Updated existing {plugin_name} entry in marketplace.json")
    else:
        plugins.append(entry)
        print(f"  [OK] Added {plugin_name} to marketplace.json")
else:
    data = {"name": "local-workspace", "plugins": [entry]}
    print("  [OK] Created marketplace.json")

with open(mf, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
PYEOF

echo ""
echo "=== Installation complete ==="
echo ""
echo "Next steps:"
echo "  1. Open your Unity project in Unity Editor"
echo "  2. Start Codex CLI in ${TARGET_DIR}"
echo '  3. Run: $unity-cli-setup   (installs the Unity C# Console package)'
echo '  4. Run: $unity-cli-status  (verify connection)'
echo ""
