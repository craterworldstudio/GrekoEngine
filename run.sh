#!/bin/bash

# FLAG: Venv Pathing
VENV_PYTHON="./venv/bin/python3"

# FLAG: The Naming Fix
# We use the system's python3-config because venvs often skip it.
# This is what generates the ".cpython-313-x86_64-linux-gnu.so" part.
PY_SUFFIX=$(python3-config --extension-suffix)

echo "🔨 [1/2] Compiling Native Engine Muscle..."

# FLAG: The Build Command
# We added -I/usr/include/GL to be safe for Kali headers.
clang++ -O3 -shared -std=c++17 -fPIC \
    $($VENV_PYTHON -m pybind11 --includes) \
    native/bridge.cpp \
    -o core/greko_native$PY_SUFFIX \
    -lGL -lGLEW -lglfw

# FLAG: True Error Checking
if [ $? -eq 0 ] && [ -f "core/greko_native$PY_SUFFIX" ]; then
    echo "✅ Compilation Successful: core/greko_native$PY_SUFFIX created."
    echo "🚀 [2/2] Launching Greko Engine..."
    
    export PYTHONPATH=$PYTHONPATH:$(pwd)
    $VENV_PYTHON greko_run.py
else
    echo "❌ Compilation Failed! The .so file was not created."
    exit 1
fi