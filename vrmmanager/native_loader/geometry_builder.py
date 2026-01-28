import os
from platform import node
from panda3d.core import (
    GeomVertexFormat, GeomVertexArrayFormat, GeomVertexData, GeomVertexAnimationSpec,
    GeomVertexWriter, GeomTriangles, Geom, GeomNode, InternalName, Notify, TransformTable, JointVertexTransform,
    OmniBoundingVolume, StringStream
)


def build_panda_mesh(gltf_json, bin_blob, primitive_data, read_accessor_func, joints_list=None, ibms=None, name="Mesh"):
    # 1. SETUP GEOMVERTEXFORMAT (Corrected for Panda3D)
    joint_name = InternalName.get_transform_index()
    weight_name = InternalName.get_transform_weight()

    #print(joint_name, weight_name)
    # First, we create an ArrayFormat which holds the column definitions
    array_format = GeomVertexArrayFormat()
    array_format.add_column(InternalName.get_vertex(), 3, Geom.NT_float32, Geom.C_point)
    array_format.add_column(InternalName.get_normal(), 3, Geom.NT_float32, Geom.C_vector)
    array_format.add_column(InternalName.get_texcoord(), 2, Geom.NT_float32, Geom.C_texcoord)
    array_format.add_column(InternalName.get_tangent(), 4, Geom.NT_float32, Geom.C_vector)
    array_format.add_column(joint_name, 4, Geom.NT_uint16, Geom.C_index)
    array_format.add_column(weight_name, 4, Geom.NT_float32, Geom.C_other)
    
    # Then we add that array to a new Format object
    v_format = GeomVertexFormat()
    v_format.add_array(array_format)

    aspec = GeomVertexAnimationSpec()
    aspec.set_hardware(4, True)
    v_format.set_animation(aspec)
    
    # Register and create the data container
    v_format = GeomVertexFormat.register_format(v_format)
    v_data = GeomVertexData(name, v_format, Geom.UH_static)
    #v_data.set_animation(aspec)
    

    # Enable GPU skinning
    """v_data.setAnimation(
        GeomVertexAnimationSpec(
            GeomVertexAnimationSpec.AM_hardware,
            GeomVertexAnimationSpec.AT_transform_blend
        )
    )"""

    # 2. POPULATE GEOMVERTEXDATA
    attrs = primitive_data["attributes"]
    
    # Extract data using your Phase 1.2 accessors
    positions = read_accessor_func(gltf_json, bin_blob, attrs["POSITION"])
    v_data.set_num_rows(len(positions))
    
    # Set up writers
    pos_writer = GeomVertexWriter(v_data, 'vertex')
    norm_writer = GeomVertexWriter(v_data, 'normal')
    uv_writer = GeomVertexWriter(v_data, 'texcoord')
    tan_writer = GeomVertexWriter(v_data, 'tangent')
    #joint_writer = GeomVertexWriter(v_data, 'jointindices')
    #weight_writer = GeomVertexWriter(v_data, 'jointweights')
    joint_writer = GeomVertexWriter(v_data, joint_name)
    weight_writer = GeomVertexWriter(v_data, weight_name)
    

    if "JOINTS_0" in attrs and "WEIGHTS_0" in attrs:
        joints_data = read_accessor_func(gltf_json, bin_blob, attrs["JOINTS_0"])
        weights_data = read_accessor_func(gltf_json, bin_blob, attrs["WEIGHTS_0"])
        joint_remap = {
            gltf_idx: panda_idx
            for panda_idx, gltf_idx in enumerate(gltf_json["skins"][0]["joints"])
        }

        # FLAG: zip()
        # This ensures that Vertex 0 gets Joint 0 AND Weight 0 simultaneously.
        for j_row, w_row in zip(joints_data, weights_data):
            # 1. Write the bone indices (The "Which" flag)
            joint_writer.add_data4i(
                joint_remap[int(j_row[0])], 
                joint_remap[int(j_row[1])], 
                joint_remap[int(j_row[2])], 
                joint_remap[int(j_row[3])])
            
            # 2. Write the bone weights (The "How Much" flag)
            weight_writer.add_data4f(w_row[0], w_row[1], w_row[2], w_row[3])

    # Fill Positions (Always present)
    for p in positions:
        pos_writer.add_data3f(p[0], p[1], p[2])

    # Fill Normals
    if "NORMAL" in attrs:
        normals = read_accessor_func(gltf_json, bin_blob, attrs["NORMAL"])
        for n in normals:
            norm_writer.add_data3f(n[0], n[1], n[2])

    # Fill UVs
    if "TEXCOORD_0" in attrs:
        uvs = read_accessor_func(gltf_json, bin_blob, attrs["TEXCOORD_0"])
        for u in uvs:
            uv_writer.add_data2f(u[0], u[1])

    # Fill Tangents (Vital for Phase 2 MToon)
    if "TANGENT" in attrs:
        tangents = read_accessor_func(gltf_json, bin_blob, attrs["TANGENT"])
        for t in tangents:
            tan_writer.add_data4f(t[0], t[1], t[2], t[3])

    #4. Build the Trnasform Table for skinning and mesh deformation
    if joints_list:
        ttable = TransformTable()
        for i, joint in enumerate(joints_list):
            # JointVertexTransform connects the table slot to the actual bone
            
            
            # THE MAGIC FIX: Apply the Inverse Bind Matrix
            # This 'zeros out' the bone's world position so the vertex moves 
            # relative to the bone, not the center of the world.
            
            jvt = JointVertexTransform(joint)
            ttable.add_transform(jvt)
           
        
        # Register the table (makes it immutable/optimized)
        ttable = TransformTable.register_table(ttable)
        # Apply the 'phone book' to the vertex data
        v_data.set_transform_table(ttable)

    # 3. BUILD GEOMTRIANGLES
    indices = read_accessor_func(gltf_json, bin_blob, primitive_data["indices"])
    tris = GeomTriangles(Geom.UH_stream)
    
    # Panda3D uses the same winding order as GLTF (counter-clockwise)
    for i in range(0, len(indices), 3):
        tris.add_vertices(indices[i], indices[i+1], indices[i+2])

    # 4. ASSEMBLE GEOMNODE
    geom = Geom(v_data)
    geom.add_primitive(tris)

    #geom.set_animation_type(Geom.AT_hardware)
    
    node = GeomNode(name)
    node.add_geom(geom)

    # 1. Capture the output in a Panda3D-compatible stream
    stream = StringStream()
    v_data.write(stream)
    raw_data = stream.get_data().decode('utf-8', errors='ignore')
    formatted_data = raw_data.replace('\r', '\n')
    # 2. Add the Transform Table info to the same stream
    ttable = v_data.get_transform_table()
    table_info = "\n--- TRANSFORM TABLE MAPPING ---\n"
    # DEBUG: Write the vertex table to a file to verify the "Nerves"
    if ttable:
        tstream = StringStream()
        #stream.set_data(stream.get_data() + b"\n--- TRANSFORM TABLE MAPPING ---\n")
        ttable.write(tstream)
        table_info += tstream.get_data().decode('utf-8', errors='ignore').replace('\r', '\n')
    else:
        table_info += "❌ ERROR: NO TRANSFORM TABLE FOUND\n"
        #stream.set_data(stream.get_data() + b"\n\xe2\x9d\x8c ERROR: NO TRANSFORM TABLE\n")

    # 3. Now dump that string into a standard Python file
    os.makedirs("MeshTransformTable", exist_ok=True)
    with open(f"MeshTransformTable/debug_mesh_{name}.txt", "w", encoding="utf-8") as f:
        #f.write(str(stream.get_data()))

        f.write(formatted_data)
        f.write(table_info)
    return node


def getIBMS(parsed_glb, read_accessor) -> list:
    skin = parsed_glb.json["skins"][0]
    ibm_accessor_idx = skin.get("inverseBindMatrices")

    ibms = []
    if ibm_accessor_idx is not None:
        print(f"[TEST] Extracting Inverse Bind Matrices from accessor {ibm_accessor_idx}...")
        # This will return a list of LMatrix4f objects
        ibms = read_accessor(parsed_glb.json, parsed_glb.bin_blob, ibm_accessor_idx)
        print(f"  -> Successfully loaded {len(ibms)} IBMs")
    else:
        print("⚠️ WARNING: No Inverse Bind Matrices found in skin!")

    return ibms