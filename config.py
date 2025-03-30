import os
from datetime import datetime

class Config:
    # Flask Configuration
    SECRET_KEY = "your_strong_secret_key_replace_in_production"  # Replace with strong key in production
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///hostel.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application Configuration
    DEBUG = True
    
    # PDF Configuration
    PDF_BILLS_FOLDER = "bills"
    
    # Get the base directory of the application
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Ensure the bills directory exists
    BILLS_PATH = os.path.join(BASE_DIR, PDF_BILLS_FOLDER)
    if not os.path.exists(BILLS_PATH):
        os.makedirs(BILLS_PATH)
    
    # Get current month-year folder for bills
    @staticmethod
    def get_current_bills_folder():
        current_date = datetime.now()
        folder_name = f"bills for {current_date.strftime('%B %Y')}"
        folder_path = os.path.join(Config.BILLS_PATH, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        return folder_path