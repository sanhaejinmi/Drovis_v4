# gui/history_window.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor

from core.services.history_json import load_all, delete_all
from gui.explanation_window import ExplanationWindow  # 새 창

from PyQt5.QtWidgets import QDialog, QScrollArea, QGridLayout, QSizePolicy
from PyQt5.QtGui import QPixmap
import os


class HistoryWindow(QWidget):
    def __init__(self, username=None, history_file="data/history.json"):
        super().__init__()
        self.setWindowTitle("분석 기록")
        self.setGeometry(300, 200, 1100, 640)
        self.resize(1175, 700)
        self.setMinimumSize(1000, 500)
        self.history_file = history_file
        self.username = username
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel("최근 분석 기록")
        title.setStyleSheet("font-size: 20px; font-weight: 600; margin-bottom: 12px;")
        layout.addWidget(title)

        # 컬럼: 파일명 | 포즈성공 | 행동비율 | 위험도 | 시간 | 근거 | 보고서 
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["파일명", "포즈 인식 성공", "탐지 행동 비율", "위험도", "시간", "근거", "보고서"]
        )
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        self.table.setWordWrap(True)
        self.table.setTextElideMode(Qt.ElideNone)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setDefaultSectionSize(72)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # 하단 버튼들
        btns = QHBoxLayout()
        btn_back = QPushButton("뒤로 가기")
        btn_back.clicked.connect(self.go_back_to_upload)
        btns.addWidget(btn_back)

        btn_logout = QPushButton("로그아웃")
        btn_logout.clicked.connect(self.logout_to_main)
        btns.addWidget(btn_logout)

        btn_clear = QPushButton("기록 삭제")
        btn_clear.clicked.connect(self.clear_history)
        btns.addWidget(btn_clear)

        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.close)
        btns.addWidget(btn_close)

        layout.addLayout(btns)
        self.setLayout(layout)

        self.load_history()
        QTimer.singleShot(0, self.table.resizeColumnsToContents)

    def make_ro_item(self, text, align_left=True):
        it = QTableWidgetItem(text)
        it.setFlags(it.flags() ^ Qt.ItemIsEditable)
        it.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter if align_left else Qt.AlignCenter)
        return it

    def format_pose_text(self, pose_stats):
        if not isinstance(pose_stats, dict):
            return "-"
        ok = pose_stats.get("success", 0)
        ng = pose_stats.get("fail", 0)
        return f"성공: {ok}프레임\n실패: {ng}프레임"

    def format_behavior_from_chunks(self, chunks):
        if not isinstance(chunks, list) or not chunks:
            return "-"
        order = ["Normal", "Loitering", "Handover", "Reapproach"]
        label_idx = {"Normal": 0, "Loitering": 1, "Handover": 2, "Reapproach": 3}
        counts = {name: 0 for name in order}
        for n in chunks:
            if n in counts:
                counts[n] += 1
        total = sum(counts.values()) or 1
        lines = []
        for name in order:
            c = counts[name]
            if c <= 0:
                continue
            pct = round(c * 100.0 / total, 2)
            lines.append(f"- {name} (라벨 {label_idx[name]}): {c}회 ({pct:.2f}%)")
        return "\n".join(lines) if lines else "-"

    def make_colored_item(self, level):
        it = QTableWidgetItem(str(level if level is not None else "-"))
        it.setFlags(it.flags() ^ Qt.ItemIsEditable)
        color = None
        if level == "상":
            color = Qt.red
        elif level == "중":
            color = Qt.darkYellow
        elif level == "하":
            color = Qt.darkGreen
        if color:
            it.setForeground(QColor(color))
        it.setTextAlignment(Qt.AlignCenter)
        return it

    def add_explain_button(self, row, record_payload):
        btn = QPushButton("설명 보기")
        btn.setCursor(Qt.PointingHandCursor)
        # record_payload에는 decision_id, filename, timestamp, model_version 등 담기
        btn.clicked.connect(lambda: self.open_explanation(record_payload))
        self.table.setCellWidget(row, 6, btn)

    def load_history(self):
        history = load_all(self.username)  # [{...}, ...]
        self.table.setRowCount(len(history))

        for row, item in enumerate(history):
            filename = item.get("filename", "-")
            risk = item.get("risk_level", item.get("result", "-"))
            pose_txt = self.format_pose_text(item.get("pose_stats"))
            beh_txt = self.format_behavior_from_chunks(item.get("result_per_chunk"))
            ts = item.get("timestamp", "-")

            # decision_id/evidence가 있으면 가져와서 버튼 payload로 전달
            payload = {
                "decision_id": item.get("decision_id", None),
                "filename": filename,
                "timestamp": ts,
                "model_version": item.get("model_version", "-"),
                "evidence": item.get("evidence", None),  # 없으면 창에서 lazy fetch
                "prediction": item.get("prediction", None),
                "thresholds": item.get("thresholds", None),
            }

            self.table.setItem(row, 0, self.make_ro_item(filename))
            self.table.setItem(row, 1, self.make_ro_item(pose_txt))
            self.table.setItem(row, 2, self.make_ro_item(beh_txt))
            self.table.setItem(row, 3, self.make_colored_item(risk))
            self.table.setItem(row, 4, self.make_ro_item(ts, align_left=False))
            self.add_explain_button(row, payload)
            self.add_evidence_button(row, payload)
            self.table.resizeRowToContents(row)

    def add_evidence_button(self, row, record_payload):
        btn = QPushButton("근거 장면 보기")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.open_evidence_dialog(record_payload))
        self.table.setCellWidget(row, 5, btn)

    def open_evidence_dialog(self, payload):
        ev_list = payload.get("evidence") or []
        if not ev_list:
            QMessageBox.information(self, "근거 없음", "이 기록에는 근거가 없습니다.")
            return
    
        dlg = QDialog(self)
        dlg.setWindowTitle(f"근거 이미지 - {payload.get('filename', '')}")
        dlg.resize(1000, 800)

        scroll = QScrollArea(dlg)
        scroll.setWidgetResizable(True)

        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(24, 24, 24, 24)
        vbox.setSpacing(28)
        
