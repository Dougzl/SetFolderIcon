import win32ui
import win32gui
import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import subprocess
import re
import time
import ctypes
from utils import set_folder_icon

# Set directory as a global variable
directory = None
highlighted_icon_canvas = None
icon_canvases = []  # 存储所有图标的 canvas

def run_cmd(command):
    subprocess.call(command, creationflags=0x08000000)

def contains_chinese(text):
    # 匹配任何中文字符
    chinese_char_pattern = re.compile(r'[\u4e00-\u9fff]')
    return bool(chinese_char_pattern.search(text))

def extract_icons(directory):
    icons = []
    for root, _, files in os.walk(directory):
        relative_root = os.path.relpath(root, directory)
        if not contains_chinese(relative_root):
            for file in files:
                if file.lower().endswith('.exe') or file.lower().endswith('.ico'):
                    icons.append(os.path.abspath(os.path.join(root, file)))
    return icons

def create_window_with_icons(icons):
    global root
    root.deiconify()
    root.geometry("300x400")  # Adjust the size as needed
    root.title("Icon Viewer")  # Set the window title

    # Create a Canvas
    canvas = tk.Canvas(root, bg='#303841', bd=0, highlightthickness=0)
    scrollable_frame = tk.Frame(canvas, bg='#303841')

    # Configure the Canvas
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # Create a window in the Canvas to contain the scrollable_frame
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.pack(side="left", fill="both", expand=True)

    # Bind mouse wheel event for scrolling
    def on_mouse_wheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", on_mouse_wheel)

    tk_images = []
    for idx, icon in enumerate(icons):
        openImg(scrollable_frame, tk_images, icon)

        # Add transparent space between icons
        spacer = tk.Canvas(scrollable_frame, width=64, height=10, bg='#303841', bd=0, highlightthickness=0)
        spacer.pack(side=tk.TOP, anchor=tk.NW, padx=0, pady=0)

    # Ensure scrollregion is updated after all images are added
    canvas.configure(scrollregion=canvas.bbox("all"))

    # Add button to choose new icon
    choose_icon_button = tk.Button(canvas, text="Choose Icon", command=choose_new_icon)
    choose_icon_button.pack(side="top", anchor="se", pady=10, padx=10)

    root.mainloop()

def openImg(container, tk_images, icon):
    try:
        img = None
        if icon.lower().endswith('exe'):
            # 获取exe文件的图标
            large, small = win32gui.ExtractIconEx(icon, 0)
            if len(large) > 0 and len(small) > 0:
                win32gui.DestroyIcon(small[0])

                # 创建一个设备上下文
                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, 32, 32)

                # 在设备上下文中绘制图标
                hdc = hdc.CreateCompatibleDC()
                hdc.SelectObject(hbmp)
                hdc.DrawIcon((0, 0), large[0])

                # 保存图标到本地文件
                bmpinfo = hbmp.GetInfo()
                bmpstr = hbmp.GetBitmapBits(True)
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1)
        else:
            img = Image.open(icon)

        if img is not None:
            img = img.resize((64, 64), Image.LANCZOS)
            tk_image = ImageTk.PhotoImage(img)
            tk_images.append(tk_image)  # 将Tkinter图片对象存储在列表中

            # Create a Canvas and draw the image
            icon_canvas = tk.Canvas(container, width=64, height=64, bg='#303841', bd=0, highlightthickness=2, highlightbackground='#303841')
            icon_canvas.pack(side=tk.TOP, anchor=tk.NW, padx=0, pady=0)
            icon_canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)

            # Store canvas for later use
            icon_canvases.append(icon_canvas)

            # Bind click and double-click event to the Canvas
            icon_canvas.bind("<Button-1>", lambda event: on_icon_click(icon, icon_canvas))
            icon_canvas.bind("<Double-Button-1>", lambda event: on_icon_double_click(icon))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open image: {e}")

def choose_new_icon():
    new_icon_path = filedialog.askopenfilename(
        title="Select Icon",
        filetypes=[("Icon Files", "*.ico")]
    )
    if new_icon_path:
        try:
            # Generate a unique filename if a file with the same name exists
            target_path = os.path.join(directory, os.path.basename(new_icon_path))
            if os.path.exists(target_path):
                base, ext = os.path.splitext(target_path)
                counter = 1
                while os.path.exists(target_path):
                    target_path = f"{base}_{counter}{ext}"
                    counter += 1

            shutil.copyfile(new_icon_path, target_path)
            run_cmd(f'attrib +h +s "{target_path}"')

            # Set the new icon as the folder icon
            process_icon(target_path)

            # Close the root window
            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy icon: {e}")

def on_icon_click(icon, icon_canvas):
    global highlighted_icon_canvas

    # Remove the highlight from the previously highlighted icon
    if highlighted_icon_canvas:
        highlighted_icon_canvas.configure(highlightbackground="#303841")

    # Highlight the currently clicked icon
    icon_canvas.configure(highlightbackground="white")
    highlighted_icon_canvas = icon_canvas

def on_icon_double_click(icon):
    # Process icon and update desktop.ini
    process_icon(icon)

    # Close the root window
    root.destroy()

def convert_to_unicode_path(path):
    return ''.join([f'\\u{ord(char):04x}' if ord(char) > 127 else char for char in path])

def process_icon(icon):
    global directory

    # Calculate relative path
    relative_icon_path = os.path.relpath(icon, directory)

    if contains_chinese(relative_icon_path):
        relative_icon_path = convert_to_unicode_path(relative_icon_path)

    # Update desktop.ini file if exists
    ini_path = os.path.join(directory, 'desktop.ini')
    if os.path.exists(ini_path):
        try:
            with open(ini_path, 'r+', encoding='utf-8') as file:
                lines = file.readlines()
                found = False
                for i, line in enumerate(lines):
                    if line.lower().startswith('iconresource'):
                        lines[i] = f'IconResource={relative_icon_path},0\n'
                        found = True
                        break
                if not found:
                    lines.append(f'IconResource={relative_icon_path},0\n')
                file.seek(0)
                file.writelines(lines)
                file.truncate()

            run_cmd(f'attrib +h +s "{ini_path}"')  # Set file attributes to hidden and system
            run_cmd(f'attrib +s "{directory}"')  # Set directory as a system folder
            set_folder_icon(directory, icon)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update desktop.ini: {e}")
    else:
        # Create and write a new desktop.ini file if it does not exist
        try:
            with open(ini_path, 'w', encoding='utf-8') as file:
                file.write(f'[.ShellClassInfo]\nIconResource={icon},0\n')
                run_cmd(f'attrib +h +s "{ini_path}"')
                run_cmd(f'attrib +s "{directory}"')
                set_folder_icon(directory, icon)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create desktop.ini: {e}")


# Main application
def main():
    global root
    global directory

    import sys

    root = tk.Tk()
    root.withdraw()  # Hide the root window

    if len(sys.argv) > 1:
        directory = sys.argv[1]
        if not os.path.isdir(directory):
            print("Provided directory does not exist.")
            directory = filedialog.askdirectory(title="Select Directory")
            sys.exit(1)
    else:
        directory = filedialog.askdirectory(title="Select Directory")
        if not directory:
            print("No directory selected.")
            sys.exit(1)

    # Set the directory to absolute path
    directory = os.path.abspath(directory)

    # Extract icons from the directory
    icons = extract_icons(directory)
    create_window_with_icons(icons)

if __name__ == "__main__":
    main()
