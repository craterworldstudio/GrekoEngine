# Greko Engine — Native Core (Technical README)

This document describes the **native C++ core** of the Greko VRM Engine, focusing on how Python-side data flows into OpenGL and how rendering and camera control are handled.

The files covered here are:

* `bridge.cpp` — Python ↔ C++ boundary (pybind11)
* `renderer.cpp` — OpenGL renderer, buffers, and draw loop
* `camera.hpp` — Free-fly camera math and input handling

---

## 1. `bridge.cpp` — Python ⇄ Native Boundary

### Purpose

`bridge.cpp` is the **only entry point** exposed to Python. It uses **pybind11** to:

* Initialize and shut down the renderer
* Upload mesh data (NumPy → OpenGL buffers)
* Drive the render loop from Python

This design keeps **all asset loading and parsing in Python**, while the C++ side remains a fast, deterministic execution layer.

### Key Responsibilities

* Accept **NumPy arrays** for:

  * Vertices (`float32`, vec3)
  * Normals (`float32`, vec3)
  * UVs (`float32`, vec2)
  * Joints (`uint16/uint32`, vec4)
  * Weights (`float32`, vec4)
  * Indices (`uint32`)
* Validate array contiguity and type safety
* Forward raw pointers and counts directly into the renderer

### Exposed API (Python)

Typical functions exported:

```python
init_renderer(width: int, height: int) -> int
upload_mesh(vertices, normals, uvs, joints, weights, indices)
draw_mesh()
clear_screen()
swap_buffers()
should_close() -> bool
terminate()
```

### Design Notes

* **No scene graph**: Python controls *what* is drawn, C++ controls *how* it is drawn
* Meshes are flattened on the Python side to avoid multi-VAO complexity (by design)
* This keeps VRM quirks (skin weights, morph accessors) out of C++

---

## 2. `renderer.cpp` — OpenGL Muscle

### Purpose

`renderer.cpp` owns **all OpenGL state**:

* Context initialization (GLFW + GLEW)
* VAO/VBO/EBO creation
* Shader compilation
* Draw submission

It assumes **fully prepared data** from Python.

---

### Renderer Initialization

* Requests **OpenGL 4.3 Compatibility/Core** profile
* Enables:

  * Depth testing (`GL_DEPTH_TEST`)
  * Back-face culling (if enabled later)
* Sets a debug clear color (magenta phase)

### Buffer Layout

A single VAO is used with multiple VBOs:

| Attribute | Location | Type  | Notes                   |
| --------- | -------- | ----- | ----------------------- |
| Position  | 0        | vec3  | Required                |
| Normal    | 1        | vec3  | Lighting-ready          |
| UV        | 2        | vec2  | Texture-ready           |
| Joints    | 3        | ivec4 | For future GPU skinning |
| Weights   | 4        | vec4  | Normalized              |

Indices are stored in an **EBO** and rendered via:

```cpp
glDrawElements(GL_TRIANGLES, index_count, GL_UNSIGNED_INT, 0);
```

---

### Shader Strategy (Current)

* Minimal vertex + fragment shader
* Hardcoded magenta output ("Pink Phase")
* Normals and UVs are already bound but unused

This ensures:

* Geometry correctness
* Correct winding order
* Correct index offsets

---

### Why Only One Mesh Before (Bug Explanation)

Earlier behavior where **only hair rendered** was caused by:

* Uploading **only the first primitive** to the GPU
* Later primitives never being appended or offset

This was fixed by:

* Flattening all primitives into one buffer
* Applying `index_offset += vertex_count` per primitive

---

## 3. `camera.hpp` — Free-Fly Camera System

### Purpose

`camera.hpp` implements a **manual FPS-style camera**, independent of any engine framework.

It provides:

* Position & orientation tracking
* View matrix generation
* Keyboard + mouse look support

---

### Camera Model

* Position: `vec3`
* Orientation: yaw / pitch (Euler)
* Direction vectors:

  * Forward
  * Right
  * Up

The camera computes:

```cpp
view = lookAt(position, position + forward, up);
```

---

### Controls

| Input      | Action                 |
| ---------- | ---------------------- |
| W / S      | Forward / Back         |
| A / D      | Strafe                 |
| Mouse      | Look around            |
| Delta Time | Movement normalization |

### Projection

* Perspective projection
* Near plane: **0.01**
* Far plane: **1000.0**

This is critical for VRM scale correctness and avoiding face clipping.

---

## Architectural Philosophy

### Why This Design Works

* Python handles **complex formats** (GLTF, VRM, morphs, expressions)
* C++ handles **only math + GPU**
* No Assimp
* No engine-side skinning assumptions

This avoids:

* Bone stripping
* Morph loss
* Engine-defined character constraints

---

## Next Planned Extensions

* Texture loading via **stb_image**
* MToon shading (GLSL port)
* GPU skinning (SSBO / UBO driven)
* Morph targets via additive vertex streams

---

## TL;DR

> Python thinks. C++ lifts. OpenGL draws.

This split is intentional — and scalable.
