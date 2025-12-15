import cv2
import mediapipe as mp

# Укажи свой путь к видео
video_path = "assets/Eston.mp4"

cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print("❌ Не удалось открыть видео:", video_path)
    exit()

print("Видео открыто. Запуск детекции рук...")

mp_hands = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5
)
mp_draw = mp.solutions.drawing_utils

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("Видео закончилось или кадр не прочитан")
        break

    frame_count += 1
    if frame_count % 30 == 0:  # Выводим каждую секунду (примерно)
        print(f"Обработано кадров: {frame_count}")

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = mp_hands.process(rgb)

    if results.multi_hand_landmarks:
        print(f"✅ Руки найдены на кадре {frame_count}!")
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(
                frame,
                hand_landmarks,
                mp.solutions.hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                mp_draw.DrawingSpec(color=(255, 0, 0), thickness=2)
            )
    else:
        print(f"🚫 Рук не найдено на кадре {frame_count}")

    cv2.imshow("MediaPipe Hands Test", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("Тест завершён.")