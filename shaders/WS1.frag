#version 430 core

in vec2 vUV;
in vec3 vNormal;

out vec4 FragColor;

// ==========================
// Textures
// ==========================
uniform sampler2D uMainTex;

// ==========================
// Material
// ==========================
uniform vec4 uBaseColorFactor;

// ==========================
// Lighting
// ==========================

// Direction TO light
uniform vec3 uLightDirection;

// Light color/intensity
uniform vec3 uLightColor;

// Ambient light
uniform vec3 uAmbientColor;

void main()
{
    // ==========================
    // Texture Sampling
    // ==========================
    vec4 texColor = texture(uMainTex, vUV);

    // Alpha clipping
    if (texColor.a < 0.05)
        discard;

    // ==========================
    // Gamma → Linear
    // ==========================
    vec3 albedo = pow(texColor.rgb, vec3(2.2));

    // Apply VRM tint
    albedo *= uBaseColorFactor.rgb;

    // ==========================
    // Normalized Normal
    // ==========================
    vec3 N = normalize(vNormal);

    // Light direction
    vec3 L = normalize(-uLightDirection);

    // ==========================
    // Directional Lighting
    // ==========================
    float NdotL = dot(N, L);

    // ==========================
    // Shadow Wrap
    // ==========================
    // Makes shadows wrap softly around cheeks
    NdotL = NdotL * 0.5 + 0.5;

    // ==========================
    // Toon Banding
    // ==========================
    float toon;

    if (NdotL > 0.75)
        toon = 1.0;
    else if (NdotL > 0.45)
        toon = 0.7;
    else if (NdotL > 0.25)
        toon = 0.4;
    else
        toon = 0.15;

    // ==========================
    // Shadow Tint
    // ==========================
    // Warm anime shadows
    vec3 shadowTint = vec3(1.0, 0.82, 0.78);

    vec3 litColor =
        mix(albedo * shadowTint,
            albedo,
            toon);

    // ==========================
    // Directional Light
    // ==========================
    litColor *= uLightColor;

    // ==========================
    // Ambient Fill
    // ==========================
    litColor += albedo * uAmbientColor;

    // ==========================
    // Optional Highlight Boost
    // ==========================
    // Creates anime white-light punch
    float highlight =
        smoothstep(0.85, 1.0, NdotL);

    litColor += vec3(0.12) * highlight;

    // ==========================
    // Linear → Gamma
    // ==========================
    litColor = pow(litColor, vec3(1.0 / 2.2));

    FragColor = vec4(litColor, texColor.a);
}
