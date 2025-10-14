# Create: PythonStudyBot/agents/rag_engine.py
import sqlite3
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Tuple, Optional
import os

class RAGEngine:
    def __init__(self, db_path: str = "studybot.db"):
        self.db_path = db_path
        # Use a lightweight, fast model that works offline
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.init_knowledge_tables()
        self.populate_initial_knowledge()
    
    def init_knowledge_tables(self):
        """Initialize RAG-specific database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Knowledge base table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    module_name TEXT,
                    difficulty_level TEXT,
                    embedding BLOB,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User interaction vectors for learning
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS interaction_vectors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    embedding BLOB,
                    success_rating INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def create_embedding(self, text: str) -> np.ndarray:
        """Create embedding for text"""
        return self.model.encode(text)
    
    def store_knowledge(self, content: str, content_type: str, 
                       module_name: str = None, difficulty_level: str = "beginner"):
        """Store content with its embedding in the knowledge base"""
        embedding = self.create_embedding(content)
        embedding_blob = embedding.tobytes()
        
        metadata = {
            "length": len(content),
            "word_count": len(content.split()),
            "module": module_name,
            "difficulty": difficulty_level
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge_base 
                (content, content_type, module_name, difficulty_level, embedding, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (content, content_type, module_name, difficulty_level, 
                  embedding_blob, json.dumps(metadata)))
            conn.commit()
    
    def find_relevant_content(self, query: str, limit: int = 3, 
                            content_type: str = None) -> List[Dict]:
        """Find most relevant content for a query"""
        query_embedding = self.create_embedding(query)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all knowledge base entries
            if content_type:
                cursor.execute("""
                    SELECT id, content, content_type, module_name, embedding, metadata
                    FROM knowledge_base WHERE content_type = ?
                """, (content_type,))
            else:
                cursor.execute("""
                    SELECT id, content, content_type, module_name, embedding, metadata
                    FROM knowledge_base
                """)
            
            results = cursor.fetchall()
            
        if not results:
            return []
        
        # Calculate similarities
        similarities = []
        for row in results:
            stored_embedding = np.frombuffer(row[4], dtype=np.float32)
            similarity = cosine_similarity([query_embedding], [stored_embedding])[0][0]
            
            similarities.append({
                'id': row[0],
                'content': row[1],
                'content_type': row[2],
                'module_name': row[3],
                'metadata': json.loads(row[5]) if row[5] else {},
                'similarity': float(similarity)
            })
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
    
    def populate_initial_knowledge(self):
        """Populate the knowledge base with initial Python learning content"""
        # Check if we already have content
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge_base")
            count = cursor.fetchone()[0]
            
        if count > 0:
            return  # Already populated
        
        # Initial Python knowledge base
        python_knowledge = [
            # Variables
            {
                "content": "Variables in Python are containers that store data values. You create a variable by assigning a value to it using the equals sign. Example: name = 'Alice', age = 25, is_student = True",
                "content_type": "concept",
                "module_name": "variables",
                "difficulty_level": "beginner"
            },
            {
                "content": "Python variable names must start with a letter or underscore, can contain letters, numbers, and underscores, and are case-sensitive. Good examples: user_name, firstName, _private_var",
                "content_type": "rules",
                "module_name": "variables",
                "difficulty_level": "beginner"
            },
            
            # Data Types
            {
                "content": "Python has several built-in data types: int (integers like 42), float (decimals like 3.14), str (text like 'Hello'), bool (True/False), list (ordered collection [1,2,3]), dict (key-value pairs {'name': 'Alice'})",
                "content_type": "concept",
                "module_name": "data_types",
                "difficulty_level": "beginner"
            },
            
            # Loops
            {
                "content": "For loops in Python iterate over sequences. Syntax: for item in sequence: # do something. Example: for i in range(5): print(i) prints numbers 0 through 4",
                "content_type": "concept",
                "module_name": "loops",
                "difficulty_level": "beginner"
            },
            {
                "content": "While loops repeat as long as a condition is True. Syntax: while condition: # do something. Example: count = 0; while count < 5: print(count); count += 1",
                "content_type": "concept",
                "module_name": "loops",
                "difficulty_level": "beginner"
            },
            
            # Functions
            {
                "content": "Functions in Python are defined using the def keyword. Syntax: def function_name(parameters): # function body; return value. Example: def greet(name): return f'Hello, {name}!'",
                "content_type": "concept",
                "module_name": "functions",
                "difficulty_level": "intermediate"
            },
            
            # Common Errors
            {
                "content": "NameError occurs when you try to use a variable that hasn't been defined. Solution: Make sure you've created the variable before using it. Example: print(x) without defining x first will cause NameError",
                "content_type": "error_help",
                "module_name": "debugging",
                "difficulty_level": "beginner"
            },
            {
                "content": "IndentationError happens when Python code isn't properly indented. Python uses indentation to group code blocks. Solution: Use consistent spaces (usually 4) for each indentation level",
                "content_type": "error_help",
                "module_name": "debugging",
                "difficulty_level": "beginner"
            },
            
            # Examples
            {
                "content": "Create a simple calculator: def add(a, b): return a + b; def subtract(a, b): return a - b; result = add(5, 3); print(result)  # Output: 8",
                "content_type": "example",
                "module_name": "functions",
                "difficulty_level": "beginner"
            },
            {
                "content": "Working with lists: my_list = [1, 2, 3]; my_list.append(4); print(my_list[0]); for item in my_list: print(item)",
                "content_type": "example",
                "module_name": "data_types",
                "difficulty_level": "beginner"
            }
        ]
        
        # Store all knowledge
        for item in python_knowledge:
            self.store_knowledge(
                content=item["content"],
                content_type=item["content_type"],
                module_name=item["module_name"],
                difficulty_level=item["difficulty_level"]
            )
        
        print(f"✅ Populated knowledge base with {len(python_knowledge)} entries")
    
    def get_smart_response(self, question: str, chat_history: List = None) -> str:
        """Generate a smart response using RAG"""
        # Find relevant content
        relevant_content = self.find_relevant_content(question, limit=3)
        
        if not relevant_content:
            return self.get_fallback_response(question)
        
        # Create context from relevant content
        context_parts = []
        for item in relevant_content:
            if item['similarity'] > 0.3:  # Only use reasonably similar content
                context_parts.append(f"• {item['content']}")
        
        if not context_parts:
            return self.get_fallback_response(question)
        
        # Generate response based on context
        context = "\n".join(context_parts)
        
        # Simple template-based response generation
        response = f"""Based on what I know about Python:

