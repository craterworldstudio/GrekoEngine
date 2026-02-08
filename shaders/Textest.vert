#version 430 core

// ==========================
// Vertex Attributes
// ==========================
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aUV;     // FLAG: Only one declaration needed
layout (location = 3) in ivec4 aJoints;
layout (location = 4) in vec4 aWeights;

// ==========================
// Uniforms
// ==========================
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

// ==========================
// Outputs
// ==========================
out vec2 vUV;
out vec3 vNormal; // Add this so your fragment shader can do lighting

void main()
{
    // FLAG: The "Forehead Eye" Fix
    // OpenGL starts (0,0) at the bottom-left. 
    // VRM/glTF textures are authored for top-left.
    // Flipping the Y axis puts the eyes in the sockets.
    vUV = vec2(aUV.x, 1.0 - aUV.y); 

    // Pass normal to fragment shader (adjust by model rotation)
    vNormal = mat3(transpose(inverse(model))) * aNormal;

    gl_Position = projection * view * model * vec4(aPos, 1.0);
}