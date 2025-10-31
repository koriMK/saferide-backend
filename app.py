# SafeRide Backend - Main Application Factory
# Flask-based ride-sharing backend with JWT authentication and M-Pesa integration

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

# Initialize JWT extension globally
jwt = JWTManager()

def create_app():
    """Application factory pattern for creating Flask app instance"""
    app = Flask(__name__)
    
    # App Configuration - Environment variables with fallback defaults
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    # Database URI - defaults to SQLite for development
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(os.path.abspath(__file__)), "safedrive.db")}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable event system for performance
    # Database connection optimization
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,  # Verify connections before use
        'pool_recycle': 300,    # Recycle connections every 5 minutes
        'connect_args': {'check_same_thread': False} if 'sqlite' in os.environ.get('DATABASE_URL', '') else {}
    }
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    
    # Initialize Flask extensions
    from models import db
    db.init_app(app)  # Initialize SQLAlchemy with app
    jwt.init_app(app)  # Initialize JWT manager
    # Configure CORS for API access from frontend
    CORS(app, 
         resources={r"/api/*": {"origins": "*"}},  # Allow all origins for API routes
         allow_headers=["Content-Type", "Authorization"],  # Required headers
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])  # Allowed HTTP methods
    
    # Database initialization and migrations
    with app.app_context():
        try:
            # Create all database tables
            db.create_all()
            
            # Handle legacy database migrations - remove problematic columns
            try:
                with db.engine.connect() as conn:
                    # Check for columns that cause deployment issues
                    result = conn.execute(db.text("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'users' AND column_name IN ('is_online', 'last_seen');
                    """))
                    existing_columns = [row[0] for row in result]
                    
                    # Remove problematic columns if they exist
                    if 'is_online' in existing_columns:
                        conn.execute(db.text("ALTER TABLE users DROP COLUMN is_online;"))
                        conn.commit()
                    
                    if 'last_seen' in existing_columns:
                        conn.execute(db.text("ALTER TABLE users DROP COLUMN last_seen;"))
                        conn.commit()
            except Exception:
                pass  # Ignore migration errors for SQLite or if columns don't exist
            
            # Seed initial configuration data on first run
            from models import Config
            if Config.query.count() == 0:
                from seed_config import run_seeds
                run_seeds()
        except Exception:
            pass  # Continue if database setup fails
    
    # Register API route blueprints
    from routes.auth import auth_bp          # Authentication routes
    from routes.users import users_bp        # User management routes
    from routes.trips import trips_bp        # Trip booking and management
    from routes.drivers import drivers_bp    # Driver registration and profile
    from routes.payments import payments_bp  # M-Pesa payment integration
    from routes.admin import admin_bp        # Admin dashboard routes
    
    # Register all blueprints with API versioning
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(users_bp, url_prefix='/api/v1/users')
    app.register_blueprint(trips_bp, url_prefix='/api/v1/trips')
    app.register_blueprint(drivers_bp, url_prefix='/api/v1/drivers')
    app.register_blueprint(payments_bp, url_prefix='/api/v1/payments')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    
    # Database migration endpoint
    from routes.migrate import migrate_bp
    app.register_blueprint(migrate_bp, url_prefix='/api/v1/migrate')
    
    # Health check endpoint for monitoring
    @app.route('/api/v1/health')
    def health_check():
        """API health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0'
        }), 200
    
    # Global error handlers for consistent API responses
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        try:
            db.session.rollback()  # Rollback any pending database transactions
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

# Create app instance for production deployment (Gunicorn)
app = create_app()

# Development server entry point
if __name__ == '__main__':
    # Run development server on all interfaces, port 5002
    app.run(debug=True, host='0.0.0.0', port=5002)