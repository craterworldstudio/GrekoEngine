#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <vector>
#include <string>

// FLAG: The Global Skeleton
// We keep this here so it's not cluttering up the main renderer.
int joint_count = 0;
glm::mat4 joint_matrices[256];
std::vector<std::string> joint_names;


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
    joint_count = num_matrices;

    for (int i = 0; i < num_matrices; i++) {
        // glm::make_mat4 copies the raw floats into our matrix array
        joint_matrices[i] = glm::make_mat4(&data[i * 16]);
    }
}