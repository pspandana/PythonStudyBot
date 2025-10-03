import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseHandler:
    def __init__(self, db_path: str = "studybot.db"):
        """Initialize database handler"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Modules table - stores GitHub repo content
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS modules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    content TEXT,
                    code_examples TEXT,
                    exercises TEXT,
                    order_index INTEGER,
                    github_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User progress table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    module_id INTEGER,
                    completed BOOLEAN DEFAULT FALSE,
                    score REAL DEFAULT 0,
                    attempts INTEGER DEFAULT 0,
                    time_spent INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (module_id) REFERENCES modules (id)
                )
            """)
            
            # Difficult topics table - track what users struggle with
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS difficult_topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    module_id INTEGER,
                    topic TEXT NOT NULL,
                    mistake_count INTEGER DEFAULT 1,
                    last_mistake TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (module_id) REFERENCES modules (id)
                )
            """)
            
            # Quiz results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quiz_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    module_id INTEGER,
                    questions TEXT,  -- JSON string of questions and answers
                    user_answers TEXT,  -- JSON string of user answers
                    score REAL,
                    total_questions INTEGER,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (module_id) REFERENCES modules (id)
                )
            """)
            
            # Learning interactions table - for Socratic method tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learning_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    module_id INTEGER,
                    question TEXT,
                    user_response TEXT,
                    bot_response TEXT,
                    interaction_type TEXT,  -- 'socratic', 'explanation', 'clarification'
                    understanding_level INTEGER,  -- 1-5 scale
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (module_id) REFERENCES modules (id)
                )
            """)
            
            # User settings table - for parental controls and other user preferences
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, setting_key)
                )
            """)
            
            conn.commit()
    
    def store_modules(self, modules: List[Dict[str, Any]]):
        """Store or update modules from GitHub parsing"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing modules to refresh content
            cursor.execute("DELETE FROM modules")
            
            for i, module in enumerate(modules):
                cursor.execute("""
                    INSERT INTO modules (
                        title, description, content, code_examples, 
                        exercises, order_index, github_path, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    module['title'],
                    module.get('description', ''),
                    json.dumps(module.get('content', [])),
                    json.dumps(module.get('code_examples', [])),
                    json.dumps(module.get('exercises', [])),
                    i,
                    module.get('github_path', ''),
                    datetime.now()
                ))
            
            conn.commit()
    
    def get_all_modules(self) -> List[Dict[str, Any]]:
        """Get all modules ordered by index"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, content, code_examples, 
                       exercises, order_index, github_path
                FROM modules 
                ORDER BY order_index
            """)
            
            modules = []
            for row in cursor.fetchall():
                modules.append({
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'content': json.loads(row[3]) if row[3] else [],
                    'code_examples': json.loads(row[4]) if row[4] else [],
                    'exercises': json.loads(row[5]) if row[5] else [],
                    'order_index': row[6],
                    'github_path': row[7]
                })
            
            return modules
    
    def get_module_by_id(self, module_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific module by ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, description, content, code_examples, 
                       exercises, order_index, github_path
                FROM modules 
                WHERE id = ?
            """, (module_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'content': json.loads(row[3]) if row[3] else [],
                    'code_examples': json.loads(row[4]) if row[4] else [],
                    'exercises': json.loads(row[5]) if row[5] else [],
                    'order_index': row[6],
                    'github_path': row[7]
                }
            return None
    
    def get_user_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's progress across all modules"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT module_id, completed, score, attempts, time_spent, last_accessed
                FROM user_progress 
                WHERE user_id = ?
                ORDER BY module_id
            """, (user_id,))
            
            progress = []
            for row in cursor.fetchall():
                progress.append({
                    'module_id': row[0],
                    'completed': bool(row[1]),
                    'score': row[2],
                    'attempts': row[3],
                    'time_spent': row[4],
                    'last_accessed': row[5]
                })
            
            return progress
    
    def update_user_progress(self, user_id: str, module_id: int, completed: bool = False, 
                           score: float = 0, time_spent: int = 0):
        """Update or insert user progress for a module"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if progress exists
            cursor.execute("""
                SELECT id, attempts FROM user_progress 
                WHERE user_id = ? AND module_id = ?
            """, (user_id, module_id))
            
            result = cursor.fetchone()
            
            if result:
                # Update existing progress
                progress_id, attempts = result
                cursor.execute("""
                    UPDATE user_progress 
                    SET completed = ?, score = ?, attempts = ?, 
                        time_spent = time_spent + ?, last_accessed = ?
                    WHERE id = ?
                """, (completed, score, attempts + 1, time_spent, datetime.now(), progress_id))
            else:
                # Insert new progress
                cursor.execute("""
                    INSERT INTO user_progress 
                    (user_id, module_id, completed, score, attempts, time_spent, last_accessed)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                """, (user_id, module_id, completed, score, time_spent, datetime.now()))
            
            conn.commit()
    
    def get_difficult_topics(self, user_id: str, module_id: int) -> List[str]:
        """Get topics that the user has struggled with in a module"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT topic FROM difficult_topics 
                WHERE user_id = ? AND module_id = ? 
                ORDER BY mistake_count DESC, last_mistake DESC
                LIMIT 5
            """, (user_id, module_id))
            
            return [row[0] for row in cursor.fetchall()]
    
    def add_difficult_topic(self, user_id: str, module_id: int, topic: str):
        """Add or increment count for a difficult topic"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if topic exists
            cursor.execute("""
                SELECT id, mistake_count FROM difficult_topics 
                WHERE user_id = ? AND module_id = ? AND topic = ?
            """, (user_id, module_id, topic))
            
            result = cursor.fetchone()
            
            if result:
                # Increment mistake count
                topic_id, mistake_count = result
                cursor.execute("""
                    UPDATE difficult_topics 
                    SET mistake_count = ?, last_mistake = ?
                    WHERE id = ?
                """, (mistake_count + 1, datetime.now(), topic_id))
            else:
                # Insert new difficult topic
                cursor.execute("""
                    INSERT INTO difficult_topics (user_id, module_id, topic, last_mistake)
                    VALUES (?, ?, ?, ?)
                """, (user_id, module_id, topic, datetime.now()))
            
            conn.commit()
    
    def save_quiz_result(self, user_id: str, module_id: int, questions: List[Dict], 
                        user_answers: List[str], score: float):
        """Save quiz results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quiz_results 
                (user_id, module_id, questions, user_answers, score, total_questions)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id, module_id, 
                json.dumps(questions), 
                json.dumps(user_answers), 
                score, 
                len(questions)
            ))
            conn.commit()
    
    def save_learning_interaction(self, user_id: str, module_id: int, question: str, 
                                user_response: str, bot_response: str, 
                                interaction_type: str = 'socratic', understanding_level: int = 3):
        """Save learning interactions for analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_interactions 
                (user_id, module_id, question, user_response, bot_response, 
                 interaction_type, understanding_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, module_id, question, user_response, bot_response, 
                  interaction_type, understanding_level))
            conn.commit()
    
    def save_chat_message(self, user_id: str, module_id: int, role: str, content: str, 
                         interaction_type: str = 'chat'):
        """Save individual chat messages for session persistence"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO learning_interactions 
                (user_id, module_id, question, user_response, bot_response, 
                 interaction_type, understanding_level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, module_id, 
                
                content if role == 'user' else '','',  # user_response
                content if role == 'assistant' else '',  # bot_response
                f"{interaction_type}_{role}",  # interaction_type with role
                3  # default understanding level
            ))
            conn.commit()
    
    def load_chat_history(self, user_id: str, module_id: int, limit: int = 50) -> List[Dict[str, str]]:
        """Load chat history for a specific user and module"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT question, user_response, bot_response, interaction_type, created_at
                FROM learning_interactions 
                WHERE user_id = ? AND module_id = ? 
                AND interaction_type LIKE 'socratic_%'
                ORDER BY created_at ASC
                LIMIT ?
            """, (user_id, module_id, limit))
            
            results = cursor.fetchall()
            chat_history = []
            
            for question, _, bot_response, interaction_type, created_at in results:
                if interaction_type.endswith('_user') and question:
                    chat_history.append({
                        'role': 'user',
                        'content': question,
                        'timestamp': created_at
                    })
                elif interaction_type.endswith('_assistant') and bot_response:
                    chat_history.append({
                        'role': 'assistant', 
                        'content': bot_response,
                        'timestamp': created_at
                    })
            
            return chat_history
    
    def clear_chat_history(self, user_id: str, module_id: int):
        """Clear chat history for a specific user and module"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM learning_interactions 
                WHERE user_id = ? AND module_id = ? 
                AND interaction_type LIKE 'chat_%'
            """, (user_id, module_id))
            conn.commit()
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total modules and completed
            cursor.execute("SELECT COUNT(*) FROM modules")
            total_modules = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM user_progress 
                WHERE user_id = ? AND completed = 1
            """, (user_id,))
            completed_modules = cursor.fetchone()[0] or 0
            
            # Average score
            cursor.execute("""
                SELECT AVG(score) FROM user_progress 
                WHERE user_id = ? AND score > 0
            """, (user_id,))
            avg_score = cursor.fetchone()[0] or 0
            
            # Total time spent
            cursor.execute("""
                SELECT SUM(time_spent) FROM user_progress 
                WHERE user_id = ?
            """, (user_id,))
            total_time = cursor.fetchone()[0] or 0
            
            # Most difficult topics
            cursor.execute("""
                SELECT topic, mistake_count FROM difficult_topics 
                WHERE user_id = ? 
                ORDER BY mistake_count DESC 
                LIMIT 3
            """, (user_id,))
            difficult_topics = cursor.fetchall()
            
            return {
                'total_modules': total_modules,
                'completed_modules': completed_modules,
                'completion_rate': (completed_modules / total_modules * 100) if total_modules > 0 else 0,
                'average_score': round(avg_score, 1),
                'total_time_minutes': total_time,
                'difficult_topics': [{'topic': topic, 'mistakes': count} for topic, count in difficult_topics]
            }
    
    def cleanup_old_data(self, days_old: int = 30):
        """Clean up old interaction data to keep database manageable"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM learning_interactions 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days_old))
            
            cursor.execute("""
                DELETE FROM quiz_results 
                WHERE completed_at < datetime('now', '-{} days')
            """.format(days_old))
            
            conn.commit()
    
    def save_user_settings(self, user_id: str, setting_key: str, setting_value: str):
        """Save user settings to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO user_settings 
                (user_id, setting_key, setting_value, updated_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, setting_key, setting_value, datetime.now()))
            conn.commit()
    
    def get_user_settings(self, user_id: str, setting_key: str) -> Optional[str]:
        """Get user settings from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT setting_value FROM user_settings 
                WHERE user_id = ? AND setting_key = ?
            """, (user_id, setting_key))
            
            result = cursor.fetchone()
            return result[0] if result else None