#pragma once
#include <glad/glad.h>
#include <string>

GLuint load_texture_from_memory(
    const unsigned char* data,
    int size,
    bool srgb = true
);

GLuint load_texture(const std::string& path, bool srgb = true);