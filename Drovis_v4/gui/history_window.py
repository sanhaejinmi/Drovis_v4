# gui/history_window.py
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from PyQt5.QtCore import Qt

from core.services.history_json import load_all, delete_all


class HistoryWindow(QWidget):
    # 분석 기록 창 초기화
    def __init__(self, username=None, history_file="data/history.json"):
        super().__init__()
        self.setWindowTitle("분석 기록")
        self.setGeometry(300, 200, 1000, 600)
        self.history_file = history_file
        self.username = username
        self.init_ui()

    # UI 구성
    def init_ui(self):
        layout = QVBoxLayout()

        # 제목 라벨
        title = QLabel("최근 분석 기록")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(title)

        # 기록 테이블 설정
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["파일명", "포즈 인식 성공", "탐지 행동 비율", "위험도", "시간"]
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # 파일명
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 포즈 인식 성공
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 행동 비율(멀티라인)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 위험도
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 시간

        self.table.setWordWrap(True)  # 텍스트 줄바꿈
        self.table.setTextElideMode(Qt.ElideNone)  # 말줄임 해제
        self.table.setSortingEnabled(True)  # 정렬 가능
        self.table.verticalHeader().setDefaultSectionSize(72)  # 기본 행 높이 설정
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # 버튼들
        btn_back = QPushButton("뒤로 가기")
        btn_back.clicked.connect(self.go_back_to_upload)
        layout.addWidget(btn_back)

        btn_logout = QPushButton("로그아웃")
        btn_logout.clicked.connect(self.logout_to_main)
        layout.addWidget(btn_logout)

        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.close)
        layout.addWidget(btn_close)

        btn_clear = QPushButton("기록 삭제")
        btn_clear.clicked.connect(self.clear_history)
        layout.addWidget(btn_clear)

        self.setLayout(layout)
        self.load_history()  # 실행 시 기록 로드

    # 읽기 전용 셀 생성
    def make_ro_item(self, text, align_left=True):
        it = QTableWidgetItem(text)
        it.setFlags(it.flags() ^ Qt.ItemIsEditable)
        it.setTextAlignment(
            Qt.AlignLeft | Qt.AlignVCenter if align_left else Qt.AlignCenter
        )
        return it

    # 포즈 인식 성공/실패 텍스트 포맷
    def format_pose_text(self, pose_stats):
        if not isinstance(pose_stats, dict):
            return "-"
        ok = pose_stats.get("success", 0)
        ng = pose_stats.get("fail", 0)
        return f"성공: {ok}프레임\n실패: {ng}프레임"

    # 탐지 행동 비율 텍스트 포맷 (터미널과 동일하게 출력)
    def format_behavior_from_chunks(self, chunks):
        if not isinstance(chunks, list) or not chunks:
            return "-"

        # 터미널 포맷과 동일한 라벨/순서/이름
        order = ["Normal", "Loitering", "Handover", "Reapproach"]
        label_idx = {"Normal": 0, "Loitering": 1, "Handover": 2, "Reapproach": 3}

        # 카운트 집계
        counts = {name: 0 for name in order}
        for n in chunks:
            if n in counts:
                counts[n] += 1
        total = sum(counts.values()) or 1

        # 터미널은 Counter에 존재하는 라벨만 출력 -> 0회는 출력 안 함
        lines = []
        for name in order:
            c = counts[name]
            if c <= 0:
                continue
            pct = round(c * 100.0 / total, 2)
            lines.append(f"- {name} (라벨 {label_idx[name]}): {c}회 ({pct:.2f}%)")
        return "\n".join(lines) if lines else "-"

    # 위험도 셀 생성
    def make_colored_item(self, level):
        it = QTableWidgetItem(str(level if level is not None else "-"))
        it.setFlags(it.flags() ^ Qt.ItemIsEditable)
        if level == "상":
            it.setForeground(Qt.red)
        elif level == "중":
            it.setForeground(Qt.darkYellow)
        elif level == "하":
            it.setForeground(Qt.darkGreen)
        it.setTextAlignment(Qt.AlignCenter)
        return it

    # 기록 데이터 로드
    def load_history(self):
        history = load_all(self.username)

        self.table.setRowCount(len(history))
        for row, item in enumerate(history):
            filename = item.get("filename", "-")
            risk = item.get("risk_level", item.get("result", "-"))
            pose_txt = self.format_pose_text(item.get("pose_stats"))

            # 터미널과 동일: result_per_chunk로 계산/표시
            chunks = item.get("result_per_chunk")
            beh_txt = self.format_behavior_from_chunks(chunks)

            ts = item.get("timestamp", "-")

            self.table.setItem(row, 0, self.make_ro_item(filename))
            self.table.setItem(row, 1, self.make_ro_item(pose_txt))
            self.table.setItem(row, 2, self.make_ro_item(beh_txt))
            self.table.setItem(row, 3, self.make_colored_item(risk))
            self.table.setItem(row, 4, self.make_ro_item(ts, align_left=False))
            self.table.resizeRowToContents(row)

    # 기록 삭제 기능
    def clear_history(self):
        reply = QMessageBox.question(
            self,
            "기록 삭제",
            "모든 분석 기록을 삭제할까요?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            deleted = delete_all(self.username)  # 추가했고 아래 주석 삭제해야 함
            # if os.path.exists(self.history_file):
            #    os.remove(self.history_file)
            self.table.setRowCount(0)
            QMessageBox.information(
                self, "삭제됨", f"{deleted}개 기록이 삭제되었습니다."
            )

    # 업로드 창으로 돌아가기
    def go_back_to_upload(self):
        from gui.upload_window import UploadWindow  # 순환 import 방지

        self.upload_window = UploadWindow(username=self.username)
        self.upload_window.show()
        self.close()

    # 메인 메뉴로 로그아웃
    def logout_to_main(self):
        from gui.main_window import MainWindow  # 순환 import 방지

        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
