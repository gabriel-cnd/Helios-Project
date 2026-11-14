from PySide6.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure


class GraphWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(6, 4), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.ax = self.figure.add_subplot(111)

        self.ax.set_title("Graphique PV", fontsize=14, fontweight="bold")
        self.ax.grid(True, linestyle="--", alpha=0.4)

        toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(toolbar)
        layout.addWidget(self.canvas)

    # Efface totalement le graphique
    def clear(self):
        self.ax.clear()
        self.ax.set_title("Graphique PV", fontsize=14, fontweight="bold")
        self.ax.set_xlabel("Temps (h)", fontsize=12)
        self.ax.set_ylabel("Valeur", fontsize=12)
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.canvas.draw_idle()

    # Méthode : tracer une courbe (en effaçant les anciennes)
    def plot(self, x, y, label=""):
        self.clear()
        self.ax.plot(x, y, marker="o", linewidth=2, label=label)
        self.ax.set_xlabel("Temps (h)")

        if "Élévation" in label:
            self.ax.set_ylabel("Élévation (rad)")
        elif "Azimut" in label:
            self.ax.set_ylabel("Azimut (rad)")

        if label:
            self.ax.legend()

        self.canvas.draw_idle()

    # Ajouter une courbe supplémentaire
    def plot_add(self, x, y, label=""):
        self.ax.plot(x, y, linewidth=2, label=label)

        if label:
            self.ax.legend()

        self.canvas.draw_idle()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    w = GraphWidget()
    w.show()
    sys.exit(app.exec())
