import cv2
import numpy as np
import cv2
import numpy as np

img = cv2.imread("traktor2.png", cv2.IMREAD_GRAYSCALE)

# Бинаризация
_, binary = cv2.threshold(img, 50, 255, cv2.THRESH_BINARY)

# Находим контуры
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

# Рисуем ВСЕ найденные контуры
output = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
for i, cnt in enumerate(contours):
    # Разные контуры разными цветами
    color = (0, 255, 0) if i == 0 else (0, 0, 255)
    cv2.drawContours(output, [cnt], -1, color, 2)
    area = cv2.contourArea(cnt)
    print(f"Контур {i}: площадь = {area:.0f} пикс")

cv2.imwrite("all_contours.png", output)
print("Сохранено all_contours.png — посмотри, какие контуры найдены")

for thresh in [200, 220, 240]:
    _, binary = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # Находим самый большой контур
    if contours:
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)
        print(f"Порог {thresh}: самый большой контур = {area:.0f} пикс")

        # Сохраняем маску
        mask = np.zeros_like(binary)
        cv2.drawContours(mask, [largest], -1, 255, -1)
        cv2.imwrite(f"mask_thresh_{thresh}.png", mask)