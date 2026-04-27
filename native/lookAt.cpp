#include "lookAt.hpp"
#include "renderer.hpp"
#include "animation.hpp"
#include <glm/gtx/quaternion.hpp>
#include <glm/gtx/vector_angle.hpp>
#include <cmath>
#include <iostream>

// ─── Persistent smoothed state ────────────────────────────────────────────────

static glm::vec2 eye_smoothed_angles_L = glm::vec2(0.0f);
static glm::vec2 eye_smoothed_angles_R = glm::vec2(0.0f);
static glm::vec2 head_smoothed_angles  = glm::vec2(0.0f);

static float pupil_dilation_current = 0.5f;
static float pupil_dilation_target  = 0.5f;
static float pupil_dilation_speed   = 3.0f;

static float debug_eye_yaw_L   = 0.0f;
static float debug_eye_yaw_R   = 0.0f;
static bool  axis_debug_printed = false;

// ─── Rest pose cache ──────────────────────────────────────────────────────────

static glm::quat eye_rest_world_rot_L  = glm::quat(1,0,0,0);
static glm::quat eye_rest_world_rot_R  = glm::quat(1,0,0,0);
static glm::mat4 eye_rest_global_L     = glm::mat4(1.0f);
static glm::mat4 eye_rest_global_R     = glm::mat4(1.0f);
static glm::quat parent_rest_world_rot = glm::quat(1,0,0,0);
static bool      rest_pose_captured    = false;

// ─── Init (call once from Python after skeleton loads) ────────────────────────

void init_look_at(int left_eye_index, int right_eye_index)
{
    Bone& L = skeleton_bones[left_eye_index];
    Bone& R = skeleton_bones[right_eye_index];

    eye_rest_global_L    = L.global_matrix;
    eye_rest_global_R    = R.global_matrix;
    eye_rest_world_rot_L = glm::quat_cast(L.global_matrix);
    eye_rest_world_rot_R = glm::quat_cast(R.global_matrix);

    parent_rest_world_rot = (L.parent_index >= 0)
        ? glm::quat_cast(skeleton_bones[L.parent_index].global_matrix)
        : glm::quat(1,0,0,0);

    eye_smoothed_angles_L = glm::vec2(0.0f);
    eye_smoothed_angles_R = glm::vec2(0.0f);
    head_smoothed_angles  = glm::vec2(0.0f);
    rest_pose_captured    = true;
    axis_debug_printed    = false;

    std::cout << "✅ [LookAt] init_look_at setup successful!" << std::endl;
}

// ─── Constraints ──────────────────────────────────────────────────────────────

void set_eye_constraints(
    float inner_yaw, float outer_yaw,
    float up_pitch,  float down_pitch
)
{
    eye_inner_yaw  = std::abs(inner_yaw);
    eye_outer_yaw  = std::abs(outer_yaw);
    eye_up_pitch   = std::abs(up_pitch);
    eye_down_pitch = std::abs(down_pitch);

    // Reset smoothed angles only — never rest pose
    eye_smoothed_angles_L = glm::vec2(0.0f);
    eye_smoothed_angles_R = glm::vec2(0.0f);

    std::cout << "[LookAt] Constraints — "
              << "inner: " << eye_inner_yaw << "  outer: " << eye_outer_yaw
              << "  up: "  << eye_up_pitch  << "  down: " << eye_down_pitch << std::endl;
}

// ─── Pupil dilation ───────────────────────────────────────────────────────────

void set_pupil_dilation(float target, float speed)
{
    pupil_dilation_target = glm::clamp(target, 0.0f, 1.0f);
    pupil_dilation_speed  = speed;
}
float get_pupil_dilation() { return pupil_dilation_current; }

static void update_pupil_dilation(float dt)
{
    float w = 1.0f - std::exp(-pupil_dilation_speed * dt);
    pupil_dilation_current = glm::mix(pupil_dilation_current, pupil_dilation_target, w);
}

// ─── Solver ───────────────────────────────────────────────────────────────────
//
//  Measures the angle from the eye bone's rest-pose forward to the target,
//  but corrects for the head's current rotation so tracking stays accurate
//  as the head moves.

