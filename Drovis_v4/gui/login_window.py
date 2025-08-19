import os
import sys

# PyQt5 플랫폼 플러그인 경로 설정 (자동 방식 권장)
from PyQt5 import QtCore  # QtCore 위치 기준으로 plugins 경로 자동 지정

plugin_path = os.path.join(os.path.dirname(QtCore.__file__), "plugins", "platforms")
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_path

# import 경로 처리 (상위 폴더를 sys.path에 추가)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

# 외부 모듈 import
from gui.upload_window import UploadWindow
from core.services.auth import verify_user

# PyQt5 위젯 모듈들
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QApplication,
)


# 로그인 창 클래스
class LoginWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("로그인")
        self.setFixedSize(600, 300)
        self.parent_window = parent

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("아이디")
        self.username_input.returnPressed.connect(self.try_login)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("비밀번호")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.try_login)
        layout.addWidget(self.password_input)

        self.login_button = QPushButton("로그인")
        self.login_button.clicked.connect(self.try_login)
        layout.addWidget(self.login_button)

        self.back_button = QPushButton("뒤로가기")
        self.back_button.clicked.connect(self.go_back)
        layout.addWidget(self.back_button)

        self.central_widget.setLayout(layout)

        self.upload = None  # 업로드 창 핸들

    def try_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        is_valid = verify_user(username, password)

        if is_valid:
            self.upload = UploadWindow(username)
            self.upload.show()
            self.close()
        else:
            QMessageBox.warning(
                self, "로그인 실패", "아이디 또는 비밀번호가 틀렸습니다."
            )
    
    def go_back(self):
        self.close()
        if self.parent_window:
            self.parent_window.show()


# 실행 진입점
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginWindow()
    login.show()
    sys.exit(app.exec_())
