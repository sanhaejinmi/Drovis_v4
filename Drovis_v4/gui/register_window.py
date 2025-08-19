import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QHBoxLayout,
)
from core.services.auth import register_user


class RegisterWindow(QWidget):
    # 회원가입 창 초기화
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("회원가입")
        self.setFixedSize(1200, 1000)
        self.parent_window = parent

        # 메인 레이아웃
        layout = QVBoxLayout()

        # 아이디 입력 필드
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("아이디 입력 (예: user123)")
        layout.addWidget(QLabel("아이디"))
        layout.addWidget(self.id_input)

        # 이메일 입력 필드
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("이메일 입력 (예: user@example.com)")
        layout.addWidget(QLabel("이메일"))
        layout.addWidget(self.email_input)

        # 비밀번호 입력 필드
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText("비밀번호 입력 (8자 이상)")
        self.pw_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("비밀번호"))
        layout.addWidget(self.pw_input)

        # 비밀번호 확인 필드
        self.pw2_input = QLineEdit()
        self.pw2_input.setPlaceholderText("비밀번호 다시 입력")
        self.pw2_input.setEchoMode(QLineEdit.Password)
        self.pw2_input.returnPressed.connect(self.handle_register)
        layout.addWidget(QLabel("비밀번호 확인"))
        layout.addWidget(self.pw2_input)

        # 가입 버튼
        self.register_btn = QPushButton("가입하기")
        self.register_btn.clicked.connect(self.handle_register)
        layout.addWidget(self.register_btn)

        # 뒤(main창)로 가기
        self.back_btn = QPushButton("뒤로가기")
        self.back_btn.clicked.connect(self.go_back)
        layout.addWidget(self.back_btn)

        self.setLayout(layout)

    # 회원가입 처리 로직
    def handle_register(self):
        username = self.id_input.text().strip()
        email = self.email_input.text().strip()
        pw1 = self.pw_input.text()
        pw2 = self.pw2_input.text()

        # 필수 입력값 검증
        if not username or not email or not pw1 or not pw2:
            QMessageBox.warning(self, "입력 오류", "모든 항목을 입력해주세요.")
            return

        # 비밀번호 일치 여부 확인
        if pw1 != pw2:
            QMessageBox.warning(self, "비밀번호 오류", "비밀번호가 일치하지 않습니다.")
            return

        # 회원가입 시도 (register_user 내부에서 bcrypt 해시 처리 및 중복 검사)
        success, message = register_user(username, pw1, email)
        if success:
            QMessageBox.information(
                self, "가입 완료", f"{username}님, 가입을 환영합니다!"
            )
            self.close()
            if self.parent_window:
                self.parent_window.show()
        else:
            QMessageBox.warning(self, "가입 실패", message)

    # 뒤로가기
    def go_back(self):
        self.close()
        if self.parent_window:
            self.parent_window.show()


# 독립 실행 시 테스트
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RegisterWindow()
    window.show()
    sys.exit(app.exec_())
