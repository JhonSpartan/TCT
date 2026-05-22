"""
test_dxf_exporter.py
Тестирование экспорта в DXF
"""

import numpy as np
import cv2
from core.models import Template, Contour, Point
from core.contour_extractor import ContourExtractor
from core.dxf_exporter import DXFExporter


def test_export_from_contour():
    """Тест 1: экспорт из готового контура"""
    print("\n=== Тест 1: Экспорт из готового контура ===")

    # Создаём простой контур — прямоугольник
    contour = Contour(closed=True)
    contour.add_point(0, 0)
    contour.add_point(100, 0)
    contour.add_point(100, 50)
    contour.add_point(0, 50)

    # Создаём шаблон
    template = Template(
        name="Прямоугольник",
        contour=contour,
        image_width_px=100,
        image_height_px=50,
        real_width_mm=1000,  # реальная ширина 1000 мм
        real_height_mm=500  # реальная высота 500 мм
    )
    template.calculate_scale()

    # Экспортируем
    exporter = DXFExporter()
    result = exporter.export(template, "rectangle.dxf")

    print(f"Результат: {'✅ Успех' if result else '❌ Ошибка'}")


def test_export_from_image():
    """Тест 2: экспорт после автоматического выделения из PNG"""
    print("\n=== Тест 2: Экспорт из изображения ===")

    # Создаём тестовое изображение — квадрат
    img = np.zeros((400, 400), dtype=np.uint8)
    cv2.rectangle(img, (50, 50), (350, 350), 255, -1)
    cv2.imwrite("traktor.png", img)

    # Автоматически выделяем контур
    extractor = ContourExtractor(epsilon_factor=0.01)
    contour, w, h = extractor.extract("traktor_export.png")

    if not contour:
        print("❌ Контур не найден")
        return

    # Создаём шаблон с реальными размерами
    template = Template(
        name="Квадрат из изображения",
        contour=contour,
        image_width_px=w,
        image_height_px=h,
        real_width_mm=500,  # квадрат 500x500 мм
        real_height_mm=500
    )
    template.calculate_scale()

    # Экспортируем
    exporter = DXFExporter()
    result = exporter.export(template, "square_from_image.dxf")

    print(f"Результат: {'✅ Успех' if result else '❌ Ошибка'}")
    print(f"Точек в контуре: {len(contour)}")
    bbox = template.get_bounding_box_mm()
    print(f"Габариты в мм: {bbox[1] - bbox[0]:.1f} x {bbox[3] - bbox[2]:.1f}")


def test_export_with_real_png():
    """Тест 3: экспорт реального PNG (если файл существует)"""
    print("\n=== Тест 3: Экспорт реального PNG ===")

    import os
    png_path = "2814ef7408490313f010f2a5b7140228.png"

    if not os.path.exists(png_path):
        print(f"⚠️ Файл {png_path} не найден, пропускаем")
        return

    # Автоматическое выделение
    extractor = ContourExtractor(epsilon_factor=0.001)
    contour, w, h = extractor.extract(png_path)

    if not contour:
        print("❌ Контур не найден автоматически")
        return

    # Экспорт с реальными размерами (94 см = 940 мм)
    template = Template(
        name="Коврик из PNG",
        contour=contour,
        image_width_px=w,
        image_height_px=h,
        real_width_mm=940  # 94 см
    )
    template.calculate_scale()

    exporter = DXFExporter()
    result = exporter.export(template, "kovrik_from_png.dxf")

    print(f"Результат: {'✅ Успех' if result else '❌ Ошибка'}")
    print(f"Точек: {len(contour)}")
    bbox = template.get_bounding_box_mm()
    print(f"Габариты: {bbox[1] - bbox[0]:.1f} x {bbox[3] - bbox[2]:.1f} мм")


if __name__ == "__main__":
    test_export_from_contour()
    test_export_from_image()
    test_export_with_real_png()

    print("\n🎉 Все тесты экспорта завершены!")
    print("Откройте получившиеся .dxf файлы в CAD программе")