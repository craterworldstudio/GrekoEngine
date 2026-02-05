#version 430 core

in vec2 vUV;
out vec4 FragColor;

uniform sampler2D uMainTex;
uniform vec4 uBaseColorFactor;

void main()
{
    vec4 tex = texture(uMainTex, vUV);

    // VRM expects alpha respected
    vec4 color = tex * uBaseColorFactor;
    // Safety clamp (optional but fine)
    FragColor = clamp(color, 0.0, 1.0);
}
