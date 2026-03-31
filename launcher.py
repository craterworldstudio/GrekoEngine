import os
import json
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

from greko_run import Engine, load_native

CONFIG_FILE = "config.json"
CACHE_DIR = "engine_cache"


class LauncherGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Greko Engine Launcher")
        self.root.geometry("500x450")

        self.pyd_path = ""
        self.assets_path = ""

        os.makedirs(CACHE_DIR, exist_ok=True)

        # --- SO Selection ---
        tk.Button(root, text="Select .pyd File", command=self.select_pyd).pack(pady=10)
        self.pyd_label = tk.Label(root, text="No .pyd selected")
        self.pyd_label.pack()

        # --- Assets Selection ---
        tk.Button(root, text="Select Assets Folder", command=self.select_assets).pack(pady=10)
        self.assets_label = tk.Label(root, text="No folder selected")
        self.assets_label.pack()

        # --- VRM List ---
        self.vrm_listbox = tk.Listbox(root, height=8)
        self.vrm_listbox.pack(fill="both", padx=20, pady=10)

        # --- Buttons ---
        tk.Button(root, text="Run Engine", command=self.run_engine, bg="green", fg="white").pack(pady=10)
        tk.Button(root, text="Load Config", command=self.load_config).pack(pady=5)

        # Auto-load config on startup
        self.load_config()

    # ===============================
    # CONFIG SYSTEM
    # ===============================
    def save_config(self):
        data = {
            "pyd_path": self.pyd_path,
            "assets_path": self.assets_path
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            return

        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)

        self.pyd_path = data.get("pyd_path", "")
        self.assets_path = data.get("assets_path", "")

        if self.pyd_path:
            self.pyd_label.config(text=os.path.basename(self.pyd_path))

        if self.assets_path:
            self.assets_label.config(text=self.assets_path)
            self.load_vrms()

    # ===============================
    # FILE PICKERS
    # ===============================
    def select_pyd(self):
        path = filedialog.askopenfilename(filetypes=[
            ("Native Module", "*.pyd"),
            ("All Files", "*.*")
                ])
        if path:
            # Copy to local cache
            filename = os.path.basename(path)
            cached_path = os.path.join(CACHE_DIR, filename)

            shutil.copy2(path, cached_path)

            self.pyd_path = cached_path
            self.pyd_label.config(text=filename)

            self.save_config()

    def select_assets(self):
        path = filedialog.askdirectory()
        if path:
            self.assets_path = path
            self.assets_label.config(text=path)
            self.load_vrms()
            self.save_config()

    def load_vrms(self):
        self.vrm_listbox.delete(0, tk.END)

        if not os.path.exists(self.assets_path):
            return

        vrms = [f for f in os.listdir(self.assets_path) if f.endswith(".vrm")]
        for vrm in vrms:
            self.vrm_listbox.insert(tk.END, vrm)

    # ===============================
    # RUN ENGINE
    # ===============================
    def run_engine(self):
        if not self.pyd_path or not self.assets_path:
            messagebox.showerror("Error", "Select .pyd and assets folder first")
            return

        selection = self.vrm_listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "Select a VRM file")
            return

        vrm_file = self.vrm_listbox.get(selection[0])
        vrm_path = os.path.join(self.assets_path, vrm_file)

        try:
            gn = load_native(self.pyd_path)

            engine = Engine(gn, vrm_path)
            engine.init_entities()
            engine.gameloop()

        except Exception as e:
            messagebox.showerror("Crash", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = LauncherGUI(root)
    root.mainloop()