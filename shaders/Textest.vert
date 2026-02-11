#version 430 core

// ==========================
// Vertex Attributes
// ==========================
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aUV;
layout (location = 3) in ivec4 aJoints;
layout (location = 4) in vec4 aWeights;


layout (location = 5) in vec3 aMorph0; // Blink
layout (location = 6) in vec3 aMorph1; // Breath/Surprise
layout (location = 7) in vec3 aMorph2; // Mouth A
layout (location = 8) in vec3 aMorph3; // Mouth I

// ==========================
// Uniforms
// ==========================
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 uJointMatrices[256];

uniform vec4 uMorphWeights; // [w0, w1, w2, w3]

// ==========================
// Outputs
// ==========================
out vec2 vUV;
out vec3 vNormal; // for lighting

void main()
{
    vec3 m0 = aMorph0 * (uMorphWeights.x + 0.000001);
    vec3 m1 = aMorph1 * (uMorphWeights.y + 0.000001);
    vec3 m2 = aMorph2 * (uMorphWeights.z + 0.000001);
    vec3 m3 = aMorph3 * (uMorphWeights.w + 0.000001);

    vec3 totalMorphOffset = m0 + m1 + m2 + m3;

    float totalWeight = aWeights.x + aWeights.y + aWeights.z + aWeights.w;

    vec3 morphedPos = aPos + totalMorphOffset;
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