#include "primitives.hpp"
#include "renderer.hpp"   // or wherever add_mesh_to_scene is declared
#include <vector>

void create_cube(int entity_index, float size)
{
    float s = size * 0.5f;

    float vertices[] = {
        -s,-s,-s,  s,-s,-s,  s, s,-s, -s, s,-s,
        -s,-s, s,  s,-s, s,  s, s, s, -s, s, s
    };

    uint32_t indices[] = {
        0,1,2, 2,3,0,
        4,5,6, 6,7,4,
        0,1,5, 5,4,0,
        2,3,7, 7,6,2,
        0,3,7, 7,4,0,
        1,2,6, 6,5,1
    };

    std::vector<float> normals(24, 0.0f);
    std::vector<float> uvs(16, 0.0f);
    std::vector<uint32_t> joints(32, 0);
    std::vector<float> weights(32, 0.0f);
    std::vector<const float*> morphs;

    add_mesh_to_scene(
        vertices, 24,
        normals.data(), normals.size(),
        uvs.data(), uvs.size(),
        joints.data(), joints.size(),
        weights.data(), weights.size(),
        indices, 36,
        morphs,
        0,
        entity_index
    );
}

void create_sphere(int entity_index, float radius, int segments)
{
    // Temporary stub so linker is happy
}