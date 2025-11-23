from flask import Flask
from App.db import db, close_db

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:db_pass@localhost/wdi_project'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Session and Flash messages secret key for security (required)
    app.secret_key = "secret_key_wdi_team1"

    # Start the ORM
    db.init_app(app)

    app.teardown_appcontext(close_db)

    from App.routes.sustainability import sustainability_bp
    app.register_blueprint(sustainability_bp)

    from flask import redirect, url_for
    @app.route('/')
    def index():
        return redirect(url_for('sustainability.list_sustainability'))

    return app