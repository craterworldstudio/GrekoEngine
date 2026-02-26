#pragma once
#include <glm/glm.hpp>
#include <vector>
#include <string>
#include <glm/gtc/quaternion.hpp>

struct Bone {
    int parent_index;
    std::string name;

    // Rest Pose (Bind Pose)
    glm::vec3 bind_pos;
    glm::quat bind_rot;
    glm::vec3 bind_scale;

    // Current Pose (Animated)
    glm::vec3 local_pos;
    glm::quat local_rot;
    glm::vec3 local_scale;

    glm::mat4 global_matrix;
    glm::mat4 inverse_bind_matrix;
};

extern glm::mat4 joint_matrices[256];
extern int joint_count;
extern std::vector<std::string> joint_names;
extern std::vector<Bone> skeleton_bones;

void init_skeleton();
void update_joints_from_buffer(const float* data, int count);
void update_skeleton_hierarchy();
void reset_to_bind_pose();