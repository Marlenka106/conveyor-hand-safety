# src/hand_detector.py
import cv2
import mediapipe as mp
import numpy as np

class HandDetector:
    def __init__(self, min_detection_confidence=0.3, min_tracking_confidence=0.5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils

    def detect(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        hands_data = []

        if results.multi_hand_landmarks:
            h, w = frame.shape[:2]
            for hand_landmarks in results.multi_hand_landmarks:
                # Сохраняем оригинальный объект landmarks (для отрисовки!)
                # И вычисляем bbox
                x_min, y_min = w, h
                x_max, y_max = 0, 0
                landmarks_list = []
                for lm in hand_landmarks.landmark:
                    x, y = int(lm.x * w), int(lm.y * h)
                    landmarks_list.append((x, y))
                    x_min, x_max = min(x_min, x), max(x_max, x)
                    y_min, y_max = min(y_min, y), max(y_max, y)

                hands_data.append({
                    'landmarks_obj': hand_landmarks,
                    'landmarks': landmarks_list,
                    'bbox': (x_min, y_min, x_max, y_max)
                })

        return hands_data

    def draw_hands(self, frame, hands_data):
        """Отрисовка скелета рук с помощью MediaPipe."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        annotated = rgb_frame.copy()
        
        for hand in hands_data:
            self.mp_draw.draw_landmarks(
                annotated,
                hand['landmarks_obj'],
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                self.mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2)
            )
        
        return cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR) 