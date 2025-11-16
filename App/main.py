# main.py
from flask import Flask, redirect, url_for
from routes.health import health_bp 

def create_app():
    app = Flask(__name__)

    #ENDPOINTS
    app.register_blueprint(health_bp, url_prefix="/health")# Health ENDPOINTS

    @app.route("/")
    def index():
        return redirect(url_for("health.list_health"))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
