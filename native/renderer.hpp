#pragma once
#include <cstdint>
#include <vector>
#include <glad/glad.h>
#include "camera.hpp"

// Forward declarations / globals
//extern unsigned int shaderProgram;
extern unsigned int vao;
//extern unsigned int current_index_count;
extern unsigned int g_texture;

// Camera
extern Camera main_camera;

struct GPUMesh {
    GLuint vao;
    GLuint vbo_pos, vbo_norm, vbo_uv, vbo_joints, vbo_weights, ebo;
    int index_count;
    GLuint texture_id;
     // Must be an array of 4
    GLuint vbo_morphs[4]; 
};


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
    const std::vector<const float*>& morph_data_ptrs,
    int tex_id
);

GLuint upload_texture_bytes(const unsigned char* data, int size);
void set_current_texture(GLuint tex_id);
void set_morph_weights(float w0, float w1, float w2, float w3);
