# src/hand_detector.py
import cv2
import mediapipe as mp
import numpy as np

class HandDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.mp_draw = mp.solutions.drawing_utils

    def detect(self, frame):
        """
        Детекция рук на кадре.
        Возвращает список: [{'landmarks': [(x, y), ...], 'bbox': (x1, y1, x2, y2)}, ...]
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)
        hands_data = []

        if results.multi_hand_landmarks:
            h, w = frame.shape[:2]
            for hand_landmarks in results.multi_hand_landmarks:
                landmarks = []
                x_min, y_min = w, h
                x_max, y_max = 0, 0

                for lm in hand_landmarks.landmark:
                    x, y = int(lm.x * w), int(lm.y * h)
                    landmarks.append((x, y))
                    x_min, x_max = min(x_min, x), max(x_max, x)
                    y_min, y_max = min(y_min, y), max(y_max, y)

                hands_data.append({
                    'landmarks': landmarks,
                    'bbox': (x_min, y_min, x_max, y_max)
                })

        return hands_data

    def draw_hands(self, frame, hands_data):
        """Отрисовка скелета рук и bounding box."""
        for hand in hands_data:
            # Отрисовка точек и связей
            for i, point in enumerate(hand['landmarks']):
                cv2.circle(frame, point, 3, (0, 255, 0), -1)
            # Простая отрисовка bbox
            x1, y1, x2, y2 = hand['bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        return frame