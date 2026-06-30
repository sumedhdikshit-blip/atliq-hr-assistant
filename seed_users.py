import sqlite3
import bcrypt
from hrms.db import DB_PATH

def seed_admin():
    email = "admin@atliq.com"
    password = "admin123"
    role = "admin"
    
    # Hash the password with bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            print(f"User {email} already exists. Updating password and role...")
            cursor.execute("UPDATE users SET password_hash = ?, role = ? WHERE email = ?", (hashed_password, role, email))
        else:
            cursor.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", (email, hashed_password, role))
            print(f"Admin user {email} successfully seeded.")
        conn.commit()
    except Exception as e:
        print("Error seeding admin user:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    seed_admin()
