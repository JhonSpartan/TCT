"""
core/models.py
Классы данных для хранения информации о шаблоне, контуре и точках
"""

from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field


class ContourType(str, Enum):
    """Тип контура: ломаная линия или сплайн"""
    POLYLINE = "polyline"
    SPLINE = "spline"


class Unit(str, Enum):
    """Единицы измерения"""
    MM = "mm"  # миллиметры
    CM = "cm"  # сантиметры
    PX = "px"  # пиксели


class Point(BaseModel):
    """
    Точка в 2D пространстве
    """
    x: float = Field(..., description="Координата X")
    y: float = Field(..., description="Координата Y")

    def to_tuple(self) -> Tuple[float, float]:
        """Преобразует точку в кортеж (x, y)"""
        return (self.x, self.y)

    def __repr__(self) -> str:
        return f"Point(x={self.x:.2f}, y={self.y:.2f})"


class Contour(BaseModel):
    """
    Контур — последовательность точек, образующих замкнутую или разомкнутую линию
    """
    points: List[Point] = Field(default_factory=list, description="Список точек контура")
    closed: bool = Field(default=True, description="Замкнут ли контур")
    contour_type: ContourType = Field(default=ContourType.POLYLINE, description="Тип линии")

    def to_mm_tuples(self) -> List[Tuple[float, float]]:
        """Возвращает список точек в виде кортежей (x, y)"""
        return [p.to_tuple() for p in self.points]

    def add_point(self, x: float, y: float) -> None:
        """Добавляет точку в конец списка"""
        self.points.append(Point(x=x, y=y))

    def clear(self) -> None:
        """Очищает все точки"""
        self.points.clear()

    def __len__(self) -> int:
        return len(self.points)


class Template(BaseModel):
    """
    Шаблон ковра — основная сущность программы
    Содержит информацию об изображении и его масштабе
    """
    name: str = Field(default="Безымянный шаблон", description="Название шаблона")
    image_path: str = Field(default="", description="Путь к исходному изображению PNG")

    # Контур (заполняется после обработки)
    contour: Optional[Contour] = Field(default=None, description="Выделенный контур")

    # Реальные размеры (в миллиметрах)
    real_width_mm: Optional[float] = Field(default=None, description="Реальная ширина в мм")
    real_height_mm: Optional[float] = Field(default=None, description="Реальная высота в мм")

    # Размеры изображения в пикселях (заполняются при загрузке)
    image_width_px: int = Field(default=0, description="Ширина картинки в пикселях")
    image_height_px: int = Field(default=0, description="Высота картинки в пикселях")

    # Масштабные коэффициенты (вычисляются автоматически)
    scale_x: float = Field(default=1.0, description="Масштаб X: пиксель → мм")
    scale_y: float = Field(default=1.0, description="Масштаб Y: пиксель → мм")

    def calculate_scale(self) -> None:
        """
        Вычисляет масштабные коэффициенты на основе реальных размеров
        """
        if self.real_width_mm and self.image_width_px > 0:
            self.scale_x = self.real_width_mm / self.image_width_px
            # Если высота не задана — используем тот же масштаб
            if not self.real_height_mm:
                self.scale_y = self.scale_x

        if self.real_height_mm and self.image_height_px > 0:
            self.scale_y = self.real_height_mm / self.image_height_px
            # Если ширина не задана — используем тот же масштаб
            if not self.real_width_mm:
                self.scale_x = self.scale_y

    def point_px_to_mm(self, point_px: Point) -> Point:
        """
        Переводит точку из пикселей в миллиметры с учётом масштаба
        """
        x_mm = point_px.x * self.scale_x
        # Инвертируем Y (в изображениях Y растёт вниз)
        y_mm = (self.image_height_px - point_px.y) * self.scale_y
        return Point(x=x_mm, y=y_mm)

    def get_contour_mm(self) -> List[Tuple[float, float]]:
        """
        Возвращает контур в миллиметрах (список кортежей)
        """
        if not self.contour:
            return []

        return [self.point_px_to_mm(p).to_tuple() for p in self.contour.points]

    def get_bounding_box_mm(self) -> Tuple[float, float, float, float]:
        """
        Возвращает габаритный прямоугольник контура в мм:
        (min_x, max_x, min_y, max_y)
        """
        points_mm = self.get_contour_mm()
        if not points_mm:
            return (0, 0, 0, 0)

        xs = [p[0] for p in points_mm]
        ys = [p[1] for p in points_mm]
        return (min(xs), max(xs), min(ys), max(ys))