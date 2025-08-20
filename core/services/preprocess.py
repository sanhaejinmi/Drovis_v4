# preprocess.py
import cv2
import numpy as np
import mediapipe as mp

def process_pose(
    video_path,
    detected_points=33,
    return_stats=True,
):
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose(
        static_image_mode=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cap = cv2.VideoCapture(video_path)
    frames = []
    success_cnt, fail_cnt = 0, 0

    if not cap.isOpened():
        print(f"[ERROR] 영상 파일을 열 수 없습니다: {video_path}")
        return (None, None) if return_stats else None

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    frame_idx = 0                     # 원본 영상의 전역 프레임 번호
    frame_index_map = []              # 성공 프레임의 전역 프레임 번호 목록

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)

        if results.pose_landmarks:
            coords = []
            for lm in results.pose_landmarks.landmark:
                # Mediapipe 포즈는 0~1 정규화 좌표 (x, y)
                coords.extend([lm.x, lm.y])
            frames.append(coords)
            frame_index_map.append(frame_idx)   # ★ 성공 프레임 매핑 기록
            success_cnt += 1
        else:
            fail_cnt += 1

        frame_idx += 1

    cap.release()
    pose.close()

    frames = np.asarray(frames, dtype=np.float32)

    if return_stats:
        return frames, {
            "success": success_cnt,
            "fail": fail_cnt,
            "fps": fps,
            "frame_index_map": frame_index_map,   # ★ 추가
        }
    return frames
