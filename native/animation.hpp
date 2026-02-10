#pragma once
#include <glm/glm.hpp>

extern glm::mat4 joint_matrices[128];

void init_skeleton();
void update_joints_from_buffer(const float* data, int count);