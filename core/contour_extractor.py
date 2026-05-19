"""
core/contour_extractor.py
Автоматическое выделение контура из изображения
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from core.models import Point, Contour


class ContourExtractor:
    """Автоматическое выделение внешнего контура"""

    def __init__(self, epsilon_factor: float = 0.001):
        """
        epsilon_factor: точность упрощения контура (0.001 = 0.1%)
        Чем меньше значение, тем точнее, но больше точек
        """
        self.epsilon_factor = epsilon_factor

    def extract(self, image_path: str) -> Tuple[Optional[Contour], int, int]:
        """
        Возвращает (контур, ширина_пикс, высота_пикс)
        """
        # 1. Загружаем изображение в оттенках серого
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None, 0, 0

        h, w = img.shape

        # 2. Бинаризация: всё, что темнее 127, становится белым (255)
        #    THRESH_BINARY_INV — инвертируем, чтобы объект был белым на чёрном
        _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

        # 3. Находим все контуры
        #    RETR_EXTERNAL — только внешние контуры (игнорируем дырки внутри)
        #    CHAIN_APPROX_NONE — сохраняем все точки
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:
            return None, w, h

        # 4. Берём самый большой контур (по площади)
        largest = max(contours, key=cv2.contourArea)

        # 5. Упрощаем контур (убираем лишние точки, но сохраняем форму)
        perimeter = cv2.arcLength(largest, True)
        epsilon = self.epsilon_factor * perimeter
        simplified = cv2.approxPolyDP(largest, epsilon, True)

        # 6. Преобразуем в наш формат Point
        points = [Point(x=float(p[0][0]), y=float(p[0][1])) for p in simplified]

        return Contour(points=points, closed=True), w, h

    def extract_with_canny(self, image_path: str,
                           low_threshold: int = 50,
                           high_threshold: int = 150) -> Optional[Contour]:
        """
        Альтернативный метод через Canny edge detector
        Лучше работает для изображений с плохим контрастом
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None

        # Обнаружение границ
        edges = cv2.Canny(img, low_threshold, high_threshold)

        # Находим контуры
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:
            return None

        largest = max(contours, key=cv2.contourArea)
        points = [Point(x=float(p[0][0]), y=float(p[0][1])) for p in largest]

        return Contour(points=points, closed=True)