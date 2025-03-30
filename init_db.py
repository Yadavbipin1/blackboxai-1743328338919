from app import app, db
from models import Room

def initialize_database():
    """Initialize the database with some sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add sample rooms if none exist
        if Room.query.count() == 0:
            sample_rooms = [
                Room("101", "1 seater"),
                Room("102", "1 seater"),
                Room("201", "3 seater"),
                Room("202", "3 seater"),
                Room("301", "4 seater"),
                Room("302", "4 seater")
            ]
            
            for room in sample_rooms:
                db.session.add(room)
            
            try:
                db.session.commit()
                print("Sample rooms added successfully!")
            except Exception as e:
                db.session.rollback()
                print(f"Error adding sample rooms: {str(e)}")

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully!")