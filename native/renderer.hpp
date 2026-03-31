#pragma once
#include <cstdint>
#include <vector>
#include <glad/glad.h>
#include "camera.hpp"
#include <string>

// Forward declarations / globals
//extern unsigned int shaderProgram;
extern unsigned int vao;
//extern unsigned int current_index_count;
extern unsigned int g_texture;
extern int selected_bone;

static std::string g_shader_base_path = "shaders/";

// Camera
extern Camera main_camera;
extern glm::vec3 cameraFront;
extern float yaw, pitch;

extern std::vector<std::string> entity_names;
extern int selected_entity_index;
extern int trackingEntity;
extern std::vector<glm::mat4> entity_world_matrices;

extern std::vector<glm::vec3> entity_positions;
extern std::vector<glm::vec3> entity_rotations; // Euler degrees for UI
extern std::vector<glm::vec3> entity_scales;

struct GPUMesh {
    GLuint vao;
    GLuint vbo_pos, vbo_norm, vbo_uv, vbo_joints, vbo_weights, ebo;
    int index_count;
    GLuint texture_id;
     // Must be an array of 4
    GLuint vbo_morphs[4];
    int entity_index;
};

enum TransformAuthority {
    AUTH_PYTHON = 0,
    AUTH_NATIVE = 1
};

extern std::vector<int> entity_authority;

// Functions
int init_renderer(int w, int h);
void clear_screen();
void swap_buffers();
bool should_close();
void shutdown_renderer();
void draw_scene();


void add_mesh_to_scene(
    const float* vertices, size_t v_size,
    const float* normals, size_t n_size,
    const float* uvs, size_t uv_size,
    const uint32_t* joints, size_t j_size,
    const float* weights, size_t w_size,
    const uint32_t* indices, size_t i_size,
    const std::vector<const float*>& morph_data_ptrs,
    int tex_id,
    int entity_index
);

GLuint upload_texture_bytes(const unsigned char* data, int size);
void set_current_texture(GLuint tex_id);
void set_morph_weights(float w0, float w1, float w2, float w3);
void update_morph_slot(int mesh_index, int slot_index, const float* new_data, size_t data_size);

bool is_key_down(int key);
bool is_key_pressed(int key);
void set_joint_count(int count);
void set_joint_names(const std::vector<std::string>& names);

void update_entity_transform( int entity_index, const float* world_matrix_16 );