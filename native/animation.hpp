#pragma once
#include <glm/glm.hpp>
#include <vector>
#include <string>
#include <glm/gtc/quaternion.hpp>

struct Bone {
    int parent_index;
    std::string name;
    
    // The "Source of Truth"
    glm::vec3 local_pos;
    glm::quat local_rot;
    glm::vec3 local_scale;

    glm::mat4 global_matrix;      // Result of hierarchy
    glm::mat4 inverse_bind_matrix; // From GLTF/VRM
};

extern glm::mat4 joint_matrices[256];
extern int joint_count;
extern std::vector<std::string> joint_names;
extern std::vector<Bone> skeleton_bones;

void init_skeleton();
void update_joints_from_buffer(const float* data, int count);
void update_skeleton_hierarchy();