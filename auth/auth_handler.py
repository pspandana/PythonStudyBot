# auth/auth_handler.py

import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import streamlit as st

class AuthHandler:
    """Handle user authentication and session management"""
    
    def __init__(self, db_path: str = "studybot.db"):
        self.db_path = db_path
        self.session_timeout = timedelta(days=7)  # Sessions last 7 days
        self.init_auth_tables()
    
    def init_auth_tables(self):
        """Initialize authentication tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT DEFAULT 'student',
                    display_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users(username)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_token 
                ON user_sessions(session_token)
            """)
            
            conn.commit()
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt using SHA-256"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 for secure password hashing
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        ).hex()
        
        return password_hash, salt
    
    def create_user(self, username: str, password: str, email: str = None, 
                    role: str = 'student', display_name: str = None) -> Dict:
        """Create a new user account"""
        try:
            # Validate username
            if len(username) < 3:
                return {'success': False, 'message': 'Username must be at least 3 characters'}
            
            if len(password) < 6:
                return {'success': False, 'message': 'Password must be at least 6 characters'}
            
            # Check if username contains only valid characters
            if not username.replace('_', '').replace('-', '').isalnum():
                return {'success': False, 'message': 'Username can only contain letters, numbers, _ and -'}
            
            # Hash password
            password_hash, salt = self.hash_password(password)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, salt, role, display_name)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username.lower(), email, password_hash, salt, role, display_name or username))
                
                user_id = cursor.lastrowid
                conn.commit()
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'message': 'Account created successfully! 🎉'
                }
        
        except sqlite3.IntegrityError:
            return {'success': False, 'message': 'Username or email already exists'}
        except Exception as e:
            return {'success': False, 'message': f'Error creating account: {str(e)}'}
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """Authenticate user and create session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, password_hash, salt, role, is_active, display_name
                    FROM users
                    WHERE username = ?
                """, (username.lower(),))
                
                result = cursor.fetchone()
                
                if not result:
                    return {'success': False, 'message': 'Invalid username or password'}
                
                user_id, stored_hash, salt, role, is_active, display_name = result
                
                if not is_active:
                    return {'success': False, 'message': 'Account is disabled'}
                
                # Verify password
                password_hash, _ = self.hash_password(password, salt)
                
                if password_hash != stored_hash:
                    return {'success': False, 'message': 'Invalid username or password'}
                
                # Create session
                session_token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + self.session_timeout
                
                cursor.execute("""
                    INSERT INTO user_sessions (user_id, session_token, expires_at)
                    VALUES (?, ?, ?)
                """, (user_id, session_token, expires_at))
                
                # Update last login
                cursor.execute("""
                    UPDATE users SET last_login = ? WHERE id = ?
                """, (datetime.now(), user_id))
                
                conn.commit()
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'username': username.lower(),
                    'display_name': display_name,
                    'role': role,
                    'session_token': session_token,
                    'message': 'Welcome back! 🎉'
                }
        
        except Exception as e:
            return {'success': False, 'message': f'Login error: {str(e)}'}
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session token and return user info"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT us.user_id, u.username, u.role, u.display_name, us.expires_at
                    FROM user_sessions us
                    JOIN users u ON us.user_id = u.id
                    WHERE us.session_token = ? AND us.is_active = TRUE
                """, (session_token,))
                
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                user_id, username, role, display_name, expires_at = result
                expires_at = datetime.fromisoformat(expires_at)
                
                # Check if session expired
                if datetime.now() > expires_at:
                    self.logout(session_token)
                    return None
                
                return {
                    'user_id': user_id,
                    'username': username,
                    'display_name': display_name,
                    'role': role
                }
        
        except Exception:
            return None
    
    def logout(self, session_token: str):
        """Invalidate session"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE user_sessions
                    SET is_active = FALSE
                    WHERE session_token = ?
                """, (session_token,))
                conn.commit()
        except Exception:
            pass
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user information by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, role, display_name, created_at, last_login
                    FROM users
                    WHERE id = ?
                """, (user_id,))
                
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'username': result[1],
                        'email': result[2],
                        'role': result[3],
                        'display_name': result[4],
                        'created_at': result[5],
                        'last_login': result[6]
                    }
        except Exception:
            pass
        
        return None