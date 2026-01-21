#!/bin/bash

# FLAG: Define the path to your project root
PROJECT_DIR="/home/tori/Codestuff/GrekoGameEngine"

# FLAG: Activate the Virtual Environment
# This ensures all dependencies like Panda3D are visible
source "$PROJECT_DIR/venv/bin/activate"

# FLAG: Run the Entry script using the venv's Python
# We use "$@" to pass any extra arguments through to the engine
python "$PROJECT_DIR/EntRunner.py" "$@"

# Optional: Deactivate after the engine closes to keep your terminal clean
deactivate