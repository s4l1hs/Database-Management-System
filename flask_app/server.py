from flask import Flask
from app.views import register_views
from app.database import get_db



def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Initialize a database connection and store it in the app config.
    db = get_db()
    app.config["DB"] = db

    # Register all views (routes) with the Flask application.
    register_views(app)
    return app


if __name__ == "__main__":
    app = create_app()
    # Run the development server on localhost at port 8080.
    app.run(host="0.0.0.0", port=8080, debug=True)
