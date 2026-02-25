#this file if for creating a database

from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():

    # Create all tables
    db.create_all()

    # Check if admin already exists
    existing_admin = User.query.filter_by(role="admin").first()

    if not existing_admin:
        admin = User(email="admin@portal.com",
            password=generate_password_hash("admin123"),
            role="admin",
            is_active=True)
        db.session.add(admin)
        db.session.commit() 
        print("Database created and admin user added.")
    else:
        print("Database already exists. Admin user already present.")