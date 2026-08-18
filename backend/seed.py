import os

from flask_migrate import upgrade

from app import create_app

# ... existing seed definitions remain unchanged above ...


if __name__ == "__main__":
    # Render currently invokes seed.py before gunicorn.  Run the schema upgrade
    # first so a fresh/behind Neon database has all application tables before
    # seed queries execute.  The seed process does not serve requests, so it
    # deliberately uses the development config while still using the real
    # DATABASE_URL supplied by Render/Neon.
    app = create_app("development")
    with app.app_context():
        print("Running database migrations...")
        upgrade()
        print("Database migrations complete.")

        summary = seed_demo_data()
        print("Seed complete:", summary)
