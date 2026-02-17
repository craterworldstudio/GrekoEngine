#pragma once
#include <glm/glm.hpp>
#include <vector>
#include <string>

extern glm::mat4 joint_matrices[128];
extern int joint_count;
extern std::vector<std::string> joint_names;


void init_skeleton();
void update_joints_from_buffer(const float* data, int count);