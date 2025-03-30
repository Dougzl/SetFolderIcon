import ctypes
import os

# 加载 shell32.dll
shell32 = ctypes.windll.shell32

# SHGFI_USEFILEATTRIBUTES 表示使用文件属性，而非实际文件
FCSM_ICONFILE = 0x00000010
SHGFI_ICON = 0x000000100
SHGFI_LARGEICON = 0x000000000
SHGFI_SMALLICON = 0x000000001

# 定义 SHFOLDERCUSTOMSETTINGS 结构体
class SHFOLDERCUSTOMSETTINGS(ctypes.Structure):
    _fields_ = [
        ("dwSize", ctypes.c_ulong),
        ("dwMask", ctypes.c_ulong),
        ("pszIconFile", ctypes.c_wchar_p),
        ("cchIconFile", ctypes.c_ulong),
        ("iIconIndex", ctypes.c_int),
    ]

def set_folder_icon(folder_path, icon_path):
    """
    修改 Windows 文件夹的图标
    :param folder_path: 文件夹路径
    :param icon_path: 图标文件路径
    """
    # 确保文件夹存在
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"文件夹 {folder_path} 不存在")

    if not os.path.exists(icon_path):
        if os.path.exists(os.path.join(folder_path, icon_path)):
            icon_path = os.path.join(folder_path, icon_path)
        raise FileNotFoundError(f"图标文件 {icon_path} 不存在")

    # 结构体实例
    settings = SHFOLDERCUSTOMSETTINGS()
    settings.dwSize = ctypes.sizeof(SHFOLDERCUSTOMSETTINGS)
    settings.dwMask = FCSM_ICONFILE
    settings.pszIconFile = icon_path
    settings.cchIconFile = len(icon_path) + 1
    settings.iIconIndex = 0  # 使用默认图标索引

    # 调用 API 设置文件夹图标
    result = shell32.SHGetSetFolderCustomSettings(
        ctypes.byref(settings), folder_path, 0
    )

    if result != 0:
        raise ctypes.WinError(result)

if __name__ == "__main__":
    # 目标路径
    folder_path = r"C:\Users\dongz\Desktop\dipper"
    icon_path = r"C:\Users\dongz\opt\icons\Folder-Ico\4k_downloader.ico"

    # 设置文件夹图标
    set_folder_icon(folder_path, icon_path)
