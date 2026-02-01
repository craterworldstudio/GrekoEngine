from panda3d.core import (
    GeomVertexFormat, GeomVertexArrayFormat, GeomVertexData,
    GeomVertexWriter, GeomTriangles, Geom, GeomNode, InternalName
)


def build_panda_mesh(gltf_json, bin_blob, primitive_data, read_accessor_func, name="Mesh"):
    """
    Build STATIC mesh (no skinning vertex format)
    We'll deform vertices manually in CPU
    """
    
    # Simple vertex format - NO joint/weight columns
    array_format = GeomVertexArrayFormat()
    array_format.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
    array_format.add_column(InternalName.get_normal(), 3, Geom.NT_float32, Geom.C_vector)
    array_format.add_column(InternalName.get_texcoord(), 2, Geom.NT_float32, Geom.C_texcoord)
    
    v_format = GeomVertexFormat()
    v_format.add_array(array_format)
    v_format = GeomVertexFormat.register_format(v_format)
    
    # Use DYNAMIC usage hint (we'll modify every frame)
    v_data = GeomVertexData(name, v_format, Geom.UH_dynamic)
    
    attrs = primitive_data["attributes"]
    positions = read_accessor_func(gltf_json, bin_blob, attrs["POSITION"])
    v_data.set_num_rows(len(positions))
    
    # Writers
    pos_writer = GeomVertexWriter(v_data, 'vertex')
    norm_writer = GeomVertexWriter(v_data, 'normal')
    uv_writer = GeomVertexWriter(v_data, 'texcoord')
    
    # Write bind pose positions
    for p in positions:
        pos_writer.add_data3f(p[0], p[1], p[2])
    
    # Write normals
    if "NORMAL" in attrs:
        normals = read_accessor_func(gltf_json, bin_blob, attrs["NORMAL"])
        for n in normals:
            norm_writer.add_data3f(n[0], n[1], n[2])
    
    # Write UVs
    if "TEXCOORD_0" in attrs:
        uvs = read_accessor_func(gltf_json, bin_blob, attrs["TEXCOORD_0"])
        for u in uvs:
            uv_writer.add_data2f(u[0], u[1])
    
    # Read skinning data (store for later use)
    joints_data = None
    weights_data = None
    if "JOINTS_0" in attrs and "WEIGHTS_0" in attrs:
        joints_data = read_accessor_func(gltf_json, bin_blob, attrs["JOINTS_0"])
        weights_data = read_accessor_func(gltf_json, bin_blob, attrs["WEIGHTS_0"])
    
    # Build triangles
    indices = read_accessor_func(gltf_json, bin_blob, primitive_data["indices"])
    tris = GeomTriangles(Geom.UH_static)
    
    for i in range(0, len(indices), 3):
        tris.add_vertices(indices[i], indices[i+1], indices[i+2])
    
    # Assemble
    geom = Geom(v_data)
    geom.add_primitive(tris)
    
    node = GeomNode(name)
    node.add_geom(geom)
    
    # CRITICAL: Store skinning data as custom attributes
    node.set_python_tag("bind_positions", positions)
    node.set_python_tag("joints_data", joints_data)
    node.set_python_tag("weights_data", weights_data)
    
    return node


def getIBMS(parsed_glb, read_accessor):
    """Helper to get IBMs (now handled in skin_builder)"""
    skin = parsed_glb.json["skins"][0]
    ibm_accessor_idx = skin.get("inverseBindMatrices")
    ibms = []
    if ibm_accessor_idx is not None:
        ibms = read_accessor(parsed_glb.json, parsed_glb.bin_blob, ibm_accessor_idx)
    return ibms