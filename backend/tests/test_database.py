
from sqlalchemy import inspect


def test_isolated_database_creates_application_tables(test_engine):
    inspector = inspect(test_engine)

    tables = inspector.get_table_names()

    expected_tables = {
        "users",
        "user_preferences",
        "saved_stocks",
        "research_tasks",
        "research_reports"
    }

    assert expected_tables.issubset(set(tables))
