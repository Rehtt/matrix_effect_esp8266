# 创建一个精简版的st7789py模块，只保留必要的功能和最小的字体数据

import time
from micropython import const
import ustruct as struct
import gc

# 常量定义
ST77XX_NOP = const(0x00)
ST77XX_SWRESET = const(0x01)
ST77XX_SLPIN = const(0x10)
ST77XX_SLPOUT = const(0x11)
ST77XX_INVOFF = const(0x20)
ST77XX_INVON = const(0x21)
ST77XX_DISPOFF = const(0x28)
ST77XX_DISPON = const(0x29)
ST77XX_CASET = const(0x2A)
ST77XX_RASET = const(0x2B)
ST77XX_RAMWR = const(0x2C)
ST7789_MADCTL = const(0x36)
ST77XX_COLMOD = const(0x3A)

ST7789_MADCTL_MY = const(0x80)
ST7789_MADCTL_MX = const(0x40)
ST7789_MADCTL_MV = const(0x20)
ST7789_MADCTL_ML = const(0x10)
ST7789_MADCTL_BGR = const(0x08)
ST7789_MADCTL_MH = const(0x04)
ST7789_MADCTL_RGB = const(0x00)

ColorMode_65K = const(0x50)
ColorMode_16bit = const(0x05)

# 颜色定义
BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

_ENCODE_PIXEL = ">H"
_ENCODE_POS = ">HH"
_BUFFER_SIZE = const(256)

