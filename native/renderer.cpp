//#include <GL/glew.h>

#include "glad/glad.h"
#include <GLFW/glfw3.h>
#include <iostream>
#include <vector>
#include <fstream>
#include <sstream>
#include <string>

#include "imgui/imgui.h"
#include "imgui/backends/imgui_impl_glfw.h"
#include "imgui/backends/imgui_impl_opengl3.h"

#include <json.hpp>

#include "camera.hpp"
#include "renderer.hpp"
#include "texture_loader.hpp"
#include "animation.hpp"
#include "scene_builder.hpp"
#include "shaders_embedded.hpp"
#include "lookAt.hpp"

ActiveEyeAxis active_eye_axis = NONE;

std::vector<int> entity_authority;
// Define the global instance
Camera main_camera;
GLuint shaderProgram;
// FLAG: The GrekoEngine Window
GLFWwindow* window;
GLuint g_texture = 0;
glm::vec4 g_base_color = glm::vec4(1.0f);
GLuint current_texture = 0;

using json = nlohmann::json;

float lastX = 640, lastY = 360;
float yaw = -90.0f, pitch = 0.0f;
bool firstMouse = true;
bool escPressedLastFrame = false;
bool mouseLocked = true;
glm::vec3 cameraFront = glm::vec3(0.0f, 0.0f, -1.0f);

float eye_inner_yaw = 8.0f;
float eye_outer_yaw = 6.0f;
float eye_up_pitch  = 4.0f;
float eye_down_pitch = 3.0f;

static bool config_saved = false;
bool manual_eye_control = false;
bool head_tracking_enabled = true;

//struct GPUMesh {
//    GLuint vao;
//    GLuint vbo_pos, vbo_norm, vbo_uv, vbo_joints, vbo_weights, ebo;
//    int index_count;
//    GLuint texture_id;
//    GLuint vbo_morphs[4];
//};

std::vector<GPUMesh> scene_meshes;
float g_morph_weights[4] = {0.0f, 0.0f, 0.0f, 0.0f};
static int last_selected_bone = -1;

// FLAG: Performance Tracking
double lastTime = 0.0;
int nbFrames = 0;
bool editMode = false;
double g_fps = 0.0;

int selected_bone = 0;
std::vector<std::string> entity_names;
int selected_entity_index = 0;
int trackingEntity = -1;

static float config_saved_timer = 0.0f;
static const float CONFIG_SAVED_DISPLAY_DURATION = 2.0f;

std::vector<glm::mat4> entity_world_matrices;
std::vector<glm::vec3> entity_positions;
std::vector<glm::vec3> entity_rotations; // Euler degrees for UI
std::vector<glm::vec3> entity_scales;

glm::vec3 g_lightDirection = glm::vec3(-0.3f, -1.0f, -0.2f); 
glm::vec3 g_lightColor = glm::vec3(1.0f, 0.941176f, 0.862745f); 
glm::vec3 g_ambientColor = glm::vec3(0.2353f, 0.2549f, 0.3137f); 
glm::vec3 g_shadowColor = glm::vec3(0.7843f, 0.6275f, 0.6863f); // Warm pinkish shadow tint — Genshin signature
glm::vec3 g_outerShadowColor = glm::vec3(0.6666667f, 0.5098039f, 0.5686275f);
glm::vec3 g_rimColor = glm::vec3(0.8627f, 0.9020f, 1.0f);;

float g_celLightSmooth = 0.08f;
float g_outerShadowOffset = 0.18f;
float g_outerShadowSmooth = 0.03f;
float g_rimPow = 4.0f;
float g_rimIntensity = 0.35f;



void framebuffer_size_callback(GLFWwindow* window, int width, int height)
{
    glViewport(0, 0, width, height);

    height = std::max(height, 1);

    main_camera.aspect = (float)width / (float)height;
}


void update_fps_counter() {
    double currentTime = glfwGetTime();
    nbFrames++;
    if (currentTime - lastTime >= 1.0) {
        // FLAG: The \r Trick
        // \r moves the cursor back to the start of the line without making a new one.
        // This creates a "live" updating line in your terminal.
        //printf("\rFPS: %d | Cam: [%.1f, %.1f, %.1f]", 
        //        nbFrames, main_camera.pos.x, main_camera.pos.y, main_camera.pos.z);
        //fflush(stdout); 

        if (currentTime - lastTime >= 1.0) {
        g_fps = nbFrames;
        nbFrames = 0;
        lastTime += 1.0;
        }


        //nbFrames = 0;
        //lastTime += 1.0;
    }
}

