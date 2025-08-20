Drovis_v4의 레포지토리입니다.

# AI 기반 영상 분석을 활용한 마약 범죄 수사 지원 프로그램: Drovis

[![Python version](https://img.shields.io/badge/python-3.10-blue.svg)]()
[![GitHub issues](https://img.shields.io/github/issues/JJeongsuu/Drovis_v3)](https://github.com/JJeongsuu/Drovis_v3/issues)

## Drovis

Drovis was developed as a project for the 2025 Convergence Security Creative Software Competition.
This project aims to develop security software that identifies the behaviors of drug droppers in crime scenes by automatically analyzing video data.
Since traditional video analysis methods relying on manual review are limited by manpower and time, the system utilizes AI-based analysis technology to enable automated detection.

In South Korea, illegal drug distribution through private messengers such as Telegram has emerged as a serious problem, with drug-related cases accounting for 31.7% of all detected illegal online transactions.
Drug crimes are characterized by anonymity and speed, making them difficult to address using conventional manual surveillance systems.

### Goals

Drovis aims to develop security software that automatically detects drug mules using AI-based multimodal analysis technology.

In particular Drovis aims to:

- automatically analyze video data to reduce manpower and time consumption
- combine Pose Estimation with LSTM to precisely recognize behavioral patterns
- detect suspicious drug dropping behaviors such as loitering and hand-offs
- assess the likelihood of criminal activity (high / medium / low) through AI analysis
- implement a flexible model architecture suitable for research, experimentation, and further expansion
- complement the limitations of traditional manual surveillance systems and contribute to public safety


## Installation & Usage

### Windows 
```sh
$ python3.10 -m venv venv310
$ \venv310\Scripts\activate
$ git clone https://github.com/JJeongsuu/Drovis_v3.git
$ pip install -r requirements.txt
$ python app.py
```

## Project Overview

### Background and Necessity

Drug-related crimes have been rapidly spreading both domestically and internationally, no longer confined to specific social groups but permeating society as a whole. According to prosecution statistics, the number of drug offenders increased from 10,589 in 2000 to 27,611 in 2024, a 2.6-fold rise. This demonstrates not a temporary fluctuation but a sustained upward trend. As cases involving various social groups—such as adolescents, housewives, and office workers—continue to grow, the drug problem is increasingly recognized not merely as an individual act of deviance but as a structural and societal issue.

In particular, a drug distribution method known as “Throwing” has recently gained attention. This method involves a courier, referred to as a “dropper,” secretly concealing drugs at designated locations. After concealment, the recipient is informed of the location and retrieves the drugs, enabling distribution without direct face-to-face interaction. During this process, the dropper performs critical tasks such as loitering, scouting the surroundings, concealing the package, and revisiting the location, which reveal identifiable behavioral patterns.

However, these covert activities are difficult to detect using conventional investigative methods that rely primarily on physical evidence collection or post-event tracking. Detecting droppers at an early stage poses significant challenges. Traditionally, investigators had to monitor CCTV feeds directly and continuously to identify suspicious movements, which not only demands extensive manpower but also imposes limitations on real-time response.

### Development Goals and Key Feautures

This project aims to develop an AI-based automatic detection system specialized in identifying drug distribution activities using the “Throwing” method. Our team has analyzed the unique characteristics of dropper crimes and established three behavioral criteria: loitering, handover, and re-approach. Based on these, we quantified the behavioral patterns of droppers and systematized them into a detectable structure. This approach addresses the limitations of existing investigative practices, reducing the burden on law enforcement personnel, enhancing operational efficiency, and contributing to preventive measures.

Moreover, the software employs MediaPipe-based pose estimation combined with an LSTM time-series model to recognize dropper behaviors. This design provides broad applicability as an AI-powered investigative support tool in diverse contexts, including CCTV monitoring centers, drone video analysis, and smart city crime prevention systems, highlighting its potential for future scalability.

### Detailed Design
```sh
project-root/
├── app.py                        # 앱 실행 진입점 
│
├── core/                         # 백엔드 로직
│   ├── config.py                 # 환경 설정
│   ├── db.py                     # SQLite 연결 객체
│   │
│   ├── models/                   # DB 테이블 구조 정의
│   │   ├── __init__.py
│   │   ├── lstm_model.py         # 모델 정의
│   │   ├── user_DB.py            # 사용자 정보 테이블
│   │   └── analysis_DB.py        # 분석 결과 테이블  (X)
│   │
│   └── services/                 # 주요 기능 로직
│       ├── __init__.py
│       ├── auth.py               # 로그인/회원가입 처리
│       ├── preprocess.py         # 영상 → npy 변환 
│       ├── predict.py            # 위의 npy 받아서 AI 모델 로딩 및 예측
│       ├── save_analysis.py      # 분석 결과 저장  (X)
│       ├── histroy_json.py       # 분석 기록 → JSON 
│       └── history.py            # 분석 기록 조회  (X)
│
├── gui/                          # 프론트엔드 UI (PyQt5)
│   ├── login_window.py           # 로그인 창
│   ├── register_window.py        # 회원가입 창
│   ├── main_window.py            # 메인 메뉴 역할
│   ├── upload_window.py          # 파일 업로드, 로딩창
│   ├── history_window.py         # 분석 기록 조회 창
│   └── styles.qss                # 전역 스타일시트 
│
├── uploads/                      # 영상 저장될 위치
│   └── __init__.py
│
├── ai_models/                    # 학습시킨 AI 모델 저장소
│   └── lstm_model.pt             # 학습시킨 AI 모델 (pytorch)
│   
│
├── database/                     # SQLite DB 파일 저장 위치
│   ├── analysis.db               # 분석 기록 DB
│   └── users.db                  # 사용자 DB
│
├── assets/                       
│   └── Drovis_logo.ico           # Drovis 로고
│
├── requirements.txt              
├── README.md                     
└── .gitignore                                                       
```

### Demonstration Video


## TEAM : 두뇌풀가동

| 장은정(팀장) | 나정수 | 
|:-------:|:-------:|
| AI 개발 <br/>프론트엔드 개발 | 백엔드 개발 <br/> 프론트엔드 개발 |

## Links

https://colab.research.google.com/drive/1hRJyIzisMv9yFO7gY9Hn1yxDeAlRBNAY?usp=sharing


0819 은정: 이제 제발 됐으면 좋겠다..... // 이건 꼭 수정!!!