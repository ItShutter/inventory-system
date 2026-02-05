from flask import Flask
from config import Config
from extensions import db, login_manager
from werkzeug.security import generate_password_hash
from models import User, Category

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register Blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp
    from routes.products import products_bp
    from routes.transactions import transactions_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(transactions_bp)

    # Database Creation & Seeding
    with app.app_context():
        db.create_all()
        
        if not User.query.first():
            print("⚡ Creating default users...")
            admin = User(username='admin', password=generate_password_hash('1234'), role='admin')
            staff = User(username='staff', password=generate_password_hash('1234'), role='staff')
            db.session.add(admin)
            db.session.add(staff)
            
            categories = ['CPU', 'RAM', 'SSD', 'Mainboard', 'VGA', 'Case', 'PSU', 'Monitor', 'Accessory', 'Cooling']
            for c in categories:
                if not Category.query.filter_by(name=c).first():
                    db.session.add(Category(name=c))
            
            db.session.commit()
            print("✅ System initialized successfully!")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)