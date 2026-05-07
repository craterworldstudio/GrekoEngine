#version 430 core

// ==========================
// Inputs
// ==========================
in vec2 vUV;
in vec3 vWorldNormal;
in vec3 vWorldPos;

// ==========================
// Output
// ==========================
out vec4 FragColor;

// ==========================
// Textures (always active)
// ==========================
uniform sampler2D uMainTex;

// ==========================
// Material
// ==========================
uniform vec4 uBaseColorFactor;

// ==========================
// Lighting
// ==========================
uniform vec3 uLightDirection; // Direction FROM the light source (will be negated below)
uniform vec3 uLightColor;
uniform vec3 uAmbientColor;

// ==========================
// Camera
// ==========================
uniform vec3 uCameraPos;

// ==========================
// Cel shading controls
// ==========================
// The article: "the most important thing is the transition between light and shadow,
// in Genshin they don't do an extreme hardness so 0.1 should be enough"
uniform float uLightSmooth;   // Main shadow edge softness — recommended: 0.1
uniform vec3  uShadowColor;   // Shadow region tint  — e.g. vec3(1.0, 0.82, 0.78) warm
uniform vec3  uBaseColor;     // Lit region tint     — e.g. vec3(1.0, 1.0, 1.0)

// ==========================
// Outer shadow controls
// ==========================
// Article: "add an outer extra small shadow with a different color.
//  Do another NdotL but offset it a bit and make the transition harder"
uniform float uOuterShadowOffset; // How far to shift the band toward shadow — try 0.15-0.25
uniform float uOuterShadowSmooth; // Edge hardness — try 0.02-0.05 (crisp)
uniform vec3  uOuterShadowColor;  // Slightly darker/cooler than uShadowColor

// ==========================
// Rim / edge highlight
// ==========================
// Article: "white outline around character, like in most animes"
// NOTE: The article implements this as a post-process Sobel pass. This is a
// shader-side fresnel approximation — good enough until you add a screen-space
// outline pass. See the #define FEATURE_SOBEL_OUTLINE note below.
uniform vec3  uRimColor;     // Usually white or pale blue — e.g. vec3(0.9, 0.95, 1.0)
uniform float uRimPow;       // Fresnel falloff — try 2.0-4.0
uniform float uRimIntensity; // Overall brightness — try 0.3-0.8

// ============================================================
// OPTIONAL FEATURES — uncomment the #define to enable each.
// Each one requires extra uniforms / textures listed above it.
// ============================================================

// ------------------------------------------------------------
// FEATURE: FACE SHADOW (SDF texture-driven shadow for face mesh)
// Article: "a simple NdotL is not the best option for the face.
//  We can edit normals but there is a better option [SDF texture]."
// Requires:
//   uniform sampler2D uFaceShadowTex; // R=0-180°, G=180-360°
//   uniform vec3 uHeadForward;        // head bone forward (world space XZ)
//   uniform vec3 uHeadRight;          // head bone right   (world space XZ)
// Only bind & set uIsFace=1 on your face draw call.
// ------------------------------------------------------------
// #define FEATURE_FACE_SHADOW

// ------------------------------------------------------------
// FEATURE: ANISOTROPIC HAIR HIGHLIGHT
// Article: "hair shines only when it receives light,
//  remove the sides with fresnel for a better result"
// Requires:
//   uniform sampler2D uHairMask;       // R channel = highlight position baked in texture
//   uniform float uAnisoFresnelPow;    // try 3.0-6.0
//   uniform float uAnisoFresnelIntensity; // try 1.0-2.0
// Only bind & set uIsHair=1 on hair draw calls.
// ------------------------------------------------------------
// #define FEATURE_ANISO_HAIR

// ------------------------------------------------------------
// FEATURE: METALLIC (gradient matcap-style)
// Article: "blend between diffuse texture and matcap.
//  Use a gradient texture, UV = dot(normal, normalize(viewDir + lightDir))"
// Requires:
//   uniform sampler2D uMetallicGradient; // 1D gradient strip texture
//   uniform float uMetallicBlend;        // 0=none, 1=full — try 0.5-1.0
// Only set uIsMetallic=1 on metallic material draw calls.
// ------------------------------------------------------------
// #define FEATURE_METALLIC

