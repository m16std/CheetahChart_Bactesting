from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFileDialog, QMessageBox, QDialog
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QDrag, QCursor, QPixmap, QIcon, QFont
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from PyQt5.QtCore import Qt, QSize
import time
import os
import sys

class PythonEditorWindow(QWidget):
    def __init__(self, file_path=None, parent=None, theme="dark"):
        super().__init__(parent)
        self.file_path = file_path
        self.theme = theme

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(2, 2, 2, 0) 
        self.layout.setSpacing(2)
        
        # Кнопки управления
        self.button_layout = QVBoxLayout()
        self.layout.addLayout(self.button_layout)

                # Create top buttons
        open_btn = QPushButton()
        open_btn.setIcon(self.recolor_svg_icon("resources/open.svg", Qt.gray))
        open_btn.setToolTip("Open Strategy")
        
        save_btn = QPushButton()
        save_btn.setIcon(self.recolor_svg_icon("resources/save.svg", Qt.gray))
        save_btn.setToolTip("Save Strategy")
        
        save_as_btn = QPushButton()
        save_as_btn.setIcon(self.recolor_svg_icon("resources/save-as.svg", Qt.gray))
        save_as_btn.setToolTip("Save As")
        
        run_btn = QPushButton()
        run_btn.setIcon(self.recolor_svg_icon("resources/play.svg", Qt.gray))
        run_btn.setToolTip("Test Code")

        # Common button style
        button_style = """
            QPushButton {
                border: none;
                padding: 3px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """
        
        for btn in [open_btn, save_btn, save_as_btn, run_btn]:
            btn.setStyleSheet(button_style)
            btn.setFixedSize(32, 32)
            btn.setIconSize(QSize(20, 20))  
            self.button_layout.addWidget(btn)

        self.button_layout.addStretch()

        # Settings button at bottom
        settings_btn = QPushButton()
        settings_btn.setIcon(self.recolor_svg_icon("resources/settings.svg", Qt.gray))
        settings_btn.setToolTip("Settings")
        settings_btn.setStyleSheet(button_style)
        settings_btn.setFixedSize(32, 32)
        settings_btn.setIconSize(QSize(20, 20)) 
        self.button_layout.addWidget(settings_btn)

        # Connect signals
        open_btn.clicked.connect(self.open_file)
        save_btn.clicked.connect(self.save_file)
        run_btn.clicked.connect(self.test_file)
        save_as_btn.clicked.connect(self.save_file_as)

        self.editor = QsciScintilla(self)
        lexer = QsciLexerPython()
        self.editor.setLexer(lexer)
        # Используем системный моноширинный шрифт
        self.editor.setFont(QFont("Menlo" if sys.platform == "darwin" else "Consolas", 12))
        self.editor.setMarginsFont(QFont("Menlo" if sys.platform == "darwin" else "Consolas", 10))
        self.editor.setMarginWidth(0, 30)  
        self.editor.setMarginLineNumbers(0, True)
        self.editor.setBraceMatching(QsciScintilla.SloppyBraceMatch) 
        self.editor.setAutoIndent(True)  # Auto indentation
        self.apply_theme(self.theme) 

        self.layout.addWidget(self.editor)

        # Загрузка содержимого файла
        if self.file_path:
            self.load_file()

        self.apply_theme(self.theme)



    def recolor_svg_icon(self, svg_path, color):
        renderer = QSvgRenderer(svg_path)
        pixmap = QPixmap(96, 96)  # Увеличиваем размер создаваемой иконки для лучшего качества
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)  # Добавляем сглаживание
        painter.setRenderHint(QPainter.SmoothPixmapTransform)  # Добавляем сглаживание при трансформации
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()

        return QIcon(pixmap)

    def load_file(self):
        """Загружает содержимое файла в редактор."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                self.editor.setText(file.read())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {e}")
            try:
                with open(self.file_path, "w", encoding="utf-8") as file:
                    file.write(self.editor.toPlainText())
                QMessageBox.information(self, "Успех", "Файл успешно сохранен.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def save_file(self):
        """Сохраняет текущий файл."""
        if not self.file_path:
            self.save_file_as()
            return

        try:
            with open(self.file_path, "w", encoding="utf-8") as file:
                file.write(self.editor.text())
            QMessageBox.information(self, "Успех", "Файл успешно сохранен.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def save_file_as(self):
        """Сохраняет файл под новым именем."""
        new_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл как", "", "Python Files (*.py)")
        if new_path:
            self.file_path = new_path
            self.save_file()

    def find_trading_app_parent(self):
        """Находит родительский TabManager"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'editors_requested'):
                return parent
            parent = parent.parent()
        return None

    def test_file(self):
        """Тестирует стратегию в выбранном редакторе."""
        if not self.file_path:
            self.save_file_as()
            if not self.file_path:  # Если пользователь отменил сохранение
                return

        # Находим TabManager
        tab_manager = self.find_trading_app_parent()
        if not tab_manager:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти TabManager")
            return

        # Получаем список редакторов
        trading_apps = tab_manager.get_trading_editors()

        # Если нет открытых редакторов, создаем новый
        if not trading_apps:
            new_tab = tab_manager.handle_tab_selection("strategy")  # Создаем новый редактор напрямую
            if new_tab:
                # Сохраняем текущий список стратегий
                old_strategies = set(new_tab.strat_input.items())
                
                # Сохраняем файл в папку стратегий
                strategy_path = os.path.join("strategies", f"strategy_{int(time.time())}.py")
                os.makedirs("strategies", exist_ok=True)
                try:
                    with open(strategy_path, "w", encoding="utf-8") as file:
                        file.write(self.editor.text())
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить стратегию: {e}")
                    return

                # Обновляем список и находим новую стратегию
                new_tab.load_external_strategies()
                new_strategies = set(new_tab.strat_input.items())
                added_strategy = list(new_strategies - old_strategies)
                
                if added_strategy:
                    strategy_index = new_tab.strat_input.findText(added_strategy[0])
                    if strategy_index >= 0:
                        new_tab.strat_input.setCurrentIndex(strategy_index)
                        new_tab.run_strategy()
            return

        # Показываем диалог выбора редактора
        from lib.managers.test_strategy_dialog import TestStrategyDialog
        dialog = TestStrategyDialog(trading_apps)
        result = dialog.exec_()

        if result == QDialog.Rejected:
            return

        # Определяем целевой редактор
        if result > len(trading_apps):  # Создание нового редактора
            tab_manager.add_new_tab()
            return

        target_app = trading_apps[result - 1]
        
        # Сохраняем текущий список стратегий
        old_strategies = set()
        for i in range(target_app.strat_input.count()):
            old_strategies.add(target_app.strat_input.itemText(i))
        
        # Сохраняем файл в папку стратегий
        strategy_path = os.path.join("strategies", f"strategy_{int(time.time())}.py")
        os.makedirs("strategies", exist_ok=True)
        try:
            with open(strategy_path, "w", encoding="utf-8") as file:
                file.write(self.editor.text())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить стратегию: {e}")
            return

        # Обновляем список и находим новую стратегию
        target_app.load_external_strategies()
        new_strategies = set()
        for i in range(target_app.strat_input.count()):
            new_strategies.add(target_app.strat_input.itemText(i))

        added_strategy = list(new_strategies - old_strategies)
        
        if added_strategy:
            strategy_index = target_app.strat_input.findText(added_strategy[0])
            if strategy_index >= 0:
                target_app.strat_input.setCurrentIndex(strategy_index)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось найти добавленную стратегию в списке.")

    def apply_theme(self, theme):
        """Apply light or dark theme to the editor."""
        self.theme = theme
        lexer = QsciLexerPython()  # Create a new lexer instance to ensure proper re-application
        if theme == "dark":
            background_color = QColor("#151924")
            text_color = QColor("#FFFFFF")
            keyword_color = QColor("#FFCC00")
            comment_color = QColor("#FF6666")
            string_color = QColor("#66CC66")
            number_color = QColor("#66CCFF")
        else:
            background_color = QColor("#FFFFFF")
            text_color = QColor("#000000")
            keyword_color = QColor("#0077CC")
            comment_color = QColor("#999999")
            string_color = QColor("#008800")
            number_color = QColor("#CC0000")

        # Apply editor-wide colors
        self.editor.setPaper(background_color)  # Background color
        self.editor.setColor(text_color)  # Text color
        self.editor.setCaretForegroundColor(text_color)  # Caret color
        self.editor.setMarginsBackgroundColor(background_color)  # Margin background
        self.editor.setMarginsForegroundColor(QColor("#AAAAAA") if theme == "dark" else QColor("#555555"))  # Margin text color

        # Update lexer colors for all token types
        lexer.setDefaultPaper(background_color)
        lexer.setDefaultColor(text_color)
        lexer.setColor(text_color, QsciLexerPython.Default)
        lexer.setColor(keyword_color, QsciLexerPython.Keyword)
        lexer.setColor(comment_color, QsciLexerPython.Comment)
        lexer.setColor(string_color, QsciLexerPython.DoubleQuotedString)
        lexer.setColor(string_color, QsciLexerPython.SingleQuotedString)
        lexer.setColor(number_color, QsciLexerPython.Number)
        lexer.setColor(text_color, QsciLexerPython.Operator)
        lexer.setColor(text_color, QsciLexerPython.Identifier)
        lexer.setColor(comment_color, QsciLexerPython.CommentBlock)
        lexer.setColor(string_color, QsciLexerPython.TripleSingleQuotedString)
        lexer.setColor(string_color, QsciLexerPython.TripleDoubleQuotedString)

        # Ensure no background color is applied to symbols
        lexer.setPaper(background_color)

        # Re-apply the lexer to ensure syntax highlighting is preserved
        self.editor.setLexer(lexer)

        # Refresh the existing text to apply the new theme and syntax highlighting
        current_text = self.editor.text()
        self.editor.clear()
        self.editor.setText(current_text)

    def open_file(self):
        """Открывает файл Python."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл Python", "", "Python Files (*.py)")
        if file_path:
            self.file_path = file_path
            self.load_file()
