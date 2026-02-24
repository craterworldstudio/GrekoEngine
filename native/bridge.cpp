#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <string>
#include "renderer.hpp"
#include "animation.hpp"
#include <iostream>

namespace py = pybind11;

// Forward declarations
extern void set_current_texture(GLuint tex_id);

//bool is_key_down(int key);
//bool is_key_pressed(int key);  // edge trigger


void upload_mesh_to_gpu(
    py::array_t<float> vertices,
    py::array_t<float> normals,
    py::array_t<float> uvs,
    py::array_t<uint32_t> joints,
    py::array_t<float> weights,
    py::array_t<uint32_t> indices,
    py::list morph_list, // FLAG: Changed to py::list for multiple arrays
    int tex_id
) {
    auto v_ptr = vertices.data();
    auto n_ptr = normals.data();
    auto uv_ptr = uvs.data();
    auto j_ptr = joints.data();
    auto w_ptr = weights.data();
    auto i_ptr = indices.data();

    // FLAG: The Converter
    // We convert the Python list of NumPy arrays into a C++ vector of pointers
    std::vector<py::array_t<float>> morph_arrays;
    std::vector<const float*> m_ptrs;

    for (auto item : morph_list) {
        py::array_t<float, py::array::c_style | py::array::forcecast> arr =
            item.cast<py::array_t<float, py::array::c_style | py::array::forcecast>>();


        if (arr.size() != vertices.size()) {
        std::cout << "⚠ Morph size mismatch: "
                  << arr.size() << " vs "
                  << vertices.size() << std::endl;
        }

        morph_arrays.push_back(arr);     // KEEP ARRAY ALIVE
        m_ptrs.push_back(arr.data());    // THEN GET POINTER
    }


    // Now this matches the signature in renderer.hpp perfectly!
    add_mesh_to_scene(
        v_ptr, vertices.size(), 
        n_ptr, normals.size(),
        uv_ptr, uvs.size(), 
        j_ptr, joints.size(), 
        w_ptr, weights.size(), 
        i_ptr, indices.size(),
        m_ptrs, // Pass the vector
        tex_id
    );
}

void update_morph_data(int mesh_index, int slot_index, py::array_t<float> new_data) {
    // FLAG: Keep memory alive during the call
    auto arr = new_data.cast<py::array_t<float, py::array::c_style | py::array::forcecast>>();
    
    
    // Call the renderer function we discussed
    update_morph_slot(mesh_index, slot_index, arr.data(), arr.size());
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
    m.def("is_key_down", &is_key_down);
    m.def("is_key_pressed", &is_key_pressed);
    m.def("set_joint_count", &set_joint_count, "Set the number of joints in the skeleton");
    m.def("set_joint_names", &set_joint_names, "Set the list of joint names from the skeleton");

    
    
    // *** Texture upload ***
    m.def("upload_texture", [](py::bytes data, bool srgb) -> int {
        std::string buf = data;
        GLuint tex_id = upload_texture_bytes(
            reinterpret_cast<const unsigned char*>(buf.data()),
            buf.size()
        );
        
        // Set as current texture
        set_current_texture(tex_id);
        
        return static_cast<int>(tex_id);
    }, py::arg("data"), py::arg("srgb") = true,
       "Upload texture from bytes and set as current");

    m.def("update_joints", [](py::array_t<float> matrices) {
        auto r = matrices.unchecked<1>();
        update_joints_from_buffer(r.data(0), (int)r.size());
    }, "Upload new bone matrices to the GPU");

    m.def("set_morph_weights", &set_morph_weights, 
        "Set how much the face expression is applied (0.0 to 1.0)");

    m.def("update_morph_data", &update_morph_data, "Hot-swap a morph target's vertex data");
    
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

   // In bridge.cpp

    m.def("setup_cpp_skeleton", [](int count, std::vector<int> parents, 
                                   py::array_t<float> ibms,
                                   py::array_t<float> rest_pos,
                                   py::array_t<float> rest_rot,
                                   py::array_t<float> rest_scale) {
        skeleton_bones.clear();
        auto r_ibm = ibms.unchecked<2>();
        auto r_pos = rest_pos.unchecked<2>();
        auto r_rot = rest_rot.unchecked<2>();
        auto r_scale = rest_scale.unchecked<2>();
                                
        for (int i = 0; i < count; i++) {
            Bone b;
            b.parent_index = parents[i];

            // 1. Load Inverse Bind Matrix
            float mat_data[16];
            for(int j=0; j<16; j++) mat_data[j] = r_ibm(i, j);
            b.inverse_bind_matrix = glm::make_mat4(mat_data);
            
            // 2. FLAG: Load the Rest Pose
            // This prevents the "Collapsed Soup" at (0,0,0)
            b.local_pos = glm::vec3(r_pos(i, 0), r_pos(i, 1), r_pos(i, 2));
            b.local_rot = glm::quat(r_rot(i, 3), r_rot(i, 0), r_rot(i, 1), r_rot(i, 2)); // W, X, Y, Z
            b.local_scale = glm::vec3(r_scale(i, 0), r_scale(i, 1), r_scale(i, 2));

            skeleton_bones.push_back(b);
        }

        // Calculate the initial world positions immediately
        update_skeleton_hierarchy();
    });
    
    m.def("set_bone_local_rotation", [](int index, float x, float y, float z, float w) {
        if(index >= 0 && index < (int)skeleton_bones.size()) {
            // We use this specific constructor to avoid W-XYZ confusion
            skeleton_bones[index].local_rot = glm::quat(w, x, y, z);

            // FLAG: The Trigger
            // After changing a bone, the whole family tree needs to move.
            update_skeleton_hierarchy(); 
        }
    });

    m.def("set_bone_local_position", [](int index, float x, float y, float z) {
        if(index >= 0 && index < (int)skeleton_bones.size()) {
            skeleton_bones[index].local_pos = glm::vec3(x, y, z);
            update_skeleton_hierarchy();
        }
    });
}