from flask import Blueprint, jsonify
from models import db

migrate_bp = Blueprint('migrate', __name__)

@migrate_bp.route('/run', methods=['POST'])
def run_migration():
    try:
        db.create_all()
        return jsonify({'success': True, 'message': 'Migration completed'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500