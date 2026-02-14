# 📸 Development Snapshots

This file tracks the evolution of the Greko Engine, from the first pink sliver to the smooth 3D camera system.

---

## Available Snapshots
▶️ **[V3.3 — Morph Stability & Live Phonemes(Previous)](./V3.3.md)**
- **Core Breakthrough:** Stable GPU morph hot-swapping using `glBufferSubData`.
- **Major Fix:** Eliminated vertex spikes and buffer corruption during runtime blendshape updates.
- **New System:** MouthSequencer with dynamic phoneme injection (A/E/I/O/U).
- **Architecture Upgrade:** Unified morph slot pipeline (Blink, Breath, Mouth separated cleanly).
- **Status:** Real-time facial morphing stable at 70–120 FPS on low-end GPU.


▶️ **[V3.0 — The Greko Hybrid "Muscle"](./V3.0.md)**
- **Tech:** Python "Brain" + C++ "Muscle" (Custom Bridge).
- **Core Change:** Ditched Assimp/Panda3D to solve the "Invisible Face" problem.
- **Status:** Movement smooth, Depth-test fixed, FPS counter live.
- **Tech:** Python + Custom C++ Bridge (`pybind11`).
- **Major Fix:** Solved the "Invisible Face" issue by bypassing Assimp.
- **Features:** Direct buffer control, WASD/Mouse flight, Terminal HUD.

▶️ **[V2.2 — The Panda3D / Assimp Era (Legacy)](./V2.2.md)**
- **Tech:** Panda3D Engine + p3assimp loader.
- **The "Invisible Face" Bug:** Documented the exact moment Assimp was caught stripping VRM blendshapes.
- **Key Discovery:** Realized that facial bones with zero weights were causing Assimp to delete the entire morph table.
---

⬅️ [Back to Main README](../README.md)
