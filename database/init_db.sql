-- StudyBot Database Schema
-- This file contains the complete database schema for the StudyBot application

-- Modules table - stores GitHub repo content
CREATE TABLE IF NOT EXISTS modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    content TEXT,  -- JSON string of content sections
    code_examples TEXT,  -- JSON string of code examples
    exercises TEXT,  -- JSON string of exercises
    order_index INTEGER,
    github_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User progress table
CREATE TABLE IF NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    module_id INTEGER,
    completed BOOLEAN DEFAULT FALSE,
    score REAL DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    time_spent INTEGER DEFAULT 0,  -- in minutes
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules (id),
    UNIQUE(user_id, module_id)
);

-- Difficult topics table - track what users struggle with
CREATE TABLE IF NOT EXISTS difficult_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    module_id INTEGER,
    topic TEXT NOT NULL,
    mistake_count INTEGER DEFAULT 1,
    last_mistake TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules (id),
    UNIQUE(user_id, module_id, topic)
);

-- Quiz results table
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
);

-- Learning interactions table - for Socratic method tracking
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
);

-- User settings table - for parental controls and other user preferences
CREATE TABLE IF NOT EXISTS user_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    setting_key TEXT NOT NULL,
    setting_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, setting_key)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_progress_module_id ON user_progress(module_id);
CREATE INDEX IF NOT EXISTS idx_difficult_topics_user_module ON difficult_topics(user_id, module_id);
CREATE INDEX IF NOT EXISTS idx_quiz_results_user_id ON quiz_results(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_interactions_user_id ON learning_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_modules_order ON modules(order_index);
CREATE INDEX IF NOT EXISTS idx_user_settings_user_key ON user_settings(user_id, setting_key);

-- Sample data (optional - for testing)
INSERT OR IGNORE INTO modules (id, title, description, content, code_examples, exercises, order_index, github_path) 
VALUES 
(1, 'Introduction to Python', 'Learn what Python is and why it''s awesome!', 
 '["Python is a friendly programming language!", "It''s used by Google, Netflix, and NASA!", "Perfect for beginners and experts alike!"]',
 '["print(\"Hello, World!\")", "name = \"Python\"\nprint(f\"I love {name}!\")"]',
 '["Try printing your name", "Create a variable with your age"]',
 0, 'intro'),
 
(2, 'Variables and Data Types', 'Learn how to store different types of information.',
 '["Variables are like labeled boxes!", "Strings are text in quotes", "Numbers can be integers or floats"]',
 '["age = 12", "name = \"Alice\"", "height = 4.5"]',
 '["Create variables for your info", "Try different data types"]',
 1, 'variables');

-- Views for common queries
CREATE VIEW IF NOT EXISTS user_stats AS
SELECT 
    user_id,
    COUNT(*) as total_modules_attempted,
    SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_modules,
    AVG(score) as average_score,
    SUM(time_spent) as total_time_spent,
    MAX(last_accessed) as last_active
FROM user_progress 
GROUP BY user_id;

CREATE VIEW IF NOT EXISTS module_stats AS
SELECT 
    m.id,
    m.title,
    COUNT(up.user_id) as students_attempted,
    AVG(up.score) as average_score,
    SUM(CASE WHEN up.completed = 1 THEN 1 ELSE 0 END) as students_completed
FROM modules m
LEFT JOIN user_progress up ON m.id = up.module_id
GROUP BY m.id, m.title;