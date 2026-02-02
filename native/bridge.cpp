#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include "renderer.cpp" // Links the actual OpenGL logic

namespace py = pybind11;

// FLAG: The Uploader
// This function takes NumPy arrays from Python and sends them to the GPU.
void upload_mesh_to_gpu(
    py::array_t<float> vertices,
    py::array_t<float> normals,
    py::array_t<float> uvs,
    py::array_t<uint32_t> joints,
    py::array_t<float> weights,
    py::array_t<uint32_t> indices
) {
    auto v_ptr = vertices.data();
    auto n_ptr = normals.data();
    auto uv_ptr = uvs.data();
    auto j_ptr = joints.data();
    auto w_ptr = weights.data();
    auto i_ptr = indices.data();

    setup_opengl_buffers(
        v_ptr, vertices.size(), 
        n_ptr, normals.size(),
        uv_ptr, uvs.size(), 
        j_ptr, joints.size(), 
        w_ptr, weights.size(), 
        i_ptr, indices.size()
    );
}



// FLAG: The Module Definition
// If it's not in this block, Python can't see it!
PYBIND11_MODULE(greko_native, m) {
    m.doc() = "Greko Engine Native Renderer Bridge";
    
    // Existing functions
    m.def("init_renderer", &init_renderer, "Initialize GLFW and OpenGL");
    m.def("upload_mesh", &upload_mesh_to_gpu, "Upload VRM mesh data to GPU");
    m.def("clear_screen", &clear_screen, "Clear the frame buffer");
    m.def("swap_buffers", &swap_buffers, "Swap window buffers");
    m.def("should_close", &should_close, "Check if the window should exit");
    m.def("terminate", &terminate, "Clean up and close the engine");
    m.def("draw_mesh", &draw_mesh, "Draw the currently loaded mesh");
    // Moves the camera relative to its current position
    m.def("move_camera", [](float x, float y, float z) {
        // Added glm::vec3 explicitly
        main_camera.pos += glm::vec3(x, y, z);
        main_camera.target += glm::vec3(x, y, z); 
    }, "Move camera by x, y, z offset");

    // Rotates the camera target (Q and E rotation)
    m.def("rotate_camera", [](float angle_deg) {
        float rad = glm::radians(angle_deg);
        // Ensure you have #include <cmath> or use glm::cos/sin
        float newX = glm::cos(rad) * (main_camera.target.x - main_camera.pos.x) - glm::sin(rad) * (main_camera.target.z - main_camera.pos.z);
        float newZ = glm::sin(rad) * (main_camera.target.x - main_camera.pos.x) + glm::cos(rad) * (main_camera.target.z - main_camera.pos.z);
        main_camera.target = main_camera.pos + glm::vec3(newX, 0, newZ);
    }, "Rotate camera around Y axis");
    
}