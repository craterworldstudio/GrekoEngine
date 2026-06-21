#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#include "glad/glad.h"
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

GLuint load_texture(const std::string& path, bool srgb) {
    int width, height, channels;
    
    // Flag: stbi_set_flip_vertically_on_load(true)
    stbi_set_flip_vertically_on_load(true);

    // Flag: STBI_rgb_alpha
    // Forces stb_image to force-convert any image (even grayscale or RGB) into 4 channels (RGBA)
    unsigned char* pixels = stbi_load(path.c_str(), &width, &height, &channels, STBI_rgb_alpha);

    if (!pixels) {
        std::cerr << "❌ STB failed to load image from file path: " << path << "\n";
        return 0;
    }

    GLuint tex;
    glGenTextures(1, &tex);
    glBindTexture(GL_TEXTURE_2D, tex);

    // Upload the raw pixel block data to the GPU memory cache
    glTexImage2D(
        GL_TEXTURE_2D,     // Target coordinate space
        0,                 // Mipmap LOD level (0 is the base original size)
        srgb ? GL_SRGB8_ALPHA8 : GL_RGBA8, // Internal GPU texture format flag (GL_SRGB8_ALPHA8 corrects washed-out colors)
        width,             // Texture pixel width
        height,            // Texture pixel height
        0,                 // Legacy border parameter (Must always be 0)
        GL_RGBA,           // Pixel format of your raw input data array
        GL_UNSIGNED_BYTE,  // Data type per channel pixel (8-bits unsigned per channel)
        pixels             // Pointer to the unpacked RAM memory byte array
    );

    // Automatically generate smaller mip down-samples for clean filtering at a distance
    glGenerateMipmap(GL_TEXTURE_2D);

    // Flag: GL_TEXTURE_MIN_FILTER -> GL_LINEAR_MIPMAP_LINEAR
    // This activates trilinear filtering. It interpolates linearly between the two closest 
    // mipmap levels, and then samples pixels linearly inside them to remove sparkling/aliasing artifacts.
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);

    // Flag: GL_TEXTURE_MAG_FILTER -> GL_LINEAR
    // Bilinear filtering when magnifying a texture close-up, preventing pixelation blockiness.
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    // Flag: GL_TEXTURE_WRAP_S / T -> GL_REPEAT
    // Tiling configurations. If your logo size or UV positions extend beyond 0.0-1.0 limits,
    // GL_REPEAT tiles the texture patterns rather than clamping edge pixels out.
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);

    stbi_image_free(pixels); // Instantly release host system RAM since data is living on the GPU VRAM now
    return tex;
}