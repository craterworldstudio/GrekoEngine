#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <vector>
#include <string>
#include <functional>
#include "renderer.hpp"
#include "animation.hpp"
#include "lookAt.hpp"
#include <iostream>
#include "gameObjectShapes/primitives.hpp"
#include "scene_builder.hpp"

namespace py = pybind11;

// Forward declarations
extern void set_current_texture(GLuint tex_id);
void set_face_morph_targets(const std::vector<std::string>& target_names);
void set_face_morph_targets_dual(const std::vector<std::string>& raw_names, const std::vector<std::string>& display_names);
void invoke_morph_assignment_callback(int behavior_id, const std::string& target_name);
// Blinker strength accessors implemented in renderer.cpp
void set_blinker_strength(float s);
float get_blinker_strength();

static PyObject* g_morph_assignment_pyobj = nullptr;

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
    int tex_id,
    int entity_index,
    int vertex_count
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
        tex_id,
        entity_index
    );
}

void set_shader_base_path(const std::string& path) {
    g_shader_base_path = path;
    // Ensure trailing slash
    if (!g_shader_base_path.empty() && g_shader_base_path.back() != '/')
        g_shader_base_path += '/';
}


void update_morph_data(int mesh_index, int slot_index, py::array_t<float> new_data) {
    // FLAG: Keep memory alive during the call
    auto arr = new_data.cast<py::array_t<float, py::array::c_style | py::array::forcecast>>();
    
    
    // Call the renderer function we discussed
    update_morph_slot(mesh_index, slot_index, arr.data(), arr.size());
}

void clear_morph_assignment_callback() {
    py::gil_scoped_acquire acquire;
    if (g_morph_assignment_pyobj) {
        Py_XDECREF(g_morph_assignment_pyobj);
        g_morph_assignment_pyobj = nullptr;
    }
}

