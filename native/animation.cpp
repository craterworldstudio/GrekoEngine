#include "animation.hpp"
#include <glm/gtc/quaternion.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

// FLAG: The Actual Memory Definitions
// These must exist in exactly one .cpp file without the 'extern' keyword
int joint_count = 0;
glm::mat4 joint_matrices[MAX_GPU_JOINTS];
std::vector<std::string> joint_names;
std::vector<Bone> skeleton_bones;

void init_skeleton() {
    // Reset bones and set identity matrices
    skeleton_bones.clear();
    for (int i = 0; i < MAX_GPU_JOINTS; i++) {
        joint_matrices[i] = glm::mat4(1.0f);
    }
}

glm::mat4 get_world_matrix(int index) {
    if (index < 0) return glm::mat4(1.0f);
    Bone& bone = skeleton_bones[index];

    // Build Local Matrix: Translation * Rotation * Scale
    glm::mat4 local = glm::translate(glm::mat4(1.0f), bone.local_pos) * glm::mat4_cast(bone.local_rot) * glm::scale(glm::mat4(1.0f), bone.local_scale);

    if (bone.parent_index == -1) return local;

    // Recurse: Parent World * My Local
    return get_world_matrix(bone.parent_index) * local;
}

// FLAG: The CPU Muscle
// This is what allows the ImGui editor to move the mesh in real-time
void update_skeleton_hierarchy() {
    for (int i = 0; i < (int)skeleton_bones.size(); i++) {
        
        skeleton_bones[i].global_matrix = get_world_matrix(i);

        // 3. Prepare for Shader (Skinning)
        // We multiply by Inverse Bind to move vertices from Model Space to Bone Space
        if (i < MAX_GPU_JOINTS) {
            joint_matrices[i] =  skeleton_bones[i].global_matrix * skeleton_bones[i].inverse_bind_matrix;
        }
    }
}

// Keep this for backward compatibility with your existing animator
void update_joints_from_buffer(const float* data, int count) {
    int num_matrices = count / 16;
    if (num_matrices > MAX_GPU_JOINTS) num_matrices = MAX_GPU_JOINTS;
    joint_count = num_matrices;

    for (int i = 0; i < num_matrices; i++) {
        joint_matrices[i] = glm::make_mat4(&data[i * 16]);
    }
}

void reset_to_bind_pose() {
    for (auto& bone : skeleton_bones) {
        bone.local_pos   = bone.bind_pos;
        bone.local_rot   = bone.bind_rot;
        bone.local_scale = bone.bind_scale;
    }

    update_skeleton_hierarchy();
}
