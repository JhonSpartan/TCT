"""
core/settings.py
Настройки программы (цвета, точность, параметры)
"""

from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class ContourSettings:
    epsilon_factor: float = 0.001  # Точность упрощения RDP
    threshold: int = 200  # Порог бинаризации (для тёмного контура на светлом фоне)
    canny_low: int = 50  # Нижний порог Canny
    canny_high: int = 150  # Верхний порог Canny
    use_canny: bool = False  # Использовать Canny вместо бинаризации
    simplify_contour: bool = True  # Упрощать контур (RDP)


@dataclass
class DXFColorSettings:
    contour: int = 1  # Красный
    bounding_box: int = 4  # Синий
    dimensions: int = 3  # Зелёный
    text: int = 7  # Белый/чёрный
    points: int = 2  # Жёлтый


@dataclass
class DXFLineSettings:
    contour_lineweight: int = 35  # 0.35 мм
    bounding_lineweight: int = 25  # 0.25 мм
    bounding_linetype: str = "DASHED"
    text_height: int = 10


@dataclass
class AppSettings:
    contour: ContourSettings = field(default_factory=ContourSettings)
    dxf_colors: DXFColorSettings = field(default_factory=DXFColorSettings)
    dxf_lines: DXFLineSettings = field(default_factory=DXFLineSettings)

    last_image_path: str = ""
    last_dxf_path: str = ""
    window_width: int = 900
    window_height: int = 700

    @classmethod
    def load(cls, config_path: str = "settings.json") -> "AppSettings":
        """Загружает настройки из JSON файла"""
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        return cls()

    def save(self, config_path: str = "settings.json"):
        """Сохраняет настройки в JSON файл"""
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, indent=2, default=str, ensure_ascii=False)