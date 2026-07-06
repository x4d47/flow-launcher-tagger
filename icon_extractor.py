# Fully AI generated

import sys
from pathlib import Path

plugindir = Path.absolute(Path(__file__).parent)
sys.path.insert(0, str(plugindir / "lib"))

import base64
import ctypes
import io

from PIL import Image

# Завантаження системних бібліотек для роботи з Win32 API
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

# --- НАЛАШТУВАННЯ ТИПІВ ДЛЯ СУМІСНОСТІ З X64 ---
# Визначення базових типів Windows
HICON = ctypes.c_void_p
HBITMAP = ctypes.c_void_p
HDC = ctypes.c_void_p
HANDLE = ctypes.c_void_p

# Оголошення прототипів функцій user32
user32.PrivateExtractIconsW.argtypes = [
    ctypes.c_wchar_p,  # szFileName
    ctypes.c_int,  # nIconIndex
    ctypes.c_int,  # cxIcon
    ctypes.c_int,  # cyIcon
    ctypes.POINTER(HICON),  # phicon
    ctypes.POINTER(ctypes.c_uint),  # piconid
    ctypes.c_uint,  # nIcons
    ctypes.c_uint,  # flags
]
user32.PrivateExtractIconsW.restype = ctypes.c_uint

user32.GetIconInfo.argtypes = [HICON, ctypes.c_void_p]
user32.GetIconInfo.restype = ctypes.c_bool

user32.GetDC.argtypes = [ctypes.c_void_p]
user32.GetDC.restype = HDC

user32.ReleaseDC.argtypes = [ctypes.c_void_p, HDC]
user32.ReleaseDC.restype = ctypes.c_int

user32.DestroyIcon.argtypes = [HICON]
user32.DestroyIcon.restype = ctypes.c_bool

# Оголошення прототипів функцій gdi32
gdi32.GetObjectW.argtypes = [HANDLE, ctypes.c_int, ctypes.c_void_p]
gdi32.GetObjectW.restype = ctypes.c_int

gdi32.GetDIBits.argtypes = [
    HDC,
    HBITMAP,
    ctypes.c_uint,
    ctypes.c_uint,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_uint,
]
gdi32.GetDIBits.restype = ctypes.c_int

gdi32.DeleteObject.argtypes = [HANDLE]
gdi32.DeleteObject.restype = ctypes.c_bool
# -----------------------------------------------


def get_dll_icon_as_data_uri(
    dll_path: str, icon_index: int, icon_size: int = 48
) -> str:
    """
    Витягує іконку з DLL за індексом і повертає її у форматі Data URI (Base64).
    """
    # Резервуємо масив для дескриптора іконки (HICON) та її ID
    phicon = (HICON * 1)()
    piconid = (ctypes.c_uint * 1)()

    # Витягуємо іконку з DLL
    result = user32.PrivateExtractIconsW(
        dll_path,
        icon_index,
        icon_size,
        icon_size,
        phicon,
        piconid,
        1,
        0,
    )

    if result == 0 or not phicon[0]:
        raise FileNotFoundError(
            f"Не вдалося витягти іконку з індексом {icon_index} із {dll_path}"
        )

    hicon = phicon[0]

    try:
        # Отримуємо інформацію про структуру іконки (ICONINFO)
        class ICONINFO(ctypes.Structure):
            _fields_ = [
                ("fIcon", ctypes.c_bool),
                ("xHotspot", ctypes.c_uint),
                ("yHotspot", ctypes.c_uint),
                ("hbmMask", HBITMAP),
                ("hbmColor", HBITMAP),
            ]

        icon_info = ICONINFO()
        user32.GetIconInfo(hicon, ctypes.byref(icon_info))

        # Отримуємо інформацію про BITMAP структури hbmColor
        class BITMAP(ctypes.Structure):
            _fields_ = [
                ("bmType", ctypes.c_long),
                ("bmWidth", ctypes.c_long),
                ("bmHeight", ctypes.c_long),
                ("bmWidthBytes", ctypes.c_long),
                ("bmPlanes", ctypes.c_ushort),
                ("bmBitsPixel", ctypes.c_ushort),
                ("bmBits", ctypes.c_void_p),
            ]

        bmp = BITMAP()
        gdi32.GetObjectW(icon_info.hbmColor, ctypes.sizeof(bmp), ctypes.byref(bmp))

        # Визначення розміру буфера для пікселів (формат BGRA / 32-bit)
        hdc = user32.GetDC(None)

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [
                ("biSize", ctypes.c_uint),
                ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long),
                ("biPlanes", ctypes.c_ushort),
                ("biBitCount", ctypes.c_ushort),
                ("biCompression", ctypes.c_uint),
                ("biSizeImage", ctypes.c_uint),
                ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long),
                ("biClrUsed", ctypes.c_uint),
                ("biClrImportant", ctypes.c_uint),
            ]

        bi = BITMAPINFOHEADER()
        bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bi.biWidth = bmp.bmWidth
        bi.biHeight = (
            -bmp.bmHeight
        )  # Негативна висота для правильного порядку рядків (Top-Down)
        bi.biPlanes = 1
        bi.biBitCount = 32
        bi.biCompression = 0  # BI_RGB

        # Виділення пам'яті під пікселі
        buffer_size = bmp.bmWidth * bmp.bmHeight * 4
        pixel_buffer = ctypes.create_string_buffer(buffer_size)

        # Копіюємо байти зображення в буфер
        gdi32.GetDIBits(
            hdc, icon_info.hbmColor, 0, bmp.bmHeight, pixel_buffer, ctypes.byref(bi), 0
        )

        # Звільнення контексту пристрою та дескрипторів BITMAP
        user32.ReleaseDC(None, hdc)
        gdi32.DeleteObject(icon_info.hbmColor)
        gdi32.DeleteObject(icon_info.hbmMask)

        # Створення зображення за допомогою Pillow
        img = Image.frombytes(
            "RGBA", (bmp.bmWidth, bmp.bmHeight), pixel_buffer.raw, "raw", "BGRA"
        )

        # Збереження у пам'ять (BytesIO) у форматі PNG
        output = io.BytesIO()
        img.save(output, format="PNG")
        png_bytes = output.getvalue()

        # Кодування в Base64 для Data URI
        base64_data = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{base64_data}"

    finally:
        # Обов'язкове звільнення дескриптора іконки
        user32.DestroyIcon(hicon)


# --- Приклад використання ---
if __name__ == "__main__":
    dll = "C:\\Windows\\System32\\imageres.dll"
    # Індекс 14 в imageres.dll зазвичай відповідає стандартній іконці невідомого додатка/файлу
    try:
        data_uri = get_dll_icon_as_data_uri(dll, icon_index=14, icon_size=48)
        print("Згенерований Data URI (перші 100 символів):")
        print(data_uri[:100] + "...")
    except Exception as e:
        print(f"Помилка: {e}")