void invoke_morph_assignment_callback(int behavior_id, const std::string& target_name) {
    if (!g_morph_assignment_pyobj) {
        std::cout << "⚠️ [C++] Morph assignment callback is not registered." << std::endl;
        return;
    }

    py::gil_scoped_acquire acquire;
    try {
        py::object cb = py::reinterpret_borrow<py::object>(g_morph_assignment_pyobj);
        cb(behavior_id, target_name);
    } catch (const std::exception& ex) {
        std::cout << "❌ [C++] Morph assignment callback failed: " << ex.what() << std::endl;
    }
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
    m.def("set_face_morph_targets", &set_face_morph_targets, "Supply the renderer with available face morph names from the loaded model");
    m.def("set_face_morph_targets_dual", &set_face_morph_targets_dual, "Supply the renderer with parallel raw keys and display names for face morphs");
    m.def("set_face_morph_slot_selections", &set_face_morph_slot_selections, "Sync the selected morph target indices for all face morph assignment slots");
    m.def("register_morph_assignment_callback", [](py::function callback) {
        py::gil_scoped_acquire acquire;
        // If we already had a stored callback, DECREF it safely here (we hold the GIL)
        if (g_morph_assignment_pyobj) {
            Py_XDECREF(g_morph_assignment_pyobj);
            g_morph_assignment_pyobj = nullptr;
        }

        // Keep a borrowed reference by INCREF'ing the raw PyObject* so it stays alive.
        Py_XINCREF(callback.ptr());
        g_morph_assignment_pyobj = callback.ptr();
    }, "Register a Python callback for morph slot assignment changes from the native UI");
    m.def("clear_morph_assignment_callback", &clear_morph_assignment_callback, 
        "Clear the stored Python morph assignment callback and release its reference");
    
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

    m.def("set_current_texture", &set_current_texture, "Set the active texture ID for rendering");

    m.def("update_joints", [](py::array_t<float> matrices) {
        auto r = matrices.unchecked<1>();
        update_joints_from_buffer(r.data(0), (int)r.size());
    }, "Upload new bone matrices to the GPU");

    m.def("set_morph_weights", &set_morph_weights, 
        "Set how much the face expression is applied (0.0 to 1.0)");

    m.def("set_blinker_strength", &set_blinker_strength, "Set the global blinker strength from Python");
    m.def("get_blinker_strength", &get_blinker_strength, "Get the global blinker strength") ;

    m.def("update_morph_data", &update_morph_data, "Hot-swap a morph target's vertex data");
    
    // Camera controls
    m.def("set_camera_position", [](float x, float y, float z) {
        main_camera.pos = glm::vec3(x, y, z);
    });
    
    m.def("set_camera_target", [](float x, float y, float z) {
        main_camera.target = glm::vec3(x, y, z);
    });

    m.def("get_camera_position", []() {
        return std::vector<float>{
            main_camera.pos.x,
            main_camera.pos.y,
            main_camera.pos.z
        };
    });
    
    m.def("get_camera_target", []() {
        return std::vector<float>{
            main_camera.target.x,
            main_camera.target.y,
            main_camera.target.z
        };
    });

    m.def("get_camera_front", []() {
        return std::vector<float>{
            cameraFront.x,
            cameraFront.y,
            cameraFront.z
        };
    });

    m.def("get_camera_yaw", []() {
        return yaw;
    });

    m.def("get_camera_pitch", []() {
        return pitch;
    });

    m.def("move_camera", [](float x, float y, float z) {
        main_camera.pos += glm::vec3(x, y, z);
        main_camera.target += glm::vec3(x, y, z); 
    });

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
            b.bind_pos = glm::vec3(r_pos(i, 0), r_pos(i, 1), r_pos(i, 2));
            b.bind_rot = glm::quat(r_rot(i, 3), r_rot(i, 0), r_rot(i, 1), r_rot(i, 2)); // W, X, Y, Z
            b.bind_scale = glm::vec3(r_scale(i, 0), r_scale(i, 1), r_scale(i, 2));

            b.local_pos = b.bind_pos ;
            b.local_rot = b.bind_rot ;
            b.local_scale= b.bind_scale ;

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

    m.def("apply_look_at", &apply_look_at);
    //m.def("apply_head_look_at", &apply_head_look_at);
    //m.def("apply_eye_look_at", &apply_eye_look_at);
    m.def("reset_to_bind_pose", &reset_to_bind_pose);

    m.def("set_entity_list", [](std::vector<std::string> names) {
        entity_names = names;

        entity_world_matrices.clear();
        entity_authority.clear();
        entity_positions.clear();
        entity_rotations.clear();
        entity_scales.clear();

        for (size_t i = 0; i < names.size(); i++) {
            entity_world_matrices.push_back(glm::mat4(1.0f));
            entity_authority.push_back(AUTH_PYTHON);
            entity_positions.push_back(glm::vec3(0.0f));
            entity_rotations.push_back(glm::vec3(0.0f));
            entity_scales.push_back(glm::vec3(1.0f));
        }
    });

    m.def("get_selected_entity_index", []() {
        return trackingEntity;
    });

    m.def("update_entity_transform", [](int index, py::array_t<float> mat) {
        if (mat.size() != 16) throw std::runtime_error("Matrix must contain 16 floats");
        auto r = mat.unchecked<1>();
        update_entity_transform(index, r.data(0));
    });

    m.def("upload_shapes", [](py::list shape_list)
    {
        std::vector<ShapeDescriptor> shapes;

        for (auto item : shape_list)
        {
            py::dict d = item.cast<py::dict>();
        
            ShapeDescriptor shape;
            shape.type = d["type"].cast<std::string>();
            shape.entity_index = d["entity"].cast<int>();
        
            if (shape.type == "cube")
                shape.size = d["size"].cast<float>();
        
            if (shape.type == "sphere")
            {
                shape.radius = d["radius"].cast<float>();
                shape.segments = d["segments"].cast<int>();
            }
        
            shapes.push_back(shape);
        }
    
        upload_shapes(shapes);
    });

    m.def("get_entity_position", [](int idx) {
        return std::vector<float>{
            entity_positions[idx].x,
            entity_positions[idx].y,
            entity_positions[idx].z
        };
    });

    m.def("get_entity_rotation", [](int idx) {
        return std::vector<float>{
            entity_rotations[idx].x,
            entity_rotations[idx].y,
            entity_rotations[idx].z
        };
    });

    m.def("get_entity_scale", [](int idx) {
        return std::vector<float>{
            entity_scales[idx].x,
            entity_scales[idx].y,
            entity_scales[idx].z
        };
    });

    m.def("get_entity_authority", [](int idx) {
        return entity_authority[idx];
    });

    m.def("add_shader_path", &set_shader_base_path);

    m.def(
        "set_eye_constraints",
        &set_eye_constraints,
        "Set eye look-at constraint values"
    );

    m.def("init_lookat", &init_look_at);
}