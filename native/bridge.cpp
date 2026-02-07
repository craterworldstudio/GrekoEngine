#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <string>
#include "renderer.hpp"

namespace py = pybind11;

// Forward declarations
extern void set_current_texture(GLuint tex_id);

void upload_mesh_to_gpu(
    py::array_t<float> vertices,
    py::array_t<float> normals,
    py::array_t<float> uvs,
    py::array_t<uint32_t> joints,
    py::array_t<float> weights,
    py::array_t<uint32_t> indices,
    int tex_id
) {
    auto v_ptr = vertices.data();
    auto n_ptr = normals.data();
    auto uv_ptr = uvs.data();
    auto j_ptr = joints.data();
    auto w_ptr = weights.data();
    auto i_ptr = indices.data();

    add_mesh_to_scene(
        v_ptr, vertices.size(), 
        n_ptr, normals.size(),
        uv_ptr, uvs.size(), 
        j_ptr, joints.size(), 
        w_ptr, weights.size(), 
        i_ptr, indices.size(),
        tex_id
    );
}

PYBIND11_MODULE(greko_native, m) {
    m.doc() = "Greko Engine Native Renderer Bridge";
    
    // Core functions
    m.def("init_renderer", &init_renderer);
    m.def("upload_mesh", &upload_mesh_to_gpu);
    m.def("clear_screen", &clear_screen);
    m.def("swap_buffers", &swap_buffers);
    m.def("should_close", &should_close);
    m.def("terminate", &terminate);
    m.def("draw_scene", &draw_scene);
    
    // *** CRITICAL FIX: Texture upload ***
    m.def("upload_texture", [](py::bytes data, bool srgb) -> int {
        std::string buf = data;
        GLuint tex_id = upload_texture_bytes(
            reinterpret_cast<const unsigned char*>(buf.data()),
            buf.size()
        );
        
        // CRITICAL: Set as current texture
        set_current_texture(tex_id);
        
        return static_cast<int>(tex_id);
    }, py::arg("data"), py::arg("srgb") = true,
       "Upload texture from bytes and set as current");
    
    // Camera controls
    m.def("set_camera_position", [](float x, float y, float z) {
        main_camera.pos = glm::vec3(x, y, z);
    });
    
    m.def("set_camera_target", [](float x, float y, float z) {
        main_camera.target = glm::vec3(x, y, z);
    });
    
    m.def("move_camera", [](float x, float y, float z) {
        main_camera.pos += glm::vec3(x, y, z);
        main_camera.target += glm::vec3(x, y, z); 
    });
    m.def("set_current_texture", &set_current_texture, "Set the active texture ID for rendering");
    m.def("rotate_camera", [](float angle_deg) {
        float rad = glm::radians(angle_deg);
        float newX = glm::cos(rad) * (main_camera.target.x - main_camera.pos.x) - 
                     glm::sin(rad) * (main_camera.target.z - main_camera.pos.z);
        float newZ = glm::sin(rad) * (main_camera.target.x - main_camera.pos.x) + 
                     glm::cos(rad) * (main_camera.target.z - main_camera.pos.z);
        main_camera.target = main_camera.pos + glm::vec3(newX, 0, newZ);
    });
}