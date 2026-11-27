import joblib
import pandas as pd

from pathlib import Path


# Resolve paths relative to this Python file
BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR / "app" / "agents" / "fundamental_analysis_model.pkl"
)

DATA_PATH = BASE_DIR / "Data" / "financial_data.csv"


class FundamentalAnalysisAgent:

    def __init__(self):
        # Load the trained ML model
        bundle = joblib.load(MODEL_PATH)

        self.model = bundle["model"]
        self.features = bundle["features"]
        self.model_name = bundle["model_name"]

        # Load company financial data
        self.financial_df = pd.read_csv(DATA_PATH)

        # Normalize company names for searching
        self.financial_df["Company"] = (
            self.financial_df["Company"].astype(str).str.strip()
        )

        print("Fundamental Analysis Agent initialized!")
        print("Model:", self.model_name)
        print("Companies:", self.financial_df["Company"].nunique())

    @staticmethod
    def safe_number(value):
        if pd.isna(value):
            return None
        return round(float(value), 2)

    def analyze_company(self, company_name):

        # Find company records
        company_data = self.financial_df[
            self.financial_df["Company"].str.casefold()
            == company_name.strip().casefold()
        ].copy()

        if company_data.empty:
            raise ValueError(
                f"Company '{company_name}' was not found in the dataset."
            )

        # Select the latest available financial year
        company_data["Year"] = pd.to_numeric(
            company_data["Year"], errors="coerce"
        )

        company_data = company_data.dropna(subset=["Year"])
        company_data = company_data.sort_values("Year")

        if company_data.empty:
            raise ValueError("No valid financial-year records found.")

        latest = company_data.iloc[-1]

        # Verify required features exist
        missing_features = [
            col for col in self.features
            if col not in company_data.columns
        ]

        if missing_features:
            raise ValueError(
                f"Missing model features: {missing_features}"
            )

        # Prepare input in exactly the training feature order
        input_data = pd.DataFrame(
            [[pd.to_numeric(latest[col], errors="coerce")
              for col in self.features]],
            columns=self.features
        )

        # Generate prediction
        prediction = int(self.model.predict(input_data)[0])
        probabilities = self.model.predict_proba(input_data)[0]

        # Extract additional financial metrics
        metrics_columns = [
            "Sales",
            "Net profit",
            "Profit_Margin",
            "Operating_Margin",
            "ROE",
            "ROA",
            "Borrowings",
            "Debt_to_Equity",
            "Interest_Coverage",
            "Cash & Bank",
            "Cash from Operating Activity"
        ]

        financial_metrics = {}

        for column in metrics_columns:
            if column in latest.index:
                financial_metrics[column] = self.safe_number(
                    pd.to_numeric(latest[column], errors="coerce")
                )

        return {
            "company": latest["Company"],
            "financial_year": int(latest["Year"]),
            "prediction": (
                "Profit Decline Expected"
                if prediction == 1
                else "No Profit Decline Expected"
            ),
            "prediction_class": prediction,
            "no_decline_probability": round(
                float(probabilities[0]) * 100, 2
            ),
            "decline_probability": round(
                float(probabilities[1]) * 100, 2
            ),
            "model_name": self.model_name,
            "financial_metrics": financial_metrics
        }


# Create one reusable agent instance
fundamental_agent = FundamentalAnalysisAgent()