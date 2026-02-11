//#include <GL/glew.h>

#include "glad/glad.h"
#include <GLFW/glfw3.h>
#include <iostream>
#include <vector>
#include <fstream>
#include <sstream>
#include <string>

#include "camera.hpp"
#include "renderer.hpp"
#include "texture_loader.hpp"
#include "animation.hpp"

// Define the global instance
Camera main_camera;
GLuint shaderProgram;
// FLAG: The GrekoEngine Window
GLFWwindow* window;
GLuint g_texture = 0;
glm::vec4 g_base_color = glm::vec4(1.0f);
GLuint current_texture = 0;

float lastX = 640, lastY = 360;
float yaw = -90.0f, pitch = 0.0f;
bool firstMouse = true;
bool escPressedLastFrame = false;
bool mouseLocked = true;
glm::vec3 cameraFront = glm::vec3(0.0f, 0.0f, -1.0f);

//struct GPUMesh {
//    GLuint vao;
//    GLuint vbo_pos, vbo_norm, vbo_uv, vbo_joints, vbo_weights, ebo;
//    int index_count;
//    GLuint texture_id;
//    GLuint vbo_morphs[4];
//};

std::vector<GPUMesh> scene_meshes;
float g_morph_weights[4] = {0.0f, 0.0f, 0.0f, 0.0f};

// FLAG: Performance Tracking
double lastTime = 0.0;
int nbFrames = 0;

void update_fps_counter() {
    double currentTime = glfwGetTime();
    nbFrames++;
    if (currentTime - lastTime >= 1.0) {
        // FLAG: The \r Trick
        // \r moves the cursor back to the start of the line without making a new one.
        // This creates a "live" updating line in your terminal.
        printf("\rFPS: %d | Cam: [%.1f, %.1f, %.1f]", 
                nbFrames, main_camera.pos.x, main_camera.pos.y, main_camera.pos.z);
        fflush(stdout); 

        nbFrames = 0;
        lastTime += 1.0;
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

void setup_debug_shader() {
    GLuint vs = compile_shader("shaders/Textest.vert", GL_VERTEX_SHADER);
    GLuint fs = compile_shader("shaders/Textest.frag", GL_FRAGMENT_SHADER);

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
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
    glfwMakeContextCurrent(window);

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
    int tex_id
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
    glVertexAttribIPointer(3, 4, GL_INT, 0, (void*)0);
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
            glBufferData(GL_ARRAY_BUFFER, v_size * sizeof(float), morph_data_ptrs[i], GL_STATIC_DRAW);
        } else {
            std::vector<float> zeros(v_size, 0.0f);
            glBufferData(GL_ARRAY_BUFFER, v_size * sizeof(float), zeros.data(), GL_STATIC_DRAW);
        }

        // FLAG: Use sizeof(float)*3 instead of 0 for the stride
        // This ensures the GPU jumps exactly 12 bytes between vertices
        glVertexAttribPointer(5 + i, 3, GL_FLOAT, GL_FALSE, 3 * sizeof(float), (void*)0);
        glEnableVertexAttribArray(5 + i);
    }

    mesh.index_count = (int)i_size;
    mesh.texture_id = (GLuint)tex_id;
    scene_meshes.push_back(mesh);
    //return scene_meshes.size() - 1;
}

// One call from Python draws EVERYTHING stored in the vector.
void draw_scene() {
    glUseProgram(shaderProgram);

    glm::mat4 view = main_camera.get_view();
    glm::mat4 proj = main_camera.get_projection();
    glm::mat4 model = glm::mat4(1.0f);

    glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "view"), 1, GL_FALSE, glm::value_ptr(view));
    glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "projection"), 1, GL_FALSE, glm::value_ptr(proj));
    glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "model"), 1, GL_FALSE, glm::value_ptr(model));

    //glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "view"), 1, GL_FALSE, &view[0][0]);
    //glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "projection"), 1, GL_FALSE, &proj[0][0]);
    //glUniformMatrix4fv(glGetUniformLocation(shaderProgram, "model"), 1, GL_FALSE, &model[0][0]);

    GLint jointLoc = glGetUniformLocation(shaderProgram, "uJointMatrices");
    if (jointLoc != -1) {
        glUniformMatrix4fv(jointLoc, 256, GL_FALSE, glm::value_ptr(joint_matrices[0]));
    }

    for (const auto& mesh : scene_meshes) {
        // FLAG: The Critical Texture Bind
        // We use mesh.texture_id (which Python sent) instead of a global variable.
        if (mesh.texture_id != 0) {
            glActiveTexture(GL_TEXTURE0); 
            glBindTexture(GL_TEXTURE_2D, mesh.texture_id);
            
            // Tell the shader: "Use Texture Unit 0"
            GLint texLoc = glGetUniformLocation(shaderProgram, "uMainTex");
            glUniform1i(texLoc, 0);
        }

        // FLAG: Base Color Safety
        // If it's black, Kisayo will be a shadow. Let's force it to White (1.0) for now.
        GLint colorLoc = glGetUniformLocation(shaderProgram, "uBaseColorFactor");
        glUniform4f(colorLoc, 1.0f, 1.0f, 1.0f, 1.0f);

        glBindVertexArray(mesh.vao);
        glDrawElements(GL_TRIANGLES, mesh.index_count, GL_UNSIGNED_INT, 0);
    }
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