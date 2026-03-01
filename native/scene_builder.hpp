#pragma once
#include <string>
#include <vector>

struct ShapeDescriptor
{
    std::string type;
    int entity_index;
    float size = 1.0f;
    float radius = 1.0f;
    int segments = 16;
};

static std::vector<ShapeDescriptor> pending_shapes;

void upload_shapes(const std::vector<ShapeDescriptor>& shapes);
void build_pending_shapes();