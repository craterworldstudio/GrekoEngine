#pragma once
#include <cstdint>
#include <glad/glad.h>
#include "camera.hpp"

// Forward declarations / globals
//extern unsigned int shaderProgram;
extern unsigned int vao;
//extern unsigned int current_index_count;
extern unsigned int g_texture;

// Camera
extern Camera main_camera;

// Functions
int init_renderer(int w, int h);
void clear_screen();
void swap_buffers();
bool should_close();
void terminate();
void draw_scene();

void add_mesh_to_scene(
    const float* vertices, size_t v_size,
    const float* normals, size_t n_size,
    const float* uvs, size_t uv_size,
    const uint32_t* joints, size_t j_size,
    const float* weights, size_t w_size,
    const uint32_t* indices, size_t i_size,
    int tex_id
);

GLuint upload_texture_bytes(const unsigned char* data, int size);
void set_current_texture(GLuint tex_id);
