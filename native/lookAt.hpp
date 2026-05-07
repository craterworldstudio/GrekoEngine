#pragma once
#include <glm/glm.hpp>

extern float eye_inner_yaw;
extern float eye_outer_yaw;
extern float eye_up_pitch ;
extern float eye_down_pitch;

void  set_pupil_dilation(float target, float speed = 3.0f);
float get_pupil_dilation();



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

void apply_look_at(int head, int left_eye, int right_eye, int target, float dt);

void apply_head_look_at(int head, const glm::vec3& target, float dt);

void apply_eye_look_at(int left, int right, const glm::vec3& target, float dt);

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

float get_left_eye_yaw() ;
float get_right_eye_yaw();
void set_look_at_distances(float near, float far);

void init_look_at(int left_eye_index, int right_eye_index);