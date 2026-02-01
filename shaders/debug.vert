#version 330 core
layout (location = 0) in vec3 aPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main() {
    // FLAG: The Standard 3D Formula
    // Multiply from right to left: Proj * View * Model * Position
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}