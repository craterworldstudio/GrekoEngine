#!/bin/bash
set -e

# ===============================
# Greko Engine Build + Run Script
# ===============================

# FLAG: Virtualenv Python
VENV_PYTHON="./venv/bin/python3"

# FLAG: Python extension suffix
PY_SUFFIX=$(python3-config --extension-suffix)

echo "🔨 [1/2] Compiling Native Engine Muscle..."

# -------------------------------
# Native build
# -------------------------------
clang++ -O3 -shared -std=c++17 -fPIC \
    $($VENV_PYTHON -m pybind11 --includes) \
    native/bridge.cpp \
    native/renderer.cpp \
    native/texture_loader.cpp \
    -x c++ native/glad/glad.c \
    -I native \
    -o core/greko_native$PY_SUFFIX \
    -lGL -lglfw -ldl

# -------------------------------
# Sanity check
# -------------------------------
if [ -f "core/greko_native$PY_SUFFIX" ]; then
    echo "✅ Compilation Successful: core/greko_native$PY_SUFFIX"
else
    echo "❌ Compilation Failed: .so not generated"
    exit 1
fi

# -------------------------------
# Run engine
# -------------------------------
echo "🚀 [2/2] Launching Greko Engine..."

export PYTHONPATH="$(pwd):$PYTHONPATH"
$VENV_PYTHON greko_run.py
