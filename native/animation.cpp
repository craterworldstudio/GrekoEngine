#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <vector>

// FLAG: The Global Skeleton
// We keep this here so it's not cluttering up the main renderer.
glm::mat4 joint_matrices[256];

void init_skeleton() {
    // FLAG: Identity Matrix Loop
    // This stops Kisayo from disappearing before you start the animation.
    for (int i = 0; i < 256; i++) {
        joint_matrices[i] = glm::mat4(1.0f);
    }
}

void update_joints_from_buffer(const float* data, int count) {
    // 16 floats per mat4
    int num_matrices = count / 16;
    if (num_matrices > 256) num_matrices = 256;

    for (int i = 0; i < num_matrices; i++) {
        // glm::make_mat4 copies the raw floats into our matrix array
        joint_matrices[i] = glm::make_mat4(&data[i * 16]);
    }
}