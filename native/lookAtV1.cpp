#include "lookAt.hpp"
#include "renderer.hpp"
#include "animation.hpp"
#include <glm/gtx/quaternion.hpp>
#include <glm/gtx/vector_angle.hpp>
#include <iostream>

void set_eye_constraints(
    float inner_yaw,
    float outer_yaw,
    float up_pitch,
    float down_pitch
)
{
    eye_inner_yaw = inner_yaw;
    eye_outer_yaw = outer_yaw;
    eye_up_pitch = up_pitch;
    eye_down_pitch = down_pitch;
}

void rotate_bone_towards(
    Bone& bone,
    const glm::vec3& target,
    float weight,
    const glm::vec3& forward_axis,
    bool use_eye_limits = false,
    bool is_left_eye = false,
    bool invert_pitch = false
)
{

    glm::vec3 bone_pos = glm::vec3(bone.global_matrix[3]);
    glm::vec3 dir = glm::normalize(target - bone_pos);

    glm::vec3 forward(0, 0, 1);
    glm::quat rot = glm::rotation(forward_axis, dir);
    glm::quat parent_rot = glm::quat(1, 0, 0, 0);


    if (bone.parent_index >= 0)
    {
        parent_rot =
            glm::quat_cast(
                skeleton_bones[bone.parent_index].global_matrix
            );

        //rot = glm::inverse(parent_rot) * rot;
    }

    //glm::vec3 euler = glm::degrees(glm::eulerAngles(rot));

    glm::vec3 local_dir =
    glm::normalize(glm::inverse(parent_rot) * dir);

    float forward_sign = (forward_axis.z < 0.0f) ? 1.0f : -1.0f;

    float yaw =
        glm::degrees(std::atan2(local_dir.x, forward_sign * local_dir.z));

    float pitch =
        glm::degrees(std::atan2(local_dir.y, forward_sign * local_dir.z));

    if (invert_pitch)
        pitch = -pitch;

    glm::vec3 euler(pitch, yaw, 0.0f);
    if (use_eye_limits)
    {
        euler.x *= 1.4f;
        euler.y *= 1.6f;
    }

    
    //std::cout
    //<< "Eye Euler: "
    //<< euler.x << ", "
    //<< euler.y << ", "
    //<< euler.z << std::endl;

    float max_up_pitch = use_eye_limits ? eye_up_pitch : 25.0f;
    float max_down_pitch = use_eye_limits ? eye_down_pitch : 20.0f;

    if (euler.x > 0)
        euler.x = glm::min(euler.x, max_up_pitch);
    else
        euler.x = glm::max(euler.x, -max_down_pitch);

    euler.z = 0.0f;

    if (use_eye_limits) {
        if (is_left_eye)
        {
            if (euler.y > 0)
                euler.y = glm::min(euler.y, eye_inner_yaw);
            else
                euler.y = glm::max(euler.y, -eye_outer_yaw);
        }
        else
        {
            if (euler.y > 0)
                euler.y = glm::min(euler.y, eye_outer_yaw);
            else
                euler.y = glm::max(euler.y, -eye_inner_yaw);
        }
    }

    rot = glm::quat(glm::radians(euler));

    bone.local_rot = glm::slerp(
        bone.local_rot,
        rot,
        weight
    );
}



void apply_eye_look_at(
    int Leye_index,
    int Reye_index, 
    const glm::vec3& target_entity_index
) {
    //float eye_weight = 1.0f - t;

    Bone& left_eye = skeleton_bones[Leye_index];
    Bone& right_eye = skeleton_bones[Reye_index];

    glm::vec3 left_eye_pos =
        glm::vec3(left_eye.global_matrix[3]);

    glm::vec3 right_eye_pos =
        glm::vec3(right_eye.global_matrix[3]);


    float target_distance =
        glm::length(target_entity_index - 0.5f * (left_eye_pos + right_eye_pos));

    float weight =
    glm::mix(0.25f, 0.12f,
        glm::clamp(target_distance / 2.0f, 0.0f, 1.0f));



    rotate_bone_towards(
        left_eye,
        target_entity_index,
        weight,
        glm::vec3(0, 0, -1),
        true,
        true
    );

    rotate_bone_towards(
        right_eye,
        target_entity_index,
        weight,
        glm::vec3(0, 0, -1),
        true,
        false
    );
}

