#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

#include "texture_loader.hpp"
#include <iostream>

GLuint load_texture_from_memory(
    const unsigned char* data,
    int size,
    bool srgb
) {
    int width, height, channels;
    stbi_set_flip_vertically_on_load(true);

    unsigned char* pixels = stbi_load_from_memory(
        data,
        size,
        &width,
        &height,
        &channels,
        STBI_rgb_alpha
    );

    if (!pixels) {
        std::cerr << "❌ STB failed to decode texture\n";
        return 0;
    }

    GLuint tex;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);

    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        srgb ? GL_SRGB8_ALPHA8 : GL_RGBA8,
        width,
        height,
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        pixels
    );

    glGenerateMipmap(GL_TEXTURE_2D);

    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);

    stbi_image_free(pixels);
    return tex;
}
