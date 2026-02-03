# 🚀 Greko Engine

A high-performance 3D VRM visualizer built with a Python "Brain" and a C++ OpenGL "Muscle."

> **TL;DR:** Transitioned to a "Thin-Client" architecture. Python handles the heavy lifting of GLB parsing, while a custom C++ Bridge (pybind11) feeds raw buffers directly to OpenGL 4.3. This bypasses the Assimp "black box" that was stripping facial data in V2.2.

## 🌟 Features
* **Hybrid Architecture:** Logic in Python, rendering in C++ via Pybind11.
* **Smooth Camera:** WASD movement and Mouse-look with Delta-Time normalization.
* **VRM Loading:** Direct ingestion of `.glb`/`.vrm` files.
* **Live HUD:** Real-time FPS and Camera coordinate tracking in the terminal.

## 🛠️ Prerequisites
* **Python 3.10+**
* **OpenGL 4.3+**
* **Libraries:** `sudo apt install libglew-dev libglfw3-dev libglm-dev`

## 🚀 Getting Started
1. **Clone the repo:**
   ```bash
    git clone <your-link>
    cd GrekoEngine
    chmod +x run.sh
    ./run.sh
   ```

🎮 Controls

- W/A/S/D: Move camera (Fly mode).
- Mouse: Look around.
- ESC: Toggle mouse lock / Emergency Exit.


---

## 📂 [Native README](`./native/README.md`)
This is for the technical details of the C++ rendering core.

# 🧠 Greko Native Muscle

This directory contains the low-level rendering logic and the Python-C++ bridge.

## 🏗️ Architecture

### 1. `renderer.cpp`
The core OpenGL implementation. Handles:
* **Shader Pipeline:** Compiling and linking GLSL.
* **Buffer Management:** VAO/VBO/EBO management for VRM meshes.
* **Input Polling:** Raw GLFW key/mouse handling for sub-millisecond latency.

### 2. `camera.hpp`
A standalone header-only module for 3D math.
* **MVP Matrix:** Calculates Model, View, and Projection matrices using GLM.
* **Clipping:** Configured for high-detail close-ups ($Near = 0.01$).

### 3. `bridge.cpp`
The **Pybind11** wrapper. It exposes C++ functions to Python as a module named `greko_native`.

## 🛠️ Build Flags
The engine is compiled with the following flags in `run.sh`:
* `-fPIC`: Position Independent Code (Required for shared libraries).
* `-shared`: Compiles into a `.so` file for Python import.
* `-lGL -lGLEW -lglfw`: Links the essential graphics drivers.

## ⚠️ Known Implementation Details
* **Depth Testing:** Enabled via `GL_DEPTH_TEST` to prevent 3D "squashing."
* **Winding Order:** Currently set to `GL_LESS` for standard VRM depth sorting.
* **VSync Details:** Toggle VSync in ```renderer.cpp``` for benchmark testing.


## 📋 Engine Documentation & History
Explore the development milestones and technical snapshots of the Greko Engine.

* **[Snapshot Archive](./snapshots/README.md)** - Version history, changelogs, and "Pink Pancake" era notes.