void mouse_callback(GLFWwindow* window, double xpos, double ypos) {
    if (!mouseLocked) return;

    if (firstMouse) {
        lastX = xpos; 
        lastY = ypos;
        firstMouse = false;
        return;
    }

    float xoffset = xpos - lastX;
    float yoffset = lastY - ypos; // Reversed: y-coordinates go from bottom to top
    lastX = xpos; lastY = ypos;

    float sensitivity = 0.1f;
    xoffset *= sensitivity;
    yoffset *= sensitivity;

    yaw   += xoffset;
    pitch += yoffset;

    // Constraint: Prevent the camera from flipping over
    //if (pitch > 89.0f) pitch = 89.0f;
    //if (pitch < -89.0f) pitch = -89.0f;
    pitch = glm::clamp(pitch, -89.0f, 89.0f);

    // Calculate the new target vector
    glm::vec3 front;
    front.x = cos(glm::radians(yaw)) * cos(glm::radians(pitch));
    front.y = sin(glm::radians(pitch));
    front.z = sin(glm::radians(yaw)) * cos(glm::radians(pitch));

    cameraFront = glm::normalize(front);
    main_camera.target = main_camera.pos + glm::normalize(front);
}

void process_input(float dt) {
    if (!window) return;

    bool escPressed = glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS;

    // FLAG: Escape to Toggle Mouse
    if (escPressed && !escPressedLastFrame) {
        mouseLocked = !mouseLocked;

        if (mouseLocked) { 
            //mouseLocked = false;
            glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
            firstMouse = true;
        } else {
            glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_NORMAL);
        }
    }

    escPressedLastFrame = escPressed;

    float speed = 2.5f * dt;
    glm::vec3 front = cameraFront;//glm::normalize(glm::vec3(cameraFront.x, 0.0f, cameraFront.z));
    //glm::vec3 front;
    //front.x = cos(glm::radians(yaw));
    //front.y = 0.0f;
    //front.z = sin(glm::radians(yaw));
    //front = glm::normalize(front);
    
    //glm::vec3 front = glm::normalize(main_camera.target - main_camera.pos);
    //front.y = 0.0f;
    //front = glm::normalize(front);
    
    glm::vec3 right = glm::normalize(glm::cross(front, main_camera.up));
    
    
    // FLAG: GLFW Key Polling
    if (glfwGetKey(window, GLFW_KEY_W) == GLFW_PRESS)
        main_camera.pos += speed * front; //glm::normalize(main_camera.target - main_camera.pos);
    if (glfwGetKey(window, GLFW_KEY_S) == GLFW_PRESS)
        main_camera.pos -= speed * front; //glm::normalize(main_camera.target - main_camera.pos);
    if (glfwGetKey(window, GLFW_KEY_A) == GLFW_PRESS)
        main_camera.pos -= speed * right; //glm::normalize(glm::cross(main_camera.target - main_camera.pos, main_camera.up)) * speed;
    if (glfwGetKey(window, GLFW_KEY_D) == GLFW_PRESS)
        main_camera.pos += speed * right; //glm::normalize(glm::cross(main_camera.target - main_camera.pos, main_camera.up)) * speed;

    if (glfwGetKey(window, GLFW_KEY_E) == GLFW_PRESS)
        main_camera.pos += speed * main_camera.up;
    if (glfwGetKey(window, GLFW_KEY_Q) == GLFW_PRESS)
        main_camera.pos -= speed * main_camera.up;

    main_camera.target = main_camera.pos + cameraFront;

    //if (glfwGetKey(window, GLFW_KEY_F1) == GLFW_PRESS)
    //    editMode = !editMode;

    if (is_key_pressed(GLFW_KEY_F1))
    {
        editMode = !editMode;
        std::cout << "Edit Mode: " << editMode << std::endl;
    }

}

// FLAG: Shader Loader
// Reads a text file and returns a string
std::string load_shader_source(const std::string& path) {
    std::ifstream file(path);
    std::stringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

GLuint compile_shader(const std::string& path, GLenum type) {
    std::string source = load_shader_source(path);
    const char* src = source.c_str();

    GLuint shader = glCreateShader(type);
    glShaderSource(shader, 1, &src, NULL);
    glCompileShader(shader);

    // FLAG: Error Check
    int success;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &success);
    if (!success) {
        char infoLog[512];
        glGetShaderInfoLog(shader, 512, NULL, infoLog);
        std::cout << "❌ Shader Error (" << path << "):\n" << infoLog << std::endl;
    }
    return shader;
}

