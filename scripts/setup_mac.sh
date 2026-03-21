#!/usr/bin/env zsh
# =============================================================================
# CSULA PDF Accessibility Checker — Mac First-Time Setup
# =============================================================================
# Safe to run multiple times — re-running after installing Java/VeraPDF will
# pick up the new installs and confirm everything is ready.
#
# Recommended first-time flow:
#   1. ./scripts/setup_mac.sh          # installs Python deps; flags missing Java/VeraPDF
#   2. Install Java 21+ (if flagged)   # brew install --cask temurin@21
#   3. Install VeraPDF (if flagged)    # download CLI zip from verapdf.org/software/
#   4. ./scripts/setup_mac.sh          # re-run to confirm all checks pass
# =============================================================================

set -euo pipefail

cd "$(dirname "$0")/.."
echo "============================================================"
echo "CSULA HomegrownPAC — Mac Setup"
echo "Working directory: $(pwd)"
echo "============================================================"
echo ""

ISSUES=0   # count of unresolved issues to surface at the end

# ---------------------------------------------------------------------------
# Step 1: Python virtual environment + dependencies
# ---------------------------------------------------------------------------
echo "--- Step 1: Python virtual environment ---"

if [[ ! -d ".venv" ]]; then
    echo "Creating .venv..."
    python3 -m venv .venv
else
    echo ".venv already exists — skipping creation."
fi

echo "Installing/updating dependencies from requirements.txt..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet
echo "[OK] Python dependencies installed."
echo ""

# ---------------------------------------------------------------------------
# Step 2: Java runtime (required by VeraPDF) — auto-install via Homebrew
# ---------------------------------------------------------------------------
echo "--- Step 2: Java runtime (required by VeraPDF) ---"

# Disable set -e for this entire block — brew and java checks may return
# non-zero for benign reasons (already installed, PATH not yet updated, etc.)
# and we never want a missing JRE to abort the rest of the setup.
set +e

# On Apple Silicon brew lives at /opt/homebrew/bin, which is not on PATH in
# non-interactive scripts. Add it directly rather than eval-ing shellenv
# (shellenv emits fpath[] assignments that fail under set -euo pipefail).
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$PATH"

java -version &>/dev/null
JAVA_FOUND=$?

if [[ $JAVA_FOUND -eq 0 ]]; then
    JAVA_VERSION=$(java -version 2>&1 | head -1)
    echo "[OK] Java found: $JAVA_VERSION"
else
    echo "[!] Java not found. Attempting to install Java 21 via Homebrew..."
    echo ""
    BREW_CMD=""
    if [[ -x "/opt/homebrew/bin/brew" ]]; then
        BREW_CMD="/opt/homebrew/bin/brew"
    elif [[ -x "/usr/local/bin/brew" ]]; then
        BREW_CMD="/usr/local/bin/brew"
    fi

    if [[ -n "$BREW_CMD" ]]; then
        "$BREW_CMD" install --cask temurin@21
        BREW_EXIT=$?
        if [[ $BREW_EXIT -ne 0 ]]; then
            echo "[!] 'brew install --cask temurin@21' exited with code $BREW_EXIT."
            echo "    Run it manually in a new terminal to see the full output."
            ISSUES=$((ISSUES + 1))
        else
            # Temurin installs to /Library/Java/JavaVirtualMachines/.
            # /usr/bin/java picks it up automatically — no PATH change needed.
            java -version &>/dev/null
            if [[ $? -eq 0 ]]; then
                echo "[OK] Java installed: $(java -version 2>&1 | head -1)"
            else
                echo "[OK] Java installed. Open a new terminal then re-run this"
                echo "     script so the JVM stub at /usr/bin/java picks it up."
                ISSUES=$((ISSUES + 1))
            fi
        fi
    else
        echo "[!] Homebrew not found — cannot auto-install Java."
        echo ""
        echo "    Option A — Install Homebrew first, then re-run this script:"
        echo "      /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo ""
        echo "    Option B — Download the .pkg directly:"
        echo "      https://adoptium.net/"
        echo "      Choose: Eclipse Temurin 21 (LTS) → macOS → .pkg"
        echo ""
        ISSUES=$((ISSUES + 1))
    fi
fi

set -e

# ---------------------------------------------------------------------------
# Step 3: VeraPDF check
# ---------------------------------------------------------------------------
echo "--- Step 3: VeraPDF ---"

