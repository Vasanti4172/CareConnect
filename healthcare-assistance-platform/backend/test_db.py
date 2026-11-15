
from sqlalchemy import text
from database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database()")
        )
        database_name = result.scalar()

        print("Database connected successfully!")
        print("Connected database:", database_name)

except Exception as error:
    print("Database connection failed!")
    print("Error:", error)
