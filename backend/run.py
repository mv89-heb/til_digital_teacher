import os

from app import create_app

# The Gunicorn/Render process is a production process. Do not let the
# application factory silently fall back to DevelopmentConfig when FLASK_ENV
# is missing; that would also load development CORS settings in production.
app = create_app(os.getenv("FLASK_ENV", "production"))

if __name__ == "__main__":
    app.run(debug=False, port=int(os.getenv("PORT", "5000")))
