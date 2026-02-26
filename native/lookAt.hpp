#pragma once
#define GLM_ENABLE_EXPERIMENTAL
#include <glm/glm.hpp>

void apply_look_at(
    int bone_index,
    float target_x,
    float target_y,
    float target_z
);