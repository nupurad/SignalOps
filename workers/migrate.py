from sqlalchemy import create_engine, text
import os

from models import Base

engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS check_results;"))
    conn.commit()

Base.metadata.create_all(engine)

with engine.connect() as conn:
    conn.execute(
        text(
            """
            SELECT create_hypertable(
                'check_results', 'checked_at',
                if_not_exists => TRUE
            );
            """
        )
    )
    conn.commit()

print("Migration complete.")
