# test_models.py
from core.models import Point, Contour, Template, ContourType

# Тест 1: Создание точки
p1 = Point(x=10.5, y=20.3)
print(f"Точка: {p1}")
print(f"Кортеж: {p1.to_tuple()}")

# Тест 2: Создание контура
contour = Contour(closed=True, contour_type=ContourType.POLYLINE)
contour.add_point(0, 0)
contour.add_point(100, 0)
contour.add_point(100, 50)
contour.add_point(0, 50)
print(f"\nКонтур: {len(contour)} точек")
print(f"Тип: {contour.contour_type}")

# Тест 3: Создание шаблона
template = Template(
    name="Тестовый коврик",
    image_path="test.png",
    image_width_px=1000,
    image_height_px=800,
    real_width_mm=2000,  # 2 метра
    contour=contour
)
template.calculate_scale()
print(f"\nШаблон: {template.name}")
print(f"Масштаб: X={template.scale_x:.3f} мм/пикс, Y={template.scale_y:.3f} мм/пикс")

# Тест 4: Перевод точки из пикселей в мм
px_point = Point(x=500, y=400)
mm_point = template.point_px_to_mm(px_point)
print(f"Точка в пикселях (500, 400) → в мм: {mm_point}")

# Тест 5: Габариты контура
bbox = template.get_bounding_box_mm()
print(f"Габариты контура в мм: X: {bbox[0]:.1f}..{bbox[1]:.1f}, Y: {bbox[2]:.1f}..{bbox[3]:.1f}")

print("\n✅ Все тесты пройдены!")