#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from stock_picker.crew import StockPicker

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

requirements = """
A simple account management system for a trading simulation platform.

The system should allow users to:
1. Create an account.
2. Deposit funds.
3. Withdraw funds.
4. Buy and sell shares by providing a stock symbol and quantity.
5. View their current stock holdings.
6. View the total value of their portfolio.
7. View profit or loss compared with their initial deposit.
8. View their transaction history.

The system must enforce these rules:
- Users cannot withdraw more money than their available cash balance.
- Users cannot buy shares they cannot afford.
- Users cannot sell more shares than they own.

The application must use SQLite for persistent storage.

The application has access to a get_share_price(symbol) function
that returns fixed test prices for AAPL, TSLA, and GOOGL.

Backend: Python and FastAPI.
Frontend: Streamlit.
Database: SQLite.
Testing: pytest.
"""

def run():
    """
    Run the crew.
    """
    
    inputs = {
         "requirements": requirements
    }

    try:
        StockPicker().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "requirements": requirements
    }
    try:
        StockPicker().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        StockPicker().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
         "requirements": requirements
    }

    try:
        StockPicker().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": "",
        "current_year": ""
    }

    try:
        result = StockPicker().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
