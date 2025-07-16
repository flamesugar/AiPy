from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QSpinBox, QDoubleSpinBox)

class FilterSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Filter Settings")
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Low cutoff frequency
        low_layout = QHBoxLayout()
        low_layout.addWidget(QLabel("Low Cutoff (Hz):"))
        self.low_cutoff = QDoubleSpinBox()
        self.low_cutoff.setRange(0.1, 1000)
        self.low_cutoff.setValue(0.1)
        low_layout.addWidget(self.low_cutoff)
        layout.addLayout(low_layout)
        
        # High cutoff frequency
        high_layout = QHBoxLayout()
        high_layout.addWidget(QLabel("High Cutoff (Hz):"))
        self.high_cutoff = QDoubleSpinBox()
        self.high_cutoff.setRange(0.1, 1000)
        self.high_cutoff.setValue(10)
        high_layout.addWidget(self.high_cutoff)
        layout.addLayout(high_layout)
        
        # Filter order
        order_layout = QHBoxLayout()
        order_layout.addWidget(QLabel("Filter Order:"))
        self.order = QSpinBox()
        self.order.setRange(1, 8)
        self.order.setValue(4)
        order_layout.addWidget(self.order)
        layout.addLayout(order_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
    def get_settings(self):
        """Return the current filter settings"""
        return {
            'low_cutoff': self.low_cutoff.value(),
            'high_cutoff': self.high_cutoff.value(),
            'order': self.order.value()
        } 