GLuint compile_shader_source(const std::string& src, GLenum type) {
    GLuint shader = glCreateShader(type);
    const char* c = src.c_str();
    glShaderSource(shader, 1, &c, nullptr);
    glCompileShader(shader);

    // Error check
    GLint ok;
    glGetShaderiv(shader, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[512];
        glGetShaderInfoLog(shader, 512, nullptr, log);
        fprintf(stderr, "Shader compile error: %s\n", log);
    }
    return shader;
}

void setup_debug_shader() {
    GLuint vs = compile_shader_source(SHADER_WS1_VERT, GL_VERTEX_SHADER); //compile_shader((g_shader_base_path + "Textest.vert").c_str(), GL_VERTEX_SHADER);
    GLuint fs = compile_shader_source(SHADER_WS1_FRAG, GL_FRAGMENT_SHADER); //compile_shader((g_shader_base_path + "Textest.frag").c_str(), GL_FRAGMENT_SHADER);

    shaderProgram = glCreateProgram();
    glAttachShader(shaderProgram, vs);
    glAttachShader(shaderProgram, fs);
    glLinkProgram(shaderProgram);

    // FLAG: Link Error Check
    int success;
    glGetProgramiv(shaderProgram, GL_LINK_STATUS, &success);
    if (!success) {
        char infoLog[512];
        glGetProgramInfoLog(shaderProgram, 512, NULL, infoLog);
        std::cout << "❌ Shader Link Error:\n" << infoLog << std::endl;
    }

    glUseProgram(shaderProgram);
}

int init_renderer(int width, int height) {
    if (!glfwInit()) return -1;

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);

    window = glfwCreateWindow(width, height, "Greko Custom Renderer", NULL, NULL);
    if (!window) {
        glfwTerminate();
        return -1;
    }
    glfwSetCursorPosCallback(window, mouse_callback);
    glfwSetFramebufferSizeCallback(window, framebuffer_size_callback);
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
    glfwMakeContextCurrent(window);
    //glfwSetKeyCallback(window, key_callback);

    if (!gladLoadGL( (GLADloadfunc)glfwGetProcAddress)) {
        std::cerr << "❌ Failed to initialize GLAD\n";
        return -1;
    }

    init_skeleton();

    glfwSwapInterval(0);  // Enabled VSync, change to 0 to turn it off.

    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LESS);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    //glEnable(GL_CULL_FACE);
    
    // FLAG: Don't forget to call this!
    setup_debug_shader();

    // ---- IMGUI INIT ----
    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO(); (void)io;
    //io.FontGlobalScale = 1.1f;
    ImGui::StyleColorsDark();

    ImGui_ImplGlfw_InitForOpenGL(window, true);
    ImGui_ImplOpenGL3_Init("#version 430");

    
    std::cout << "✅ Renderer Initialized: OpenGL " << glGetString(GL_VERSION) << std::endl;
    return 0;
}

void clear_screen() {
    glClearColor(0.1f, 0.1f, 0.12f, 1.0f); // Nice dark grey
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
}

void swap_buffers() {
    // We need dt to make movement smooth regardless of FPS
    static float lastFrame = 0.0f;
    float currentFrame = glfwGetTime();
    float dt = currentFrame - lastFrame;
    lastFrame = currentFrame;

    process_input(dt);
    update_fps_counter();
    
    glfwSwapBuffers(window);
    glfwPollEvents();
}

bool should_close() {
    if (!window) return true;
    glfwPollEvents();
    return glfwWindowShouldClose(window);
}

void terminate() {
    if (window) {
        glfwDestroyWindow(window);
    }
    glfwTerminate();
}