static glm::vec2 solve_in_bone_space(
    const glm::mat4& bone_rest_global,
    const glm::quat& bone_rest_world_rot,
    const glm::vec3& bone_world_pos,
    const glm::vec3& target_world,
    int              parent_index,
    const char*      label = nullptr
)
{
    glm::vec3 dir = glm::normalize(target_world - bone_world_pos);

    // Current parent (head) rotation
    glm::quat live_parent = (parent_index >= 0)
        ? glm::quat_cast(skeleton_bones[parent_index].global_matrix)
        : glm::quat(1,0,0,0);

    // Delta rotation the head has moved since rest pose
    glm::quat head_delta = live_parent * glm::inverse(parent_rest_world_rot);

    // Rotate rest axes by head delta so they follow the head
    glm::vec3 bone_right   = head_delta * glm::normalize(glm::vec3(bone_rest_global[0]));
    glm::vec3 bone_up      = head_delta * glm::normalize(glm::vec3(bone_rest_global[1]));
    glm::vec3 bone_forward = head_delta * glm::normalize(glm::vec3(bone_rest_global[2]));

    float d_right   = glm::dot(dir, bone_right);
    float d_up      = glm::dot(dir, bone_up);
    float d_forward = glm::dot(dir, bone_forward);

    float horiz = std::sqrt(d_right * d_right + d_forward * d_forward);
    float yaw   = glm::degrees(std::atan2(d_right,  d_forward));
    float pitch = glm::degrees(std::atan2(d_up,     horiz));

    if (label && !axis_debug_printed)
    {
        std::cout << "[LookAt][" << label << "] "
                  << "fwd(" << bone_forward.x << "," << bone_forward.y << "," << bone_forward.z << ") "
                  << "yaw=" << yaw << " pitch=" << pitch << std::endl;
    }

    return glm::vec2(pitch, yaw);
}

// ─── Angles → parent-local quaternion ────────────────────────────────────────

static glm::quat angles_to_parent_local(
    float            pitch_deg,
    float            yaw_deg,
    const glm::quat& bone_rest_world_rot,
    int              parent_index
)
{
    glm::quat delta = glm::quat(glm::radians(glm::vec3(pitch_deg, yaw_deg, 0.0f)));

    // Apply delta in bone rest-local space → world space
    glm::quat target_world_rot = bone_rest_world_rot * delta;

    // Convert to live parent-local space
    glm::quat live_parent = (parent_index >= 0)
        ? glm::quat_cast(skeleton_bones[parent_index].global_matrix)
        : glm::quat(1,0,0,0);

    return glm::inverse(live_parent) * target_world_rot;
}

// ─── Elliptic clamp ───────────────────────────────────────────────────────────

static glm::vec2 apply_elliptic_clamp(glm::vec2 angles, bool is_left)
{
    float pitch = angles.x;
    float yaw   = angles.y;

    float yaw_inner = is_left ? yaw : -yaw;

    float max_yaw   = (yaw_inner >= 0.0f) ? eye_inner_yaw : eye_outer_yaw;
    float max_pitch = (pitch     >= 0.0f) ? eye_up_pitch  : eye_down_pitch;

    if (max_yaw   < 0.5f) max_yaw   = 0.5f;
    if (max_pitch < 0.5f) max_pitch = 0.5f;

    float ey = yaw_inner / max_yaw;
    float ep = pitch     / max_pitch;
    float r2 = ey*ey + ep*ep;
    if (r2 > 1.0f)
    {
        float inv_r = 1.0f / std::sqrt(r2);
        yaw_inner *= inv_r;
        pitch     *= inv_r;
    }

    yaw = is_left ? yaw_inner : -yaw_inner;
    return glm::vec2(pitch, yaw);
}

// ─── Eye look-at ──────────────────────────────────────────────────────────────

void apply_eye_look_at(
    int              left_eye_index,
    int              right_eye_index,
    const glm::vec3& target_world,
    float            dt
)
{
    if (!rest_pose_captured)
    {
        std::cout << "[LookAt] WARNING — call init_look_at first!" << std::endl;
        return;
    }

    Bone& L = skeleton_bones[left_eye_index];
    Bone& R = skeleton_bones[right_eye_index];

    glm::vec3 left_pos  = glm::vec3(L.global_matrix[3]);
    glm::vec3 right_pos = glm::vec3(R.global_matrix[3]);

    glm::vec2 raw_L = solve_in_bone_space(
        eye_rest_global_L, eye_rest_world_rot_L,
        left_pos, target_world, L.parent_index, "LEFT");

    glm::vec2 raw_R = solve_in_bone_space(
        eye_rest_global_R, eye_rest_world_rot_R,
        right_pos, target_world, R.parent_index, "RIGHT");

    if (!axis_debug_printed)
    {
        std::cout << "[LookAt] raw_L: pitch=" << raw_L.x << " yaw=" << raw_L.y << std::endl;
        std::cout << "[LookAt] raw_R: pitch=" << raw_R.x << " yaw=" << raw_R.y << std::endl;
        axis_debug_printed = true;
    }

    glm::vec2 clamped_L = apply_elliptic_clamp(raw_L, true);
    glm::vec2 clamped_R = apply_elliptic_clamp(raw_R, false);

    const float eye_speed = 12.0f;
    float s = 1.0f - std::exp(-eye_speed * dt);

    eye_smoothed_angles_L = glm::mix(eye_smoothed_angles_L, clamped_L, s);
    eye_smoothed_angles_R = glm::mix(eye_smoothed_angles_R, clamped_R, s);

    debug_eye_yaw_L = eye_smoothed_angles_L.y;
    debug_eye_yaw_R = eye_smoothed_angles_R.y;

    // VRM pitch negated on apply
    L.local_rot = angles_to_parent_local(
        -eye_smoothed_angles_L.x,
         eye_smoothed_angles_L.y,
        eye_rest_world_rot_L, L.parent_index
    );

    R.local_rot = angles_to_parent_local(
        -eye_smoothed_angles_R.x,
         eye_smoothed_angles_R.y,
        eye_rest_world_rot_R, R.parent_index
    );

    update_pupil_dilation(dt);
}

