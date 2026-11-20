
from pathlib import Path
import sys
import unittest

# Make project modules accessible
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.copilot_engine import answer_question


class TestInsightPilotCopilot(unittest.TestCase):

    def test_01_database_exists(self):
        database = ROOT / "data" / "insightpilot.duckdb"
        self.assertTrue(database.exists())

    def test_02_executive_kpis(self):
        response = answer_question(
            "What are our total sales and profit?"
        )

        self.assertIn("1,661,105.99", response)
        self.assertIn("792,654.99", response)
        self.assertIn("15,000", response)
        self.assertIn("47.72%", response)

    def test_03_category_performance(self):
        response = answer_question(
            "Which category has the highest revenue?"
        )

        self.assertIn("CATEGORY PERFORMANCE", response)
        self.assertIn("Home", response)
        self.assertIn("494,709.46", response)

    def test_04_regional_profitability(self):
        response = answer_question(
            "Which region has the highest profit?"
        )

        self.assertIn("Alberta", response)
        self.assertIn("162,462.09", response)

    def test_05_sales_channel(self):
        response = answer_question(
            "Which sales channel performs best?"
        )

        self.assertIn("Retail Store", response)
        self.assertIn("565,525.48", response)

    def test_06_monthly_revenue(self):
        response = answer_question(
            "How is our monthly revenue trending?"
        )

        self.assertIn("80,485.56", response)
        self.assertIn("74,994.80", response)
        self.assertIn("+7.32%", response)

    def test_07_discount_anomaly(self):
        response = answer_question(
            "What happened to Electronics discounts "
            "in September 2026?"
        )

        self.assertIn("5.07%", response)
        self.assertIn("30.22%", response)
        self.assertIn("25.15 percentage points", response)

    def test_08_empty_question(self):
        response = answer_question("")

        self.assertIn(
            "Please enter a business question",
            response
        )

    def test_09_unsupported_question(self):
        response = answer_question(
            "What is inventory turnover?"
        )

        self.assertIn(
            "I can currently answer questions about",
            response
        )


if __name__ == "__main__":

    print("=" * 60)
    print("INSIGHTPILOT - AUTOMATED COPILOT VALIDATION")
    print("=" * 60)

    unittest.main(verbosity=2)