void add_mesh_to_scene(
    const float* vertices, size_t v_size,
    const float* normals, size_t n_size,
    const float* uvs, size_t uv_size,
    const uint32_t* joints, size_t j_size,
    const float* weights, size_t w_size,
    const uint32_t* indices, size_t i_size,
    const std::vector<const float*>& morph_data_ptrs, // List of pointers
    //const std::vector<size_t>& morph_sizes,
    int tex_id,
    int entity_index
) {

    GPUMesh mesh;
    glGenVertexArrays(1, &mesh.vao);
    glBindVertexArray(mesh.vao);
    

    // Positions
    glGenBuffers(1, &mesh.vbo_pos);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo_pos);
    glBufferData(GL_ARRAY_BUFFER, v_size * sizeof(float), vertices, GL_STATIC_DRAW);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, 0);
    glEnableVertexAttribArray(0);

    // Normals
    glGenBuffers(1, &mesh.vbo_norm);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo_norm);
    glBufferData(GL_ARRAY_BUFFER, n_size * sizeof(float), normals, GL_STATIC_DRAW);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, 0);
    glEnableVertexAttribArray(1);

    // UVs
    glGenBuffers(1, &mesh.vbo_uv);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo_uv);
    glBufferData(GL_ARRAY_BUFFER, uv_size * sizeof(float), uvs, GL_STATIC_DRAW);
    glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, 0);
    glEnableVertexAttribArray(2);

    // Indices
    glGenBuffers(1, &mesh.ebo);
    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh.ebo);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, i_size * sizeof(uint32_t), indices, GL_STATIC_DRAW);

    // Joints (location 3)
    glGenBuffers(1, &mesh.vbo_joints);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo_joints);
    glBufferData(GL_ARRAY_BUFFER, j_size * sizeof(uint32_t), joints, GL_STATIC_DRAW);
    glVertexAttribIPointer(3, 4, GL_UNSIGNED_INT, 0, (void*)0);
    glEnableVertexAttribArray(3);

    // Weights (location 4)
    glGenBuffers(1, &mesh.vbo_weights);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo_weights);
    glBufferData(GL_ARRAY_BUFFER, w_size * sizeof(float), weights, GL_STATIC_DRAW);
    glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, 0, 0);
    glEnableVertexAttribArray(4);

    // Morph Targets (locations 5, 6, 7, 8)
    for (int i = 0; i < 4; i++) {
        glGenBuffers(1, &mesh.vbo_morphs[i]);
        glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo_morphs[i]);
        
        if (i < morph_data_ptrs.size() && morph_data_ptrs[i] != nullptr) {
            glBufferData(GL_ARRAY_BUFFER, v_size * sizeof(float), morph_data_ptrs[i], GL_DYNAMIC_DRAW);
        } else {
            std::vector<float> zeros(v_size, 0.0f);
            glBufferData(GL_ARRAY_BUFFER, v_size * sizeof(float), zeros.data(), GL_DYNAMIC_DRAW);
        }

        // FLAG: Use sizeof(float)*3 instead of 0 for the stride
        // This ensures the GPU jumps exactly 12 bytes between vertices
        glVertexAttribPointer(5 + i, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), (void*)0);
        glEnableVertexAttribArray(5 + i);
    }

    mesh.index_count = (int)i_size;
    mesh.texture_id = (GLuint)tex_id;
    mesh.entity_index = entity_index;
    scene_meshes.push_back(mesh);
    //return scene_meshes.size() - 1;
}


