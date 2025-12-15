# src/main.py
import argparse
import os
import json
import cv2
import time
from src.hand_detector import HandDetector
from src.zone_checker import is_point_in_any_zone, draw_zones

CONFIG_PATH = "config/conveyor_zones.json"

def load_zones():
    """Загрузка зоны конвейера из JSON."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    return []


def annotation_mode(video_path):
    """
    Режим разметки: пользователь задаёт зону конвейера (где должны быть руки при работе).
    """
    cap = cv2.VideoCapture(video_path)
    # Перемотка к 3-й секунде (3000 миллисекунд)
    cap.set(cv2.CAP_PROP_POS_MSEC, 3000)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("⚠️ Не удалось прочитать кадр на 3-й секунде. Используется первый кадр.")
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

    cv2.namedWindow("Conveyor Work Zone - Annotation", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("Conveyor Work Zone - Annotation", mouse_callback)

    print("Инструкция:")
    print("- ЛКМ: добавить точку полигона зоны конвейера")
    print("- Нажмите 's', чтобы сохранить зону")
    print("- Нажмите 'q', чтобы завершить разметку")

    while True:
        display_frame = frame.copy()

        for i, point in enumerate(current_polygon):
            cv2.circle(display_frame, point, 5, (0, 255, 0), -1)
            if i > 0:
                cv2.line(display_frame, current_polygon[i - 1], point, (0, 255, 0), 2)

        cv2.imshow("Conveyor Work Zone - Annotation", display_frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            if len(current_polygon) >= 3:
                zones = [{"points": current_polygon.copy()}]  # одна зона
                print("✅ Зона конвейера сохранена")
                break
            else:
                print("⚠️ Зона должна содержать минимум 3 точки!")

        elif key == ord("q"):
            break

    cv2.destroyAllWindows()

    if zones:
        os.makedirs("config", exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(zones, f, indent=4)
        print(f"✅ Зона сохранена в {CONFIG_PATH}")
    else:
        print("Нет сохранённых зон.")

def work_monitoring_mode(video_path):
    print("🎬 Запуск режима мониторинга работы оператора...")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ Не удалось открыть видео")
        return

    # Параметры видео
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Подготовка записи
    os.makedirs("output", exist_ok=True)
    output_path = "output/work_monitoring.mp4"
    video_writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    zones = load_zones()
    if not zones:
        print("⚠️ Нет зоны конвейера. Запустите разметку.")
        return

    detector = HandDetector()

    # Таймеры
    work_start_time = None
    pause_start_time = time.time()
    total_work_time = 0
    total_pause_time = 0
    is_working = False  # True = руки в зоне

    cv2.namedWindow("Conveyor Work Monitoring", cv2.WINDOW_NORMAL)
    print("▶️ Мониторинг запущен. Нажмите 'q' для остановки.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        current_time = time.time()

        # Детекция рук
        hands = detector.detect(frame)
        hand_in_zone = False

        # Проверяем, есть ли хотя бы одна точка хотя бы одной руки в зоне
        for hand in hands:
            for point in hand['landmarks']:
                if is_point_in_any_zone(point, zones):
                    hand_in_zone = True
                    break
            if hand_in_zone:
                break
            
        current_time = time.time()

        # Обновление состояния и таймеров
        if hand_in_zone:
             # Руки в зоне → РАБОТА
            if not is_working:
                # Переход в режим работы
                if pause_start_time:
                    total_pause_time += current_time - pause_start_time
                is_working = True
                work_start_time = current_time
                pause_start_time = None
            # Иначе — продолжаем работать (таймер идёт в фоне)
        else:
            # Рук нет в зоне (или совсем нет рук) → ПАУЗА
            if is_working:
                # Переход в паузу
                if work_start_time:
                    total_work_time += current_time - work_start_time
                is_working = False
                pause_start_time = current_time
                work_start_time = None
            # Иначе — продолжаем паузу (таймер идёт в фоне)

        # Текущие значения для отображения
        display_work = total_work_time
        display_pause = total_pause_time
        if is_working and work_start_time:
            display_work = total_work_time + (current_time - work_start_time)
        if not is_working and pause_start_time:
            display_pause = total_pause_time + (current_time - pause_start_time)

        # Отрисовка
        frame = detector.draw_hands(frame, hands)
        frame = draw_zones(frame, zones)

        if is_working:
            status = f"Process: {int(display_work)} s"
            color = (0, 255, 0)  # зелёный
        else:
            status = f"Pause: {int(display_pause)} s"
            color = (0, 255, 255)  # жёлтый

        cv2.putText(frame, status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

        # Запись и вывод
        video_writer.write(frame)
        
        cv2.imshow("Conveyor Work Monitoring", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Финальное обновление таймеров
    final_time = time.time()
    if is_working and work_start_time:
        total_work_time += final_time - work_start_time
    elif not is_working and pause_start_time:
        total_pause_time += final_time - pause_start_time

    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()

    # Итог
    print(f"\n✅ Видео сохранено: {output_path}")
    print(f"Process time — {int(total_work_time)} s,  Pause — {int(total_pause_time)} s")


def main():
    parser = argparse.ArgumentParser(description="Мониторинг работы оператора у конвейера")
    parser.add_argument("--video", required=True, help="Путь к видеофайлу с конвейером")
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"❌ Видеофайл не найден: {args.video}")
        return

    zones = load_zones()
    if not zones:
        print("📋 Файл зоны конвейера не найден — запускаем режим разметки")
        annotation_mode(args.video)
    else:
        print("✅ Зона конвейера загружена — запускаем мониторинг")
        work_monitoring_mode(args.video)


if __name__ == "__main__":
    main()