#pragma once
#include <glm/glm.hpp>

extern float eye_inner_yaw;
extern float eye_outer_yaw;
extern float eye_up_pitch ;
extern float eye_down_pitch;

enum ActiveEyeAxis
{
    NONE,
    INNER_YAW,
    OUTER_YAW,
    UP_PITCH,
    DOWN_PITCH
};

extern ActiveEyeAxis active_eye_axis;

extern bool manual_eye_control;
extern bool head_tracking_enabled;

void apply_look_at(
    int head_bone_index,
    int Leye_index,
    int Reye_index, 
    int target_entity_index
);

void apply_head_look_at(
    int head_bone_index,
    const glm::vec3& target_entity_index
    //float target_x,
    //float target_y,
    //float target_z
);

void apply_eye_look_at(
    int Leye_index,
    int Reye_index, 
    const glm::vec3& target_entity_index
);

void set_eye_constraints(
    float inner_yaw,
    float outer_yaw,
    float up_pitch,
    float down_pitch
);

void apply_manual_eye_pose(
    int left_eye_index,
    int right_eye_index
);