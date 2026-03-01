#include "scene_builder.hpp"
#include "renderer.hpp"
#include "gameObjectShapes/primitives.hpp"

void upload_shapes(const std::vector<ShapeDescriptor>& shapes)
{
    pending_shapes = shapes;
}

void build_pending_shapes()
{
    for (auto& shape : pending_shapes)
    {
        if (shape.type == "cube")
            create_cube(shape.entity_index, shape.size);

        else if (shape.type == "sphere")
            create_sphere(shape.entity_index, shape.radius, shape.segments);
    }

    pending_shapes.clear();
}