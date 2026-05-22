"""
core/dxf_exporter.py
Экспорт контура и шаблона в DXF файл
"""

import ezdxf
from typing import List, Tuple
from pathlib import Path
from core.models import Template


class DXFExporter:
    """Экспорт шаблона в DXF"""

    def __init__(self):
        self.doc = None
        self.msp = None

    def export(self, template: Template, output_path: str) -> bool:
        """
        Экспортирует шаблон в DXF файл
        """
        # Проверяем, есть ли контур
        if not template.contour or len(template.contour.points) < 3:
            print("❌ Нет контура или меньше 3 точек")
            return False

        # Создаём документ DXF
        self.doc = ezdxf.new("R2010")
        self.msp = self.doc.modelspace()

        # Получаем контур в миллиметрах
        points_mm = template.get_contour_mm()

        if not points_mm:
            print("❌ Ошибка пересчёта координат")
            return False

        # Замыкаем контур если нужно
        if template.contour.closed and points_mm[0] != points_mm[-1]:
            points_mm.append(points_mm[0])

        # Рисуем основной контур
        self._add_contour(points_mm, template.contour.contour_type.value)

        # Добавляем габаритную рамку
        bbox = template.get_bounding_box_mm()
        self._add_bounding_box(bbox)

        # Добавляем информационный текст
        self._add_info_text(template, bbox)

        # Создаём папку если не существует
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Сохраняем
        self.doc.saveas(output_path)
        print(f"✅ DXF сохранён: {output_path}")
        return True

    def _add_contour(self, points_mm: List[Tuple[float, float]], contour_type: str):
        """Добавляет контур в DXF"""
        if contour_type == "polyline":
            self.msp.add_lwpolyline(points_mm, dxfattribs={
                'color': 1,
                'layer': 'CONTOUR',
                'lineweight': 35
            })
        else:
            self.msp.add_spline(points_mm, dxfattribs={
                'color': 1,
                'layer': 'CONTOUR'
            })

    def _add_bounding_box(self, bbox: Tuple[float, float, float, float]):
        """Добавляет габаритный прямоугольник"""
        min_x, max_x, min_y, max_y = bbox

        if min_x == max_x or min_y == max_y:
            return

        box_points = [
            (min_x, min_y),
            (max_x, min_y),
            (max_x, max_y),
            (min_x, max_y),
            (min_x, min_y)
        ]

        self.msp.add_lwpolyline(box_points, dxfattribs={
            'color': 4,
            'linetype': 'DASHED',
            'layer': 'BOUNDING_BOX',
            'lineweight': 25
        })

    def _add_info_text(self, template: Template, bbox: Tuple[float, float, float, float]):
        """Добавляет текстовую информацию - работает в ezdxf 1.3.5"""
        min_x, max_x, min_y, max_y = bbox
        width = max_x - min_x
        height = max_y - min_y

        text_lines = [
            f"Шаблон: {template.name}",
            f"Размеры: {width:.1f} x {height:.1f} мм",
            f"Точек: {len(template.contour.points)}",
            f"Масштаб: X={template.scale_x:.3f} Y={template.scale_y:.3f} мм/пикс"
        ]
        text = "\n".join(text_lines)

        # Способ 1: через add_text с dxfattribs
        text_entity = self.msp.add_text(
            text,
            dxfattribs={
                'height': 10,
                'layer': 'TEXT',
                'color': 7
            }
        )
        # Устанавливаем позицию через dxf.insert (работает во всех версиях)
        text_entity.dxf.insert = (min_x, min_y - 30)