void apply_manual_eye_pose(
    int left_eye_index,
    int right_eye_index
)
{

    Bone& left_eye = skeleton_bones[left_eye_index];
    Bone& right_eye = skeleton_bones[right_eye_index];

    glm::vec3 left_eye_pos =
        glm::vec3(
            left_eye.global_matrix[3]
        );

    glm::vec3 right_eye_pos =
        glm::vec3(
            right_eye.global_matrix[3]
        );
    

    float yaw = 0.0f;
    float pitch = 0.0f;

    switch (active_eye_axis)
    {
        case INNER_YAW:
            yaw = eye_inner_yaw;
            break;

        case OUTER_YAW:
            yaw = eye_outer_yaw;
            break;

        case UP_PITCH:
            pitch = eye_up_pitch;
            break;

        case DOWN_PITCH:
            pitch = eye_down_pitch;
            break;

        default:
            return;
    }

    glm::vec3 forward(0, 0, 1);

    glm::quat manual_rot =
        glm::quat(
            glm::radians(
                glm::vec3(pitch, yaw, 0.0f)
            )
        );

    glm::quat left_rot =
        glm::quat(
            glm::radians(glm::vec3(pitch, yaw, 0.0f))
        );

    glm::quat right_rot =
        glm::quat(
            glm::radians(glm::vec3(pitch, -yaw, 0.0f))
        );

    //glm::vec3 left_target =
    //    left_eye_pos + (manual_rot * forward);
//
    //glm::vec3 right_target =
    //    right_eye_pos + (manual_rot * forward);

    //rotate_bone_towards(
    //    skeleton_bones[left_eye_index],
    //    left_target,
    //    1.0f,
    //    180.0f,
    //    180.0f,
    //    glm::vec3(0, 0, 1)
    //);
//
    //rotate_bone_towards(
    //    skeleton_bones[right_eye_index],
    //    right_target,
    //    1.0f,
    //    180.0f,
    //    180.0f,
    //    glm::vec3(0, 0, 1)
    //);

    left_eye.local_rot = glm::slerp(
        left_eye.local_rot,
        left_rot,
        1.0f
    );

    right_eye.local_rot = glm::slerp(
        right_eye.local_rot,
        right_rot,
        1.0f
    );

    update_skeleton_hierarchy();
}


void apply_head_look_at(
    int head_bone_index,
    const glm::vec3& target_entity_index
)
{
    
    if (head_bone_index < 0 || head_bone_index >= (int)skeleton_bones.size())
        return;
    

    //if (target_entity_index < 0 || 
    //    target_entity_index >= (int)entity_world_matrices.size())
    //    return;

    //glm::vec3 target =
    //    glm::vec3(entity_world_matrices[target_entity_index][3]);

    float weight = 0.6f;

    //Bone& bone = skeleton_bones[head_bone_index];
    //
    //glm::vec3 target = glm::vec3(entity_world_matrices[target_entity_index][3]);
    //glm::vec3 bone_world_pos = glm::vec3(bone.global_matrix[3]);
    //glm::vec3 dir = glm::normalize(target - bone_world_pos);
    //
    //// Forward axis assumption (+Z)
    //glm::vec3 forward = glm::vec3(0, 0, 1);
    //glm::quat look_rot = glm::rotation(forward, dir);
    //
    //// Convert to local space relative to parent
    //if (bone.parent_index >= 0)
    //{
    //    glm::mat4 parent_world = skeleton_bones[bone.parent_index].global_matrix;
    //    glm::quat parent_rot = glm::quat_cast(parent_world);
    //    look_rot = glm::inverse(parent_rot) * look_rot;
    //}
    //
    //bone.local_rot = glm::slerp(bone.local_rot, look_rot, weight);
    //
    Bone& head = skeleton_bones[head_bone_index];

    glm::vec3 head_pos =
        glm::vec3(head.global_matrix[3]);

    glm::vec3 current_forward =
        glm::normalize(
            glm::vec3(head.global_matrix * glm::vec4(0,0,1,0))
        );

    glm::vec3 target_dir =
        glm::normalize(target_entity_index - head_pos);

    float angle_deg =
        glm::degrees(
            glm::angle(current_forward, target_dir)
        );

    float t = glm::clamp(
        angle_deg / 40.0f,
        0.0f,
        0.7f
    );
    
    float head_weight = t;
    

    rotate_bone_towards(
        skeleton_bones[head_bone_index],
        target_entity_index,
        head_weight,
        glm::vec3(0, 0, -1),
        false,
        false,
        true
    );

    update_skeleton_hierarchy();
}

void apply_look_at(
    int head_index,
    int left_eye_index,
    int right_eye_index,
    int target_entity_index
)
{
    if (target_entity_index < 0 ||
        target_entity_index >= entity_world_matrices.size())
        return;

    glm::vec3 target =
        glm::vec3(entity_world_matrices[target_entity_index][3]);
    
    if (!manual_eye_control) {
        apply_eye_look_at(
        left_eye_index,
        right_eye_index,
        target
        );
    } 

    else
    {
        apply_manual_eye_pose(
            left_eye_index, 
            right_eye_index
        );
    }
    
    
    if (head_tracking_enabled) {
        apply_head_look_at(
            head_index,
            target
        );
    }
    //apply_head_look_at(
    //    head_index,
    //    target
    //);

    update_skeleton_hierarchy();
}