# SafeRide Backend - Database Migration Routes
# Manual database migration utilities

from flask import Blueprint, jsonify
from models import db

# Create migration blueprint
migrate_bp = Blueprint('migrate', __name__)

@migrate_bp.route('/run', methods=['POST'])
def run_migration():
    """Manually run database migrations (create all tables)"""
    try:
        # Create all database tables based on models
        db.create_all()
        return jsonify({'success': True, 'message': 'Migration completed'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500