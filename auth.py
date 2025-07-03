import pyodbc
from flask_login import UserMixin
from werkzeug.security import check_password_hash
import hashlib

# Database connection string
CONN_STR = (
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=kalvwprdsql01;'
    'DATABASE=TRI_ProcessOptimisation;'
    'UID=tri_pro_opt;'
    'PWD=Tiger@2k25;'
)

#Replace email with password
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email
    
    def is_authenticated(self):
        return True
    
    def is_anonymous(self):
        return False

class AuthManager:
    def __init__(self):
        self.conn_str = CONN_STR
    
    def get_connection(self):
        """Get database connection"""
        try:
            return pyodbc.connect(self.conn_str)
        except Exception as e:
            print(f"Database connection error: {e}")
            return None
    
    def hash_password(self, password):
        """Simple password hashing - you might want to use bcrypt in production"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, stored_hash, provided_password):
        """Verify password against stored hash"""
        return stored_hash == self.hash_password(provided_password)
    
    def authenticate_user(self, username, password):
        """
        Authenticate user against database
        Returns User object if successful, None if failed
        
        MODIFY THIS QUERY TO MATCH YOUR EXISTING DATABASE SCHEMA:
        - Change table name from 'users' to your actual table name
        - Change column names to match your schema
        - Adjust password verification logic if needed
        """
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # TODO: Update this query to match your existing user table structure
            # Example queries for common scenarios:
            
            # If your table is named differently:
            # query = "SELECT id, username, email, password_hash, role, is_active FROM your_user_table WHERE username = ?"
            
            # If you don't have all these columns:
            # query = "SELECT id, username, password FROM your_user_table WHERE username = ?"
            
            # If passwords are stored in plain text (NOT RECOMMENDED):
            # query = "SELECT id, username, password FROM your_user_table WHERE username = ? AND password = ?"
            
            # Replace email with password
            query = """
                SELECT GlobalEmpCode, AdUsername, Email
                FROM [TRI_ProcessOptimisation].[dbo].[Users]
                WHERE AdUsername = ? AND Email = ?
            """
            
            cursor.execute(query, (username,password))
            user_data = cursor.fetchone()
            
            if user_data:
                user_id, db_username, email = user_data

                return User(
                        id=user_id,
                        username=db_username,
                        email=email
                    )
                
                # TODO: Adjust password verification based on how passwords are stored
                # If passwords are hashed:

                # if self.verify_password(password_hash, password):
                #     return User(
                #         id=user_id,
                #         username=db_username,
                #         email=email,
                #         role=role,
                #         is_active=bool(is_active)
                #     )
                
                # If passwords are stored in plain text (update accordingly):
                # if password_hash == password:
                #     return User(id=user_id, username=db_username, email=email, role=role)
            
            return None
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """
        Get user by ID for Flask-Login user_loader
        
        MODIFY THIS QUERY TO MATCH YOUR EXISTING DATABASE SCHEMA
        """
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            cursor = conn.cursor()
            
            # TODO: Update this query to match your existing user table structure
            query = """
                SELECT GlobalEmpCode, AdUsername, email
                FROM [TRI_ProcessOptimisation].[dbo].[Users]
                WHERE GlobalEmpCode = ?
            """
            
            cursor.execute(query, (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                user_id, username, email = user_data
                return User(
                    id=user_id,
                    username=username,
                    email=email
                )
            
            return None
            
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None
        finally:
            conn.close()
    
    
    def update_last_login(self, user_id):
        """
        Update user's last login timestamp
        """
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            update_query = """
                UPDATE users 
                SET last_login = GETDATE() 
                WHERE id = ?
            """
            
            cursor.execute(update_query, (user_id,))
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error updating last login: {e}")
            return False
        finally:
            conn.close()

# Initialize auth manager
auth_manager = AuthManager()

# Helper functions for easy import
def authenticate_user(username, password):
    """Authenticate user - returns User object or None"""
    return auth_manager.authenticate_user(username, password)

def get_user_by_id(user_id):
    """Get user by ID - for Flask-Login user_loader"""
    return auth_manager.get_user_by_id(user_id)

def update_last_login(user_id):
    """Update last login timestamp - optional function"""
    return auth_manager.update_last_login(user_id)