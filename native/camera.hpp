#ifndef CAMERA_H
#define CAMERA_H

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

// FLAG: Camera State
// We put this in a struct to keep it organized
struct Camera {
    glm::vec3 pos    = glm::vec3(0.0f, 1.0f, 1.0f); // Start 4 meters back
    glm::vec3 target = glm::vec3(0.0f, 1.0f, 0.0f); // Look at the chest area
    glm::vec3 up     = glm::vec3(0.0f, 1.0f, 0.0f);
    
    float fov = 45.0f;
    float aspect = 1280.0f / 720.0f;

    // FLAG: Matrix Calculation
    glm::mat4 get_view() {
        return glm::lookAt(pos, target, up);
    }

    glm::mat4 get_projection() {
        return glm::perspective(glm::radians(fov), aspect, 0.1f, 100.0f);
    }
};

// Global camera instance
extern Camera main_camera;

#endif