from PyQt5 import QtWidgets


class ModeSelectionWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выбор режима")
        self.setGeometry(100, 100, 300, 150)

        layout = QtWidgets.QVBoxLayout()

        self.label = QtWidgets.QLabel("Выберите режим работы:")
        layout.addWidget(self.label)

        self.server_button = QtWidgets.QPushButton("Сервер")
        layout.addWidget(self.server_button)

        self.client_button = QtWidgets.QPushButton("Клиент")
        layout.addWidget(self.client_button)

        self.setLayout(layout)


class ServerWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сервер")
        self.setGeometry(100, 100, 300, 100)

        layout = QtWidgets.QVBoxLayout()

        self.info_label = QtWidgets.QLabel("Ожидание подключения клиента...")
        layout.addWidget(self.info_label)

        self.setLayout(layout)


class ClientWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Клиент")
        self.setGeometry(100, 100, 300, 200)

        layout = QtWidgets.QVBoxLayout()
