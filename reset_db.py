"""Drop all tables and reseed — dev convenience after a schema change.

Stop the running server first (so SQLite releases the file lock), then:

    python reset_db.py

This recreates the schema from the current models and reloads the demo data.
"""

from app.config.database import Base, engine, import_models
from seed import main as seed_main


def main() -> None:
    import_models()
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    seed_main()  # init_db (create_all) + seed admin + demo data


if __name__ == "__main__":
    main()
