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
layout (location = 7) in vec3 aMorph2; // Mouth Phenomes
layout (location = 8) in vec3 aMorph3; // Buffer

// ==========================
// Uniforms
// ==========================
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 uJointMatrices[200];
uniform vec4 uMorphWeights; // [w0, w1, w2, w3]

// ==========================
// Outputs
// ==========================
out vec2 vUV;
out vec3 vWorldNormal; // World-space normal  — for NdotL, fresnel
out vec3 vWorldPos;    // World-space position — for view direction

void main()
{
    // ---- Morph targets ----
    vec3 totalMorphOffset = aMorph0 * uMorphWeights.x
                          + aMorph1 * uMorphWeights.y
                          + aMorph2 * uMorphWeights.z
                          + aMorph3 * uMorphWeights.w;

    vec3 morphedPos = aPos + totalMorphOffset;

    // ---- Skinning ----
    float totalWeight = aWeights.x + aWeights.y + aWeights.z + aWeights.w;
    mat4 skinMatrix;
    if (totalWeight < 0.01) {
        skinMatrix = mat4(1.0);
    } else {
        skinMatrix =
            aWeights.x * uJointMatrices[aJoints.x] +
            aWeights.y * uJointMatrices[aJoints.y] +
            aWeights.z * uJointMatrices[aJoints.z] +
            aWeights.w * uJointMatrices[aJoints.w];
    }

    vec4 skinnedPos = skinMatrix * vec4(morphedPos, 1.0);

    // ---- UV flip (OpenGL bottom-left -> glTF/VRM top-left) ----
    // FLAG: The "Forehead Eye" Fix — keep this
    vUV = vec2(aUV.x, 1.0 - aUV.y);

    // ---- World-space normal ----
    // inverse-transpose handles non-uniform scale correctly
    mat3 normalMatrix = transpose(inverse(mat3(model * skinMatrix)));
    vWorldNormal = normalize(normalMatrix * aNormal);

    // ---- World-space position ----
    vWorldPos = vec3(model * skinnedPos);

    gl_Position = projection * view * model * skinnedPos;
}
