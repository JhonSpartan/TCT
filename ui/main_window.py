"""
ui/main_window.py
Главное окно приложения
"""

import sys
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QStatusBar, QGroupBox, QLineEdit, QTextEdit,
    QProgressBar, QTabWidget, QSplitter, QFrame,
    QSlider, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QPixmap, QFont, QIcon

from core.models import Template
from core.contour_extractor import ContourExtractor
from core.manual_digitizer import ManualDigitizer
from core.dxf_exporter import DXFExporter


class WorkerThread(QThread):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, mode, image_path, width_mm, height_mm, epsilon_factor=0.000075):
        super().__init__()
        self.mode = mode
        self.image_path = image_path
        self.width_mm = width_mm
        self.height_mm = height_mm
        self.epsilon_factor = epsilon_factor  # ← новое

    def run(self):
        try:
            if self.mode == 'auto':
                from core.contour_extractor import ContourExtractor
                extractor = ContourExtractor(epsilon_factor=self.epsilon_factor)
                contour, full_w, full_h = extractor.extract(self.image_path)

                if not contour:
                    self.error.emit("Контур не найден. Попробуйте ручной режим.")
                    return

                # ========== НОВАЯ ЛОГИКА МАСШТАБИРОВАНИЯ ==========
                # Вычисляем габариты контура в пикселях
                xs = [p.x for p in contour.points]
                ys = [p.y for p in contour.points]
                contour_width_px = max(xs) - min(xs)
                contour_height_px = max(ys) - min(ys)
                # ================================================

                self.progress.emit(f"✅ Найдено {len(contour)} точек")
                self.progress.emit(f"📐 Контур в пикселях: {contour_width_px:.0f} x {contour_height_px:.0f}")

            else:  # manual
                from core.manual_digitizer import ManualDigitizer
                self.progress.emit("Открывается окно обводки...")
                digitizer = ManualDigitizer(self.image_path)
                contour = digitizer.start()

                if len(contour) < 3:
                    self.error.emit("Поставлено недостаточно точек (минимум 3)")
                    return

                # Вычисляем габариты контура в пикселях
                xs = [p.x for p in contour.points]
                ys = [p.y for p in contour.points]
                contour_width_px = max(xs) - min(xs)
                contour_height_px = max(ys) - min(ys)

                self.progress.emit(f"✅ Поставлено {len(contour)} точек")
                self.progress.emit(f"📐 Контур в пикселях: {contour_width_px:.0f} x {contour_height_px:.0f}")

            # ========== ИСПРАВЛЕННЫЙ ШАБЛОН ==========
            template = Template(
                name=os.path.basename(self.image_path),
                contour=contour,
                image_width_px=contour_width_px,  # ← больше не full_w
                image_height_px=contour_height_px,  # ← больше не full_h
                real_width_mm=self.width_mm,
                real_height_mm=self.height_mm
            )
            template.calculate_scale()
            # ========================================

            # Показываем финальные размеры
            bbox = template.get_bounding_box_mm()
            final_width = bbox[1] - bbox[0]
            final_height = bbox[3] - bbox[2]
            self.progress.emit(f"📐 Реальные размеры: {final_width:.1f} x {final_height:.1f} мм")

            self.finished.emit(template)

        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kovrik DXF Tool — Конвертер шаблонов")
        self.setMinimumSize(900, 700)

        self.current_image_path = None
        self.current_template = None

        self.setup_ui()
        self.setup_menu()
        self.setup_statusbar()

    def setup_ui(self):
        """Создаёт интерфейс"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Верхняя панель с кнопками
        top_panel = self.create_top_panel()
        main_layout.addLayout(top_panel)

        # Разделитель
        splitter = QSplitter(Qt.Horizontal)

        # Левая панель — управление
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # Правая панель — предпросмотр
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([350, 550])
        main_layout.addWidget(splitter)

        # Нижняя панель — лог
        bottom_panel = self.create_bottom_panel()
        main_layout.addWidget(bottom_panel)

    def create_top_panel(self):
        """Верхняя панель с кнопками"""
        layout = QHBoxLayout()

        self.btn_load = QPushButton("📂 Загрузить изображение")
        self.btn_load.clicked.connect(self.load_image)
        layout.addWidget(self.btn_load)

        self.btn_auto = QPushButton("🤖 Автоматическое выделение")
        self.btn_auto.clicked.connect(self.auto_extract)
        self.btn_auto.setEnabled(False)
        layout.addWidget(self.btn_auto)

        self.btn_manual = QPushButton("✏️ Ручная обрисовка")
        self.btn_manual.clicked.connect(self.manual_extract)
        self.btn_manual.setEnabled(False)
        layout.addWidget(self.btn_manual)

        self.btn_save = QPushButton("💾 Сохранить DXF")
        self.btn_save.clicked.connect(self.save_dxf)
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)

        layout.addStretch()

        return layout

    def create_left_panel(self):
        """Левая панель — настройки"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Группа размеров
        size_group = QGroupBox("📏 Реальные размеры (для масштаба)")
        size_layout = QVBoxLayout(size_group)

        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Ширина (см):"))
        self.input_width = QLineEdit()
        self.input_width.setPlaceholderText("например: 94")
        width_layout.addWidget(self.input_width)
        size_layout.addLayout(width_layout)

        height_layout = QHBoxLayout()
        height_layout.addWidget(QLabel("Высота (см):"))
        self.input_height = QLineEdit()
        self.input_height.setPlaceholderText("оставьте пустым для пропорции")
        height_layout.addWidget(self.input_height)
        size_layout.addLayout(height_layout)

        layout.addWidget(size_group)

        # Группа информации
        info_group = QGroupBox("ℹ️ Информация")
        info_layout = QVBoxLayout(info_group)

        self.lbl_image_info = QLabel("Файл: не загружен")
        self.lbl_image_info.setWordWrap(True)
        info_layout.addWidget(self.lbl_image_info)

        self.lbl_contour_info = QLabel("Контур: не выделен")
        self.lbl_contour_info.setWordWrap(True)
        info_layout.addWidget(self.lbl_contour_info)

        self.lbl_size_info = QLabel("Размеры: —")
        info_layout.addWidget(self.lbl_size_info)

        layout.addWidget(info_group)

        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Группа: настройки выделения
        options_group = QGroupBox("⚙️ Настройки выделения")
        options_layout = QVBoxLayout(options_group)

        # Ползунок детализации
        self.detail_label = QLabel("Детализация контура:")
        options_layout.addWidget(self.detail_label)

        self.detail_slider = QSlider(Qt.Horizontal)
        self.detail_slider.setRange(0, 100)
        self.detail_slider.setValue(75)  # 75 = epsilon 0.000075
        self.detail_slider.valueChanged.connect(self.on_detail_changed)
        options_layout.addWidget(self.detail_slider)

        self.detail_value_label = QLabel("Норма (~450-500 точек)")
        options_layout.addWidget(self.detail_value_label)

        # Флаги
        self.auto_orient_checkbox = QCheckBox("Авто-ориентация (ширина/высота)")
        self.auto_orient_checkbox.setChecked(True)
        options_layout.addWidget(self.auto_orient_checkbox)

        layout.addWidget(options_group)

        # Сохраняем текущее значение epsilon
        self.current_epsilon = 0.000075

        layout.addStretch()

        return widget

    def create_right_panel(self):
        """Правая панель — предпросмотр изображения"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.lbl_preview = QLabel("Загрузите изображение")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setStyleSheet("border: 1px solid gray; background-color: #f0f0f0;")
        self.lbl_preview.setMinimumHeight(400)
        layout.addWidget(self.lbl_preview)

        return widget

    def create_bottom_panel(self):
        """Нижняя панель — лог сообщений"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("📋 Лог операций:"))

        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setMaximumHeight(150)
        self.text_log.setFont(QFont("Consolas", 9))
        layout.addWidget(self.text_log)

        return widget

    def setup_menu(self):
        """Создаёт меню"""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("📁 Файл")

        open_action = file_menu.addAction("📂 Открыть...")
        open_action.triggered.connect(self.load_image)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("🚪 Выход")
        exit_action.triggered.connect(self.close)

        help_menu = menubar.addMenu("❓ Помощь")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self.show_about)

    def setup_statusbar(self):
        """Создаёт строку состояния"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Готов. Загрузите изображение шаблона")

    def log(self, message):
        """Добавляет сообщение в лог"""
        self.text_log.append(message)
        self.statusbar.showMessage(message)
        print(message)

    def load_image(self):
        """Загружает изображение"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите изображение шаблона",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp);;Все файлы (*.*)"
        )

        if file_path:
            self.current_image_path = file_path
            self.current_template = None

            # Показываем превью
            pixmap = QPixmap(file_path)
            scaled = pixmap.scaled(
                self.lbl_preview.width() - 20,
                self.lbl_preview.height() - 20,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.lbl_preview.setPixmap(scaled)

            # Обновляем информацию
            self.lbl_image_info.setText(f"Файл: {os.path.basename(file_path)}")
            self.lbl_contour_info.setText("Контур: не выделен")

            # Включаем кнопки
            self.btn_auto.setEnabled(True)
            self.btn_manual.setEnabled(True)
            self.btn_save.setEnabled(False)

            self.log(f"✅ Загружен: {file_path}")

    def get_real_sizes(self):
        """Получает реальные размеры из полей ввода"""
        width_cm = self.input_width.text().strip()
        height_cm = self.input_height.text().strip()

        width_mm = float(width_cm) * 10 if width_cm else None
        height_mm = float(height_cm) * 10 if height_cm else None

        if not width_mm and not height_mm:
            QMessageBox.warning(self, "Внимание", "Укажите хотя бы один реальный размер (ширина или высота)")
            return None, None

        return width_mm, height_mm

    def auto_extract(self):
        if not self.current_image_path:
            return

        width_mm, height_mm = self.get_real_sizes()
        if not width_mm and not height_mm:
            return

        self.log("🤖 Запуск автоматического выделения...")
        self.set_buttons_enabled(False)

        # Передаём текущее значение epsilon_factor
        self.worker = WorkerThread(
            mode='auto',
            image_path=self.current_image_path,
            width_mm=width_mm,
            height_mm=height_mm,
            epsilon_factor=self.current_epsilon  # ← новое
        )
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.error.connect(self.on_extraction_error)
        self.worker.progress.connect(self.log)
        self.worker.start()

    def manual_extract(self):
        """Ручная обрисовка контура"""
        if not self.current_image_path:
            return

        width_mm, height_mm = self.get_real_sizes()
        if not width_mm and not height_mm:
            return

        self.log("✏️ Запуск ручной обрисовки...")
        self.set_buttons_enabled(False)

        self.worker = WorkerThread('manual', self.current_image_path, width_mm, height_mm)
        self.worker.finished.connect(self.on_extraction_finished)
        self.worker.error.connect(self.on_extraction_error)
        self.worker.progress.connect(self.log)
        self.worker.start()

    def on_extraction_finished(self, template):
        """Обработчик успешного выделения"""
        self.current_template = template
        self.btn_save.setEnabled(True)

        bbox = template.get_bounding_box_mm()
        width = bbox[1] - bbox[0]
        height = bbox[3] - bbox[2]

        self.lbl_contour_info.setText(f"Контур: {len(template.contour.points)} точек")
        self.lbl_size_info.setText(f"Размеры: {width:.1f} x {height:.1f} мм")

        self.log(f"🎉 Готово! Контур содержит {len(template.contour.points)} точек")
        self.log(f"📐 Габариты в мм: {width:.1f} x {height:.1f}")

        self.set_buttons_enabled(True)

    def on_extraction_error(self, error_msg):
        """Обработчик ошибки"""
        self.log(f"❌ Ошибка: {error_msg}")
        QMessageBox.critical(self, "Ошибка", error_msg)
        self.set_buttons_enabled(True)

    def save_dxf(self):
        """Сохраняет DXF файл"""
        if not self.current_template:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить DXF файл",
            f"{self.current_template.name.replace('.png', '')}.dxf",
            "DXF файлы (*.dxf)"
        )

        if file_path:
            exporter = DXFExporter()
            success = exporter.export(self.current_template, file_path)

            if success:
                self.log(f"💾 DXF сохранён: {file_path}")
                QMessageBox.information(self, "Успех", f"DXF файл сохранён:\n{file_path}")
            else:
                self.log("❌ Ошибка сохранения DXF")
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить DXF")

    def set_buttons_enabled(self, enabled):
        """Включает/выключает кнопки"""
        self.btn_load.setEnabled(enabled)
        self.btn_auto.setEnabled(enabled and self.current_image_path is not None)
        self.btn_manual.setEnabled(enabled and self.current_image_path is not None)
        self.btn_save.setEnabled(enabled and self.current_template is not None)

        # Если уже выделен контур — не обновляем автоматически
    def show_about(self):
        """Показывает окно 'О программе'"""
        QMessageBox.about(
            self,
            "О программе",
            "Kovrik DXF Tool v1.0\n\n"
            "Конвертация шаблонов ковров из PNG в DXF\n"
            "Автоматическое и ручное выделение контура\n"
            "Экспорт в масштабе 1:1\n\n"
            "© 2025"
        )

    def on_detail_changed(self, value):
        """Обработчик изменения ползунка детализации"""
        if value == 0:
            self.current_epsilon = 0
            self.detail_value_label.setText("Оригинал (все точки, ~6000)")
        elif value <= 10:
            self.current_epsilon = 0.00001
            self.detail_value_label.setText("Максимальная (~2000 точек)")
        elif value <= 30:
            self.current_epsilon = 0.00003
            self.detail_value_label.setText("Очень детально (~1000 точек)")
        elif value <= 50:
            self.current_epsilon = 0.00005
            self.detail_value_label.setText("Детально (~700 точек)")
        elif value <= 75:
            self.current_epsilon = 0.000075
            self.detail_value_label.setText("Норма (~450-500 точек)")
        elif value <= 90:
            self.current_epsilon = 0.0001
            self.detail_value_label.setText("Средне (~380 точек)")
        else:
            self.current_epsilon = 0.0005
            self.detail_value_label.setText("Грубо (~60 точек)")