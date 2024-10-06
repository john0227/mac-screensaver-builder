import os
import re
import shutil
import subprocess
import tkinter
import tkinter.filedialog as filedialog
import tkinter.ttk as ttk
import uuid
from typing import Callable

import cv2


class TargetTemplate:
    def __init__(self, target_name: str, project_path: str):
        self.target_name = target_name
        
        self.project_path = project_path
        self.template_folder = os.path.join(os.path.dirname(__file__), "template")
        self.target_folder = os.path.join(self.project_path, self.target_name)
        
        self.template_filepaths = [
            os.path.join(self.template_folder, "project.pbxproj.template"),
            os.path.join(self.template_folder, "templateView.h.template"),
            os.path.join(self.template_folder, "templateView.m.template")
        ]
        self.rendered_filepaths = [
            os.path.join(self.project_path, "myscreensaver.xcodeproj", "project.pbxproj"),
            os.path.join(self.target_folder, f"{self.target_name}View.h"),
            os.path.join(self.target_folder, f"{self.target_name}View.m")
        ]
        self.template_mapping = dict(zip(self.template_filepaths, self.rendered_filepaths))
            
    def __create_target(self):
        # Create target directory
        if not os.path.isdir(self.target_folder):
            os.mkdir(self.target_folder)
            
        # Back up project.pbxproj
        project_pbxproj = self.rendered_filepaths[0]
        backed_project_pbxproj = os.path.join(self.template_folder, "project.pbxproj.bak")
        if os.path.isfile(project_pbxproj):
            shutil.copy(project_pbxproj, backed_project_pbxproj)
    
    def create_target(self, **kwargs):
        self.__create_target()
        
        for template_fp in self.template_filepaths:
            with open(template_fp) as f:
                template = f.read()
        
            for k, v in kwargs.items():
                template_str = "{{" + k + "}}"
                template = template.replace(template_str, v)
            
            with open(self.template_mapping[template_fp], "w") as f:
                f.write(template)
                
    def delete_target(self):
        # Remove target directory
        if os.path.isdir(self.target_folder):
            shutil.rmtree(self.target_folder)
        
        # Restore project.pbxproj
        project_pbxproj = self.rendered_filepaths[0]
        backed_project_pbxproj = os.path.join(self.template_folder, "project.pbxproj.bak")
        if os.path.isfile(backed_project_pbxproj):
            shutil.copy(backed_project_pbxproj, project_pbxproj)


