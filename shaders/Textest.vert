#version 430 core

// ==========================
// Vertex Attributes
// ==========================
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aUV;
layout (location = 3) in ivec4 aJoints;
layout (location = 4) in vec4 aWeights;

// ==========================
// Uniforms (MATCH C++)
// ==========================
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

// ==========================
// Outputs
// ==========================
out vec2 vUV;

void main()
{
    vUV = aUV;
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
