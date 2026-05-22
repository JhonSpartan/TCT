"""
core/manual_digitizer.py
Ручная оцифровка контура — пользователь кликает по изображению мышкой
"""

import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton, KeyEvent
from typing import List, Tuple, Optional, Callable
from core.models import Point, Contour, ContourType


class ManualDigitizer:
    """
    Интерактивный инструмент для ручной обводки контура
    Пользователь кликает по изображению, программа запоминает точки
    """

    def __init__(self, image_path: str, on_complete: Optional[Callable] = None):
        """
        image_path: путь к PNG изображению
        on_complete: функция, которая вызовется после сохранения (опционально)
        """
        self.image_path = image_path
        self.on_complete = on_complete

        # Загружаем изображение
        self.img = plt.imread(image_path)
        self.h, self.w = self.img.shape[:2]  # высота и ширина в пикселях

        # Хранилище точек (в пикселях)
        self.points_px: List[Tuple[float, float]] = []

        # Настройки отображения
        self.fig = None
        self.ax = None

    def start(self) -> Contour:
        """
        Запускает интерактивный режим.
        Возвращает Contour после завершения (нажатия Enter)
        """
        # Создаём окно
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        self.ax.imshow(self.img)
        self.ax.set_title(
            "🖱️ Кликайте по контуру по часовой стрелке\n"
            "⏎ Enter — сохранить | ⌫ Backspace — отменить последнюю | Esc — выйти без сохранения"
        )

        # Привязываем обработчики
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)

        # Показываем окно (блокирует выполнение до закрытия)
        plt.show()

        # Возвращаем контур
        return self._build_contour()

    def _on_click(self, event):
        """Обработчик клика мышкой"""
        if not event.inaxes:
            return  # клик вне изображения

        if event.button == MouseButton.LEFT:
            x, y = event.xdata, event.ydata
            self.points_px.append((x, y))

            # Рисуем точку
            self.ax.plot(x, y, 'ro', markersize=5, markeredgecolor='white', markeredgewidth=1)

            # Рисуем линию от предыдущей точки
            if len(self.points_px) >= 2:
                prev_x, prev_y = self.points_px[-2]
                self.ax.plot([prev_x, x], [prev_y, y], 'r-', linewidth=1.5, alpha=0.7)

            self.fig.canvas.draw()
            print(f"📍 Точка {len(self.points_px)}: ({x:.1f}, {y:.1f})")

    def _on_key(self, event):
        """Обработчик нажатий клавиш"""

        if event.key == 'enter':
            if len(self.points_px) < 3:
                print("❌ Нужно минимум 3 точки для создания контура!")
                return

            print(f"\n✅ Сохранено {len(self.points_px)} точек")
            plt.close(self.fig)  # закрываем окно

        elif event.key == 'backspace':
            if self.points_px:
                self.points_px.pop()
                print(f"↩️ Отменена последняя точка. Осталось {len(self.points_px)}")
                self._redraw()

        elif event.key == 'escape':
            print("❌ Выход без сохранения")
            self.points_px = []  # очищаем
            plt.close(self.fig)

    def _redraw(self):
        """Перерисовывает изображение со всеми точками"""
        self.ax.clear()
        self.ax.imshow(self.img)
        self.ax.set_title(self.ax.get_title())

        # Перерисовываем все точки и линии
        for i, (x, y) in enumerate(self.points_px):
            self.ax.plot(x, y, 'ro', markersize=5, markeredgecolor='white', markeredgewidth=1)
            if i > 0:
                prev_x, prev_y = self.points_px[i - 1]
                self.ax.plot([prev_x, x], [prev_y, y], 'r-', linewidth=1.5, alpha=0.7)

        self.fig.canvas.draw()

    def _build_contour(self) -> Contour:
        """Создаёт объект Contour из накопленных точек"""
        points = [Point(x=x, y=y) for x, y in self.points_px]
        return Contour(points=points, closed=True, contour_type=ContourType.POLYLINE)