// ------------------------------------------------------------
// FEATURE: POST-PROCESS SOBEL OUTLINE
// Article: "detect edges using depth + normal scene texture, combine both"
// This requires a separate full-screen pass reading your depth/normal buffers.
// See: vrm_outline.frag (separate shader) for that implementation.
// The rim highlight below is your placeholder until that pass is wired up.
// ------------------------------------------------------------
// #define FEATURE_SOBEL_OUTLINE  <- implemented in vrm_outline.frag, not here


// ============================================================
// Conditional uniform declarations for optional features
// ============================================================
#ifdef FEATURE_FACE_SHADOW
uniform sampler2D uFaceShadowTex;
uniform vec3 uHeadForward;
uniform vec3 uHeadRight;
#endif

#ifdef FEATURE_ANISO_HAIR
uniform sampler2D uHairMask;
uniform float uAnisoFresnelPow;
uniform float uAnisoFresnelIntensity;
#endif

#ifdef FEATURE_METALLIC
uniform sampler2D uMetallicGradient;
uniform float uMetallicBlend;
#endif


// ============================================================
// Gran Turismo tonemapper
// Article: "keeps color saturation and fixes burned areas — ideal for cartoon style"
// Curve: https://www.desmos.com/calculator/gslcdxvipg
// Chosen over Neutral (blown brights) and ACES (desaturates) from Unity URP.
// ============================================================
vec3 granTurismoTonemap(vec3 x) {
    // GT constants tuned for anime saturation retention
    const float P  = 1.0;   // max display brightness
    const float a  = 1.0;   // contrast
    const float m  = 0.22;  // linear section start
    const float l  = 0.4;   // linear section length
    const float c  = 1.33;  // black tightness
    const float b  = 0.0;   // black pedestal

    float l0 = ((P - m) * l) / a;
    float S0 = m + l0;
    float S1 = m + a * l0;
    float C2 = (a * P) / (P - S1);
    float CP = -C2 / P;

    vec3 w0 = 1.0 - smoothstep(vec3(0.0), vec3(m), x);
    vec3 w2 = step(vec3(S0), x);
    vec3 w1 = 1.0 - w0 - w2;

    vec3 T = m * pow(clamp(x / m, 0.0, 1.0), vec3(c)) + b;
    vec3 L = m + a * (x - m);
    vec3 S = P - (P - S1) * exp(CP * (x - S0));

    return clamp(T * w0 + L * w1 + S * w2, 0.0, 1.0);
}


