import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.models.user import db
from src.routes.auth import auth_bp
from src.routes.agency import agency_bp
from src.routes.client import client_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ai-growth-secret-key-2025')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'ai-growth-jwt-secret-2025')

# Enable CORS for frontend-backend communication
CORS(app, origins="*")

# Initialize JWT
jwt = JWTManager(app)

# Database configuration - Railway MySQL
if os.getenv('DATABASE_URL'):
    # Railway provides DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
elif os.getenv('DB_HOST'):
    # Use individual Railway variables
    db_user = os.getenv('DB_USERNAME', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'railway')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
else:
    # Local development fallback
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(agency_bp, url_prefix='/api/agency')
app.register_blueprint(client_bp, url_prefix='/api/client')

# Health check endpoint
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'service': 'AI.GROWTH Backend'}, 200

# Create tables
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database error: {e}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
