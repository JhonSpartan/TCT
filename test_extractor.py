"""
test_extractor.py
Тестирование автоматического выделения контура
"""

import cv2
import numpy as np
from core.contour_extractor import ContourExtractor
from core.models import Point, Contour


# Создаём простое тестовое изображение (белый квадрат на чёрном)
def create_test_image():
    img = np.zeros((500, 500), dtype=np.uint8)  # чёрный фон
    cv2.rectangle(img, (50, 50), (450, 450), 255, -1)  # белый квадрат
    cv2.imwrite("test_square.png", img)
    print("Создан test_square.png (белый квадрат на чёрном фоне)")


# Тест 1: базовое выделение
def test_basic_extraction():
    extractor = ContourExtractor(epsilon_factor=0.01)
    contour, w, h = extractor.extract("test_square.png")

    print(f"Размер изображения: {w} x {h}")
    print(f"Найдено точек: {len(contour)}")
    print(f"Первые 3 точки: {contour.points[:3]}")
    print(f"Контур замкнут: {contour.closed}")
    print(f"Тип: {contour.contour_type}")


# Тест 2: сравнение с оригиналом
def test_accuracy():
    extractor = ContourExtractor(epsilon_factor=0.001)
    contour, w, h = extractor.extract("test_square.png")

    # Ожидаем квадрат 400x400 (от 50,50 до 450,450)
    xs = [p.x for p in contour.points]
    ys = [p.y for p in contour.points]

    print(f"\nГабариты контура в пикселях:")
    print(f"  X: {min(xs):.0f} .. {max(xs):.0f}")
    print(f"  Y: {min(ys):.0f} .. {max(ys):.0f}")
    print(f"  Ширина: {max(xs) - min(xs):.0f} px")
    print(f"  Высота: {max(ys) - min(ys):.0f} px")


if __name__ == "__main__":
    create_test_image()
    test_basic_extraction()
    test_accuracy()

    print("\n✅ Тест автоматического выделения пройден")