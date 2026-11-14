
from dotenv import load_dotenv

# Load backend environment variables
load_dotenv()

import database
import models


def setup_database():
    print("Connecting to database...")

    try:
        # Create any tables that do not already exist.
        models.Base.metadata.create_all(bind=database.engine)

        print("Database connection successful.")
        print("Database tables initialized successfully.")

    except Exception as error:
        print("Database setup failed.")
        print(f"Error: {error}")
        raise

    finally:
        database.engine.dispose()


if __name__ == "__main__":
    setup_database()
