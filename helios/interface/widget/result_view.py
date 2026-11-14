from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
)


class ResultsView(QWidget):
    energy_simulation_requested = Signal()

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        title = QLabel("<h2>Résultats</h2>")
        layout.addWidget(title)

        inst_title = QLabel("<h3>Résultats instantanés</h3>")
        layout.addWidget(inst_title)

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setText("Résultats du calcul s'afficheront ici…")

        layout.addWidget(self.text)

        layout.addWidget(QLabel("<h3>Météo</h3>"))
        self.weather_status = QLabel("Météo : aucune connexion.")
        self.weather_status.setWordWrap(True)
        layout.addWidget(self.weather_status)

        self.weather_details = QLabel("Aucune donnée météo.")
        self.weather_details.setWordWrap(True)
        layout.addWidget(self.weather_details)

        layout.addWidget(QLabel("<h3>Simulation énergétique</h3>"))

        self.energy_summary = QLabel(
            'Cliquez sur "Simuler" pour obtenir l\'énergie journalière, mensuelle et annuelle.'
        )
        self.energy_summary.setWordWrap(True)
        layout.addWidget(self.energy_summary)

        self.sim_btn = QPushButton("Simuler la production énergétique")
        self.sim_btn.clicked.connect(self.energy_simulation_requested.emit)
        layout.addWidget(self.sim_btn)

        self.loss_table = QTableWidget(0, 4)
        self.loss_table.setHorizontalHeaderLabels(
            [
                "Poste",
                "Pertes (%)",
                "Pertes (kWh)",
                "Énergie restante (kWh)",
            ]
        )
        header = self.loss_table.horizontalHeader()
        header.setStretchLastSection(True)
        self.loss_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.loss_table.verticalHeader().setVisible(False)
        layout.addWidget(self.loss_table)

        self.setLayout(layout)

    def set_text(self, text):
        self.text.setText(text)

    def set_weather_status(self, text: str, *, success: bool | None = True):
        color = "#9ab0d6"
        if success is False:
            color = "#d66"
        elif success is None:
            color = "#f6c177"
        self.weather_status.setText(f"<span style='color:{color}'>{text}</span>")

    def set_weather_details(self, data: dict | None):
        if not data:
            self.weather_details.setText("Aucune donnée météo.")
            return

        station = data.get("station", {})
        station_name = station.get("name", "Station inconnue")
        timestamp = data.get("timestamp", "--")
        temp = data.get("temperature")
        humidity = data.get("relative_humidity")
        wind = data.get("wind_speed")
        ghi = data.get("global_radiation")
        source = data.get("source", "")

        def fmt(value, unit=""):
            if value is None:
                return "--"
            return f"{value:.1f}{unit}"

        html = (
            f"<b>Station:</b> {station_name} ({source})<br>"
            f"<b>Horodatage:</b> {timestamp}<br>"
            f"Température: {fmt(temp, ' °C')} – Humidité: {fmt(humidity, ' %')}<br>"
            f"Vent: {fmt(wind, ' m/s')} – GHI: {fmt(ghi, ' W/m²')}"
        )
        self.weather_details.setText(html)

    def set_energy_results(self, data):
        """Affiche les énergies intégrées + le tableau de pertes."""

        energies = data.get("energies", {})

        def fmt(segment):
            chunk = energies.get(segment, {"net": 0.0, "raw": 0.0})
            return f"{chunk['net']:.1f} kWh (brut {chunk['raw']:.1f})"

        net_factor = data.get("net_factor", 1.0) * 100.0
        summary = (
            f"Énergie journalière : {fmt('daily')}\n"
            f"Énergie mensuelle : {fmt('monthly')}\n"
            f"Énergie annuelle : {fmt('annual')}\n"
            f"Facteur global après pertes : {net_factor:.1f} %"
        )
        self.energy_summary.setText(summary)

        losses = data.get("losses", [])
        final_energy = data.get("final_annual_energy", 0.0)
        self._populate_loss_table(losses, final_energy)

    def _populate_loss_table(self, losses, final_energy):
        rows = len(losses) + 1
        self.loss_table.setRowCount(rows)

        for idx, loss in enumerate(losses):
            self._set_table_item(idx, 0, loss.get("name", "-"))
            self._set_table_item(idx, 1, f"{loss.get('percent', 0.0):.1f}")
            self._set_table_item(idx, 2, f"{loss.get('loss_kwh', 0.0):.2f}")
            self._set_table_item(idx, 3, f"{loss.get('remaining_kwh', 0.0):.2f}")

        self._set_table_item(rows - 1, 0, "Énergie nette annuelle")
        self._set_table_item(rows - 1, 1, "-")
        self._set_table_item(rows - 1, 2, "-")
        self._set_table_item(rows - 1, 3, f"{final_energy:.2f}")

    def _set_table_item(self, row, col, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loss_table.setItem(row, col, item)
