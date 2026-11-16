
from database import engine, Base
import models

# Create all tables defined in models.py
Base.metadata.create_all(bind=engine)

print("Users table created successfully!")
