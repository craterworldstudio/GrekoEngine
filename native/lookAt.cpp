#include "lookAt.hpp"
#include "animation.hpp"
#define GLM_ENABLE_EXPERIMENTAL
#include <glm/gtx/quaternion.hpp>

void apply_look_at(int bone_index, float tx, float ty, float tz) {
    if (bone_index < 0 || bone_index >= (int)skeleton_bones.size())
        return;

    float weight = 0.6f;

    Bone& bone = skeleton_bones[bone_index];

    glm::vec3 target(tx, ty, tz);

    // Get bone world position
    glm::vec3 bone_world_pos = glm::vec3(bone.global_matrix[3]);

    glm::vec3 dir = glm::normalize(target - bone_world_pos);

    // Assuming forward axis is +Z
    glm::vec3 forward = glm::vec3(0, 0, 1);

    glm::quat look_rot = glm::rotation(forward, dir);

    // Convert to local space (relative to parent)
    if (bone.parent_index >= 0) {
        glm::mat4 parent_world = skeleton_bones[bone.parent_index].global_matrix;
        glm::quat parent_rot = glm::quat_cast(parent_world);
        look_rot = glm::inverse(parent_rot) * look_rot;
    }

    bone.local_rot = glm::slerp(bone.local_rot, look_rot, weight);

    update_skeleton_hierarchy();
}