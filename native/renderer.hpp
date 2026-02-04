#pragma once
#include <cstdint>
#include <glad/glad.h>
#include "camera.hpp"

// Forward declarations / globals
extern unsigned int shaderProgram;
extern unsigned int vao;
extern unsigned int current_index_count;
extern unsigned int g_texture;

// Camera
extern Camera main_camera;

// Functions
int init_renderer(int w, int h);
void clear_screen();
void swap_buffers();
bool should_close();
void terminate();
void draw_mesh();

void setup_opengl_buffers(
    const float* vertices, size_t v_count,
    const float* normals, size_t n_count,
    const float* uvs, size_t uv_count,
    const uint32_t* joints, size_t j_count,
    const float* weights, size_t w_count,
    const uint32_t* indices, size_t i_count
);

GLuint upload_texture_bytes(const unsigned char* data, int size);
