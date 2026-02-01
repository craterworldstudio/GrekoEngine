#version 330 core
in vec2 TexCoords;
out vec4 FragColor;

void main() {
    // If we see this neon pink, we know the shader is working
    FragColor = vec4(1.0, 0.0, 1.0, 1.0); 
}