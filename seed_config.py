from models import db, Config

def run_seeds():
    try:
        configs = [
            {'key': 'base_fare', 'value': '50.0'},
            {'key': 'per_km_rate', 'value': '25.0'},
            {'key': 'minimum_fare', 'value': '100.0'}
        ]
        
        for config_data in configs:
            existing = Config.query.filter_by(key=config_data['key']).first()
            if not existing:
                config = Config(key=config_data['key'], value=config_data['value'])
                db.session.add(config)
        
        db.session.commit()
    except Exception:
        db.session.rollback()