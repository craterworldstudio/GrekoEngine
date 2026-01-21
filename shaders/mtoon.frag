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