# 精简的字体数据 - 只包含数字和几个基本字符
_FONT = {
    (8, 8): {
        "0": [0x3E, 0x7F, 0x71, 0x59, 0x4D, 0x7F, 0x3E, 0x00],
        "1": [0x40, 0x42, 0x7F, 0x7F, 0x40, 0x40, 0x00, 0x00],
        "2": [0x62, 0x73, 0x59, 0x49, 0x6F, 0x66, 0x00, 0x00],
        "3": [0x22, 0x63, 0x49, 0x49, 0x7F, 0x36, 0x00, 0x00],
        "4": [0x18, 0x1C, 0x16, 0x53, 0x7F, 0x7F, 0x50, 0x00],
        "5": [0x27, 0x67, 0x45, 0x45, 0x7D, 0x39, 0x00, 0x00],
        "6": [0x3C, 0x7E, 0x4B, 0x49, 0x79, 0x30, 0x00, 0x00],
        "7": [0x03, 0x03, 0x71, 0x79, 0x0F, 0x07, 0x00, 0x00],
        "8": [0x36, 0x7F, 0x49, 0x49, 0x7F, 0x36, 0x00, 0x00],
        "9": [0x06, 0x4F, 0x49, 0x69, 0x3F, 0x1E, 0x00, 0x00],
        "A": [0x7C, 0x7E, 0x13, 0x13, 0x7E, 0x7C, 0x00, 0x00],
        "E": [0x7F, 0x7F, 0x49, 0x49, 0x63, 0x63, 0x00, 0x00],
        "S": [0x66, 0x6F, 0x49, 0x49, 0x7B, 0x33, 0x00, 0x00],
        "P": [0x7F, 0x7F, 0x09, 0x09, 0x0F, 0x06, 0x00, 0x00],
        " ": [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        ":": [0x00, 0x36, 0x36, 0x00, 0x00, 0x00, 0x00, 0x00],
        ".": [0x00, 0x60, 0x60, 0x00, 0x00, 0x00, 0x00, 0x00],
        "-": [0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x00, 0x00],
    }
}

def delay_ms(ms):
    time.sleep_ms(ms)
    
def color565(r, g=0, b=0):
    """Convert red, green and blue values (0-255) into a 16-bit 565 encoding.  As
    a convenience this is also available in the parent adafruit_rgb_display
    package namespace."""
    try:
        r, g, b = r  # see if the first var is a tuple/list
    except TypeError:
        pass
    return (r & 0xF8) << 8 | (g & 0xFC) << 3 | b >> 3
class ST7789:
    def __init__(self, spi, width, height, reset, dc, cs=None, backlight=None):
        self.width = width
        self.height = height
        self.spi = spi
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        self.xstart = 0
        self.ystart = 0

    def dc_low(self):
        self.dc.off()

    def dc_high(self):
        self.dc.on()

    def reset_low(self):
        if self.reset:
            self.reset.off()

    def reset_high(self):
        if self.reset:
            self.reset.on()

    def cs_low(self):
        if self.cs:
            self.cs.off()

    def cs_high(self):
        if self.cs:
            self.cs.on()

    def write(self, command=None, data=None):
        self.cs_low()
        if command is not None:
            self.dc_low()
            self.spi.write(bytes([command]))
        if data is not None:
            self.dc_high()
            self.spi.write(data)
        self.cs_high()

    def hard_reset(self):
        self.cs_low()
        self.reset_high()
        delay_ms(50)
        self.reset_low()
        delay_ms(50)
        self.reset_high()
        delay_ms(150)
        self.cs_high()

    def soft_reset(self):
        self.write(ST77XX_SWRESET)
        delay_ms(150)

    def _set_color_mode(self, mode):
        self.write(ST77XX_COLMOD, bytes([mode & 0x77]))

    def _set_mem_access_mode(self, rotation, vert_mirror, horz_mirror, is_bgr):
        rotation &= 7
        value = {
            0: 0,
            1: ST7789_MADCTL_MX,
            2: ST7789_MADCTL_MY,
            3: ST7789_MADCTL_MX | ST7789_MADCTL_MY,
            4: ST7789_MADCTL_MV,
            5: ST7789_MADCTL_MV | ST7789_MADCTL_MX,
            6: ST7789_MADCTL_MV | ST7789_MADCTL_MY,
            7: ST7789_MADCTL_MV | ST7789_MADCTL_MX | ST7789_MADCTL_MY,
        }[rotation]

        if vert_mirror:
            value = ST7789_MADCTL_ML
        elif horz_mirror:
            value = ST7789_MADCTL_MH

        if is_bgr:
            value |= ST7789_MADCTL_BGR
        self.write(ST7789_MADCTL, bytes([value]))

    def init(self, *, color_mode=ColorMode_65K | ColorMode_16bit):
        self.hard_reset()
        self.soft_reset()
        self.write(ST77XX_SLPOUT)
        delay_ms(50)
        self._set_color_mode(color_mode)
        delay_ms(50)
        self._set_mem_access_mode(4, True, True, False)
        self.write(ST77XX_INVON)
        delay_ms(10)
        self.write(ST77XX_DISPON)
        delay_ms(100)
        self.fill(0)
        gc.collect()

    def _encode_pos(self, x, y):
        return struct.pack(_ENCODE_POS, x, y)

    def _encode_pixel(self, color):
        return struct.pack(_ENCODE_PIXEL, color)

    def _set_columns(self, start, end):
        if start > end or end >= self.width:
            return
        start += self.xstart
        end += self.xstart
        self.write(ST77XX_CASET, self._encode_pos(start, end))

    def _set_rows(self, start, end):
        if start > end or end >= self.height:
            return
        start += self.ystart
        end += self.ystart
        self.write(ST77XX_RASET, self._encode_pos(start, end))

    def set_window(self, x0, y0, x1, y1):
        self._set_columns(x0, x1)
        self._set_rows(y0, y1)
        self.write(ST77XX_RAMWR)

    def pixel(self, x, y, color):
        self.set_window(x, y, x, y)
        self.write(None, self._encode_pixel(color))

    def fill_rect(self, x, y, width, height, color):
        self.set_window(x, y, x + width - 1, y + height - 1)
        chunks, rest = divmod(width * height, _BUFFER_SIZE)
        pixel = self._encode_pixel(color)
        self.dc_high()
        if chunks:
            data = pixel * _BUFFER_SIZE
            for _ in range(chunks):
                self.write(None, data)
        if rest:
            self.write(None, pixel * rest)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    def text(self, x, y, string, color=WHITE, bg=BLACK, scale=1, font=(8, 8)):
        font_data = _FONT.get(font)
        if not font_data:
            return

        font_width, font_height = font
        for char in string:
            glyph = font_data.get(char, font_data.get(" "))
            if not glyph:
                continue

            for row in range(font_height):
                if row >= len(glyph):
                    continue
                line = glyph[row]
                for col in range(font_width):
                    if line & (0x80 >> col):
                        self.fill_rect(
                            x + col * scale, y + row * scale, scale, scale, color
                        )
                    elif bg is not None:
                        self.fill_rect(
                            x + col * scale, y + row * scale, scale, scale, bg
                        )
            x += font_width * scale
