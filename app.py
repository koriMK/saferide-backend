from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

# Initialize extensions
jwt = JWTManager()

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "safedrive.db")}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'connect_args': {'check_same_thread': False} if 'sqlite' in os.environ.get('DATABASE_URL', '') else {}
    }
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Initialize extensions
    from models import db
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # Create tables and handle migrations
    with app.app_context():
        try:
            db.create_all()
            
            # Handle database migrations - remove problematic columns
            try:
                with db.engine.connect() as conn:
                    # Check if problematic columns exist and remove them
                    result = conn.execute(db.text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' AND column_name IN ('is_online', 'last_seen');
                    """))
                    existing_columns = [row[0] for row in result]
                    
                    # Remove problematic columns
                    if 'is_online' in existing_columns:
                        conn.execute(db.text("ALTER TABLE users DROP COLUMN is_online;"))
                        conn.commit()
                    
                    if 'last_seen' in existing_columns:
                        conn.execute(db.text("ALTER TABLE users DROP COLUMN last_seen;"))
                        conn.commit()
            except Exception:
                pass  # Ignore migration errors for SQLite or if columns don't exist
            
            # Only seed if config table is empty (first run)
            from models import Config
            if Config.query.count() == 0:
                from seed_config import run_seeds
                run_seeds()
        except Exception:
            pass
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.trips import trips_bp
    from routes.drivers import drivers_bp
    from routes.payments import payments_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(trips_bp, url_prefix='/api/v1/trips')
    app.register_blueprint(drivers_bp, url_prefix='/api/v1/drivers')
    app.register_blueprint(payments_bp, url_prefix='/api/v1/payments')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    
    # Migration endpoint
    from routes.migrate import migrate_bp
    app.register_blueprint(migrate_bp, url_prefix='/api/v1/migrate')
    
    # Health check endpoint
    @app.route('/api/v1/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0'
        }), 200
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        try:
            db.session.rollback()
        except:
            pass
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Internal server error'
            }
        }), 500
    
    return app

# Create app instance for Gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)