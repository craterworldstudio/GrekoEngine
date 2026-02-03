#version 330

uniform sampler2D uTexture;
in vec2 vUV;
out vec4 FragColor;

void main() {
    FragColor = texture(uTexture, vUV);
}
