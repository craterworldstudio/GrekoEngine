from setuptools import setup, Extension
import pybind11
import sysconfig

ext_modules = [
    Extension(
        "greko_native",
        sources=[
            "native/bridge.cpp",
            "native/renderer.cpp",
            "native/animation.cpp",
            "native/lookAt.cpp",
            "native/scene_builder.cpp",
            "native/texture_loader.cpp",
            "native/gameObjectShapes/primitives.cpp",
            "native/glad/glad.c",


            "native/imgui/imgui.cpp",
            "native/imgui/imgui_draw.cpp",
            "native/imgui/imgui_widgets.cpp",
            "native/imgui/imgui_tables.cpp",
            "native/imgui/backends/imgui_impl_glfw.cpp",
            "native/imgui/backends/imgui_impl_opengl3.cpp",
        ],
        include_dirs=[
            pybind11.get_include(),
            "native",
            "native/glad",
            "native/KHR",
            "native/imgui",
            "libs/glm",
            "libs/glfw/include"
        ],
        library_dirs=[
            "libs/glfw/lib-vc2022",
        ],
        libraries=[
            "glfw3",
            "opengl32",
            "user32",
            "gdi32",
            "shell32"
        ],
        language="c++",
        extra_compile_args=["/std:c++17", "/O2", "/DGLM_ENABLE_EXPERIMENTAL"]
    ),
]

setup(
    name="greko_native",
    version="1.0",
    ext_modules=ext_modules,
)