// One call from Python draws EVERYTHING stored in the vector.
void draw_scene() {
    build_pending_shapes();

    float dt = (g_fps > 0.0f) ? (1.0f / g_fps) : (1.0f / 60.0f);

    ImGui_ImplOpenGL3_NewFrame();
    ImGui_ImplGlfw_NewFrame();
    ImGui::NewFrame();

    if (manual_eye_control)
    {set_eye_constraints(eye_inner_yaw, eye_outer_yaw, eye_up_pitch, eye_down_pitch);}

    if (config_saved_timer > 0.0f)
        config_saved_timer -= dt;


    // ---- DEBUG OVERLAY (Top-Left HUD Style) ----
    ImGui::SetNextWindowPos(ImVec2(0, 10));
    ImGui::SetNextWindowSize(ImVec2(140, 170));
    ImGui::SetNextWindowBgAlpha(0.35f);
    ImGui::Begin("Debug", nullptr,
        ImGuiWindowFlags_NoMove |
        ImGuiWindowFlags_NoResize |
        ImGuiWindowFlags_NoCollapse |
        ImGuiWindowFlags_AlwaysAutoResize);

    ImGui::Text("FPS: %.0f", g_fps);
    ImGui::Separator();
    ImGui::Text("Camera Position:");
    ImGui::Text("X: %.2f", main_camera.pos.x);
    ImGui::Text("Y: %.2f", main_camera.pos.y);
    ImGui::Text("Z: %.2f", main_camera.pos.z);
    ImGui::Separator();
    ImGui::Text("Yaw: %.2f", yaw);
    ImGui::Text("Pitch: %.2f", pitch);

    ImGui::End();

    if (editMode) {
        ImGui::SetNextWindowPos(ImVec2(0, 180));
        ImGui::SetNextWindowSize(ImVec2(300, 600));
        ImGui::Begin("Bone Inspector", nullptr,
        ImGuiWindowFlags_NoMove 
        | ImGuiWindowFlags_NoResize
        );
        
        // 1. Bone Selection Dropdown
        std::string preview = (selected_bone >= 0 && selected_bone < joint_names.size()) ? 
                              joint_names[selected_bone] : "Select Bone";

        if (ImGui::BeginCombo("Bone##Selector", preview.c_str())) {
            for (int i = 0; i < skeleton_bones.size(); i++) {
                std::string unique_name = std::to_string(i) + " " + skeleton_bones[i].name + "##" + std::to_string(i);
                if (ImGui::Selectable(unique_name.c_str(), selected_bone == i)) {
                    selected_bone = i;  
                }
            }
            ImGui::EndCombo();
        }

        if (ImGui::BeginCombo("Entities", 
            entity_names.empty() ? "None" : entity_names[selected_entity_index].c_str()))
        {
            for (int i = 0; i < entity_names.size(); i++)
            {
                bool is_selected = (selected_entity_index == i);
                if (ImGui::Selectable(entity_names[i].c_str(), is_selected))
                    selected_entity_index = i;
                if (is_selected)
                    ImGui::SetItemDefaultFocus();
            }
            ImGui::EndCombo();
        }

        if (ImGui::Button("Track Selected"))
            trackingEntity = selected_entity_index;
            
        if (trackingEntity >= 0 && trackingEntity < entity_names.size())
            ImGui::Text("Track: %s", entity_names[trackingEntity].c_str());
        else
            ImGui::Text("Track: None");

        if (ImGui::Button("Release Control"))
            entity_authority[selected_entity_index] = AUTH_PYTHON;

        ImGui::Separator();

        if (selected_bone >= 0 && selected_bone < (int)skeleton_bones.size()) {
            Bone& bone = skeleton_bones[selected_bone];
            ImGui::PushID(selected_bone);
        
            if (ImGui::DragFloat3("Position", &bone.local_pos.x, 0.01f))
                update_skeleton_hierarchy();
        
            static glm::vec3 euler = glm::vec3(0.0f);
            if (last_selected_bone != selected_bone) {
                euler = glm::degrees(glm::eulerAngles(bone.local_rot));
                last_selected_bone = selected_bone;
            }
        
            if (ImGui::DragFloat3("Rotation", &euler.x, 0.5f)) {
                bone.local_rot = glm::quat(glm::radians(euler));
                update_skeleton_hierarchy();
            }
        
            if (ImGui::DragFloat3("Scale", &bone.local_scale.x, 0.01f))
                update_skeleton_hierarchy();
        
            if (ImGui::Button("Reset Transform")) {
                bone.local_pos   = glm::vec3(0.0f);
                bone.local_rot   = glm::quat(1,0,0,0);
                bone.local_scale = glm::vec3(1.0f);
                update_skeleton_hierarchy();
            }
            ImGui::PopID();
        }

        ImGui::Separator();
        ImGui::Text("Entity Transform");
            
        if (selected_entity_index >= 0 &&
            selected_entity_index < entity_positions.size())
        {
            glm::vec3& pos = entity_positions[selected_entity_index];
            glm::vec3& rot = entity_rotations[selected_entity_index];
            glm::vec3& scl = entity_scales[selected_entity_index];
        
            bool changed = false;
            changed |= ImGui::DragFloat3("Position##Entity", &pos.x, 0.01f);
            changed |= ImGui::DragFloat3("Rotation##Entity", &rot.x, 0.5f);
            changed |= ImGui::DragFloat3("Scale##Entity",    &scl.x, 0.01f);

            if (changed) {
                int idx = selected_entity_index;
                entity_authority[idx] = AUTH_NATIVE;
                glm::mat4 T  = glm::translate(glm::mat4(1.0f), pos);
                glm::mat4 Rx = glm::rotate(glm::mat4(1.0f), glm::radians(rot.x), glm::vec3(1,0,0));
                glm::mat4 Ry = glm::rotate(glm::mat4(1.0f), glm::radians(rot.y), glm::vec3(0,1,0));
                glm::mat4 Rz = glm::rotate(glm::mat4(1.0f), glm::radians(rot.z), glm::vec3(0,0,1));
                glm::mat4 S  = glm::scale(glm::mat4(1.0f), scl);
                entity_world_matrices[idx] = T * Rz * Ry * Rx * S;
                entity_positions[idx] = pos;
                entity_rotations[idx] = rot;
                entity_scales[idx]    = scl;
            }
        }

        ImGui::Separator();
        ImGui::Text("Head Setting and Eye Constraints");
        
        ImGui::BeginGroup();
        ImGui::Checkbox("Manual Eye Calibration", &manual_eye_control);
        ImGui::Checkbox("Head Tracking",          &head_tracking_enabled);
        float yawL = get_left_eye_yaw();
        float yawR = get_right_eye_yaw();
        ImGui::Text("Left Eye Yaw:  %.3f", yawL);
        ImGui::Text("Right Eye Yaw: %.3f", yawR);
        ImGui::Text("Separation:    %.3f", yawL - yawR);
        ImGui::EndGroup();

        ImGui::Separator();

        if (ImGui::SliderFloat("Eye Inner Yaw", &eye_inner_yaw, 0.0f, 50.0f)) {
            active_eye_axis = INNER_YAW;
            set_eye_constraints(eye_inner_yaw, eye_outer_yaw, eye_up_pitch, eye_down_pitch);
        }
        if (ImGui::SliderFloat("Eye Outer Yaw", &eye_outer_yaw, 0.0f, 50.0f)) {
            active_eye_axis = OUTER_YAW;
            set_eye_constraints(eye_inner_yaw, eye_outer_yaw, eye_up_pitch, eye_down_pitch);
        }
        if (ImGui::SliderFloat("Eye Up Pitch", &eye_up_pitch, 0.0f, 50.0f)) {
            active_eye_axis = UP_PITCH;
            set_eye_constraints(eye_inner_yaw, eye_outer_yaw, eye_up_pitch, eye_down_pitch);
        }
        if (ImGui::SliderFloat("Eye Down Pitch", &eye_down_pitch, 0.0f, 50.0f)) {
            active_eye_axis = DOWN_PITCH;
            set_eye_constraints(eye_inner_yaw, eye_outer_yaw, eye_up_pitch, eye_down_pitch);
        }

        ImGui::Spacing();

        if (ImGui::Button("Save to Config")) {
            save_eye_constraints_to_config();
            config_saved_timer = CONFIG_SAVED_DISPLAY_DURATION;
        }

        if (config_saved_timer > 0.0f) {
            float alpha = glm::clamp(config_saved_timer / 0.5f, 0.0f, 1.0f);
            ImGui::SameLine();
            ImGui::PushStyleColor(ImGuiCol_Text, ImVec4(0.4f, 0.9f, 0.4f, alpha));
            ImGui::Text("Saved!");
            ImGui::PopStyleColor();
        }

        ImGui::End();

        // ---- Lighting + Cel Shader Controls (top-right) ----
        ImGuiViewport* viewport = ImGui::GetMainViewport(); 
        float windowWidth = 320.0f;
        float padding     = 10.0f; 
        ImGui::SetNextWindowPos(ImVec2(viewport->WorkSize.x - windowWidth - padding, 10.0f));
        ImGui::SetNextWindowSize(ImVec2(windowWidth, 520));
            
        ImGui::Begin("Lighting Controls", nullptr, ImGuiWindowFlags_NoCollapse);
        
        ImGui::Text("Directional Light");
        ImGui::DragFloat3("Light Direction", &g_lightDirection.x, 0.01f, -1.0f, 1.0f);
        g_lightDirection = glm::normalize(g_lightDirection);
        ImGui::ColorEdit3("Light Color",   &g_lightColor.x);
        ImGui::ColorEdit3("Ambient Color", &g_ambientColor.x);

        ImGui::Separator();
        ImGui::Text("Cel Shading");

        // uLightSmooth: controls how soft the light/shadow boundary is.
        // 0.0 = perfectly hard (classic toon), 0.1 = Genshin-style slight softness.
        ImGui::SliderFloat("Light Smooth",         &g_celLightSmooth,       0.0f, 0.5f);

        // uShadowColor / uBaseColor: tint lerped across the shadow boundary.
        // Think of shadowColor as "what colour is the dark side", baseColor as "what colour is the lit side".
        // Warm shadows (pinkish) are the Genshin signature look.
        ImGui::ColorEdit3("Shadow Color",          &g_shadowColor.x);
        ImGui::ColorEdit3("Base (Lit) Color",      &g_base_color.x);

        ImGui::Separator();
        ImGui::Text("Outer Shadow");

        // The outer shadow is a second, harder shadow band that sits just outside
        // the main shadow. Offset pushes it further from the terminator, smooth
        // controls how crisp its edge is (keep this low, ~0.02-0.05).
        ImGui::SliderFloat("Outer Offset",         &g_outerShadowOffset,    0.0f, 0.5f);
        ImGui::SliderFloat("Outer Smooth",         &g_outerShadowSmooth,    0.0f, 0.1f);
        ImGui::ColorEdit3("Outer Shadow Color",    &g_outerShadowColor.x);

        ImGui::Separator();
        ImGui::Text("Rim Highlight");

        // Rim highlight: a fresnel-based glow on the lit silhouette edge.
        // The article uses a post-process Sobel pass for this; this is the
        // shader-side fresnel approximation until you add that pass.
        // RimPow controls how tight the rim band is (higher = thinner).
        ImGui::ColorEdit3("Rim Color",             &g_rimColor.x);
        ImGui::SliderFloat("Rim Power",            &g_rimPow,               0.5f, 8.0f);
        ImGui::SliderFloat("Rim Intensity",        &g_rimIntensity,         0.0f, 1.0f);

        ImGui::End();
    }
    

    glUseProgram(shaderProgram);

    // ============================================================
    // CAMERA UNIFORM
    // The fragment shader needs the camera world position to compute
    // the view direction V for fresnel (rim) and metallic UV.
    // ============================================================
    glUniform3fv(
        glGetUniformLocation(shaderProgram, "uCameraPos"),
        1, glm::value_ptr(main_camera.pos)
    );

    // ============================================================
    // LIGHT UNIFORMS (unchanged from before)
    // ============================================================
    glUniform3fv(glGetUniformLocation(shaderProgram, "uLightDirection"), 1, glm::value_ptr(g_lightDirection));
    glUniform3fv(glGetUniformLocation(shaderProgram, "uLightColor"),     1, glm::value_ptr(g_lightColor));
    glUniform3fv(glGetUniformLocation(shaderProgram, "uAmbientColor"),   1, glm::value_ptr(g_ambientColor));

    // ============================================================
    // CEL SHADING UNIFORMS — NEW
    // These were all missing before, which is why the world was dark.
    // ============================================================

    // Main cel boundary softness. 0.1 = Genshin-style. 0.0 = hard toon.
    glUniform1f(
        glGetUniformLocation(shaderProgram, "uLightSmooth"),
        g_celLightSmooth
    );

    // Shadow/lit tint lerp — "more color control" per the article.
    // Warm pink shadow tint is the Genshin signature. Lit side stays white.
    glUniform3fv(glGetUniformLocation(shaderProgram, "uShadowColor"), 1, glm::value_ptr(g_shadowColor));
    glUniform3fv(glGetUniformLocation(shaderProgram, "uBaseColor"),   1, glm::value_ptr(g_base_color));

    // Outer shadow band — thin darker ring just before the main shadow.
    glUniform1f(glGetUniformLocation(shaderProgram, "uOuterShadowOffset"), g_outerShadowOffset);
    glUniform1f(glGetUniformLocation(shaderProgram, "uOuterShadowSmooth"), g_outerShadowSmooth);
    glUniform3fv(glGetUniformLocation(shaderProgram, "uOuterShadowColor"), 1, glm::value_ptr(g_outerShadowColor));

    // Rim / edge highlight (fresnel approximation until Sobel pass is added).
    glUniform3fv(glGetUniformLocation(shaderProgram, "uRimColor"),    1, glm::value_ptr(g_rimColor));
    glUniform1f(glGetUniformLocation(shaderProgram, "uRimPow"),       g_rimPow);
    glUniform1f(glGetUniformLocation(shaderProgram, "uRimIntensity"), g_rimIntensity);

    // ============================================================
    // CAMERA / PROJECTION
    // ============================================================
    glm::mat4 view = main_camera.get_view();
    glm::mat4 proj = main_camera.get_projection();
    glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "view"),       1, GL_FALSE, glm::value_ptr(view));
    glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "projection"), 1, GL_FALSE, glm::value_ptr(proj));

    // ============================================================
    // JOINT MATRICES
    // ============================================================
    GLint jointLoc = glGetUniformLocation(shaderProgram, "uJointMatrices");
    if (jointLoc != -1)
        glUniformMatrix4fv(jointLoc, joint_count, GL_FALSE, glm::value_ptr(joint_matrices[0]));

    // ============================================================
    // PER-MESH DRAW
    // ============================================================
    GLint modelLoc = glGetUniformLocation(shaderProgram, "model");

    for (const auto& mesh : scene_meshes) {
        glm::mat4 model = glm::mat4(1.0f);
        if (mesh.entity_index >= 0 && mesh.entity_index < entity_world_matrices.size())
            model = entity_world_matrices[mesh.entity_index];
        
        glUniformMatrix4fv(modelLoc, 1, GL_FALSE, glm::value_ptr(model));

        // Texture bind
        if (mesh.texture_id != 0) {
            glActiveTexture(GL_TEXTURE0);
            glBindTexture(GL_TEXTURE_2D, mesh.texture_id);
            glUniform1i(glGetUniformLocation(shaderProgram, "uMainTex"), 0);
        }

        // Base color factor
        glUniform4f(glGetUniformLocation(shaderProgram, "uBaseColorFactor"), 1.0f, 1.0f, 1.0f, 1.0f);

        glBindVertexArray(mesh.vao);
        glDrawElements(GL_TRIANGLES, mesh.index_count, GL_UNSIGNED_INT, 0);
    }

    ImGui::Render();
    ImGui_ImplOpenGL3_RenderDrawData(ImGui::GetDrawData());
}

