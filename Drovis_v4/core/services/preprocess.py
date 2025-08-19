import cv2
import numpy as np
import mediapipe as mp


def process_pose(
    video_path,
    detected_points=33,
    return_stats=True,
):
    # Mediapipe Pose 객체 초기화
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False, 
        min_detection_confidence=0.5,     # 탐지 최소 신뢰도 (0~1)
        min_tracking_confidence=0.5       # 추적 최소 신뢰도 (0~1)
        )

    # OpenCV로 영상 열기
    cap = cv2.VideoCapture(video_path)
    frames = []
    success_cnt, fail_cnt = 0, 0

    # 영상 파일 열기 실패 시 에러 반환
    if not cap.isOpened():
        print(f"[ERROR] 영상 파일을 열 수 없습니다: {video_path}")
        return (None, None) if return_stats else None

    # 프레임 단위로 영상 읽기
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        # 포즈 좌표 검출된 경우
        if results.pose_landmarks:
            coords = []
            for lm in results.pose_landmarks.landmark:
                # 각 랜드마크의 (x, y) 좌표 저장
                coords.extend([lm.x, lm.y])
            frames.append(coords)
            success_cnt += 1
        else:
            fail_cnt += 1
            continue

    cap.release()
    pose.close()

    # 리스트를 numpy로 변환
    frames = np.asarray(frames, dtype=np.float32)  

    if return_stats:
        return frames, {"success": success_cnt, "fail": fail_cnt}
    return frames
