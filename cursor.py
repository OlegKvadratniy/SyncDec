import pyautogui

# Получаем размеры экрана
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()

def get_cursor_position():
    x, y = pyautogui.position()
    return x, y

def move_cursor(x, y):
    pyautogui.moveTo(x, y)

def on_cursor_move(data):
    # Обработчик движения курсора
    x = data['x']
    y = data['y']
    move_cursor(x, y)