GLuint upload_texture_bytes(const unsigned char* data, int size) {
    g_texture = load_texture_from_memory(data, size, true);
    return g_texture;
}
// Store the uploaded texture ID
void set_current_texture(GLuint tex_id) {
    current_texture = tex_id;
}

void set_morph_weights(float w0, float w1, float w2, float w3) {
    g_morph_weights[0] = w0;
    g_morph_weights[1] = w1;
    g_morph_weights[2] = w2;
    g_morph_weights[3] = w3;

    glUseProgram(shaderProgram);
    GLint loc = glGetUniformLocation(shaderProgram, "uMorphWeights");
    if (loc != -1) {
        // Send all 4 weights to the vec4 in the shader
        glUniform4f(loc, w0, w1, w2, w3);
    }
}

void update_morph_slot(int mesh_index, int slot_index, const float* new_data, size_t data_size) {
    if (mesh_index < 0 || mesh_index >= scene_meshes.size() || slot_index < 0 || slot_index >= 4) {
        return;
    }

    //std::cout << " Mesh: " << mesh_index 
    //      << " Slot: " << slot_index 
    //      << " Size: " << data_size
    //      << std::endl;



    GPUMesh& mesh = scene_meshes[mesh_index];
    glBindVertexArray(mesh.vao);
    glBindBuffer(GL_ARRAY_BUFFER, mesh.vbo_morphs[slot_index]);
    
    // FLAG: glBufferSubData
    // We don't re-allocate (glBufferData), we just "paste" over the existing memory.
    // This is much faster than recreating the buffer.
    glBufferSubData(GL_ARRAY_BUFFER, 0, data_size * sizeof(float), new_data);

    
    // Re-tell the VAO exactly where this slot is. Location for Morph2 is 7.
    //int location = 5 + slot_index; 
    //glVertexAttribPointer(location, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), (void*)0);
    //glEnableVertexAttribArray(location);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindVertexArray(0);
}

