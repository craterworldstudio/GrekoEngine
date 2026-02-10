#version 430 core

// ==========================
// Vertex Attributes
// ==========================
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aUV;
layout (location = 3) in ivec4 aJoints;
layout (location = 4) in vec4 aWeights;
layout (location = 5) in vec3 aPosTarget;

// ==========================
// Uniforms
// ==========================
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 uJointMatrices[256];
uniform float uMorphWeight;

// ==========================
// Outputs
// ==========================
out vec2 vUV;
out vec3 vNormal; // for lighting

void main()
{
    float totalWeight = aWeights.x + aWeights.y + aWeights.z + aWeights.w;

    vec3 morphedPos = aPos + (aPosTarget * uMorphWeight);
    mat4 skinMatrix;
    if (totalWeight < 0.01) {
        // If no weights exist, fall back to a standard static pose
        skinMatrix = mat4(1.0);
    } else {
        skinMatrix = 
            aWeights.x * uJointMatrices[aJoints.x] +
            aWeights.y * uJointMatrices[aJoints.y] +
            aWeights.z * uJointMatrices[aJoints.z] +
            aWeights.w * uJointMatrices[aJoints.w];
    }

    // FLAG: The "Forehead Eye" Fix
    // OpenGL starts (0,0) at the bottom-left. 
    // VRM/glTF textures are authored for top-left.
    // Flipping the Y axis puts the eyes in the sockets.
    vec4 skinnedPos = skinMatrix * vec4(morphedPos, 1.0);
    vUV = vec2(aUV.x, 1.0 - aUV.y); 

    // Pass normal to fragment shader (adjust by model rotation)
    vNormal = mat3(transpose(inverse(model * skinMatrix))) * aNormal;

    gl_Position = projection * view * model * skinnedPos;
}