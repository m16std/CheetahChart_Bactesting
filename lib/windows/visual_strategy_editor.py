from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                           QListWidgetItem, QPushButton, QScrollArea, QLabel, QApplication, QFrame, QSizePolicy, QSplitter)
from PyQt5.QtCore import Qt, QMimeData, QPointF, QRectF, pyqtSignal, QPoint, QSize
from PyQt5.QtGui import QPainter, QPainterPath, QPen, QColor, QDrag, QCursor, QPixmap, QIcon
from PyQt5.QtSvg import QSvgRenderer
from ..strategy_constructor.block_model import StrategyModel, Block, BlockPort
from ..strategy_constructor.blocks import BLOCK_REGISTRY
from ..strategy_constructor.code_generator import CodeGenerator
from NodeGraphQt import NodeGraph, constants
from ..strategy_constructor.node_blocks import StrategyNode

class BlockWidget(QWidget):
    connection_started = pyqtSignal(str, QPointF, object)
    connection_ended = pyqtSignal(str, QPointF, object)  

    def __init__(self, block_type: str, parent=None):
        super().__init__(parent)
        self.block_type = block_type
        self.block_def = BLOCK_REGISTRY[block_type]()
        self.setFixedSize(150, 80)
        self.setAcceptDrops(True)
        self.input_ports = []
        self.output_ports = []
        self.connections = []
        self.drag_start_position = None
        self.is_dragging_connection = False
        self.port_dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.fillRect(self.rect(), QColor("#2d2d2d"))
        painter.setPen(QPen(Qt.white))
        painter.drawText(self.rect(), Qt.AlignCenter, self.block_type)

        port_size = 8
        input_spacing = self.height() / (len(self.block_def.get_inputs()) + 1)
        output_spacing = self.height() / (len(self.block_def.get_outputs()) + 1)

        for i, port in enumerate(self.block_def.get_inputs(), 1):
            y = int(i * input_spacing)
            painter.setBrush(Qt.white)
            painter.drawEllipse(0, y - port_size//2, port_size, port_size)
        for i, port in enumerate(self.block_def.get_outputs(), 1):
            y = int(i * output_spacing)
            painter.setBrush(Qt.white)
            painter.drawEllipse(self.width() - port_size, y - port_size//2, 
                              port_size, port_size)
        painter.end()  

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            for port in self.get_port_rects():
                if port['rect'].contains(event.pos()):
                    self.port_dragging = True
                    port_pos = self.get_port_position(port['id'])
                    global_pos = self.mapToParent(port_pos)
                    self.connection_started.emit(port['id'], QPointF(global_pos), self)
                    event.accept()
                    return
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if self.port_dragging:
            # Обновляем позицию связи при перетаскивании
            event.accept()
            return

        # Существующий код для перетаскивания блока
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self.drag_start_position:
            return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return

        # Move the widget to new position
        new_pos = self.mapToParent(event.pos() - self.drag_start_position)
        self.move(new_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.port_dragging:
            self.port_dragging = False
            # Проверяем, находится ли курсор над портом
            port_hit = False
            for port in self.get_port_rects():
                if port['rect'].contains(event.pos()):
                    port_pos = self.get_port_position(port['id'])
                    global_pos = self.mapToParent(port_pos)
                    self.connection_ended.emit(port['id'], QPointF(global_pos), self)
                    port_hit = True
                    break
            
            # Если отпустили не над портом - отменяем соединение
            if not port_hit:
                self.connection_ended.emit('', QPointF(), None)
            
            event.accept()
            return

        self.drag_start_position = None
        super().mouseReleaseEvent(event)

    def get_port_rects(self):
        """Get rectangles for all ports for hit testing"""
        rects = []
        port_size = 8
        input_spacing = self.height() / (len(self.block_def.get_inputs()) + 1)
        output_spacing = self.height() / (len(self.block_def.get_outputs()) + 1)

        for i, port in enumerate(self.block_def.get_inputs(), 1):
            y = i * input_spacing
            rects.append({
                'id': f'in_{port}',
                'rect': QRectF(0, y - port_size/2, port_size, port_size)
            })

        for i, port in enumerate(self.block_def.get_outputs(), 1):
            y = i * output_spacing 
            rects.append({
                'id': f'out_{port}',
                'rect': QRectF(self.width() - port_size, y - port_size/2,
                              port_size, port_size)
            })

        return rects

    def get_port_position(self, port_id):
        """Get actual port position in widget coordinates"""
        port_size = 8
        is_input = port_id.startswith('in_')
        
        if is_input:
            x = 0
            ports = self.block_def.get_inputs()
            spacing = self.height() / (len(ports) + 1)
            idx = ports.index(port_id[3:]) + 1 
        else:
            x = self.width() - port_size
            ports = self.block_def.get_outputs()
            spacing = self.height() / (len(ports) + 1)
            idx = ports.index(port_id[4:]) + 1  
            
        y = int(idx * spacing)
        return QPoint(x + port_size//2, y)

class CanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(2000, 1000)
        self.connections = []
        self.current_connection = None
        self.dragging = False
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        if self.dragging and self.current_connection:
            # Обновляем позицию курсора для отрисовки линии
            self.current_cursor_pos = event.pos()
            self.update()
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Рисуем существующие соединения
        for conn in self.connections:
            start_block = conn['start_block']
            end_block = conn['end_block']
            
            # Получаем позиции в координатах холста
            start_global = start_block.mapToGlobal(start_block.rect().center())
            end_global = end_block.mapToGlobal(end_block.rect().center())
            
            start_pos = self.mapFromGlobal(start_global)
            end_pos = self.mapFromGlobal(end_global)
            
            self.draw_connection(painter, start_pos, end_pos)

        # Рисуем создаваемое соединение
        if self.dragging and self.current_connection and hasattr(self, 'current_cursor_pos'):
            start_block = self.current_connection['start_block']
            start_global = start_block.mapToGlobal(start_block.rect().center())
            start_pos = self.mapFromGlobal(start_global)
            self.draw_connection(painter, start_pos, self.current_cursor_pos)

    def draw_connection(self, painter, start_pos, end_pos):
        path = QPainterPath()
        path.moveTo(start_pos)
        
        dx = end_pos.x() - start_pos.x()
        ctrl1 = QPointF(start_pos.x() + dx * 0.5, start_pos.y())
        ctrl2 = QPointF(start_pos.x() + dx * 0.5, end_pos.y())
        
        path.cubicTo(ctrl1, ctrl2, end_pos)
        painter.strokePath(path, QPen(Qt.white, 2))

class VisualStrategyEditor(QWidget):
    theme_changed = pyqtSignal(str)  

    def __init__(self, theme="dark", parent=None):
        super().__init__(parent)
        self.current_theme = theme
        self.model = StrategyModel()
        self.buttons = {}
        self.initUI()
        self.apply_theme(theme)

    def initUI(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStretchFactor(1, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setMinimumWidth(120)
        scroll.setMaximumWidth(250)
        self.scroll_content = QWidget()
        self.scroll_content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        scroll_layout = QVBoxLayout(self.scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(5)

        for category, blocks in BLOCK_REGISTRY.items():
            category_frame = QFrame()
            category_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            category_frame.setFrameShape(QFrame.StyledPanel)
            category_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    padding: 3px;
                }
            """)
            
            category_layout = QVBoxLayout(category_frame)
            category_layout.setContentsMargins(0, 0, 0, 0)
            category_layout.setSpacing(1)
            
            header_frame = QFrame()
            header_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            header_frame.setCursor(Qt.PointingHandCursor)
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 0)
            
            title = QLabel(f"▼ {category}")
            title.setStyleSheet("font-size: 14px; font-weight: bold; color: #669FD3;")
            header_layout.addWidget(title)
            
            category_layout.addWidget(header_frame)
            
            block_list = QListWidget()
            block_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            block_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            block_list.setStyleSheet("""
                QListWidget {
                    background: transparent;
                    border: none;
                }
                QListWidget::item {
                    color: white;
                    padding: 5px;
                    font-size: 12px;
                }
                QListWidget::item:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }
            """)
            
            for block_name, block_class in blocks.items():
                item = QListWidgetItem(block_name)
                item.setData(Qt.UserRole, block_name)
                block_list.addItem(item)
            
            item_height = 30 
            total_height = len(blocks) * item_height
            block_list.setFixedHeight(total_height)
            
            category_layout.addWidget(block_list)
            scroll_layout.addWidget(category_frame)
        
            header_frame.mousePressEvent = lambda e, w=block_list, t=title: self.toggle_category(w, t)
            block_list.itemDoubleClicked.connect(self.create_block_from_library)

        scroll.setWidget(self.scroll_content)
        self.splitter.addWidget(scroll)

        self.graph = NodeGraph()
        self.graph_widget = self.graph.widget
        self.splitter.addWidget(self.graph_widget)

        for category, blocks in BLOCK_REGISTRY.items():
            for block_name, block_class in blocks.items():
                node_class = type(
                    block_name, 
                    (StrategyNode,),
                    {
                        'NODE_NAME': block_name,
                        'block_type': block_name,
                        '__identifier__': 'examples.nodes'
                    }
                )
                self.graph.register_node(node_class)

        controls = QVBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(2)

        button_configs = {
            'open': ("resources/open.svg", "Open Strategy"),
            'save': ("resources/save.svg", "Save Strategy"),
            'search': ("resources/search.svg", "Find Node"),
            'run': ("resources/play.svg", "Generate Code"),
            'settings': ("resources/settings.svg", "Settings")
        }

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
        
        controls = QVBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(2)

        for btn_id, (icon_path, tooltip) in button_configs.items():
            self.buttons[btn_id] = QPushButton()
            btn = self.buttons[btn_id]
            btn.icon_path = icon_path  
            btn.setIcon(self.recolor_svg_icon(icon_path, Qt.gray))
            btn.setToolTip(tooltip)
            btn.setStyleSheet(button_style)
            btn.setFixedSize(32, 32)
            btn.setIconSize(QSize(20, 20))
            if btn_id != 'settings':
                controls.addWidget(btn)

        controls.addStretch()
        controls.addWidget(self.buttons['settings'])

        # Connect signals
        self.buttons['open'].clicked.connect(self.load_strategy)
        self.buttons['save'].clicked.connect(self.save_strategy)
        self.buttons['run'].clicked.connect(self.generate_code)
        
        layout.addLayout(controls)
        layout.addWidget(self.splitter)
        self.setLayout(layout)

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

    def toggle_category(self, widget, title_label):
        """Toggle category list visibility and update arrow"""
        if widget.isVisible():
            widget.hide()
            title_label.setText(f"▶ {title_label.text()[2:]}") 
        else:
            widget.show()
            title_label.setText(f"▼ {title_label.text()[2:]}")

    def create_block_from_library(self, item):
        """Create a new block when double-clicking a library item"""
        block_name = item.text()
        
        try:
            node = self.graph.create_node(f'examples.nodes.{block_name}')
            cursor_pos = self.graph_widget.mapFromGlobal(QCursor.pos())
            try:
                node.set_pos(cursor_pos.x(), cursor_pos.y())
            except (AttributeError, TypeError):
                try:
                    node.setPos(cursor_pos.x(), cursor_pos.y())
                except (AttributeError, TypeError):
                    print(f"Warning: Could not position node {block_name}")
            
            print(f"Created node: {node}")
        except Exception as e:
            print(f"Error creating node: {str(e)}")

    def save_strategy(self):
        """Save the current node graph"""
        self.graph.save_session('strategy.json')

    def load_strategy(self):
        """Load a saved node graph"""
        self.graph.clear()
        self.graph.load_session('strategy.json')

    def generate_code(self):
        """Generate Python code from the node graph"""
        nodes = self.graph.all_nodes()
        connections = []
        
        for node in nodes:
            for port in node.input_ports():
                if port.connected_ports():
                    for connected in port.connected_ports():
                        connections.append({
                            'from_node': connected.node().name(),
                            'from_port': connected.name(),
                            'to_node': node.name(),
                            'to_port': port.name()
                        })

        generator = CodeGenerator(self.model)
        code = generator.generate_from_graph(nodes, connections)
        print(code)

    def apply_theme(self, theme):
        """Apply theme to all visual components, including NodeGraphQt."""
        self.current_theme = theme
        icon_color = Qt.white if theme == "dark" else Qt.black
        background_color = "#151924" if theme == "dark" else "#ffffff"
        text_color = "#ffffff" if theme == "dark" else "#000000"
        hover_color = "rgba(255, 255, 255, 0.1)" if theme == "dark" else "rgba(0, 0, 0, 0.1)"
        graph_border_color = "#ffffff" if theme == "light" else Qt.black

        button_style = f"""
            QPushButton {{
                border: none;
                padding: 4px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

        for btn in self.buttons.values():
            if hasattr(btn, 'icon_path'):
                btn.setIcon(self.recolor_svg_icon(btn.icon_path, icon_color))
            btn.setStyleSheet(button_style)

        category_frame_style = f"""
            QFrame {{
                background-color: {background_color};
                border-radius: 8px;
                padding: 3px;
            }}
        """

        list_style = f"""
            QListWidget {{
                background: transparent;
                border: none;
            }}
            QListWidget::item {{
                color: {text_color};
                padding: 5px;
                font-size: 12px;
            }}
            QListWidget::item:hover {{
                background: {hover_color};
                border-radius: 4px;
            }}
        """

        for i in range(self.scroll_content.layout().count()):
            widget = self.scroll_content.layout().itemAt(i).widget()
            if isinstance(widget, QFrame):
                widget.setStyleSheet(category_frame_style)
                for child in widget.findChildren(QListWidget):
                    child.setStyleSheet(list_style)


        if theme == "dark":
            self.graph.set_background_color(21, 25, 36) 
            self.graph.set_grid_color(50, 50, 50)       
        else:
            self.graph.set_background_color(255, 255, 255)
            self.graph.set_grid_color(200, 200, 200)    


        self.graph_widget.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid {graph_border_color};
                    border-radius: 4px;
                }}
            """)
        
        for node in self.graph.all_nodes():
            if isinstance(node, StrategyNode):
                node.update_theme(theme)
                print('recolor')

        self.theme_changed.emit(theme) 
