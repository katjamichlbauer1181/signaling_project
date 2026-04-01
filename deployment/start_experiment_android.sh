#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# Symbol Matrix Experiment — Android / Termux startup script
# Run from Termux: bash start_experiment_android.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "Resetting database for clean session..."
otree resetdb --noinput

echo "Starting oTree server..."
# Start server in background
otree devserver &
SERVER_PID=$!

echo "Waiting for server to start..."
sleep 4

# Open browser (works with Termux:API or via am command)
# Try Termux-open first, fall back to am
if command -v termux-open-url &> /dev/null; then
    termux-open-url "http://localhost:8000/demo"
else
    am start -a android.intent.action.VIEW -d "http://localhost:8000/demo" &> /dev/null || true
fi

echo ""
echo "============================================================"
echo " Experiment is running at http://localhost:8000/demo"
echo " Open your browser manually if it did not open automatically."
echo ""
echo " Press Ctrl+C to stop the server when the session is done."
echo " To export data: go to http://localhost:8000/export"
echo "============================================================"

# Wait for server process (keeps script alive)
wait $SERVER_PID
