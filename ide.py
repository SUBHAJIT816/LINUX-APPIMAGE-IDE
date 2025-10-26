import tkinter as tk
from tkinter import filedialog, messagebox
import os
import subprocess
import shutil
import urllib.request
import tempfile
import venv

class AppImageIDE:
    def __init__(self, root):
        self.root = root
        self.root.title("AppImage Maker IDE")
        self.root.geometry("500x450")

        # Input fields
        tk.Label(root, text="App Name:").pack(pady=5)
        self.app_name = tk.Entry(root, width=50)
        self.app_name.pack()

        tk.Label(root, text="Version:").pack(pady=5)
        self.version = tk.Entry(root, width=50)
        self.version.pack()

        tk.Label(root, text="Description:").pack(pady=5)
        self.description = tk.Entry(root, width=50)
        self.description.pack()

        # Icon upload
        tk.Label(root, text="Icon (PNG/JPG):").pack(pady=5)
        self.icon_path = tk.StringVar()
        tk.Button(root, text="Upload Icon", command=self.upload_icon).pack()
        tk.Label(root, textvariable=self.icon_path).pack()

        # Python code upload
        tk.Label(root, text="Python Code (.py file):").pack(pady=5)
        self.code_path = tk.StringVar()
        tk.Button(root, text="Upload Python Code", command=self.upload_code).pack()
        tk.Label(root, textvariable=self.code_path).pack()

        # Requirements upload
        tk.Label(root, text="Requirements File (optional, .txt with pip packages):").pack(pady=5)
        self.req_path = tk.StringVar()
        tk.Button(root, text="Upload Requirements", command=self.upload_req).pack()
        tk.Label(root, textvariable=self.req_path).pack()

        # Create button
        tk.Button(root, text="Create AppImage", command=self.create_appimage, bg="green", fg="white").pack(pady=20)

    def upload_icon(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if file_path:
            self.icon_path.set(file_path)

    def upload_code(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if file_path:
            self.code_path.set(file_path)

    def upload_req(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if file_path:
            self.req_path.set(file_path)

    def create_appimage(self):
        app_name = self.app_name.get().strip()
        version = self.version.get().strip()
        description = self.description.get().strip()
        icon_path = self.icon_path.get()
        code_path = self.code_path.get()
        req_path = self.req_path.get()

        if not all([app_name, version, description, icon_path, code_path]):
            messagebox.showerror("Error", "App Name, Version, Description, Icon, and Python Code are required!")
            return

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create virtual environment for dependencies
            venv_dir = os.path.join(temp_dir, "venv")
            venv.create(venv_dir, with_pip=True)
            pip_exe = os.path.join(venv_dir, "bin", "pip")

            # Install requirements if provided
            if req_path:
                subprocess.run([pip_exe, "install", "-r", req_path], check=True)

            # Install PyInstaller in venv
            subprocess.run([pip_exe, "install", "pyinstaller"], check=True)

            # Run PyInstaller with activated venv
            dist_dir = os.path.join(temp_dir, "dist")
            os.makedirs(dist_dir, exist_ok=True)  # Ensure dist_dir exists
            activate_cmd = f"source {venv_dir}/bin/activate && pyinstaller --onefile --distpath {dist_dir} {code_path}"
            subprocess.run(["bash", "-c", activate_cmd], check=True)

            # Rest of the process
            app_dir = os.path.join(temp_dir, "AppDir")
            os.makedirs(app_dir)
            usr_dir = os.path.join(app_dir, "usr", "bin")
            os.makedirs(usr_dir)

            exe_name = os.path.splitext(os.path.basename(code_path))[0]
            exe_path = os.path.join(dist_dir, exe_name)
            shutil.move(exe_path, os.path.join(usr_dir, app_name))

            # Copy icon
            icon_dest = os.path.join(app_dir, f"{app_name}.png")
            shutil.copy(icon_path, icon_dest)

            # Create AppRun script
            apprun_content = f"""#!/bin/bash
export APPDIR="$(dirname "$(readlink -f "$0")")"
export PATH="$APPDIR/usr/bin:$PATH"
exec "$APPDIR/usr/bin/{app_name}" "$@"
"""
            with open(os.path.join(app_dir, "AppRun"), "w") as f:
                f.write(apprun_content)
            os.chmod(os.path.join(app_dir, "AppRun"), 0o755)

            # Create desktop file
            desktop_content = f"""[Desktop Entry]
Name={app_name}
Exec=AppRun
Icon={app_name}
Type=Application
Categories=Utility;
Comment={description}
"""
            with open(os.path.join(app_dir, f"{app_name}.desktop"), "w") as f:
                f.write(desktop_content)

            # Download appimagetool if not present
            appimagetool_path = "/tmp/appimagetool"
            if not os.path.exists(appimagetool_path):
                urllib.request.urlretrieve("https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage", appimagetool_path)
                os.chmod(appimagetool_path, 0o755)

            # Build AppImage
            output_path = os.path.join(os.getcwd(), f"{app_name}-{version}.AppImage")
            subprocess.run([appimagetool_path, app_dir, output_path], check=True)

        messagebox.showinfo("Success", f"AppImage created: {output_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppImageIDE(root)
    root.mainloop()
