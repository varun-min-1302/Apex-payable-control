import os
import sys
from alembic import command
from alembic.config import Config
from sqlalchemy import text

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.session import engine

def reset_database() -> None:
    """Reset the database by dropping schemas cascade and running Alembic migrations."""
    print("Connecting to database to drop existing schemas...")
    with engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        for schema in ["audit", "ap", "procurement", "identity"]:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS public.alembic_version;"))
        print("Existing schemas and version table dropped.")

    print("Running Alembic migration to 'head'...")
    alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "migrations"))
    command.upgrade(alembic_cfg, "head")
    print("Database reset and migrated to head successfully!")

if __name__ == "__main__":
    reset_database()
