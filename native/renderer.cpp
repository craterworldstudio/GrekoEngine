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
bool mouseLocked = true;

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
        lastX = xpos; lastY = ypos;
        firstMouse = false;
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
    if (pitch > 89.0f) pitch = 89.0f;
    if (pitch < -89.0f) pitch = -89.0f;

    // Calculate the new target vector
    glm::vec3 front;
    front.x = cos(glm::radians(yaw)) * cos(glm::radians(pitch));
    front.y = sin(glm::radians(pitch));
    front.z = sin(glm::radians(yaw)) * cos(glm::radians(pitch));
    main_camera.target = main_camera.pos + glm::normalize(front);
}

void process_input(float dt) {
    if (!window) return;

    // FLAG: Escape to Toggle Mouse
    if (glfwGetKey(window, GLFW_KEY_M) == GLFW_PRESS) {
        if (mouseLocked == true) { 
            mouseLocked = false;
            glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_NORMAL); 
        } else if (mouseLocked == false) {
            mouseLocked = true;
            glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_DISABLED);
        }
    }

    float speed = 2.5f * dt;
    glm::vec3 front = glm::normalize(main_camera.target - main_camera.pos);
    front.y = 0.0f;
    front = glm::normalize(front);
    
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

    glfwSwapInterval(1);  // Enabled VSync, change to 0 to turn it off.

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

struct GPUMesh {
    GLuint vao;
    GLuint vbo_pos, vbo_norm, vbo_uv, vbo_joints, vbo_weights, ebo;
    int index_count;
    GLuint texture_id;
};

std::vector<GPUMesh> scene_meshes;

void add_mesh_to_scene(
    const float* vertices, size_t v_size,
    const float* normals, size_t n_size,
    const float* uvs, size_t uv_size,
    const uint32_t* joints, size_t j_size,
    const float* weights, size_t w_size,
    const uint32_t* indices, size_t i_size,
    int tex_id
) {
    GPUMesh mesh;
    mesh.index_count = i_size;
    mesh.texture_id = tex_id;

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
    g_texture = load_texture_from_memory(data, size);
    return g_texture;
}
// Store the uploaded texture ID
void set_current_texture(GLuint tex_id) {
    current_texture = tex_id;
}