void main()
{
    // ================================================================
    // BASE SETUP
    // ================================================================
    vec4 texColor = texture(uMainTex, vUV);

    // Alpha clip — keep your threshold
    if (texColor.a < 0.05)
        discard;

    // Gamma -> linear (keep your existing conversion)
    vec3 albedo = pow(texColor.rgb, vec3(2.2));
    albedo *= uBaseColorFactor.rgb;

    vec3 N = normalize(vWorldNormal);
    vec3 L = normalize(-uLightDirection); // negate: uniform is direction FROM light
    vec3 V = normalize(uCameraPos - vWorldPos);


    // ================================================================
    // STEP 1 — MAIN CEL LIGHTING
    // Article: NdotL -> smoothstep(0, lightSmooth, NdotL) -> lerp shadow/base
    //
    // Replaces your hard if/else toon bands with the Genshin approach:
    // a single soft threshold. uLightSmooth=0.1 gives the characteristic
    // Genshin "not too hard, not too soft" transition.
    // ================================================================
    float lDot    = dot(L, N);
    float lSmooth = smoothstep(0.0, uLightSmooth, lDot);

    // Article: "lerp to tint shadow and light for more color control"
    // uShadowColor tints shadow regions, uBaseColor tints lit regions.
    // Your warm shadow tint (1.0, 0.82, 0.78) goes into uShadowColor.
    vec3 celColor = mix(uShadowColor, uBaseColor, lSmooth) * albedo;


    // ================================================================
    // STEP 2 — OUTER SHADOW
    // Article: "extra small shadow with a different color — another NdotL
    //  but offset a bit and make the transition harder, tint with similar color"
    //
    // This creates the thin darker band that appears just at the shadow
    // boundary — very visible on Genshin character bodies.
    // ================================================================
    float outerDot    = lDot - uOuterShadowOffset;
    float outerSmooth = smoothstep(0.0, uOuterShadowSmooth, outerDot);
    celColor = mix(uOuterShadowColor * albedo, celColor, outerSmooth);


    // ================================================================
    // STEP 3 — FACE SHADOW (optional — #define FEATURE_FACE_SHADOW)
    // Article: "use forward/right of head bone + SDF texture to avoid
    //  NdotL artifacts on rounded face geometry"
    // ================================================================
#ifdef FEATURE_FACE_SHADOW
    {
        // Project light direction onto the horizontal plane of the head
        float dotF = dot(uHeadForward.xz, L.xz);  // are we lit from front?
        float dotR = dot(uHeadRight.xz,   L.xz);  // which side is the light on?

        // Remap dotR through acos to get a 0-1 value representing light angle
        float dotRAcos    = (acos(clamp(dotR, -1.0, 1.0)) / 3.14159) * 2.0;
        float dotRAcosDir = (dotR < 0.0) ? (1.0 - dotRAcos) : (dotRAcos - 1.0);

        // Article: Channel R = 0-180°, Channel G = 180-360°
        vec2  shadowSample = texture(uFaceShadowTex, vUV).rg;
        float texShadowDir = (dotR < 0.0) ? shadowSample.g : shadowSample.r;

        // step: shadowed when light angle exceeds the SDF value at this UV
        float dotFStep  = step(0.0, dotF); // 0 when light is behind head
        float faceShadow = step(dotRAcosDir, texShadowDir) * dotFStep;

        celColor = mix(uShadowColor * albedo, celColor, faceShadow);
    }
#endif


    // ================================================================
    // STEP 4 — ANISOTROPIC HAIR (optional — #define FEATURE_ANISO_HAIR)
    // Article: "hair shines when it receives light, remove sides with fresnel"
    // ================================================================
#ifdef FEATURE_ANISO_HAIR
    {
        float NdotV       = clamp(dot(N, V), 0.0, 1.0);
        float hairFresnel = pow(1.0 - NdotV, uAnisoFresnelPow) * uAnisoFresnelIntensity;
        float hairMask    = texture(uHairMask, vUV).r;
        // Gate by NdotL so hair only shines when facing the light
        float hairHighlight = clamp(1.0 - hairFresnel, 0.0, 1.0)
                            * hairMask
                            * clamp(lDot, 0.0, 1.0);
        celColor += vec3(hairHighlight); // additive white highlight
    }
#endif


    // ================================================================
    // STEP 5 — METALLIC (optional — #define FEATURE_METALLIC)
    // Article: "dot(normal, normalize(viewDir + lightDir)) for UV,
    //  sample gradient texture, optionally distort with normal map"
    // ================================================================
#ifdef FEATURE_METALLIC
    {
        vec3  H          = normalize(V + L);
        float metallicU  = dot(N, H) * 0.5 + 0.5; // remap [-1,1] to [0,1]
        vec3  metalColor = texture(uMetallicGradient, vec2(metallicU, 0.5)).rgb;
        celColor = mix(celColor, metalColor * albedo, uMetallicBlend);
    }
#endif


    // ================================================================
    // STEP 6 — LIGHT COLOR MULTIPLY
    // Article: "multiply final result by color light and fog"
    // ================================================================
    celColor *= uLightColor;


    // ================================================================
    // STEP 7 — AMBIENT FILL (kept from your original shader — good practice)
    // ================================================================
    celColor += albedo * uAmbientColor;


    // ================================================================
    // STEP 8 — RIM / EDGE HIGHLIGHT
    // Article: "white outline around character, detected via post-process Sobel"
    // This fresnel is a shader-side stand-in until you wire up vrm_outline.frag.
    // Gate it to the lit side so it doesn't glow in shadow.
    // ================================================================
    float rimDot    = 1.0 - clamp(dot(N, V), 0.0, 1.0);
    float rimFactor = pow(rimDot, uRimPow) * uRimIntensity;
    rimFactor      *= step(0.0, lDot); // only on lit side
    celColor       += uRimColor * rimFactor;


    // ================================================================
    // STEP 9 — GRAN TURISMO TONEMAPPER
    // Article recommends this over Unity's Neutral/ACES for anime style.
    // Keeps saturation intact while preventing blown-out brights.
    // ================================================================
    celColor = granTurismoTonemap(celColor);

    // Linear -> Gamma (keep your existing conversion)
    celColor = pow(celColor, vec3(1.0 / 2.2));

    FragColor = vec4(celColor, texColor.a);
}
