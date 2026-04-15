"""Entry point for the Local Waste Services application.

Run with:  python main.py [--seed] [--test]
  --seed   Populate the database with sample data before launching the CLI.
  --test   Run the pytest test suite instead of the CLI.
"""
import sys
import os

# Ensure project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    args = sys.argv[1:]

    if "--test" in args:
        import pytest
        sys.exit(pytest.main(["-v", "tests/"]))

    if "--seed" in args:
        from utils.seed_data import seed
        seed()

    from ui.cli import main as run_cli
    run_cli()


if __name__ == "__main__":
    main()
