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