import os
import subprocess
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APPID = "3834090"
GAME_EXE_NAME = "YAPYAP.exe"

STEAM_ROOT_CANDIDATES = [
    os.path.expanduser("~/.local/share/Steam"),
    os.path.expanduser("~/.steam/steam"),
]

EXE_BLACKLIST = ["unitycrashhandler", "crashhandler", "unitycrashhandler64"]

DEFAULT_GALE_PRELOADER = os.path.expanduser(
    "~/.local/share/com.kesomannen.gale/yapyap/profiles/Default/BepInEx/core/BepInEx.Preloader.dll"
)

def find_steam_root():
    for p in STEAM_ROOT_CANDIDATES:
        if os.path.isdir(os.path.join(p, "steamapps")):
            return p
    return ""

def list_proton_installs(steam_root):
    common = os.path.join(steam_root, "steamapps/common")
    out = []
    if not os.path.isdir(common):
        return out
    for name in os.listdir(common):
        if "Proton" in name:
            proton = os.path.join(common, name, "proton")
            if os.path.isfile(proton):
                out.append((name, proton))
    out.sort(key=lambda x: x[0].lower())
    return out

def detect_game_exe(steam_root):
    game_dir = os.path.join(steam_root, "steamapps/common/YAPYAP")
    if not os.path.isdir(game_dir):
        return ""
    target = os.path.join(game_dir, GAME_EXE_NAME)
    if os.path.isfile(target):
        return target
    for name in os.listdir(game_dir):
        low_name = name.lower()
        if low_name.endswith(".exe") and not any(bad in low_name for bad in EXE_BLACKLIST):
            return os.path.join(game_dir, name)
    return ""

