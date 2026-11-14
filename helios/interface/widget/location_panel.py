from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QComboBox,
    QHBoxLayout,
)
from PySide6.QtCore import Signal
from datetime import datetime
from helios.calculus.sun import get_sun_position


class LocationPanel(QWidget):
    # Signal qui émet un dictionnaire {"azimuth": x, "elevation": y}
    sun_position_computed = Signal(dict)
    simulate_day = Signal(dict)  # Signal pour simuler une journée complète

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        title = QLabel("<h2>Paramètres de localisation</h2>")
        layout.addWidget(title)

        form = QFormLayout()
        self.lat = QLineEdit()
        self.lon = QLineEdit()

        self.lat.setPlaceholderText("Exemple : 46.5")
        self.lon.setPlaceholderText("Exemple : 6.6")

        form.addRow("Latitude (°) :", self.lat)
        form.addRow("Longitude (°) :", self.lon)

        layout.addLayout(form)

        layout.addWidget(QLabel("<h3>Source météo</h3>"))
        self.weather_combo = QComboBox()
        self.weather_combo.addItem("Ciel clair (offline)", userData="clear_sky")
        self.weather_combo.addItem("MeteoSwiss (temps réel)", userData="meteoswiss")
        layout.addWidget(self.weather_combo)

        buttons_row = QHBoxLayout()
        self.submit_btn = QPushButton("Calculer la position du soleil")
        self.submit_btn.clicked.connect(self.compute_sun_position)
        buttons_row.addWidget(self.submit_btn)

        self.sim_button = QPushButton("Simuler la journée")
        buttons_row.addWidget(self.sim_button)

        layout.addLayout(buttons_row)
        self.setLayout(layout)

        self.sim_button.clicked.connect(self.emit_simulation_request)

    def compute_sun_position(self):
        """Called when the user clicks the button."""
        try:
            latitude = float(self.lat.text())
            longitude = float(self.lon.text())
        except ValueError:
            QMessageBox.warning(
                self, "Erreur", "Veuillez entrer des valeurs numériques valides."
            )
            return

        now = datetime.now()
        pos = get_sun_position(now, latitude, longitude)

        # émet la position du soleil à la fenêtre principale
        self.sun_position_computed.emit(pos)

    def emit_simulation_request(self):
        """Émet un signal pour simuler une journée complète."""
        try:
            latitude = float(self.lat.text())
            longitude = float(self.lon.text())
        except ValueError:
            print("Erreur : latitude ou longitude invalide")
            return

        date = datetime.now().date()  # journée actuelle
        self.simulate_day.emit({"lat": latitude, "lon": longitude, "date": date})

    def get_coordinates(self):
        """Retourne la latitude/longitude saisies par l'utilisateur."""

        latitude = float(self.lat.text())
        longitude = float(self.lon.text())
        return latitude, longitude

    def get_weather_source(self) -> str:
        """Renvoie la source météo choisie."""

        data = self.weather_combo.currentData()
        return data or "clear_sky"
