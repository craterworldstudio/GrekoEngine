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