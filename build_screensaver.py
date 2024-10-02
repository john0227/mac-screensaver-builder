import os
import shutil
import subprocess
import re
import time
import tkinter
import tkinter.filedialog as filedialog
import tkinter.ttk as ttk
from typing import Callable

import cv2


class ScreenSaverBuilder:
    def __init__(self):
        self.scheme = 'myscreensaver'
        self.ssbuilder_path = os.path.join(os.path.dirname(__file__), self.scheme)
        self.asset_path = os.path.join(self.ssbuilder_path, self.scheme)
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

    def build_screensaver(self, video_path: str, ss_name: str, set_result: Callable[[str], None]):
        """Build the screensaver using the video_path"""
        if video_path.endswith(('.mp4', '.mov')):
            # Read first frame into preview image
            self.get_preview_image(video_path)
            
            # Copy video to asset path
            video_ext = os.path.splitext(video_path)[1]
            shutil.copy2(video_path, self.ss_video_name + video_ext)
            
            # TODO: try rm -rf ./build and ~/Library/Developer/Xcode/DerivedData/myscreensaver/Build/*
            
            xcode_build_cmd = [
                'xcodebuild',
                'clean',
                'build',
                '-project',
                os.path.join(self.ssbuilder_path, f"{self.scheme}.xcodeproj"),
                '-configuration',
                'Debug',
                f'PRODUCT_NAME={ss_name}'
                # '-scheme',
                # self.scheme,
                # '-archivePath',
                # archive_path,
                # 'archive'
            ]
            p = subprocess.Popen(xcode_build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # TODO: log stderr to tmp file and give user option to open text editor
            stdout, stderr = p.communicate()
            with open('build.txt', 'w') as f:
                f.write(stdout.decode('utf-8'))
                f.write('\n=======================\n')
                f.write(stderr.decode('utf-8'))
                
            if p.returncode != 0:
                set_result("Something went wrong!")
                return
            
            # xcode_export_cmd = [
            #     'xcodebuild',
            #     '-exportArchive',
            #     '-archivePath',
            #     archive_path,
            #     '-exportPath',
            #     f'{self.ssbuilder_path}/{ss_name}.saver',
            #     '-exportOptionsPlist',
            #     os.path.join(self.ssbuilder_path, 'ExportOptions.plist')
            # ]
            # p = subprocess.Popen(xcode_export_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # # TODO: log stderr to tmp file and give user option to open text editor
            # stdout, stderr = p.communicate()
            # with open('export.txt', 'w') as f:
            #     f.write(stdout.decode('utf-8'))
            #     f.write('\n=======================\n')
            #     f.write(stderr.decode('utf-8'))
            # if p.returncode != 0:
            #     set_result("Something went wrong!")
            #     return
            set_result("Screensaver built successfully!")
        else:
            set_result("Please select a video file!!")


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
        result_label = ttk.Label(mainframe, text="", name="result_label")
            
        ttk.Button(
            mainframe,
            text="Build",
            command=lambda: self.build_screensaver(video_entry.get(), ss_name_entry.get(), result_label)
        ).grid(column=0, row=2, sticky=tkinter.W)
    
    def build_screensaver(self, video_path: str, ss_name: str, result_label: tkinter.Label):
        # Create a build button
        def set_result(res: str):
            result_label.grid(column=0, row=3, columnspan=3, sticky=tkinter.W)
            result_label['text'] = res
        
        set_result('Building screen saver...')
        time.sleep(5)
        self.ssb.build_screensaver(video_path, ss_name, set_result)

    def start(self):
        self.root.mainloop()
        
    def browse_for_file(self, video_entry, ss_name_entry):
        """Open a file dialog and fill in the entry with the selected file path"""
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
