from app.auth.db import Base, engine
from app.auth.models import User, Trip, Booking
import logging

# Configure logging to see SQLAlchemy output if needed
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

def init_db():
    print("Creating all tables via SQLAlchemy...")
    try:
        Base.metadata.create_all(bind=engine)
        print("Success.")
        
        # Seed test user
        from app.auth.db import SessionLocal
        from app.auth.security import get_password_hash
        
        db = SessionLocal()
        if not db.query(User).filter(User.id == 1).first():
            test_user = User(
                id=1,
                email="test@example.com",
                hashed_password=get_password_hash("password"),
                is_active=True
            )
            db.add(test_user)
            db.commit()
            print("Test user created.")
        db.close()

    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_db()
