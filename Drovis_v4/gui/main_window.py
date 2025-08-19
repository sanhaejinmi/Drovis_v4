import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
)
from PyQt5.QtCore import Qt  # 중앙정렬

# 현재 파일 상위 폴더를 sys.path에 추가 (내부 모듈 import 가능)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

# 다른 창 불러오기 (로그인, 회원가입)
from gui.login_window import LoginWindow
from gui.register_window import RegisterWindow


# 스타일시트(QSS) 로드 함수
def load_stylesheet():
    qss_path = os.path.join(os.path.dirname(__file__), "styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


class MainWindow(QMainWindow):
    # 앱 실행 시 가장 먼저 보이는 메인 메뉴 창
    def __init__(self):
        super().__init__()

        # 창 제목 및 크기 설정
        self.setWindowTitle("Drovis")
        self.setFixedSize(1200, 1000)

        # 중앙 위젯과 세로 레이아웃 생성
        central_widget = QWidget()
        layout = QVBoxLayout()

        # 환영 문구 라벨
        welcome_label = QLabel("마약 드라퍼 탐지를 도와주는 Drovis입니다.")
        welcome_label.setObjectName("welcomeLabel")  # QSS에서 지정할 이름

        # (1) 텍스트 중앙 정렬
        welcome_label.setAlignment(Qt.AlignCenter)

        # (2) 레이아웃 내에서 위젯 위치도 중앙 정렬
        layout.addWidget(welcome_label)
        layout.setAlignment(welcome_label, Qt.AlignCenter)

        # 버튼들
        login_btn = QPushButton("로그인")
        login_btn.clicked.connect(self.open_login_window)
        layout.addWidget(login_btn)

        register_btn = QPushButton("회원가입")
        register_btn.clicked.connect(self.open_register_window)
        layout.addWidget(register_btn)

        # 중앙 위젯에 레이아웃 장착 후 메인 창에 설정
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # 다른 창 참조 변수 초기화
        self.login_window = None
        self.register_window = None

    # 로그인 창 열기
    def open_login_window(self):
        self.login_window = LoginWindow(parent=self)
        self.login_window.show()
        self.hide()

    # 회원가입 창 열기
    def open_register_window(self):
        self.register_window = RegisterWindow(parent=self)
        self.register_window.show()
        self.hide()


# 프로그램 실행 진입점
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 앱 전체에 스타일시트 적용
    app.setStyleSheet(load_stylesheet())

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
