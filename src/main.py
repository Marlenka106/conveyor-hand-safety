# src/main.py
import argparse
import os
import json
import cv2

CONFIG_PATH = "config/restricted_zones.json"


def load_zones():
    """Загрузка опасных зон из JSON."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    return []


def annotation_mode(video_path):
    """
    Режим разметки: пользователь кликает, чтобы задать опасную зону конвейера.
    """
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("❌ Не удалось прочитать видео")
        return

    zones = []
    current_polygon = []

    def mouse_callback(event, x, y, flags, param):
        nonlocal current_polygon
        if event == cv2.EVENT_LBUTTONDOWN:
            current_polygon.append((x, y))
            print(f"Добавлена точка: ({x}, {y})")

    cv2.namedWindow("Conveyor Safety - Annotation Mode")
    cv2.setMouseCallback("Conveyor Safety - Annotation Mode", mouse_callback)

    print("Инструкция:")
    print("- ЛКМ: добавить точку полигона опасной зоны")
    print("- Нажмите 's', чтобы сохранить текущую зону")
    print("- Нажмите 'n', чтобы начать новую зону")
    print("- Нажмите 'q', чтобы завершить разметку")

    while True:
        display_frame = frame.copy()

        # Отрисовка текущего полигона
        for i, point in enumerate(current_polygon):
            cv2.circle(display_frame, point, 5, (0, 255, 0), -1)
            if i > 0:
                cv2.line(display_frame, current_polygon[i - 1], point, (0, 255, 0), 2)

        cv2.imshow("Conveyor Safety - Annotation Mode", display_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            if len(current_polygon) >= 3:
                zones.append({"points": current_polygon.copy()})
                print(f"Опасная зона сохранена. Всего зон: {len(zones)}")
            else:
                print("⚠️ Опасная зона должна содержать минимум 3 точки!")

        elif key == ord("n"):
            current_polygon.clear()
            print("Начата новая опасная зона")

        elif key == ord("q"):
            break

    cv2.destroyAllWindows()

    if zones:
        os.makedirs("config", exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(zones, f, indent=4)
        print(f"✅ Опасные зоны сохранены в {CONFIG_PATH}")
    else:
        print("Нет сохранённых зон.")


def safety_mode(video_path):
    """Пока заглушка — будет обнаружение рук и тревога."""
    print("🎬 Режим безопасности: обнаружение рук и тревога (пока не реализован)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="Путь к видеофайлу с конвейером")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"❌ Видеофайл не найден: {args.video}")
        return

    zones = load_zones()
    if not zones:
        print("📋 Файл опасных зон не найден — запускаем режим разметки")
        annotation_mode(args.video)
    else:
        print(f"✅ Найдено {len(zones)} опасных зон — запускаем режим безопасности")
        safety_mode(args.video)


if __name__ == "__main__":
    main()