class ScreenSaverBuilder:
    def __init__(self):
        self.xcode_projname = "myscreensaver"
        self.bundle_id = "com.cupcakes.myscreensaver"
        
        self.root_path = os.path.dirname(__file__)
        self.project_path = os.path.join(self.root_path, self.xcode_projname)
        self.log_path = os.path.join(self.root_path, "logs")
        
        self.ss_path = os.path.join(os.path.expanduser("~"), "Library", "Screen Savers")
    
    def init_target_paths(self, target_name: str):
        self.asset_path = os.path.join(self.project_path, target_name)
        self.build_path = os.path.join(self.project_path, target_name, "build")
        self.ss_video_name = os.path.join(self.asset_path, "video")
        self.ss_preview_name = os.path.join(self.asset_path, "preview.png")
    
    def get_preview_image(self, video_path: str):
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return

        ret, frame = cap.read()
        if ret:
            cv2.imwrite(self.ss_preview_name, frame)

        cap.release()
    
    def clear_build_cache(self):
        # Clear local build folder
        if os.path.isdir(self.build_path):
            shutil.rmtree(self.build_path, ignore_errors=True)
        
        # Clear Library DerivedData build folder
        derived_data = os.path.expanduser("~/Library/Developer/Xcode/DerivedData")
        if os.path.isdir(derived_data):
            for folder in os.listdir(derived_data):
                folder_abspath = os.path.join(derived_data, folder)
                if os.path.isdir(folder_abspath) and folder.startswith(self.xcode_projname):
                    shutil.rmtree(folder_abspath, ignore_errors=True)
    
    @staticmethod
    def refresh_screensaver_procs():
        os.system("killall -KILL ScreenSaverAgent 2> /dev/null")
        os.system("killall -KILL legacyScreenSaver 2> /dev/null")
        os.system('killall -KILL "Screen Saver" 2> /dev/null')
        
    def delete_assets(self):
        for asset in os.listdir(self.asset_path):
            if asset.startswith("video") or asset == "preview.png":
                os.remove(os.path.join(self.asset_path, asset))
    
    def install_screensaver(self, ss_name: str):
        saver_path = os.path.join(self.build_path, f"{ss_name}.saver")
        shutil.move(saver_path, self.ss_path)

    def build_screensaver(self, video_path: str, ss_name: str, set_result: Callable[[str], None], is_retry=False):
        """Build the screensaver using the video_path"""
        if not video_path.endswith((".mp4", ".mov", ".m4v")):
            set_result("Please select a video file in .mp4, .mov, or .m4v format")
            return
        
        target_name = re.sub(r"\s+", "", ss_name)
        self.init_target_paths(target_name)
        
        target_builder = TargetTemplate(target_name, self.project_path)
        try:
            # Create new target
            generate_uuid = lambda: "".join(str(uuid.uuid4()).upper().split('-')[1:])
            target_builder.create_target(
                TARGET_NAME=target_name,
                UUID_BUILD_CONFIGURATION=generate_uuid(),
                UUID_DEBUG_CONFIGURATION=generate_uuid(),
                UUID_FRAMEWORKS=generate_uuid(),
                UUID_GROUP=generate_uuid(),
                UUID_HEADERS=generate_uuid(),
                UUID_PROJECT=generate_uuid(),
                UUID_RELEASE_CONFIGURATION=generate_uuid(),
                UUID_RESOURCES=generate_uuid(),
                UUID_SAVER=generate_uuid(),
                UUID_SOURCES=generate_uuid(),
            )
            
            # Clear previous build cache
            self.clear_build_cache()
            
            # Read first frame into preview image
            self.get_preview_image(video_path)
            
            # Copy video to asset path
            video_ext = os.path.splitext(video_path)[1]
            shutil.copy2(video_path, self.ss_video_name + video_ext)
            
            xcode_build_cmd = [
                "xcodebuild",
                "clean",
                "build",
                "-project",
                os.path.join(self.project_path, f"{self.xcode_projname}.xcodeproj"),
                "-target",
                target_name,
                "-configuration",
                "Release",
                f"PRODUCT_NAME={ss_name}",
                f"SYMROOT={self.build_path}",
                f"CONFIGURATION_BUILD_DIR={self.build_path}",
            ]
            p = subprocess.Popen(xcode_build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                if is_retry:
                    # TODO: log stderr to tmp file and give user option to open text editor
                    set_result("Something went wrong")
                    with open("logs/err.log", "w") as f:
                        f.write((stderr or b'').decode('utf-8'))
                else:
                    self.build_screensaver(video_path, ss_name, set_result, is_retry=True)
                return
            
            os.system(f'echo "{stdout.decode('utf-8') or b''}" > logs/run.log')
            
            self.install_screensaver(ss_name)
            set_result("Screensaver built successfully!")
        except Exception as e:
            # TODO: log error
            print(str(e))
        finally:
            # Clean up after build
            self.delete_assets()
            self.clear_build_cache()
            self.refresh_screensaver_procs()
            target_builder.delete_target()


class ScreenSaverUI:
    def __init__(self, ssb=None):
        self.root = None
        self.ssb = ssb or ScreenSaverBuilder()

    def build(self):
        root = self.root = tkinter.Tk()
        root.title("Build ScreenSaver")
        root.resizable(False, False)

        # Create a frame
        mainframe = ttk.Frame(root, padding="3 3 12 12")
        mainframe.grid(column=0, row=0, sticky=(tkinter.N, tkinter.W, tkinter.E, tkinter.S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        # Screen saver name
        ttk.Label(mainframe, text="Screen Saver Name:").grid(column=0, row=1, sticky=tkinter.W)
        ss_name_entry = ttk.Entry(mainframe, width=20)
        ss_name_entry.grid(column=1, row=1, sticky=(tkinter.W, tkinter.E))
        
        # Choose video label/button
        ttk.Label(mainframe, text="Choose a video file:").grid(column=0, row=0, sticky=tkinter.W)
        video_entry = ttk.Entry(mainframe, width=20)
        video_entry.grid(column=1, row=0, sticky=(tkinter.W, tkinter.E))
        ttk.Button(
            mainframe,
            text="Browse",
            command=lambda: self.browse_for_file(video_entry, ss_name_entry)
        ).grid(column=2, row=0, sticky=tkinter.W)

        # Result label (don't show yet)
        self.result_label = ttk.Label(mainframe, text="", name="result_label")
            
        # Create a build button
        ttk.Button(
            mainframe,
            text="Build",
            command=lambda: self.build_screensaver(video_entry.get(), ss_name_entry.get())
        ).grid(column=0, row=2, sticky=tkinter.W)
    
    def set_result(self, res: str):
        if not res:
            self.result_label.grid_forget()
        else:
            self.result_label.grid(column=0, row=3, columnspan=3, sticky=tkinter.W)
            self.result_label["text"] = res
        self.result_label.update()
    
    def build_screensaver(self, video_path: str, ss_name: str):
        self.set_result("Building screen saver...")
        self.ssb.build_screensaver(video_path, ss_name, self.set_result)

    def start(self):
        self.root.mainloop()
        
    def browse_for_file(self, video_entry, ss_name_entry):
        """Open a file dialog and fill in the entry with the selected file path"""
        
        # Clear result if present
        self.set_result("")
        
        video_path = filedialog.askopenfilename(parent=self.root, filetypes=[("Movie files", ".mp4 .mov")])
        if video_path:
            # Update video path
            video_entry.delete(0, tkinter.END)
            video_entry.insert(0, video_path)
            # Update screensaver name
            ss_name_entry.delete(0, tkinter.END)
            ss_name_entry.insert(0, os.path.splitext(os.path.basename(video_path))[0])


def main():
    ssb = ScreenSaverBuilder()
    ui = ScreenSaverUI(ssb)
    ui.build()
    ui.start()

if __name__ == "__main__":
    main()
