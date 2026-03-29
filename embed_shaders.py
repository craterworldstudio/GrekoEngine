#!/usr/bin/env python3
"""Run this before compiling C++ to regenerate shaders_embedded.hpp"""
import os

SHADER_DIR = "shaders"
OUT_FILE = "native/shaders_embedded.hpp"

SHADERS = {
    "SHADER_TEXTEST_VERT": "Textest.vert",
    "SHADER_TEXTEST_FRAG": "Textest.frag",
    "SHADER_MTOON_VERT":   "mtoon.vert",
    "SHADER_MTOON_FRAG":   "mtoon.frag",
    "SHADER_DEBUG_VERT":   "debug.vert",
    "SHADER_DEBUG_FRAG":   "debug.frag",
}

lines = ["#pragma once", "#include <string>", ""]

for var, filename in SHADERS.items():
    path = os.path.join(SHADER_DIR, filename)
    with open(path, "r") as f:
        src = f.read()
    lines.append(f"static const std::string {var} = R\"GLSL(")
    lines.append(src)
    lines.append(")GLSL\";")
    lines.append("")

with open(OUT_FILE, "w") as f:
    f.write("\n".join(lines))

print(f"✅ Generated {OUT_FILE}")