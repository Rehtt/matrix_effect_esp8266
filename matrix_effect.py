import st7789py_lite as st
from machine import Pin, SPI
import random as urandom  # 使用urandom替代random
import time
import gc

# 初始化显示屏
backlight = Pin(5, Pin.OUT)
backlight.on()
display = st.ST7789(
    SPI(1, baudrate=40000000, polarity=1),
    240,
    240,
    reset=Pin(2, Pin.OUT),
    dc=Pin(0, Pin.OUT),
)
display.init()

# 定义颜色
GREEN_BRIGHT = st.color565(0, 255, 0)
GREEN_MEDIUM = st.color565(0, 200, 0)
GREEN_DIM = st.color565(0, 150, 0)
GREEN_DARK = st.color565(0, 100, 0)
GREEN_VERY_DARK = st.color565(0, 50, 0)

# 字符集 - 使用已有的字体数据中的字符
CHARS = "0123456789AEPS:.-"

# 屏幕参数
CHAR_WIDTH = 8
CHAR_HEIGHT = 8
COLS = display.width // CHAR_WIDTH
ROWS = display.height // CHAR_HEIGHT

# 添加随机数生成函数
def random_int(min_val, max_val):
    """生成min_val到max_val之间的随机整数（包含两端）"""
    span = max_val - min_val + 1
    div = 0x3fffffff // span
    val = urandom.getrandbits(30) // div
    return min_val + val

def random_float():
    """生成0到1之间的随机浮点数"""
    return urandom.getrandbits(24) / 16777216  # 2^24

def random_choice(seq):
    """从序列中随机选择一个元素"""
    return seq[random_int(0, len(seq) - 1)]

# 创建雨滴数组
class Drop:
    def __init__(self, x, y, speed, length):
        self.x = x
        self.y = y
        self.speed = speed
        self.length = length
        self.chars = [random_choice(CHARS) for _ in range(length)]
        self.update_counter = 0
        
    def update(self):
        self.update_counter += 1
        if self.update_counter >= self.speed:
            self.update_counter = 0
            self.y += 1
            if random_float() < 0.3:  # 30%概率更新字符
                self.chars.pop()
                self.chars.insert(0, random_choice(CHARS))
            return True
        return False
    
    def draw(self):
        for i in range(self.length):
            y_pos = self.y - i
            if 0 <= y_pos < ROWS:
                # 根据位置设置不同亮度
                if i == 0:
                    color = GREEN_BRIGHT  # 头部最亮
                elif i < 3:
                    color = GREEN_MEDIUM
                elif i < 5:
                    color = GREEN_DIM
                else:
                    color = GREEN_DARK
                
                display.text(
                    self.x * CHAR_WIDTH,
                    y_pos * CHAR_HEIGHT,
                    self.chars[i],
                    color=color,
                    bg=st.BLACK
                )

def create_drops(count):
    drops = []
    for _ in range(count):
        x = random_int(0, COLS - 1)
        y = random_int(-20, 0)  # 从屏幕上方开始
        speed = random_int(1, 3)  # 下落速度
        length = random_int(5, 15)  # 雨滴长度
        drops.append(Drop(x, y, speed, length))
    return drops

def matrix_effect():
    display.fill(st.BLACK)
    
    # 创建初始雨滴
    drops = create_drops(30)  # 初始雨滴数量
    
    try:
        while True:
            # 清屏
            # display.fill(st.BLACK)
            
            # 更新并绘制所有雨滴
            for drop in drops[:]:  # 使用副本进行迭代，避免修改迭代中的列表
                drop.draw()
                if drop.update():
                    # 如果雨滴完全离开屏幕，创建新雨滴
                    if drop.y - drop.length > ROWS:
                        drops.remove(drop)
                        # 随机位置创建新雨滴
                        x = random_int(0, COLS - 1)
                        drops.append(Drop(x, -drop.length, 
                                         random_int(1, 3),
                                         random_int(5, 15)))
            
            # 随机添加新雨滴
            if random_float() < 0.1 and len(drops) < 50:  # 限制最大雨滴数量
                x = random_int(0, COLS - 1)
                drops.append(Drop(x, -random_int(1, 5), 
                                 random_int(1, 3),
                                 random_int(5, 15)))
            
            # 内存管理
            gc.collect()
            
            # 控制帧率
            # time.sleep_ms(5)
            
    except KeyboardInterrupt:
        display.fill(st.BLACK)
        print("程序已停止")

if __name__ == "__main__":
    matrix_effect()