#include <unordered_map>

static std::unordered_map<int, bool> previousKeyState;

bool is_key_pressed(int key) {
    if (!window) return false;

    bool current = glfwGetKey(window, key) == GLFW_PRESS;
    bool pressed = current && !previousKeyState[key];

    previousKeyState[key] = current;
    return pressed;
}

bool is_key_down(int key) {
    if (!window) return false;
    return glfwGetKey(window, key) == GLFW_PRESS;
}

void set_joint_count(int count)
{
    joint_count = count;
}

void set_joint_names(const std::vector<std::string>& names)
{
    // 1. Update the global list (used for the dropdown preview text)
    joint_names = names;

    // 2. FLAG: The Internal Sync
    // We need to push these names into the actual Bone structs 
    // so the Inspector loop can find them.
    for (size_t i = 0; i < names.size(); i++) {
        if (i < skeleton_bones.size()) {
            skeleton_bones[i].name = names[i];
        }
    }
    
    std::cout << "🦴 Renderer Sync: Applied names to " << names.size() << " bones." << std::endl;
}

void update_entity_transform(int entity_index, const float* data)
    {
        if (entity_index < 0 || entity_index >= entity_world_matrices.size())
            return;
        if (entity_authority[entity_index] == AUTH_NATIVE)
        return;


        entity_world_matrices[entity_index] = glm::transpose(glm::make_mat4(data));
    }

void save_eye_constraints_to_config()
{
    const std::string config_path = "config.json";

    json config;

    // Load existing config if present
    std::ifstream in(config_path);
    if (in.is_open())
    {
        try
        {
            in >> config;
        }
        catch (...)
        {
            config = json::object();
        }
        in.close();
    }

    config["eye_constraints"] = {
        {"inner_yaw", eye_inner_yaw},
        {"outer_yaw", eye_outer_yaw},
        {"up_pitch", eye_up_pitch},
        {"down_pitch", eye_down_pitch}
    };

    std::ofstream out(config_path);
    out << config.dump(4);
    out.close();
}