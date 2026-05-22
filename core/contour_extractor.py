"""
core/contour_extractor.py
Автоматическое выделение контура
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from core.models import Point, Contour
from core.settings import ContourSettings


class ContourExtractor:
    def __init__(self, epsilon_factor: float = 0.000075):
        """
        epsilon_factor: коэффициент упрощения контура
        0.000075 = ~450-500 точек для типового контура
        0 = без упрощения (все точки)
        """
        self.epsilon_factor = epsilon_factor

    def extract(self, image_path: str):
        # Загружаем изображение в оттенках серого
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None, 0, 0

        h, w = img.shape  # ← вот откуда берутся h, w

        # Бинаризация: порог 200 (для тёмного контура на светлом фоне)
        _, binary = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY_INV)

        # Поиск контуров
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        if not contours:
            return None, w, h

        # Берём самый большой контур
        largest = max(contours, key=cv2.contourArea)

        # Упрощение контура (если epsilon_factor > 0)
        if self.epsilon_factor > 0:
            perimeter = cv2.arcLength(largest, True)
            epsilon = self.epsilon_factor * perimeter
            simplified = cv2.approxPolyDP(largest, epsilon, True)
            points = [Point(x=float(p[0][0]), y=float(p[0][1])) for p in simplified]
        else:
            # Без упрощения — все точки
            points = [Point(x=float(p[0][0]), y=float(p[0][1])) for p in largest]

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

    def get_contour_bounds_px(self, contour: Contour) -> Tuple[float, float, float, float]:
        """Возвращает габариты контура в пикселях (min_x, max_x, min_y, max_y)"""
        xs = [p.x for p in contour.points]
        ys = [p.y for p in contour.points]
        return (min(xs), max(xs), min(ys), max(ys))