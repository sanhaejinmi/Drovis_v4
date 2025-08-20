# gui/explanation_window.py
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer

from core.services.explanations_cache import get_cached, set_cached
from core.services.llm_explainer import build_prompt_from_evidence, call_llm, validate_llm_output, render_fallback_text
from core.services.history_json import load_evidence_by_decision  # 필요 시 구현

class ExplanationWindow(QWidget):
    def __init__(self, username=None, record_payload=None):
        super().__init__()
        self.username = username
        self.payload = record_payload or {}
        self.setWindowTitle(f"판단 설명 · {self.payload.get('filename','-')} · {self.payload.get('timestamp','-')}")
        self.setGeometry(360, 220, 900, 640)

        self.decision_id = self.payload.get("decision_id")
        self.model_version = self.payload.get("model_version", "-")

        # 데이터 홀더
        self.prediction = self.payload.get("prediction")
        self.thresholds = self.payload.get("thresholds")
        self.evidence = self.payload.get("evidence")

        self.init_ui()
        self.load_all_data()

    def init_ui(self):
        root = QVBoxLayout()

        # 헤더: 라벨/신뢰도/불확실성/모델 버전/디시전
        self.header_label = QLabel("결과 요약")
        self.header_label.setStyleSheet("font-size: 16px; font-weight: 600; margin-bottom: 6px;")
        root.addWidget(self.header_label)

        # 탭
        self.tabs = QTabWidget()
        # 탭1: 요약
        self.summary_widget = QWidget()
        self.summary_layout = QVBoxLayout()
        self.lbl_one_liner = QLabel("(한 줄 요약)")
        self.lbl_one_liner.setStyleSheet("font-size: 15px; font-weight: 600;")
        self.txt_reason = QTextEdit()
        self.txt_reason.setReadOnly(True)
        self.txt_reason.setStyleSheet("font-size: 13px;")
        self.lbl_caution = QLabel("(주의/불확실성)")
        self.btn_regenerate = QPushButton("문장 재생성")
        self.btn_regenerate.clicked.connect(self.on_regenerate)

        self.summary_layout.addWidget(self.lbl_one_liner)
        self.summary_layout.addWidget(self.txt_reason)
        self.summary_layout.addWidget(self.lbl_caution)
        self.summary_layout.addWidget(self.btn_regenerate, alignment=Qt.AlignRight)
        self.summary_widget.setLayout(self.summary_layout)
        self.tabs.addTab(self.summary_widget, "요약")

        # 탭2: 수치 근거
        self.metrics_widget = QWidget()
        self.metrics_layout = QVBoxLayout()

        self.tbl_overlap = QTableWidget(0, 2)
        self.tbl_overlap.setHorizontalHeaderLabels(["행동", "비율"])
        self.tbl_overlap.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_overlap.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.tbl_rules = QTableWidget(0, 4)
        self.tbl_rules.setHorizontalHeaderLabels(["규칙", "통과", "값", "여유도/임계"])
        self.tbl_rules.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_rules.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tbl_rules.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tbl_rules.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        self.tbl_metrics = QTableWidget(0, 2)
        self.tbl_metrics.setHorizontalHeaderLabels(["지표", "값"])
        self.tbl_metrics.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tbl_metrics.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        self.metrics_layout.addWidget(QLabel("중첩 비율(overlap_summary)"))
        self.metrics_layout.addWidget(self.tbl_overlap)
        self.metrics_layout.addWidget(QLabel("규칙 통과 여부(rule_hits)"))
        self.metrics_layout.addWidget(self.tbl_rules)
        self.metrics_layout.addWidget(QLabel("세부 지표(metrics / 품질)"))
        self.metrics_layout.addWidget(self.tbl_metrics)
        self.metrics_widget.setLayout(self.metrics_layout)
        self.tabs.addTab(self.metrics_widget, "수치 근거")

        # 탭3: 타임라인
        self.timeline_widget = QWidget()
        self.timeline_layout = QVBoxLayout()
        self.timeline_list = QTableWidget(0, 3)
        self.timeline_list.setHorizontalHeaderLabels(["시작", "끝", "요약"])
        self.timeline_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.timeline_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.timeline_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self.timeline_bar = QProgressBar()
        self.timeline_bar.setRange(0, 100)
        self.timeline_bar.setValue(0)
        self.timeline_bar.setFormat("결정적 구간 강조 바 (예시)")

        self.timeline_layout.addWidget(self.timeline_list)
        self.timeline_layout.addWidget(self.timeline_bar)
        self.timeline_widget.setLayout(self.timeline_layout)
        self.tabs.addTab(self.timeline_widget, "타임라인")

        # 탭4: 원본 JSON
        self.json_widget = QWidget()
        self.json_layout = QVBoxLayout()
        self.json_view = QTextEdit()
        self.json_view.setReadOnly(True)
        self.btn_copy_json = QPushButton("클립보드 복사")
        self.btn_copy_json.clicked.connect(self.copy_json)
        self.json_layout.addWidget(self.json_view)
        self.json_layout.addWidget(self.btn_copy_json, alignment=Qt.AlignRight)
        self.json_widget.setLayout(self.json_layout)
        self.tabs.addTab(self.json_widget, "원본 JSON")

        root.addWidget(self.tabs)

        # 하단 액션바
        actions = QHBoxLayout()
        self.btn_back = QPushButton("뒤로")
        self.btn_back.clicked.connect(self.close)
        self.btn_refresh = QPushButton("리프레시")
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_save = QPushButton("설명 저장")
        self.btn_save.clicked.connect(self.save_explanation)
        actions.addWidget(self.btn_back)
        actions.addStretch(1)
        actions.addWidget(self.btn_refresh)
        actions.addWidget(self.btn_save)
        root.addLayout(actions)

        self.setLayout(root)

    def load_all_data(self):
        # evidence 없으면 decision_id로 lazy fetch
        if self.evidence is None and self.decision_id:
            self.evidence = load_evidence_by_decision(self.decision_id) or {}
        # 헤더 요약
        head = self._build_header_text()
        self.header_label.setText(head)
        # 수치/타임라인/JSON 채우기
        self.populate_numeric_tabs()
        self.populate_json_tab()
        # 요약 탭(LLM 또는 템플릿)
        self.populate_summary_tab()

    def _build_header_text(self):
        label = "-"
        conf = "-"
        uncert = "-"
        if isinstance(self.prediction, dict):
            label = self.prediction.get("label", "-")
            conf = self.prediction.get("confidence", "-")
            uncert = self.prediction.get("uncertainty", "-")
        did = self.decision_id or "-"
        mv = self.model_version
        return f"결과: {label} · 신뢰도 {conf} · 불확실성 {uncert} | model {mv} · decision {did}"

    def populate_numeric_tabs(self):
        ev = self.evidence or {}
        # overlap
        self.tbl_overlap.setRowCount(0)
        overlap = ev.get("overlap_summary", {})
        for k, v in overlap.items():
            r = self.tbl_overlap.rowCount()
            self.tbl_overlap.insertRow(r)
            self.tbl_overlap.setItem(r, 0, QTableWidgetItem(str(k)))
            self.tbl_overlap.setItem(r, 1, QTableWidgetItem(f"{v:.2f}"))
        # rules
        self.tbl_rules.setRowCount(0)
        for rh in ev.get("rule_hits", []):
            r = self.tbl_rules.rowCount()
            self.tbl_rules.insertRow(r)
            self.tbl_rules.setItem(r, 0, QTableWidgetItem(str(rh.get("rule","-"))))
            self.tbl_rules.setItem(r, 1, QTableWidgetItem("O" if rh.get("pass") else "X"))
            self.tbl_rules.setItem(r, 2, QTableWidgetItem(str(rh.get("value","-"))))
            margin = rh.get("margin", None)
            thr = rh.get("threshold", None)
            self.tbl_rules.setItem(r, 3, QTableWidgetItem(f"margin={margin} / thr={thr}"))
        # metrics
        self.tbl_metrics.setRowCount(0)
        metrics = ev.get("metrics", {})
        quality = {}
        if "frame_success_rate" in ev:
            quality["frame_success_rate"] = ev.get("frame_success_rate")
        if "quality_weight" in ev:
            quality["quality_weight"] = ev.get("quality_weight")
        def add_kv(table, k, v):
            r = table.rowCount(); table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(str(k)))
            table.setItem(r, 1, QTableWidgetItem(str(v)))
        for k, v in metrics.items():
            add_kv(self.tbl_metrics, k, v)
        for k, v in quality.items():
            add_kv(self.tbl_metrics, k, v)
        # timeline
        self.timeline_list.setRowCount(0)
        wins = ev.get("top_windows", [])
        for w in wins:
            r = self.timeline_list.rowCount()
            self.timeline_list.insertRow(r)
            self.timeline_list.setItem(r, 0, QTableWidgetItem(str(w.get("t_start","-"))))
            self.timeline_list.setItem(r, 1, QTableWidgetItem(str(w.get("t_end","-"))))
            self.timeline_list.setItem(r, 2, QTableWidgetItem(str(w.get("reason",""))))
        # progress bar 예시 (상위 구간이 있을 때 100으로)
        self.timeline_bar.setValue(100 if wins else 0)

    def populate_json_tab(self):
        payload = {
            "prediction": self.prediction,
            "thresholds": self.thresholds,
            "evidence": self.evidence,
        }
        self.json_view.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))

    def populate_summary_tab(self):
        # 캐시 우선
        if self.decision_id:
            cached = get_cached(self.decision_id)
        else:
            cached = None

        if cached:
            self.lbl_one_liner.setText(cached.get("one_liner",""))
            self.txt_reason.setPlainText(cached.get("reason_text",""))
            self.lbl_caution.setText(cached.get("caution_text",""))
            return

        # LLM 호출 시도
        if not self.evidence:
            # 근거가 없으면 템플릿으로만
            fb = render_fallback_text({
                "prediction": self.prediction or {},
                "thresholds": self.thresholds or {},
                "evidence": {}
            })
            self.lbl_one_liner.setText("근거 부족으로 템플릿 설명을 표시합니다.")
            self.txt_reason.setPlainText(fb)
            self.lbl_caution.setText("주의: evidence 미존재")
            return

        self.lbl_one_liner.setText("설명 생성 중…")
        self.txt_reason.setPlainText("")
        self.lbl_caution.setText("")

        # 비동기처럼 보이는 UX를 위해 타이머 사용(실제는 동기 호출일 수도)
        def run_llm():
            try:
                prompt = build_prompt_from_evidence({
                    "prediction": self.prediction,
                    "thresholds": self.thresholds,
                    "evidence": self.evidence
                })
                llm_text = call_llm(prompt)
                ok, checked = validate_llm_output(llm_text, {
                    "prediction": self.prediction,
                    "thresholds": self.thresholds,
                    "evidence": self.evidence
                })
                if ok:
                    self.lbl_one_liner.setText(checked.get("one_liner",""))
                    self.txt_reason.setPlainText(checked.get("reason_text",""))
                    self.lbl_caution.setText(checked.get("caution_text",""))
                    if self.decision_id:
                        set_cached(self.decision_id, checked)
                else:
                    # 후검증 실패 → 템플릿
                    fb = render_fallback_text({
                        "prediction": self.prediction,
                        "thresholds": self.thresholds,
                        "evidence": self.evidence
                    })
                    self.lbl_one_liner.setText("자동 후검증 불일치로 템플릿 설명을 표시합니다.")
                    self.txt_reason.setPlainText(fb)
                    self.lbl_caution.setText("주의: 수치 검증 불일치")
            except Exception as e:
                fb = render_fallback_text({
                    "prediction": self.prediction,
                    "thresholds": self.thresholds,
                    "evidence": self.evidence
                })
                self.lbl_one_liner.setText("LLM 호출 실패로 템플릿 설명을 표시합니다.")
                self.txt_reason.setPlainText(fb)
                self.lbl_caution.setText(f"오류: {e}")

        QTimer.singleShot(10, run_llm)

    def on_regenerate(self):
        # 캐시 무시하고 다시 생성
        if self.decision_id:
            set_cached(self.decision_id, None)
        self.populate_summary_tab()

    def refresh(self):
        self.load_all_data()

    def copy_json(self):
        payload = self.json_view.toPlainText()
        cb = self.clipboard() if hasattr(self, "clipboard") else None
        if cb:
            cb.setText(payload)
        else:
            # Qt 기본 클립보드
            from PyQt5.QtWidgets import QApplication
            QApplication.clipboard().setText(payload)
        QMessageBox.information(self, "복사됨", "원본 JSON을 클립보드에 복사했습니다.")

    def save_explanation(self):
        # 필요 시 파일 저장 다이얼로그로 확장
        QMessageBox.information(self, "저장", "저장 기능은 후속 구현 예정입니다.")
