from curses import window
import os
import json
from pyexpat import model
import shutil
from tkinter import Listbox
from turtle import color
import customtkinter as ctk
from tkinter import filedialog, messagebox
import datetime, time

from greko_run import Engine, load_native

CONFIG_FILE = "config.json"
CACHE_DIR = "engine_cache"


class LauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Greko Engine Hub")
        ctk.set_appearance_mode("Dark")      # or "Light" / "System"
        ctk.set_default_color_theme("blue")  # blue, green, dark-blue
        self.root.geometry("720x720")
        self.root.minsize(650, 650)

        self.so_path = ""
        self.assets_path = ""
        self.current_avatar = None
        self.available_vrms = []

        self.eye_constraints = {
            "inner_yaw": 8.0,
            "outer_yaw": 6.0,
            "up_pitch": 4.0,
            "down_pitch": 3.0
        }

        os.makedirs(CACHE_DIR, exist_ok=True)

        self.main = ctk.CTkFrame(root, corner_radius=0)
        self.main.pack(fill="both", expand=True)

        self.create_header()
        self.create_home_page()
        self.create_footer()
        #ctk.CTkButton(root, text="Run Engine", command=self.run_engine, bg="green", fg="white").pack(pady=10)
        #ctk.CTkButton(root, text="Load Config", command=self.load_config).pack(pady=5)

        # Auto-load config on startup
        self.load_config()
        self.update_launch_state()

    # ===============================
    # CONFIG SYSTEM
    # ===============================
    def save_config(self):
        data = {}

        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)

        data["launcher"] = {
            "Cversion": 1,
            "Lversion": "GEL_1.0.0",
            "Rversion": "GER_1.00.000",
            "theme": "dark",
            "language": "en",
            "so_path": self.so_path,
            "assets_path": self.assets_path,
            "current_avatar": self.current_avatar
        }

        data.setdefault("models", [])

        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return

        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)

        launcher = data.get("launcher", {})

        self.so_path = launcher.get("so_path", "")
        self.assets_path = launcher.get("assets_path", "")
        self.current_avatar = launcher.get("current_avatar", "")

        if self.so_path:
            self.runtime_name.configure(
                text=os.path.basename(self.so_path)
            )

        if self.assets_path:
            self.avatar_folder.configure(
                text=f"Assets Folder : {self.assets_path}"
            )

            self.load_vrms()

            # Restore the previously selected avatar
            if self.current_avatar:
                self.selected_avatar = self.current_avatar
                self.avatar_name.configure(text=self.current_avatar)

    def get_current_model(self):

        from datetime import datetime

        now = datetime.now()

        timen = int(now.second)
        dated = int(now.day)
        datem = int(now.month)
        datey = int(now.year)

        new_model = {
            "name": self.current_avatar,
            "id": timen * dated * datem * datey,#self.generate_model_id(self.current_avatar),
            "VRMVersion": 0,

            "lighting": {},

            "eye_constraints": {
                "down_pitch": 0.0,
                "inner_yaw": 17.017000198364258,
                "outer_yaw": 29.097999572753906,
                "up_pitch": 5.5329999923706055
            },

            "morphs": {
                "Blink_U": "Unassigned",
                "Blink_L": "Unassigned",
                "Blink_R": "Unassigned",
                "Breather": "Unassigned",
                "Blank": "Unassigned",
                "A": "Unassigned",
                "E": "Unassigned",
                "I": "Unassigned",
                "O": "Unassigned",
                "U": "Unassigned"
            },

            "BlinkerStrength": 0.0,

            "bones": {
                "Head": "Unassigned",
                "Neck": "Unassigned"
            }
        }
        

        if not os.path.exists(CONFIG_FILE):
            return None

        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)

        current = data.get("launcher", {}).get("current_avatar")


        for model in data.get("models", []):
            if model.get("name") == current:
                return model
            
        data["models"].append(new_model)
        self.save_config()
        return new_model

    # ===============================
    # FILE PICKERS
    # ===============================
    def select_so(self):
        path = filedialog.askopenfilename(filetypes=[("Shared Object", "*.so")])
        if path:
            # Copy to local cache
            filename = os.path.basename(path)
            cached_path = os.path.join(CACHE_DIR, filename)

            shutil.copy2(path, cached_path)

            self.so_path = cached_path
            self.runtime_name.configure(text=filename)
            self.update_launch_state()
            self.save_config()

    def select_assets(self):
        path = filedialog.askdirectory()
        if path:
            self.assets_path = path
            self.current_avatar = None
            self.avatar_name.configure(text="No Avatar Selected" )

            self.avatar_folder.configure(text=f"Assets Folder : {self.assets_path}")
            
            self.load_vrms()
            self.save_config()
            self.update_launch_state()

    def load_vrms(self):
        self.available_vrms = []
    
        if not os.path.exists(self.assets_path):
            return
    
        self.available_vrms = sorted(
            f for f in os.listdir(self.assets_path)
            if f.lower().endswith(".vrm")
        )
        if len(self.available_vrms) == 1:
            self.current_avatar = self.available_vrms[0]

            self.avatar_name.configure(
                text=self.current_avatar
            )
        self.update_launch_state()

    # ===============================
    # RUN ENGINE
    # ===============================
    def run_engine(self):
        if not self.so_path:
            messagebox.showerror("Error", "Select a runtime first.")
            return

        if not self.assets_path:
            messagebox.showerror("Error", "Select an assets folder first.")
            return

        if self.current_avatar is None:
            messagebox.showerror("Error", "Select an avatar first.")
            return

        vrm_path = os.path.join(
            self.assets_path,
            self.current_avatar
        )
        
        
        try:
            model = self.get_current_model()


            self.set_status(
                "🚀 Launching Engine...",
                "#60a5fa"
            )
            gn = load_native(self.so_path)
            engine = Engine(gn, vrm_path, model_config=model)
            


            engine.eye_constraints = self.eye_constraints
            engine.init_entities()
            self.set_status(
                "🟢 Engine Running",
                "#4ade80"
            )
            engine.gameloop()

        except Exception as e:
            self.set_status(
                "🔴 Launch Failed",
                "#ef4444"
            )
            messagebox.showerror("Crash", str(e))

    def create_header(self):
        self.header = ctk.CTkFrame(self.main, fg_color="transparent")
        self.header.pack(fill="x", padx=25, pady=(20, 15))

        ctk.CTkLabel(
            self.header,
            text="GREKO ENGINE",
            font=("Segoe UI", 34, "bold")
        ).pack()

        ctk.CTkLabel(
            self.header,
            text="Modular Avatar Runtime",
            font=("Segoe UI", 15),
            text_color="gray"
        ).pack(pady=(4, 0))

    def create_home_page(self):
        self.home = ctk.CTkFrame(self.main, fg_color="transparent")
        self.home.pack(fill="both", expand=True, padx=20)

        self.create_selection_cards()
        self.create_preview()
        self.create_launch_button()

    def create_selection_cards(self):
        self.selection = ctk.CTkFrame(self.home, fg_color="transparent")
        self.selection.pack(fill="x", pady=(0, 15))

        self.selection.grid_columnconfigure(0, weight=1)
        self.selection.grid_columnconfigure(1, weight=1)

        self.create_avatar_card()
        self.create_runtime_card()

    def create_avatar_card(self):
        self.avatar_card = ctk.CTkFrame(self.selection)
        self.avatar_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            self.avatar_card,
            text="🎭 Avatar",
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", padx=20, pady=(18, 10))

        self.avatar_name = ctk.CTkLabel(
            self.avatar_card,
            text="No Avatar Selected",
            font=("Segoe UI", 16)
        )
        self.avatar_name.pack(anchor="w", padx=20)

        self.avatar_version = ctk.CTkLabel(
            self.avatar_card,
            text="VRM Version : Unknown",
            text_color="gray"
        )
        self.avatar_version.pack(anchor="w", padx=20, pady=(3, 0))

        self.avatar_folder = ctk.CTkLabel(
            self.avatar_card,
            text="Assets Folder : Not Selected",
            text_color="gray"
        )
        self.avatar_folder.pack(anchor="w", padx=20, pady=(3, 15))

        ctk.CTkButton(
            self.avatar_card,
            text="Change Avatar",
            command=self.select_avatar,
            height=36
        ).pack(anchor="e", padx=20, pady=(0, 20))

    def create_runtime_card(self):
        self.runtime_card = ctk.CTkFrame(self.selection)
        self.runtime_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        ctk.CTkLabel(
            self.runtime_card,
            text="⚙ Runtime",
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", padx=20, pady=(18, 10))

        self.runtime_name = ctk.CTkLabel(
            self.runtime_card,
            text="No Runtime Selected",
            font=("Segoe UI", 16)
        )
        self.runtime_name.pack(anchor="w", padx=20)

        self.runtime_version = ctk.CTkLabel(
            self.runtime_card,
            text="Version : Unknown",
            text_color="gray"
        )
        self.runtime_version.pack(anchor="w", padx=20, pady=(3, 0))

        self.runtime_renderer = ctk.CTkLabel(
            self.runtime_card,
            text="Renderer : OpenGL",
            text_color="gray"
        )
        self.runtime_renderer.pack(anchor="w", padx=20, pady=(3, 15))

        ctk.CTkButton(
            self.runtime_card,
            text="Change Runtime",
            command=self.select_so,
            height=36
        ).pack(anchor="e", padx=20, pady=(0, 20))

    def create_preview(self):
        self.preview = ctk.CTkFrame(self.home)
        self.preview.pack(fill="both", expand=True, pady=(0, 15))

        ctk.CTkLabel(
            self.preview,
            text="Avatar Preview",
            font=("Segoe UI", 20, "bold")
        ).pack(pady=(20, 10))

        self.preview_placeholder = ctk.CTkLabel(
            self.preview,
            text="Coming Soon",
            font=("Segoe UI", 16),
            text_color="gray"
        )

        self.preview_placeholder.pack(expand=True)

    def create_launch_button(self):
        self.launch_frame = ctk.CTkFrame(self.home, fg_color="transparent")
        self.launch_frame.pack(fill="x")

        self.launch_button = ctk.CTkButton(
            self.launch_frame,
            text="🚀 Launch Avatar",
            command=self.run_engine,
            height=55,
            font=("Segoe UI", 18, "bold"),
            fg_color="#16a34a",
            hover_color="#15803d"
        )

        self.launch_button.pack(fill="x")

    def select_avatar(self):
        if not self.assets_path:
            if not messagebox.askyesno(
                "Assets Folder Required",
                "No assets folder has been selected.\n\nWould you like to choose one now?"
            ):
                return

            self.select_assets()

            if not self.assets_path:
                return

        if not self.available_vrms:
            self.load_vrms()

        if not self.available_vrms:
            messagebox.showerror(
                "No Models Found",
                "The selected assets folder contains no .vrm files."
            )

            self.select_assets()
            return

        window = ctk.CTkToplevel(self.root)
        window.title("Select Avatar")
        window.geometry("420x420")
        window.resizable(False, False)

        #window.update()
        window.focus()

        listbox = Listbox(
            window,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#2563eb",
            borderwidth=0,
            highlightthickness=0
        )

        listbox.pack(fill="both", expand=True, padx=20, pady=20)

        for vrm in self.available_vrms:
            listbox.insert("end", vrm)

        def confirm():
            selection = listbox.curselection()

            if not selection:
                return

            self.current_avatar = self.available_vrms[selection[0]]

            self.avatar_name.configure(text=self.current_avatar)
            self.update_launch_state()
            window.destroy()

        ctk.CTkButton(
            self.avatar_card,
            text="Browse Folder",
            command=self.select_assets,
            height=36
        ).pack(fill="x", padx=20, pady=(0,8))


        ctk.CTkButton(
            window,
            text="Select",
            command=confirm
        ).pack(pady=(0,20))

    def create_footer(self):
        self.footer = ctk.CTkFrame(self.main)
        self.footer.pack(fill="x", padx=20, pady=20)

        self.status_label = ctk.CTkLabel(
            self.footer,
            text="🟢 Ready"
        )

        self.status_label.pack(side="left", padx=15)

        ctk.CTkButton(
            self.footer,
            text="❤️ About",
            width=90,
            command=self.open_about
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            self.footer,
            text="⬇ Updates",
            width=90,
            command=self.open_updates
        ).pack(side="right", padx=5)

        ctk.CTkButton(
            self.footer,
            text="⚙ Settings",
            width=90,
            command=self.open_settings
        ).pack(side="right", padx=5)

    def open_settings(self):
        print("Settings")

    def open_updates(self):
        print("Updates")

    def open_about(self):
        print("About")

    def set_status(self, text, color="white"):
        self.status_label.configure(
            text=text,
            text_color=color
        )

    def update_launch_state(self):
        ready = (
            bool(self.so_path)
            and bool(self.assets_path)
            and self.current_avatar is not None
        )

        self.launch_button.configure(
            state="normal" if ready else "disabled"
        )

        if ready:
            self.set_status(
                "🟢 Ready to Launch",
                "#4ade80"
            )
        elif not self.so_path:
            self.set_status(
                "⚪ Select a Runtime",
                "#cbd5e1"
            )
        elif not self.assets_path:
            self.set_status(
                "🟡 Select an Assets Folder",
                "#facc15"
            )
        else:
            self.set_status(
                "🟡 Select an Avatar",
                "#facc15"
            )

if __name__ == "__main__":
    root = ctk.CTk()
    app = LauncherGUI(root)
    root.mainloop()