def get_profile_root(preloader_path):
    try:
        return os.path.dirname(os.path.dirname(os.path.dirname(preloader_path)))
    except:
        return ""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("☠ EMPRESS YAPYAP LAUNCHER ☠")
        self.geometry("720x480")
        self.configure(bg="#050000")
        self.attributes("-alpha", 0.95)

        style = ttk.Style()
        style.theme_use('clam')

        style.configure(".", background="#050000", foreground="#ff0000", font=("Segoe UI", 9, "bold"))
        style.configure("TFrame", background="#050000")

        style.configure("TLabel", background="#050000", foreground="#ff0000", font=("Consolas", 10, "bold"))

        style.configure("TButton",
                        background="#1a0000",
                        foreground="#ff0000",
                        borderwidth=1,
                        focuscolor="#ff0000",
                        font=("Segoe UI", 10, "bold"))
        style.map("TButton",
                  background=[("active", "#ff0000"), ("pressed", "#ffffff")],
                  foreground=[("active", "#000000"), ("pressed", "#000000")])

        style.configure("TEntry",
                        fieldbackground="#1a0000",
                        foreground="#ff0000",
                        insertcolor="#ff0000",
                        borderwidth=1,
                        relief="flat")

        style.configure("TCombobox",
                        fieldbackground="#1a0000",
                        background="#330000",
                        foreground="#ff0000",
                        arrowcolor="#ff0000")
        style.map("TCombobox", fieldbackground=[("readonly", "#1a0000")])

        style.configure("TCheckbutton",
                        background="#050000",
                        foreground="#ff0000",
                        indicatorcolor="#1a0000",
                        indicatorrelief="flat")
        style.map("TCheckbutton", indicatorcolor=[("selected", "#ff0000")])

        style.configure("TSpinbox",
                        fieldbackground="#1a0000",
                        foreground="#ff0000",
                        arrowcolor="#ff0000")

        self.steam_root = tk.StringVar(value=find_steam_root())
        self.preloader = tk.StringVar(
            value=DEFAULT_GALE_PRELOADER if os.path.isfile(DEFAULT_GALE_PRELOADER) else ""
        )
        self.game_exe = tk.StringVar()
        self.proton_choice = tk.StringVar()
        self.dual = tk.BooleanVar(value=True)
        self.delay = tk.IntVar(value=8)
        self.symlink_fix = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="WAITING FOR COMMAND...")

        self.protons = []
        self.build_ui()
        self.refresh()

    def build_ui(self):
        pad = {"padx": 15, "pady": 8}

        def row(label, var, browse=None):
            f = ttk.Frame(self)
            f.pack(fill="x", **pad)
            ttk.Label(f, text=label.upper(), width=20).pack(side="left")
            ttk.Entry(f, textvariable=var).pack(side="left", fill="x", expand=True)
            if browse:
                ttk.Button(f, text="SEARCH", command=browse).pack(side="left", padx=6)

        row("Steam Root", self.steam_root, self.browse_steam)

        f = ttk.Frame(self)
        f.pack(fill="x", **pad)
        ttk.Label(f, text="PROTON VERSION", width=20).pack(side="left")
        self.proton_box = ttk.Combobox(f, textvariable=self.proton_choice, state="readonly")
        self.proton_box.pack(side="left", fill="x", expand=True)
        ttk.Button(f, text="RELOAD", command=self.refresh).pack(side="left", padx=6)

        row("Game Executable", self.game_exe, self.browse_exe)
        row("BepInEx Core", self.preloader, self.browse_dll)

        f = ttk.Frame(self)
        f.pack(fill="x", **pad)
        ttk.Checkbutton(f, text="ACTIVATE DUAL INSTANCE (HOST + CLIENT)", variable=self.dual).pack(side="left")
        ttk.Label(f, text="INJECTION DELAY (S)").pack(side="left", padx=12)
        ttk.Spinbox(f, from_=1, to=60, textvariable=self.delay, width=5).pack(side="left")

        f = ttk.Frame(self)
        f.pack(fill="x", **pad)
        ttk.Checkbutton(f, text="FORCE SYMLINK DOORSTOP (REQUIRED)", variable=self.symlink_fix).pack(side="left")

        f = ttk.Frame(self)
        f.pack(fill="x", pady=20, padx=15)
        self.launch_btn = ttk.Button(f, text="EXECUTE LAUNCH", command=self.start_launch_thread)
        self.launch_btn.pack(side="left", fill="x", expand=True)
        ttk.Button(f, text="TERMINATE", command=self.destroy).pack(side="left", padx=6)

        status_lbl = ttk.Label(self, textvariable=self.status_var, font=("Consolas", 11, "italic"))
        status_lbl.pack(side="bottom", pady=10)

    def browse_steam(self):
        p = filedialog.askdirectory()
        if p:
            self.steam_root.set(p)
            self.refresh()

    def browse_exe(self):
        p = filedialog.askopenfilename(filetypes=[("EXE", "*.exe")])
        if p: self.game_exe.set(p)

    def browse_dll(self):
        p = filedialog.askopenfilename(filetypes=[("DLL", "*.dll")])
        if p: self.preloader.set(p)

    def refresh(self):
        sr = self.steam_root.get()
        self.protons = list_proton_installs(sr)
        self.proton_box["values"] = [n for n, _ in self.protons]
        if self.protons:
            self.proton_choice.set(self.protons[0][0])
        exe = detect_game_exe(sr)
        if exe:
            self.game_exe.set(exe)

    def start_launch_thread(self):
        self.launch_btn.config(state="disabled")
        threading.Thread(target=self.run_launch_logic, daemon=True).start()

    def detect_doorstop_version(self, profile_root):
        version_file = os.path.join(profile_root, ".doorstop_version")
        version = 3
        if os.path.exists(version_file):
            try:
                with open(version_file, "r") as f:
                    content = f.read().split('.')[0]
                    version = int(content)
            except:
                pass

        if version == 4:
            return "--doorstop-enabled", "--doorstop-target-assembly"
        else:
            return "--doorstop-enable", "--doorstop-target"

    def ensure_symlink(self, game_root, profile_root):
        candidates = ["winhttp.dll", "version.dll", "winmm.dll"]
        found_dll = None

        for c in candidates:
            p = os.path.join(profile_root, c)
            if os.path.isfile(p):
                found_dll = p
                break

        if not found_dll:
            return None

        dll_name = os.path.basename(found_dll)
        target_path = os.path.join(game_root, dll_name)

        if os.path.islink(target_path):
            current = os.readlink(target_path)
            if current != found_dll:
                os.remove(target_path)
                os.symlink(found_dll, target_path)
        elif os.path.isfile(target_path):
            pass
        else:
            os.symlink(found_dll, target_path)

        return dll_name.split('.')[0]

    def launch_instance(self, instance_label, steam_root, proton_path, game_exe, preloader, compat_path, doorstop_args, dll_override_name):
        self.status_var.set(f"INITIATING {instance_label.upper()}...")
        os.makedirs(compat_path, exist_ok=True)

        env = os.environ.copy()

        dll_ovr = f"{dll_override_name}=n,b" if dll_override_name else "winhttp=n,b"

        env.update({
            "STEAM_COMPAT_CLIENT_INSTALL_PATH": steam_root,
            "STEAM_COMPAT_DATA_PATH": compat_path,
            "SteamAppId": APPID,
            "SteamGameId": APPID,
            "WINEDLLOVERRIDES": dll_ovr,
            "DOORSTOP_ENABLE": "TRUE",
            "DOORSTOP_TARGET_ASSEMBLY": preloader
        })

        arg_enable, arg_target = doorstop_args

        launch_args = [
            proton_path, "run", game_exe,
            arg_enable, "true",
            arg_target, preloader
        ]

        subprocess.Popen(launch_args, env=env)

    def run_launch_logic(self):
        try:
            steam_root = self.steam_root.get()
            proton_path = dict(self.protons).get(self.proton_choice.get())
            game_exe = self.game_exe.get()
            preloader = self.preloader.get()
            is_dual = self.dual.get()
            delay_sec = self.delay.get()
            do_symlink = self.symlink_fix.get()

            game_root = os.path.dirname(game_exe)
            profile_root = get_profile_root(preloader)

            if not all(map(os.path.isfile, [proton_path, game_exe, preloader])):
                raise RuntimeError("CRITICAL FILE MISSING")

            if not os.path.isdir(profile_root):
                raise RuntimeError("PROFILE ROOT NOT FOUND")

            doorstop_args = self.detect_doorstop_version(profile_root)
            dll_name = "winhttp"

            if do_symlink:
                dll_name = self.ensure_symlink(game_root, profile_root)

            main_compat = os.path.join(steam_root, f"steamapps/compatdata/{APPID}")
            self.launch_instance("Host", steam_root, proton_path, game_exe, preloader, main_compat, doorstop_args, dll_name)

            if not is_dual:
                self.reset_ui("SINGLE INJECTION COMPLETE.")
                return

            for i in range(delay_sec, 0, -1):
                self.status_var.set(f"AWAITING CLIENT INJECTION... {i}")
                time.sleep(1)

            client_compat = os.path.join(steam_root, f"steamapps/compatdata/{APPID}_2")
            self.launch_instance("Client", steam_root, proton_path, game_exe, preloader, client_compat, doorstop_args, dll_name)

            self.reset_ui("SYSTEMS OPERATIONAL.")

        except Exception as e:
            self.reset_ui(f"ERROR: {e}")

    def reset_ui(self, msg):
        self.status_var.set(msg)
        self.launch_btn.config(state="normal")

if __name__ == "__main__":
    App().mainloop()
