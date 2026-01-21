from panda3d.core import WindowProperties, ClockObject

class CameraController:
    def __init__(self, app):
        self.app = app
        self.mouse_senst = 0.1
        self.move_speed = 5.0

        # --- 1. SETUP FLAGS ---
        self.app.disable_mouse()
        self.app.camera_locked = False
        self.app.mouse_sensitivity = self.mouse_senst
        self.app.move_speed = self.move_speed      # Increased slightly for better movement

        # --- 2. KEYBOARD TRACKING ---
        self.app.keys = {"w": False, "a": False, "s": False, "d": False, "e": False, "q": False}

        def set_key(key, value):
            self.app.keys[key] = value

        # Bind keys
        for key in ["w", "a", "s", "d", "e", "q"]:
            self.app.accept(key, set_key, [key, True])
            self.app.accept(f"{key}-up", set_key, [key, False])

        # --- 3. MOUSE TOGGLE ---
        self.app.accept('m', self.toggle_mouse)

        # --- 4. START THE TASK ---
        self.app.taskMgr.add(self.update_camera, "CameraTask")

    def update(self, sent, speed):
        self.mouse_senst = sent
        self.move_speed = speed
        self.app.mouse_sensitivity = self.mouse_senst
        self.app.move_speed = self.move_speed

    def toggle_mouse(self):
        self.app.camera_locked = not self.app.camera_locked
        props = WindowProperties()
        props.set_cursor_hidden(self.app.camera_locked)
        # Use Relative for locking, Absolute for menu/standard mode
        mode = WindowProperties.M_relative if self.app.camera_locked else WindowProperties.M_absolute
        props.set_mouse_mode(mode)
        self.app.win.request_properties(props)
        print(f"🚩 Look Mode: {'ON' if self.app.camera_locked else 'OFF'}")

    def update_camera(self, task):
        dt = ClockObject.get_global_clock().get_dt()

        # A. ROTATION (MOUSE)
        if self.app.camera_locked and self.app.mouseWatcherNode.has_mouse():
            x = self.app.mouseWatcherNode.get_mouse_x()
            y = self.app.mouseWatcherNode.get_mouse_y()

            self.app.camera.set_h(self.app.camera.get_h() - x * self.app.mouse_sensitivity * 100 * dt)
            self.app.camera.set_p(self.app.camera.get_p() + y * self.app.mouse_sensitivity * 100 * dt)

            # FLAG: The Anchor (Reset to center)
            self.app.win.move_pointer(0, self.app.win.get_x_size() // 2, self.app.win.get_y_size() // 2)

        # B. MOVEMENT (WASD)
        if self.app.keys["w"]: self.app.camera.set_y(self.app.camera, self.app.move_speed * dt)
        if self.app.keys["s"]: self.app.camera.set_y(self.app.camera, -self.app.move_speed * dt)
        if self.app.keys["a"]: self.app.camera.set_x(self.app.camera, -self.app.move_speed * dt)
        if self.app.keys["d"]: self.app.camera.set_x(self.app.camera, self.app.move_speed * dt)
        if self.app.keys["e"]: self.app.camera.set_z(self.app.camera, self.app.move_speed * dt)
        if self.app.keys["q"]: self.app.camera.set_z(self.app.camera, -self.app.move_speed * dt)

        return task.cont