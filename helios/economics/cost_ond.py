import pandas as pd


class OptimalInverter:
    """Determine the optimal inverter based on cost analysis and comparative data."""

    def __init__(self, csv_path="Comparatif de 10 onduleurs.csv"):
        """Load inverter comparison data."""
        self.df = pd.read_csv(csv_path)

    def select_optimal(self, project_specs, cost_panel_results):
        """
        Select optimal inverter based on project specs and cost analysis.

        Args:
            project_specs: dict with project requirements (power, voltage, etc.)
            cost_panel_results: dict with cost analysis results

        Returns:
            dict: optimal inverter specifications
        """
        # Filter inverters matching project power requirements
        power_range = project_specs.get("power_kwh", 10)
        compatible = self.df[
            (self.df["Puissance"] >= power_range * 0.8)
            & (self.df["Puissance"] <= power_range * 1.2)
        ].copy()

        if compatible.empty:
            raise ValueError("No compatible inverter found for project specs")

        # Score based on efficiency, cost, and reliability
        compatible["score"] = (
            compatible["Rendement"] * 0.5  # 50% efficiency
            + (1 / compatible["Coût"].max() * compatible["Coût"]) * 0.3  # 30% cost
            + compatible["Fiabilité"] * 0.2  # 20% reliability
        )

        optimal = compatible.loc[compatible["score"].idxmax()]
        return optimal.to_dict()

    def display_recommendation(self, optimal_inverter):
        """Display the recommended inverter."""
        print("=== ONDULEUR OPTIMAL RECOMMANDÉ ===")
        for key, value in optimal_inverter.items():
            print(f"{key}: {value}")


# Usage example
if __name__ == "__main__":
    inverter_selector = OptimalInverter()

    project_specs = {
        "power_kwh": 10,
        "voltage": 48,
    }

    cost_panel_results = {}  # Add your cost_panel results

    optimal = inverter_selector.select_optimal(project_specs, cost_panel_results)
    inverter_selector.display_recommendation(optimal)
