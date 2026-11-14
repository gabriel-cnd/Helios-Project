from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit


class PanelGeometry(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        title = QLabel("<h2>Géométrie du panneau PV</h2>")
        layout.addWidget(title)

        form = QFormLayout()

        self.tilt = QLineEdit()
        self.azimuth = QLineEdit()
        self.area = QLineEdit()

        form.addRow("Inclinaison (°) :", self.tilt)
        form.addRow("Azimut (°) :", self.azimuth)
        form.addRow("Surface (m²) :", self.area)

        layout.addLayout(form)
        self.setLayout(layout)

    def get_tilt(self):
        try:
            return float(self.tilt.text())
        except Exception:
            return 0.0

    def get_azimuth(self):
        try:
            return float(self.azimuth.text())
        except Exception:
            return 180.0

    def get_area(self):
        """Retourne la surface totale des modules ; 1 m² par défaut."""

        try:
            value = float(self.area.text())
            if value <= 0:
                raise ValueError
            return value
        except Exception:
            return 1.0