// ─── Manual eye pose ──────────────────────────────────────────────────────────

void apply_manual_eye_pose(int left_eye_index, int right_eye_index)
{
    if (!rest_pose_captured) return;

    float yaw_L = 0.0f;
    float yaw_R = 0.0f;
    float pitch = 0.0f;

    switch (active_eye_axis)
    {
        case INNER_YAW:
            yaw_L =  eye_inner_yaw;
            yaw_R = -eye_inner_yaw;
            break;
        case OUTER_YAW:
            yaw_L = -eye_outer_yaw;
            yaw_R =  eye_outer_yaw;
            break;
        case UP_PITCH:   pitch =  eye_up_pitch;   break;
        case DOWN_PITCH: pitch =  eye_down_pitch; break;
        default: return;
    }

    // Use cached rest rotations — not live global_matrix
    skeleton_bones[left_eye_index].local_rot = angles_to_parent_local(
        -pitch, yaw_L,
        eye_rest_world_rot_L,
        skeleton_bones[left_eye_index].parent_index
    );

    skeleton_bones[right_eye_index].local_rot = angles_to_parent_local(
        -pitch, yaw_R,
        eye_rest_world_rot_R,
        skeleton_bones[right_eye_index].parent_index
    );

    update_skeleton_hierarchy();
}

// ─── Head look-at ─────────────────────────────────────────────────────────────

void apply_head_look_at(
    int              head_bone_index,
    const glm::vec3& target_world,
    float            dt
)
{
    if (head_bone_index < 0 ||
        head_bone_index >= (int)skeleton_bones.size())
        return;

    Bone& head         = skeleton_bones[head_bone_index];
    glm::vec3 head_pos = glm::vec3(head.global_matrix[3]);

    glm::quat parent_rot = (head.parent_index >= 0)
        ? glm::quat_cast(skeleton_bones[head.parent_index].global_matrix)
        : glm::quat(1.0f, 0.0f, 0.0f, 0.0f);

    glm::vec3 target_dir = glm::normalize(target_world - head_pos);
    glm::vec3 local      = glm::inverse(parent_rot) * target_dir;

    float horiz = glm::length(glm::vec2(local.x, local.z));
    float yaw   = glm::degrees(std::atan2(local.x, local.z));
    float pitch = glm::degrees(std::atan2(local.y, horiz));

    const float head_speed = 5.0f;
    float t = 1.0f - std::exp(-head_speed * dt);
    head_smoothed_angles = glm::mix(head_smoothed_angles, glm::vec2(pitch, yaw), t);

    float s_pitch = glm::clamp(head_smoothed_angles.x, -20.0f, 25.0f);
    float s_yaw   = glm::clamp(head_smoothed_angles.y, -40.0f, 40.0f);

    head.local_rot = glm::quat(glm::radians(glm::vec3(-s_pitch, s_yaw, 0.0f)));

    update_skeleton_hierarchy();
}

// ─── Master entry point ───────────────────────────────────────────────────────

void apply_look_at(
    int   head_index,
    int   left_eye_index,
    int   right_eye_index,
    int   target_entity_index,
    float dt
)
{
    if (target_entity_index < 0 ||
        target_entity_index >= (int)entity_world_matrices.size())
        return;

    glm::vec3 target =
        glm::vec3(entity_world_matrices[target_entity_index][3]);

    if (!manual_eye_control)
        apply_eye_look_at(left_eye_index, right_eye_index, target, dt);
    else
        apply_manual_eye_pose(left_eye_index, right_eye_index);

    if (head_tracking_enabled)
        apply_head_look_at(head_index, target, dt);

    update_skeleton_hierarchy();
}

float get_left_eye_yaw()  { return debug_eye_yaw_L; }
float get_right_eye_yaw() { return debug_eye_yaw_R; }