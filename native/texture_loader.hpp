#pragma once
#include <glad/glad.h>

GLuint load_texture_from_memory(
    const unsigned char* data,
    int size,
    bool srgb = true
);
