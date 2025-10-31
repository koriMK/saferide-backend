# SafeRide Backend - Database Seeding
# Initial configuration data for the application

from models import db, Config

def run_seeds():
    """Seed initial configuration data into the database"""
    try:
        # Default fare calculation configuration
        configs = [
            {'key': 'base_fare', 'value': '50.0'},      # Base fare in KES
            {'key': 'per_km_rate', 'value': '25.0'},    # Rate per kilometer in KES
            {'key': 'minimum_fare', 'value': '100.0'}   # Minimum fare in KES
        ]
        
        # Insert configuration if it doesn't exist
        for config_data in configs:
            existing = Config.query.filter_by(key=config_data['key']).first()
            if not existing:
                config = Config(key=config_data['key'], value=config_data['value'])
                db.session.add(config)
        
        # Commit all changes
        db.session.commit()
    except Exception:
        # Rollback on error
        db.session.rollback()