# 📸 Development Snapshots

This file tracks the evolution of the Greko Engine, from the first pink sliver to the smooth 3D camera system.

---

## Available Snapshots

▶️ **[V3.0 — The Greko Hybrid "Muscle" (Current)](./V3.0.md)**
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