{context}

Let me help you with your question: "{question}"

Would you like me to explain any of these concepts in more detail or show you some examples?"""
        
        return response
    
    def get_fallback_response(self, question: str) -> str:
        """Fallback response when no relevant content is found"""
        fallback_responses = {
            "hello": "Hi! I'm StudyBot, your Python learning companion! 🐍 What would you like to learn about today?",
            "help": "I can help you learn Python! Try asking about variables, loops, functions, data types, or any Python concept.",
            "variables": "Variables are like labeled boxes that store information in Python. You create them by assigning values: name = 'Alice'",
            "loops": "Loops help you repeat code. Use 'for' loops to go through items, and 'while' loops to repeat until a condition changes.",
            "functions": "Functions are reusable blocks of code. Define them with 'def function_name():' and call them by name.",
            "error": "Python errors are helpful! Read the error message carefully - it usually tells you what went wrong and where."
        }
        
        question_lower = question.lower()
        for key, response in fallback_responses.items():
            if key in question_lower:
                return response
        
        return "I'm still learning about that topic! Can you try asking about Python basics like variables, loops, or functions? Or feel free to share what you're trying to do!"
    
    def learn_from_interaction(self, user_id: str, question: str, 
                             answer: str, success_rating: int = 3):
        """Store successful interactions for future learning"""
        if success_rating >= 4:  # Only store good interactions
            embedding = self.create_embedding(question)
            embedding_blob = embedding.tobytes()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO interaction_vectors 
                    (user_id, question, answer, embedding, success_rating)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, question, answer, embedding_blob, success_rating))
                conn.commit()