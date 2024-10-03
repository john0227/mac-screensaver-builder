import os
import shutil
import subprocess
import re
import tkinter
import tkinter.filedialog as filedialog
import tkinter.ttk as ttk
from typing import Callable

import cv2


class ScreenSaverBuilder:
    def __init__(self):
        self.xcode_projname = 'myscreensaver'
        
        self.root_path = os.path.dirname(__file__)
        self.ssbuilder_path = os.path.join(self.root_path, self.xcode_projname)
        self.asset_path = os.path.join(self.ssbuilder_path, self.xcode_projname)
        self.build_path = os.path.join(self.ssbuilder_path, self.xcode_projname, 'build')
        self.log_path = os.path.join(self.root_path, 'logs')
        
        self.ss_path = os.path.join(os.path.expanduser('~'), 'Library', 'Screen Savers')
        
        self.ss_video_name = os.path.join(self.asset_path, 'video')
        self.ss_preview_name = os.path.join(self.asset_path, 'preview.png')
    
    def get_preview_image(self, video_path: str):
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return

        ret, frame = cap.read()
        if ret:
            cv2.imwrite(self.ss_preview_name, frame)

        cap.release()
    
    def clear_cache(self):
        # Clear local build folder
        if os.path.isdir(self.build_path):
            shutil.rmtree(self.build_path, ignore_errors=True)
        
        # Clear Library DerivedData build folder
        derived_data = os.path.expanduser('~/Library/Developer/Xcode/DerivedData')
        if not os.path.isdir(derived_data):
            return
        for folder in os.listdir(derived_data):
            folder_abspath = os.path.join(derived_data, folder)
            if os.path.isdir(folder_abspath) and folder.startswith(self.xcode_projname):
                shutil.rmtree(folder_abspath, ignore_errors=True)
    
    @staticmethod
    def refresh_screensaver_procs():
        # Kill ScreenSaverAgent
        os.system('killall ScreenSaverAgent')
        
        # Kill legacyScreenSaver
        p = subprocess.Popen(['pgrep', 'legacyScreenSaver'], stdout=subprocess.PIPE)
        stdout, _ = p.communicate()
        pids = stdout.decode('utf-8').split()
        for pid in pids:
            os.system(f'kill -9 {pid}')
        
    def delete_assets(self):
        assets = [
            os.path.join(self.asset_path, 'video.mp4'),
            os.path.join(self.asset_path, 'video.mov'),
            os.path.join(self.asset_path, 'preview.png')
        ]
        for asset in assets:
            if os.path.exists(asset):
                os.remove(asset)
    
    def install_screensaver(self, ss_name: str):
        saver_path = os.path.join(self.build_path, f'{ss_name}.saver')
        shutil.move(saver_path, self.ss_path)

    def build_screensaver(self, video_path: str, ss_name: str, set_result: Callable[[str], None]):
        """Build the screensaver using the video_path"""
        if not video_path.endswith(('.mp4', '.mov')):
            set_result("Please select a video file in mp4 or mov format")
            return
        
        # Clear previous build cache
        self.clear_cache()
        
        # Read first frame into preview image
        self.get_preview_image(video_path)
        
        # Copy video to asset path
        video_ext = os.path.splitext(video_path)[1]
        shutil.copy2(video_path, self.ss_video_name + video_ext)
        
        xcode_build_cmd = [
            'xcodebuild',
            'clean',
            'build',
            '-project',
            os.path.join(self.ssbuilder_path, f"{self.xcode_projname}.xcodeproj"),
            '-configuration',
            'Debug',
            f'PRODUCT_NAME={ss_name}',
            f'SYMROOT={self.build_path}',
            f'CONFIGURATION_BUILD_DIR={self.build_path}'
        ]
        p = subprocess.Popen(xcode_build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # TODO: log stderr to tmp file and give user option to open text editor
        stdout, stderr = p.communicate()
        
        # TODO: retry once if fail
        if p.returncode != 0:
            set_result("Something went wrong")
            os.system(f'echo "{stderr.decode('utf-8')}" > logs/err.log')
            return
        
        set_result("Screensaver built successfully!")
        
        self.install_screensaver(ss_name)
        self.delete_assets()
        self.refresh_screensaver_procs()


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
            self.result_label['text'] = res
            self.result_label.grid_forget()
        else:
            self.result_label.grid(column=0, row=3, columnspan=3, sticky=tkinter.W)
            self.result_label['text'] = res
        self.result_label.update()
    
    def build_screensaver(self, video_path: str, ss_name: str):
        self.set_result('Building screen saver...')
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

if __name__ == '__main__':
    main()