# ... (dlg/scroll/container/vbox 세팅은 동일)

        img_labels, orig_pixmaps = [], []

        for ev in ev_list:
            path = ev.get("image_path")
            if not path or not os.path.exists(path):
                continue

            # 카드 컨테이너 (이미지 + 캡션)
            card = QWidget()
            card_v = QVBoxLayout(card)
            card_v.setContentsMargins(0, 0, 18, 32)  # 아래 여백 조금
            card_v.setSpacing(10)

            # 1) 이미지
            img = QLabel()
            img.setAlignment(Qt.AlignCenter)
            img.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

            pm = QPixmap(path)
            if not pm.isNull():
                w = max(600, int(scroll.viewport().width() * 0.95))
                img.setPixmap(pm.scaledToWidth(w, Qt.SmoothTransformation))

                # (옵션) 클릭 시 원본 보기
                def open_full(p=path, t=ev.get("label","-")):
                    full = QDialog(self)
                    full.setWindowTitle(t)
                    full.resize(1200, 900)
                    s = QScrollArea(full); s.setWidgetResizable(True)
                    lab = QLabel(); lab.setPixmap(QPixmap(p))
                    s.setWidget(lab)
                    lay = QVBoxLayout(full); lay.addWidget(s)
                    full.exec_()
                img.mousePressEvent = lambda _e, f=open_full: f()

            card_v.addWidget(img, 0, Qt.AlignHCenter)
            img_labels.append(img); orig_pixmaps.append(pm)

            # 2) 캡션 (가운데 정렬)
            caption_txt = f"{ev.get('label','-')} @ {ev.get('timestamp_sec','-')}s"
            caption = QLabel(caption_txt)
            caption.setAlignment(Qt.AlignHCenter)              # <- 핵심
            caption.setStyleSheet("font-size:28px; font-weight:600; color:#333;")
            caption.setWordWrap(True)
            card_v.addWidget(caption, 0, Qt.AlignHCenter)

            # 카드 추가
            vbox.addWidget(card, 0, Qt.AlignHCenter)

        scroll.setWidget(container)
        lay = QVBoxLayout(dlg)
        lay.addWidget(scroll)

        # ... (scroll.setWidget(container), 레이아웃/리사이즈 핸들러 동일)
        def _rescale():
            w = max(600, int(scroll.viewport().width() * 0.95))
            for lbl, pm in zip(img_labels, orig_pixmaps):
                if not pm.isNull():
                    lbl.setPixmap(pm.scaledToWidth(w, Qt.SmoothTransformation))

        old_resize = dlg.resizeEvent
        def new_resizeEvent(e):
            _rescale()
            if old_resize:
                old_resize(e)
        dlg.resizeEvent = new_resizeEvent

        QTimer.singleShot(0, _rescale)
        dlg.exec_()


    def clear_history(self):
        reply = QMessageBox.question(
            self, "기록 삭제", "모든 분석 기록을 삭제할까요?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            deleted = delete_all(self.username)
            self.table.setRowCount(0)
            QMessageBox.information(self, "삭제됨", f"{deleted}개 기록이 삭제되었습니다.")

    def open_explanation(self, payload):
        self.explain_window = ExplanationWindow(username=self.username, record_payload=payload)
        self.explain_window.show()

    def go_back_to_upload(self):
        from gui.upload_window import UploadWindow
        self.upload_window = UploadWindow(username=self.username)
        self.upload_window.show()
        self.close()

    def logout_to_main(self):
        from gui.main_window import MainWindow
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()