VERAPDF="$HOME/veraPDF/verapdf"
if [[ -f "$VERAPDF" ]]; then
    # Only attempt to run verapdf if Java was found (otherwise it will crash)
    if command -v java &>/dev/null; then
        VERA_VERSION=$("$VERAPDF" --version 2>&1 | head -1)
        echo "[OK] VeraPDF found at $VERAPDF"
        echo "     Version: $VERA_VERSION"
    else
        echo "[OK] VeraPDF binary found at $VERAPDF (install Java above to run it)"
    fi
else
    echo "[!] VeraPDF NOT found at $VERAPDF"
    echo ""
    echo "    Install steps (do this AFTER confirming Java is installed):"
    echo "    1. Go to https://verapdf.org/software/"
    echo "       Download the 'CLI' build (.zip — not the GUI installer)."
    echo "    2. Extract the zip. Inside you will find a folder named 'veraPDF'."
    echo "    3. Move that folder to your home directory:"
    echo "         mv ~/Downloads/veraPDF ~/veraPDF"
    echo "       so that ~/veraPDF/verapdf exists."
    echo "    4. Make it executable:"
    echo "         chmod +x ~/veraPDF/verapdf"
    echo "    5. Re-run this script to verify."
    echo ""
    ISSUES=$((ISSUES + 1))
fi

# ---------------------------------------------------------------------------
# Step 4: OneDrive / Teams folder check
# ---------------------------------------------------------------------------
echo "--- Step 4: OneDrive (Teams channel sync) ---"

ONEDRIVE_PAC="$HOME/OneDrive - Cal State LA/PDF Accessibility Checker (PAC) - General"
echo "Expected path: $ONEDRIVE_PAC"
echo ""

if [[ -d "$ONEDRIVE_PAC" ]]; then
    echo "[OK] OneDrive PAC folder is synced and accessible."
    echo "     Contents (top level):"
    ls "$ONEDRIVE_PAC" | sed 's/^/       /'
else
    echo "[!] OneDrive PAC folder NOT found."
    echo ""
    echo "    Sync steps:"
    echo "    1. Open Microsoft Teams → PDF Accessibility Checker (PAC) team."
    echo "    2. Click the 'General' channel → Files tab."
    echo "    3. Click Sync (or Open in SharePoint → Sync)."
    echo "    4. The folder will appear at the path above once OneDrive syncs it."
    echo "    5. Re-run this script to verify."
    ISSUES=$((ISSUES + 1))
fi
echo ""

# ---------------------------------------------------------------------------
# Step 5: Setup database (non-destructive — safe to re-run)
# ---------------------------------------------------------------------------
echo "--- Step 5: Setup/Verify Database ---"
echo "(Creates schema tables if missing. Will NOT delete drupal_pdfs.db.)"
echo ""
.venv/bin/python scripts/setup_test_environment.py --force --no-reset
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo "============================================================"
if [[ $ISSUES -eq 0 ]]; then
    echo "All checks passed. Setup complete."
    echo "============================================================"
    echo ""
    echo "Run the full workflow:"
    echo "  ./scripts/run_workflow.sh"
    echo ""
    echo "Test a single domain end-to-end:"
    echo "  ./scripts/run_workflow.sh --domain calstatela.edu_ecst"
    echo ""
    echo "Full pipeline including reports and OneDrive sync:"
    echo "  ./scripts/run_workflow.sh && \\"
    echo "    .venv/bin/python scripts/sharepoint_sync.py && \\"
    echo "    .venv/bin/python scripts/historical_analysis.py && \\"
    echo "    .venv/bin/python scripts/generate_master_report.py && \\"
    echo "    .venv/bin/python scripts/generate_master_report_html.py"
    echo ""
    echo "Note: Email sending (send_emails.py) requires Windows + Outlook COM."
else
    echo "$ISSUES item(s) need attention (see [!] above). Re-run after fixing."
    echo "============================================================"
    echo ""
    echo "Typical fix order:"
    echo "  1. Install Java 21+:   brew install --cask temurin@21"
    echo "  2. Install VeraPDF:    download CLI zip from verapdf.org/software/"
    echo "                         extract → mv ~/Downloads/veraPDF ~/veraPDF"
    echo "                         chmod +x ~/veraPDF/verapdf"
    echo "  3. Sync OneDrive:      Teams → PAC General → Files → Sync"
    echo "  4. Re-run:             ./scripts/setup_mac.sh"
fi
