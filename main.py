import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QProgressBar, QStackedWidget, QFrame)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont

class TempGauge(QWidget):
    """Vertical temperature gauge with a dynamic warning color."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.temp = 45 
        self.setFixedWidth(60)
        self.setMinimumHeight(200)

    def set_temp(self, val):
        self.temp = min(max(val, 0), 120)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        padding = 20
        w = 12
        h = self.height() - (padding * 2)
        x = (self.width() - w) // 2
        y = padding
        
        painter.fillRect(x, y, w, h, QColor("#222222"))
        
        fill_h = int((self.temp / 120.0) * h)
        fill_y = y + h - fill_h
        
        if self.temp > 100: color = QColor("#FF0000") 
        elif self.temp > 80: color = QColor("#FFA500") 
        else: color = QColor("#00E5FF") 
        
        painter.fillRect(x, fill_y, w, fill_h, color)
        
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, f"{int(self.temp)}°C")
        painter.setFont(QFont("Arial", 8))
        painter.drawText(self.rect().adjusted(0, 5, 0, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, "TEMP")

class Speedometer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.accent_color = "#00E5FF"
        self.setMinimumSize(250, 250)

    def set_value(self, val, color):
        self.value = min(max(val, 0), 160) 
        self.accent_color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(10, 10, self.width() - 20, self.height() - 20)
        
        pen = QPen(QColor("#333333"), 15)
        painter.setPen(pen)
        painter.drawArc(rect, -30 * 16, 240 * 16)
        
        pen.setColor(QColor(self.accent_color))
        span_angle = int(-(self.value / 160.0) * 240 * 16)
        painter.setPen(pen)
        painter.drawArc(rect, 210 * 16, span_angle)
        
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Arial", 44, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.value)}")
        painter.setFont(QFont("Arial", 12))
        painter.drawText(rect.adjusted(0, 70, 0, 70), Qt.AlignmentFlag.AlignCenter, "km/h")

class NavXDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # State Management
        self.gear_status = "N"        
        self.selected_mode = "MOTOR"  
        self.is_engine_running = False
        self.current_speed = 0
        self.current_temp = 45
        self.show_gear_error = False # For start-up check
        
        self.color_electric = "#00FF66"
        self.color_engine = "#FF4400"
        self.current_theme_color = self.color_electric
        
        self.setWindowTitle("NavX Pro Dashboard")
        self.setFixedSize(800, 480)
        self.init_ui()
        self.update_dashboard()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        # Header
        header = QHBoxLayout()
        self.batt_bar = self.create_bar("ENERGY", self.color_electric)
        self.fuel_bar = self.create_bar("FUEL", "#FFD700")
        header.addLayout(self.batt_bar)
        header.addLayout(self.fuel_bar)
        self.main_layout.addLayout(header)

        # Center Stack
        self.stack = QStackedWidget()
        
        # Standby Page
        self.start_page = QFrame()
        start_lay = QVBoxLayout(self.start_page)
        self.alert_msg = QLabel("SYSTEM STANDBY\nPRESS [E] TO START")
        self.alert_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        start_lay.addWidget(self.alert_msg)
        
        # Dashboard Page
        self.dash_page = QFrame()
        dash_vlay = QVBoxLayout(self.dash_page)
        
        self.mode_label = QLabel("MOTOR ACTIVE")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setStyleSheet("font-size: 18px; font-weight: bold; letter-spacing: 2px;")
        
        gauge_hlay = QHBoxLayout()
        self.temp_gauge = TempGauge()
        self.speedometer = Speedometer()
        
        gauge_hlay.addStretch(1)
        gauge_hlay.addWidget(self.temp_gauge)
        gauge_hlay.addSpacing(30)
        gauge_hlay.addWidget(self.speedometer)
        gauge_hlay.addStretch(1)

        dash_vlay.addWidget(self.mode_label)
        dash_vlay.addLayout(gauge_hlay)
        
        self.stack.addWidget(self.start_page)
        self.stack.addWidget(self.dash_page)
        self.main_layout.addWidget(self.stack)

        # Footer
        footer = QHBoxLayout()
        self.gear_lbl = QLabel("GEAR: N")
        self.gear_lbl.setStyleSheet("font-size: 28px; font-weight: bold;")
        footer.addWidget(self.gear_lbl)
        footer.addStretch()
        footer.addWidget(QLabel("[E] Start | [N/F/R] Gears | [M] Mode", styleSheet="color: #888;"))
        self.main_layout.addLayout(footer)

    def create_bar(self, title, color):
        lay = QVBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 10px; color: #888;")
        lay.addWidget(lbl)
        
        bar = QProgressBar()
        bar.setFixedHeight(8)
        bar.setTextVisible(False)
        bar.setValue(85)
        bar.setStyleSheet(f"""
            QProgressBar {{ background-color: #222; border-radius: 4px; border: none; }} 
            QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}
        """)
        lay.addWidget(bar)
        return lay

    def keyPressEvent(self, event):
        key = event.key()

        # Engine Ignition Logic
        if key == Qt.Key.Key_E:
            if self.gear_status == "N":
                self.is_engine_running = not self.is_engine_running
                self.show_gear_error = False
                if not self.is_engine_running:
                    self.current_speed = 0
            else:
                self.show_gear_error = True # Trigger the error state

        # Gear Controls
        if key == Qt.Key.Key_N:
            self.gear_status = "N"
            if not self.is_engine_running:
                self.show_gear_error = False # Clear error if they move to N
            else:
                self.current_speed = 0
        
        # Only allow shifting to Drive/Reverse if engine is on
        elif self.is_engine_running:
            if key == Qt.Key.Key_F: self.gear_status = "F"
            if key == Qt.Key.Key_R: self.gear_status = "R"
        
        # Allow pre-selecting gear even if off (standard vehicle logic)
        elif not self.is_engine_running:
            if key == Qt.Key.Key_F: self.gear_status = "F"
            if key == Qt.Key.Key_R: self.gear_status = "R"

        # Mode Toggles
        if key == Qt.Key.Key_M:
            self.selected_mode = "ENGINE" if self.selected_mode == "MOTOR" else "MOTOR"
        
        # Speed/Temp simulation
        if self.is_engine_running and self.gear_status != "N":
            if key == Qt.Key.Key_Up: 
                self.current_speed += 5
                self.current_temp = min(120, self.current_temp + 1)
            if key == Qt.Key.Key_Down: 
                self.current_speed = max(0, self.current_speed - 5)
                self.current_temp = max(40, self.current_temp - 0.5)

        self.update_dashboard()

    def update_dashboard(self):
        # Handle Theme
        if self.selected_mode == "MOTOR":
            self.current_theme_color = self.color_electric
            bg = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #050505, stop:1 #001a0d)"
        else:
            self.current_theme_color = self.color_engine
            bg = "qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #050505, stop:1 #1a0500)"

        self.set_style_sheet_custom(bg)
        
        # Page Switching Logic
        if not self.is_engine_running:
            self.stack.setCurrentIndex(0)
            if self.show_gear_error:
                self.alert_msg.setText("⚠️ START ERROR\nSHIFT TO NEUTRAL BEFORE STARTING")
                self.alert_msg.setStyleSheet("color: #FF0000; font-size: 24px; font-weight: bold;")
            else:
                self.alert_msg.setText("SYSTEM STANDBY\nPRESS [E] TO START")
                self.alert_msg.setStyleSheet("color: #FFA500; font-size: 24px; font-weight: bold;")
        else:
            self.stack.setCurrentIndex(1)
            self.mode_label.setText(f"{self.selected_mode} ACTIVE")
            self.mode_label.setStyleSheet(f"color: {self.current_theme_color}; font-size: 18px; font-weight: bold;")
        
        self.gear_lbl.setText(f"GEAR: {self.gear_status}")
        self.gear_lbl.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {self.current_theme_color};")
        
        self.speedometer.set_value(self.current_speed, self.current_theme_color)
        self.temp_gauge.set_temp(self.current_temp)

    def set_style_sheet_custom(self, bg):
        self.setStyleSheet(f"QMainWindow {{ background-color: {bg}; }} color: #FFFFFF; font-family: 'Segoe UI';")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NavXDashboard()
    window.show()
    sys.exit(app.exec())