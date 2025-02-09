import pyperclip
import base64

def get_clipboard_data():
    data = pyperclip.paste()
    return data

def set_clipboard_data(data):
    pyperclip.copy(data)

def on_clipboard_change(data):
    # Обработчик изменения буфера обмена
    set_clipboard_data(data['content'])

def send_clipboard_data():
    data = get_clipboard_data()
    message = {
        "type": "clipboard",
        "content": data
    }
    # Отправка данных по сети
    return message

# Для передачи файлов
def serialize_file(file_path):
    with open(file_path, 'rb') as file:
        encoded = base64.b64encode(file.read())
    return encoded.decode('utf-8')

def deserialize_file(encoded_data, output_path):
    with open(output_path, 'wb') as file:
        file.write(base64.b64decode(encoded_data))
