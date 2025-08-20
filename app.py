# app.py
import sys, os, ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from core.models import create_user_table, create_analysis_table
from gui.main_window import MainWindow, load_stylesheet
from pathlib import Path

def resource_path(*parts):
    # PyInstaller로 빌드해도 동작하도록 안전한 경로 생성
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


BASE_DIR = Path(__file__).resolve().parent        # Drovis_v4
DB_DIR = BASE_DIR / "database"                    # Drovis_v4/database
DB_DIR.mkdir(parents=True, exist_ok=True)


# DB 테이블 생성
create_user_table()
create_analysis_table()

# 앱 실행
if __name__ == "__main__":

    # 윈도우에서 작업표시줄 그룹/아이콘을 이 앱용으로 분리
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Drovis.App")
    except Exception:
        pass

    app = QApplication(sys.argv)

    # 아이콘: 반드시 창 생성 전에 전역으로 설정 + 절대경로
    ICON_PATH = resource_path("assets", "Drovis_logo.ico")
    app.setWindowIcon(QIcon(ICON_PATH))

    # 스타일
    app.setStyleSheet(load_stylesheet())

    # 메인 창 (보수적으로 창에도 한번 더 설정)
    window = MainWindow()
    window.setWindowIcon(QIcon(ICON_PATH))
    window.show()

    sys.exit(app.exec_())
