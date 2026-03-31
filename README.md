# 🚀 Greko Engine

A lightweight, high-performance **VRM / VRoid character renderer** built with a **Python “Brain”** and a **C++ OpenGL “Muscle.”**

---

## 🌟 Architecture

Greko uses a **hybrid thin-client design**:

- **Python → Brain**
  - VRM parsing
  - behaviors (blink, breathing, lookAt, etc.)
  - scripting & control

- **C++ → Muscle**
  - OpenGL rendering
  - skeletal animation
  - morph blending
  - real-time performance

Python sends processed mesh data into C++ via **Pybind11**, bypassing heavy loaders like Assimp.

---

## ✨ Features

- 🧍 VRM / VRoid support
- 🦴 Full skeletal animation (100+ bones)
- 🎭 Morph targets (blendshapes)
- 👁️ LookAt tracking
- 😴 Blinking + breathing
- 🗣️ Mouth sequencing
- 🎮 Interactive camera
- ⚡ OpenGL 4.3 renderer
- 🧠 Python-controlled behaviors

---

# ⚠️ IMPORTANT: Dependencies

The repository **does NOT include prebuilt libraries**.

You must manually provide required native dependencies.

---

# 🪟 Windows Setup Guide

---

## 📦 Requirements

### 1. Python
- Python **3.10+** (3.13 recommended)

```bash
python --version
```

---

### 2. Visual Studio

Install:

- Visual Studio 2022 Community
- Desktop development with C++

---

### 3. Python Packages

```bash
pip install pybind11 numpy pyinstaller
```

---

## 📁 Required Native Libraries

You must provide these manually:

### 🔹 GLFW

Download prebuilt binaries from:
👉 https://www.glfw.org/download.html

Expected structure:

```
libs/glfw/
│
├── include/GLFW/glfw3.h
└── lib-vc2022/
    ├── glfw3.lib
    ├── glfw3dll.lib
    └── glfw3.dll
```

---

### 🔹 GLAD

Already included in:
```
native/glad/
```

---

### 🔹 GLM

Header-only library:

```
libs/glm/
```

---

## 🔨 Compile Native Module

From project root:

```bash
python setup.py build_ext --inplace
```

Output:

```
greko_native.cpXXX-win_amd64.pyd
```

---

## ▶ Run Engine

```bash
python launcher.py
```

---

## 📦 Build EXE (Optional)

```bash
pyinstaller launcher.spec
```

Output:

```
dist/launcher/
```

---

# 🧠 Behavior System

Behavior scripts are located in:

```
core/behaviours/
```

Includes:

- Blinker
- Breather
- LookAt
- MouthSequencer

---

# 🎮 Controls

- WASD → Move
- Mouse → Look
- Q/E → Up/Down
- ESC → Toggle mouse

---

# 📂 Project Structure

```
GrekoEngine/
│
├── launcher.py
├── setup.py
├── launcher.spec
├── greko_run.py
├── core/
│   ├── animator.py
│   ├── entity
│   ├── glb_parser.py
│   ├── gltf_accessours.py
│   ├── mesh_data.py
│   ├── scene.py
│   ├── skeleton.py
│   ├── behaviours_manager.py (Coupled with BaseClasses)
│   └── behaviours/
│       ├── blinker.py
│       ├── breather.py
│       ├── lookAt.py
│       └── mouthsequence.py (incomplete - works but hardcoding is require will fix next time!)
│
├── native/
│   ├── renderer.cpp
│   ├── bridge.cpp
│   ├── animation.cpp
│   ├── lookAt.cpp
│   ├── scene_builder.cpp
│   ├── texture_loader.cpp
│   └── camera.hpp
│
├── libs/        ⚠️ NOT INCLUDED IN REPO
├── shaders/
├── assets/
```

---

# ⚠️ Known Issues

- Windows shader limits (morph targets)
- Packaging requires hidden imports
- Behavior system needs PyInstaller config

---

# 🔥 Philosophy

Greko is not a VTuber app.

> It is a **programmable VRM sandbox**.

---

# 🔮 Future

- Editor UI
- Better material system
- Animation tools
- AI integration

---

# 🙌 Final Note

If something breaks:

> It’s probably a missing dependency 😄

(seriously, 90% of issues are)

---

More updates coming soon.