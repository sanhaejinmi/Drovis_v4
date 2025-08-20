import os
import sys
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QProgressBar,
    QDialog,
    QHeaderView,
)
from PyQt5.QtCore import Qt, QTimer
from gui.history_window import HistoryWindow
from core.services.predict import predict_from_video
from core.services.history_json import append_record  # 0815 추가


# Qt 플러그인 경로 및 모듈 경로 설정
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = r"C:\경로\plugins\platforms"
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)


class UploadWindow(QWidget):
    # 업로드 창 초기화
    def __init__(self, username="guest"):
        super().__init__()
        self.setWindowTitle("Drovis - 영상 분석")
        self.resize(1000, 600)
        self.file_path = None
        self.history_window = None
        self.username = username
        self.loading_dialog = None  # 분석중 다이얼로그 핸들
        self.progress_timer = None  # 게이지 애니메이션용 타이머
        self.progress_value = 0  # 게이지 현재 값
        self.setup_ui()

    # 로딩 다이얼로그 표시
    def show_loading_dialog(self, message="분석 중입니다...", estimated_ms=4000):
        # QDialog로 로딩창 생성
        self.loading_dialog = QDialog(self)
        self.loading_dialog.setWindowTitle("예측 진행 중")
        self.loading_dialog.setModal(True)
        self.loading_dialog.setFixedSize(300, 100)

        # 레이아웃 및 위젯 설정
        layout = QVBoxLayout()
        self.loading_label = QLabel(message)
        self.loading_label.setAlignment(Qt.AlignCenter)

        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 100)  # 0~100% 진행
        self.loading_bar.setValue(0)  # 초기값 0%

        layout.addWidget(self.loading_label)
        layout.addWidget(self.loading_bar)
        self.loading_dialog.setLayout(layout)
        self.loading_dialog.show()

        # 진행률 타이머 시작
        self.progress_value = 0
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(lambda: self.update_progress(estimated_ms))
        self.progress_timer.start(estimated_ms // 100)

    # 로딩 다이얼로그 진행률 업데이트
    def update_progress(self, estimated_ms):
        if self.progress_value < 100:
            self.progress_value += 1
            self.loading_bar.setValue(self.progress_value)
        else:
            self.progress_timer.stop()

    # UI 구성
    def setup_ui(self):
        layout = QVBoxLayout()

        # 업로드 버튼 + 파일명 표시
        upload_layout = QHBoxLayout()
        self.upload_btn = QPushButton("영상 업로드")
        self.upload_btn.clicked.connect(self.upload_file)
        self.file_label = QLabel("업로드된 파일 없음")
        upload_layout.addWidget(self.upload_btn)
        upload_layout.addWidget(self.file_label)
        layout.addLayout(upload_layout)

        # 분석 시작 버튼
        self.analyze_btn = QPushButton("분석 시작")
        self.analyze_btn.clicked.connect(self.start_analysis)
        layout.addWidget(self.analyze_btn)

        # 분석 기록 보기 버튼
        self.history_btn = QPushButton("분석 기록 보기")
        self.history_btn.clicked.connect(self.open_history_window)
        layout.addWidget(self.history_btn)

        # 결과 테이블
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(
            ["파일명", "상태", "위험도", "시간"]
        )
        header = self.result_table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.Stretch)  # 칼럼 균등 분배

        self.result_table.setWordWrap(True)
        self.result_table.setTextElideMode(Qt.ElideNone)
        self.result_table.verticalHeader().setDefaultSectionSize(36)
        self.result_table.setSortingEnabled(True)

        layout.addWidget(self.result_table)
        self.setLayout(layout)

    # 분석 시작
    def start_analysis(self):
        if not self.file_path:
            QMessageBox.warning(self, "경고", "먼저 영상을 업로드하세요.")
            return

        # 분석 중 로딩창 표시
        self.show_loading_dialog("AI 분석 중입니다...", estimated_ms=4000)

        # 게이지바 완료 후 예측 실행
        def run_prediction_after_progress():
            result_data = predict_from_video(self.file_path, self.username)

            if not result_data.get("success"):
                if self.progress_timer:
                    self.progress_timer.stop()
                if self.loading_dialog:
                    self.loading_dialog.close()
                QMessageBox.critical(
                    self, "오류", result_data.get("message", "분석 실패")
                )
                return

            result = result_data["result"]
            filename = result_data["filename"]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

            # 결과 표시
            self.loading_label.setText(f"분석 결과: {result}")
            QApplication.processEvents()
            QTimer.singleShot(1200, self.loading_dialog.close)  # 결과 보여준 뒤 닫기

            # 결과 테이블에 결과 추가
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(filename))
            self.result_table.setItem(row, 1, QTableWidgetItem("완료"))
            self.result_table.setItem(row, 2, QTableWidgetItem(result))
            self.result_table.setItem(row, 3, QTableWidgetItem(timestamp))

            # 기록 저장
            append_record(
                {
                    "username": self.username,
                    "filename": result_data["filename"],
                    "result": result_data["result"],  # 위험도
                    "risk_level": result_data["result"],  # (옵션)
                    "pose_stats": result_data.get("pose_stats"),
                    "behavior_counts": result_data.get("behavior_counts"),
                    "result_per_chunk": result_data.get("result_per_chunk"),
                    "confidence": None,
                    "timestamp": timestamp,
                    "description": "AI 자동 분석 결과",
                    "evidence": result_data.get("evidence", []),
                }
            )

        QTimer.singleShot(4000, run_prediction_after_progress)

    # 파일 업로드
    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "영상 선택", "", "Video Files (*.mp4)"
        )
        if not file_path:
            return

        # 다른 확장자가 들어오는 경우
        if not file_path.lower().endswith(".mp4"):
            QMessageBox.warning(self, "형식 오류", "mp4 파일만 업로드할 수 있습니다.")
            return

        self.file_path = file_path
        self.file_label.setText(os.path.basename(file_path))

    # 분석 기록 창 열기
    def open_history_window(self):
        self.history_window = HistoryWindow(username=self.username)
        self.history_window.show()
        self.hide()


# 독립 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # QSS 적용
    qss_path = os.path.join(os.path.dirname(__file__), "styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = UploadWindow()
    window.show()
    sys.exit(app.exec_())
