#version 130 // or use 330

// FLAG: Standard Panda3D Uniforms
uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat3 p3d_NormalMatrix;

// FLAG: Standard Panda3D Inputs
in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;

// FLAG: Passing data to the Fragment Shader
out vec2 uv;
out vec3 v_normal;

void main() {
    // Standard vertex position calculation
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    
    // Pass UVs to fragment shader for texturing
    uv = p3d_MultiTexCoord0;
    
    // Transform normals into view space so lighting works as the camera moves
    v_normal = normalize(p3d_NormalMatrix * p3d_Normal);
}