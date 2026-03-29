#pragma once
#include <string>

// ── Textest Vertex Shader ──────────────────────────────────────────
static const std::string SHADER_TEXTEST_VERT = R"GLSL(

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
uniform mat4 uJointMatrices[256];

uniform vec4 uMorphWeights; // [w0, w1, w2, w3]

// ==========================
// Outputs
// ==========================
out vec2 vUV;
out vec3 vNormal; // for lighting

void main()
{
    vec3 m0 = aMorph0 * uMorphWeights.x;
    vec3 m1 = aMorph1 * uMorphWeights.y;
    vec3 m2 = aMorph2 * uMorphWeights.z;
    vec3 m3 = aMorph3 * uMorphWeights.w;

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


)GLSL";

// ── Textest Fragment Shader ────────────────────────────────────────
static const std::string SHADER_TEXTEST_FRAG = R"GLSL(

#version 430 core

in vec2 vUV;
out vec4 FragColor;

uniform sampler2D uMainTex;
uniform vec4 uBaseColorFactor;

void main()
{
    vec4 texColor = texture(uMainTex, vUV);

    // FLAG: Alpha Testing
    // This removes the "square" around eyelashes and the "fog" in the eyes.
    if (texColor.a < 0.05) {
        discard; 
    }

    // FLAG: Color Mixing
    // VRM models use uBaseColorFactor to tint the mesh (like making skin warmer).
    // If you only use 'texColor', you might lose some of the artist's intended look.
    vec4 color = texColor * uBaseColorFactor;

    // Output the final color
    FragColor = color;
}

)GLSL";

// ── MToon Vertex ──────────────────────────────────────────────────
static const std::string SHADER_MTOON_VERT = R"GLSL(

#version 130 core    //or 330

// FLAG: Standard Attributes (Passed from C++/Python)
layout (location = 0) in vec3 in_Vertex;
layout (location = 1) in vec3 in_Normal;
layout (location = 2) in vec2 in_UV;
layout (location = 3) in vec4 in_Joints;  // Which bones affect this vertex
layout (location = 4) in vec4 in_Weights; // How much each bone pulls

// FLAG: Uniforms (The "Muscle" data)
uniform mat4 u_ViewProjection;   // Camera Camera Camera
uniform mat4 u_Model;            // World Position of the Entity
uniform mat4 u_JointMatrices[128]; // The Skeleton (Max 128 bones)

// FLAG: Data for the MToon Fragment Shader
out vec2 uv;
out vec3 v_normal;
out vec3 v_worldPos;

void main() {
    // FLAG: The Skinning Calculation
    // This is the line that fixes the "explosion." 
    // We blend the matrices of the 4 joints based on their weights.
    mat4 skinMat = 
        in_Weights.x * u_JointMatrices[int(in_Joints.x)] +
        in_Weights.y * u_JointMatrices[int(in_Joints.y)] +
        in_Weights.z * u_JointMatrices[int(in_Joints.z)] +
        in_Weights.w * u_JointMatrices[int(in_Joints.w)];

    // Transform position into world space using the skin
    vec4 worldPos = u_Model * skinMat * vec4(in_Vertex, 1.0);
    
    // Final position on screen
    gl_Position = u_ViewProjection * worldPos;

    // Data for MToon lighting
    uv = in_UV;
    v_worldPos = worldPos.xyz;
    
    // Normal must be transformed by the same skinning matrix to stay aligned
    v_normal = normalize(mat3(u_Model * skinMat) * in_Normal);
}

)GLSL";

// ── MToon Fragment ─────────────────────────────────────────────────
static const std::string SHADER_MTOON_FRAG = R"GLSL(


#version 130 // or use 330

uniform sampler2D p3d_Texture0;
uniform struct {
    vec4 color;
    vec4 position;
} p3d_LightSource[1];

uniform vec4 ambient;
in vec2 uv;
in vec3 v_normal;

void main() {
    vec4 tex = texture2D(p3d_Texture0, uv);
    
    // FLAG: Gamma Correction (Linear Space)
    // This is the #1 reason faces look "White ASF". 
    // It converts the texture to math-friendly values.
    vec3 linear_tex = pow(tex.rgb, vec3(2.2));

    // FLAG: Genshin Shadow Tint
    // Instead of black, shadows on skin should be a mix of Orange and Pink.
    // vec3(Red, Green, Blue) -> 1.0, 0.7, 0.6 is a warm peach.
    vec3 shadow_tint = vec3(1.0, 0.7, 0.6); 

    vec3 light_dir = normalize(p3d_LightSource[0].position.xyz);
    
    // FLAG: Shadow Wrap (-0.3)
    // Pushing this negative forces the shadow to wrap around her cheeks.
    float dot_prod = dot(v_normal, light_dir) - 0.3;
    float intensity = smoothstep(0.0, 0.05, dot_prod);
    
    // FLAG: The Multi-Tone Mix
    // We mix the texture with our warm shadow tint for the dark side.
    vec3 shadow_side = linear_tex * shadow_tint * 0.5; 
    vec3 lit_side = linear_tex;
    
    vec3 linear_ambient = pow(ambient.rgb, vec3(2.2));

    vec3 lit_rgb = mix(shadow_side, lit_side, intensity);
    vec3 final_rgb = lit_rgb + (linear_tex * linear_ambient);
    
    // FLAG: Global Brightness Cap (0.7)
    // This prevents your GT 710 from blowing out the white pixels.
    final_rgb *= p3d_LightSource[0].color.rgb * 0.7;
    
    // Convert back to Gamma Space for the monitor
    gl_FragColor = vec4(pow(final_rgb, vec3(1.0/2.2)), tex.a);
}

)GLSL";

// ── Debug shaders ─────────────────────────────────────────────────
static const std::string SHADER_DEBUG_VERT = R"GLSL(

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


)GLSL";

static const std::string SHADER_DEBUG_FRAG = R"GLSL(

#version 330 core
in vec2 TexCoords;
out vec4 FragColor;

void main() {
    // If we see this neon pink, we know the shader is working
    FragColor = vec4(1.0, 0.0, 1.0, 1.0); 
}
    
)GLSL";