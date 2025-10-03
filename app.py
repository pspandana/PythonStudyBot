import streamlit as st
import os
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, List

# Import custom modules (keeping your existing imports)
from database.db_handler import DatabaseHandler
from content.github_parser import GitHubParser
from content.prompts import PromptManager
from agents.socratic_tutor import SocraticTutor
from agents.quiz_generator import QuizGenerator
from agents.code_evaluator import CodeEvaluator
from utils.openai_client import OpenAIClient

# Page configuration
st.set_page_config(
    page_title="StudyBot - Learn Python with AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        'Get Help': 'https://www.python.org/',
        'Report a bug': None,
        'About': "StudyBot - Your Python Learning Buddy! 🐍✨"
    }
)

# Enhanced CSS with modern, animated design
st.markdown("""
<style>
/* Modern Color Palette */
:root {
    --primary: #667eea;
    --secondary: #764ba2;
    --success: #48bb78;
    --warning: #f6ad55;
    --danger: #fc8181;
    --info: #4299e1;
    --bg-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    --card-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

/* Animated Background */
.stApp {
    background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Main Container */
.main .block-container {
    padding: 2rem;
    max-width: 1400px;
}

/* Glass-morphism Cards */
.glass-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 2rem;
    box-shadow: var(--card-shadow);
    border: 1px solid rgba(255, 255, 255, 0.3);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.glass-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.15);
}

/* Header with Animation */
.main-header {
    background: var(--bg-gradient);
    padding: 2rem;
    border-radius: 20px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: var(--card-shadow);
    animation: fadeInDown 0.8s ease;
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.main-header h1 {
    font-size: 2.5rem;
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

/* Sidebar Enhancements */
.css-1d391kg {
    background: rgba(255, 255, 255, 0.95);
}

/* Module Cards */
.module-card {
    background: white;
    border-radius: 15px;
    padding: 1rem;
    margin: 0.5rem 0;
    border-left: 5px solid var(--primary);
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    transition: all 0.3s ease;
    cursor: pointer;
}

.module-card:hover {
    transform: translateX(5px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}

.module-card.completed {
    border-left-color: var(--success);
    background: linear-gradient(to right, rgba(72, 187, 120, 0.1), white);
}

.module-card.locked {
    opacity: 0.6;
    border-left-color: #cbd5e0;
}

/* Progress Bar with Animation */
.progress-container {
    background: #e2e8f0;
    border-radius: 20px;
    height: 30px;
    overflow: hidden;
    margin: 1rem 0;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}

.progress-fill {
    background: var(--bg-gradient);
    height: 100%;
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 0.9rem;
    transition: width 1s ease;
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { background-position: -1000px 0; }
    100% { background-position: 1000px 0; }
}

/* Chat Messages */
.chat-message {
    padding: 1.2rem;
    border-radius: 18px;
    margin: 1rem 0;
    animation: fadeIn 0.5s ease;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.bot-message {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    border-left: 5px solid var(--primary);
}

.user-message {
    background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
    border-left: 5px solid var(--info);
}

/* Buttons */
.stButton > button {
    min-height: 50px;
    font-size: 1rem;
    border-radius: 15px;
    font-weight: 600;
    transition: all 0.3s ease;
    border: none;
    background: var(--bg-gradient);
    color: white;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

/* Achievement Badges */
.achievement-badge {
    display: inline-block;
    background: var(--bg-gradient);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    margin: 0.3rem;
    font-size: 0.9rem;
    font-weight: bold;
    box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
    animation: bounceIn 0.6s ease;
}

@keyframes bounceIn {
    0% { transform: scale(0); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

/* XP Bar */
.xp-container {
    background: #e2e8f0;
    border-radius: 15px;
    height: 25px;
    overflow: hidden;
    margin: 1rem 0;
    position: relative;
}

.xp-fill {
    background: linear-gradient(90deg, #f6ad55, #fc8181);
    height: 100%;
    transition: width 1s ease;
    position: relative;
}

.xp-sparkle {
    position: absolute;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
    animation: sparkle 2s infinite;
}

@keyframes sparkle {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* Stats Cards */
.stat-card {
    background: white;
    border-radius: 15px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    transition: transform 0.3s ease;
}

.stat-card:hover {
    transform: scale(1.05);
}

.stat-value {
    font-size: 2.5rem;
    font-weight: bold;
    background: var(--bg-gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.stat-label {
    color: #718096;
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

/* Parental Control Panel */
.parent-panel {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 20px;
    margin: 1rem 0;
    box-shadow: var(--card-shadow);
}

.parent-panel h3 {
    color: white;
    margin-bottom: 1rem;
}

/* Time Limit Warning */
.time-warning {
    background: linear-gradient(135deg, #fc8181 0%, #f6ad55 100%);
    color: white;
    padding: 1rem;
    border-radius: 15px;
    text-align: center;
    font-weight: bold;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem 0.5rem;
    }
    
    .main-header h1 {
        font-size: 1.8rem;
    }
    
    .stat-value {
        font-size: 1.8rem;
    }
}

/* Input Fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    font-size: 16px !important;
    border-radius: 12px;
    border: 2px solid #e2e8f0;
    transition: border-color 0.3s ease;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Streak Counter */
.streak-badge {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(135deg, #fc8181 0%, #f6ad55 100%);
    color: white;
    padding: 0.7rem 1.2rem;
    border-radius: 25px;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(252, 129, 129, 0.3);
    animation: flameFlicker 1.5s infinite;
}

@keyframes flameFlicker {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

/* Loading Animation */
.loading-spinner {
    display: inline-block;
    width: 40px;
    height: 40px;
    border: 4px solid rgba(102, 126, 234, 0.3);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)


class ParentalControlManager:
    """Manages parental controls and monitoring"""
    
    def __init__(self, db: DatabaseHandler):
        self.db = db
        
    def initialize_parental_settings(self, user_id: str):
        """Initialize parental control settings for a user"""
        if 'parental_settings' not in st.session_state:
            st.session_state.parental_settings = {
                'enabled': False,
                'pin': None,
                'daily_time_limit': 60,  # minutes
                'time_used_today': 0,
                'last_reset': datetime.now().date(),
                'safe_mode': True,
                'difficulty_level': 'beginner',
                'allow_code_execution': True,
                'require_quiz_passing': True,
                'email_reports': False,
                'parent_email': None
            }
    
    def check_time_limit(self) -> Dict[str, any]:
        """Check if student has exceeded daily time limit"""
        settings = st.session_state.parental_settings
        
        # Reset timer if it's a new day
        if settings['last_reset'] != datetime.now().date():
            settings['time_used_today'] = 0
            settings['last_reset'] = datetime.now().date()
        
        time_remaining = settings['daily_time_limit'] - settings['time_used_today']
        
        return {
            'allowed': time_remaining > 0 or not settings['enabled'],
            'time_remaining': time_remaining,
            'time_used': settings['time_used_today'],
            'limit': settings['daily_time_limit']
        }
    
    def increment_session_time(self, minutes: int = 1):
        """Increment time used in current session"""
        if st.session_state.parental_settings['enabled']:
            st.session_state.parental_settings['time_used_today'] += minutes
    
    def verify_parent_pin(self, pin: str) -> bool:
        """Verify parent PIN for accessing controls"""
        return pin == st.session_state.parental_settings.get('pin')
    
    def get_progress_report(self, user_id: str) -> Dict:
        """Generate progress report for parents"""
        modules = self.db.get_all_modules()
        user_progress = self.db.get_user_progress(user_id)
        
        completed = len([p for p in user_progress if p['completed']])
        avg_score = sum([p.get('score', 0) for p in user_progress]) / len(user_progress) if user_progress else 0
        
        return {
            'total_modules': len(modules),
            'completed_modules': completed,
            'completion_rate': (completed / len(modules) * 100) if modules else 0,
            'average_score': avg_score,
            'time_spent_today': st.session_state.parental_settings['time_used_today'],
            'streak_days': self.calculate_streak(user_id),
            'last_activity': datetime.now()
        }
    
    def calculate_streak(self, user_id: str) -> int:
        """Calculate learning streak in days"""
        # This would query your database for consecutive days of activity
        # Simplified version:
        if 'streak' not in st.session_state:
            st.session_state.streak = 1
        return st.session_state.streak


class GamificationManager:
    """Manages XP, achievements, and gamification"""
    
    def __init__(self):
        self.initialize_gamification()
    
    def initialize_gamification(self):
        """Initialize gamification state"""
        if 'xp' not in st.session_state:
            st.session_state.xp = 0
        if 'level' not in st.session_state:
            st.session_state.level = 1
        if 'achievements' not in st.session_state:
            st.session_state.achievements = []
        if 'streak' not in st.session_state:
            st.session_state.streak = 1
    
    def award_xp(self, amount: int, reason: str):
        """Award XP to the student"""
        st.session_state.xp += amount
        
        # Check for level up
        old_level = st.session_state.level
        new_level = self.calculate_level(st.session_state.xp)
        
        if new_level > old_level:
            st.session_state.level = new_level
            st.balloons()
            st.success(f"🎉 Level Up! You're now Level {new_level}!")
            self.check_achievements('level_up', new_level)
        
        return new_level > old_level
    
    def calculate_level(self, xp: int) -> int:
        """Calculate level from XP (100 XP per level)"""
        return 1 + (xp // 100)
    
    def get_xp_for_next_level(self) -> Dict:
        """Get XP needed for next level"""
        current_level = st.session_state.level
        xp_for_current = (current_level - 1) * 100
        xp_for_next = current_level * 100
        current_xp = st.session_state.xp
        
        return {
            'current': current_xp - xp_for_current,
            'needed': 100,
            'percentage': ((current_xp - xp_for_current) / 100) * 100
        }
    
    def check_achievements(self, achievement_type: str, value: any):
        """Check and award achievements"""
        achievements = {
            'first_module': {'title': '🎯 First Steps', 'description': 'Complete your first module!'},
            'quiz_master': {'title': '🧠 Quiz Master', 'description': 'Score 100% on a quiz!'},
            'code_ninja': {'title': '💻 Code Ninja', 'description': 'Write 10 working code snippets!'},
            'level_5': {'title': '⭐ Rising Star', 'description': 'Reach Level 5!'},
            'level_10': {'title': '🌟 Python Pro', 'description': 'Reach Level 10!'},
            'week_streak': {'title': '🔥 Week Warrior', 'description': 'Learn for 7 days in a row!'},
            'perfect_score': {'title': '💯 Perfectionist', 'description': 'Get 100% on 3 quizzes!'},
        }
        
        # Add achievement if earned and not already unlocked
        earned = None
        if achievement_type == 'module_complete' and value == 1:
            earned = 'first_module'
        elif achievement_type == 'quiz_score' and value == 100:
            earned = 'perfect_score'
        elif achievement_type == 'level_up' and value == 5:
            earned = 'level_5'
        elif achievement_type == 'level_up' and value == 10:
            earned = 'level_10'
        elif achievement_type == 'streak' and value >= 7:
            earned = 'week_streak'
        
        if earned and earned not in st.session_state.achievements:
            st.session_state.achievements.append(earned)
            st.toast(f"🏆 Achievement Unlocked: {achievements[earned]['title']}", icon="🎉")
    
    def display_achievements(self):
        """Display earned achievements"""
        st.markdown("### 🏆 Your Achievements")
        
        if not st.session_state.achievements:
            st.info("Start learning to unlock achievements! 🌟")
            return
        
        cols = st.columns(3)
        for idx, achievement in enumerate(st.session_state.achievements):
            with cols[idx % 3]:
                st.markdown(f'<div class="achievement-badge">{achievement.replace("_", " ").title()}</div>', 
                          unsafe_allow_html=True)


class EnhancedStudyBotApp:
    def __init__(self):
        # Initialize existing components
        self.db = DatabaseHandler()
        self.github_parser = GitHubParser()
        self.prompt_manager = PromptManager()
        self.openai_client = OpenAIClient()
        self.socratic_tutor = SocraticTutor(self.openai_client, self.prompt_manager)
        self.quiz_generator = QuizGenerator(self.openai_client, self.prompt_manager)
        self.code_evaluator = CodeEvaluator(self.openai_client)
        
        # Initialize new managers
        self.parental_control = ParentalControlManager(self.db)
        self.gamification = GamificationManager()
        
        # Initialize session state
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize all session state variables"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if 'current_module' not in st.session_state:
            st.session_state.current_module = 0
            
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
            
        if 'learning_mode' not in st.session_state:
            st.session_state.learning_mode = 'socratic'
            
        if 'quiz_active' not in st.session_state:
            st.session_state.quiz_active = False
            
        if 'quiz_data' not in st.session_state:
            st.session_state.quiz_data = None
            
        if 'modules_loaded' not in st.session_state:
            st.session_state.modules_loaded = False
            
        if 'first_visit' not in st.session_state:
            st.session_state.first_visit = True
        
        if 'show_parent_panel' not in st.session_state:
            st.session_state.show_parent_panel = False
        
        # Initialize parental controls and gamification
        self.parental_control.initialize_parental_settings(st.session_state.user_id)
        self.gamification.initialize_gamification()
    
    def render_header(self):
        """Render enhanced animated header"""
        col1, col2, col3 = st.columns([2, 3, 2])
        
        with col2:
            st.markdown("""
            <div class="main-header">
                <h1>🤖 StudyBot</h1>
                <p>Your Python Learning Adventure! 🐍✨</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display XP bar and level
        xp_info = self.gamification.get_xp_for_next_level()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 1rem;">
                <h3 style="color: white;">Level {st.session_state.level} 🌟</h3>
                <div class="xp-container">
                    <div class="xp-fill" style="width: {xp_info['percentage']}%;">
                        <div class="xp-sparkle"></div>
                    </div>
                </div>
                <p style="color: white;">{int(xp_info['current'])} / {int(xp_info['needed'])} XP</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Streak display
            if st.session_state.streak > 0:
                st.markdown(f"""
                <div style="text-align: center;">
                    <span class="streak-badge">
                        🔥 {st.session_state.streak} Day Streak!
                    </span>
                </div>
                """, unsafe_allow_html=True)
    
    def render_parent_control_button(self):
        """Render parent control access button"""
        if st.sidebar.button("👨‍👩‍👧 Parent Dashboard", key="parent_btn"):
            st.session_state.show_parent_panel = not st.session_state.show_parent_panel
            st.rerun()
    
    def render_parental_dashboard(self):
        """Render parental control dashboard"""
        st.markdown('<div class="parent-panel">', unsafe_allow_html=True)
        st.markdown("### 👨‍👩‍👧 Parental Control Dashboard")
        
        # PIN verification for first-time setup or access
        if not st.session_state.parental_settings.get('pin'):
            st.info("Set up parental controls with a 4-digit PIN")
            pin = st.text_input("Create PIN:", type="password", max_chars=4, key="setup_pin")
            if st.button("Set PIN") and len(pin) == 4:
                st.session_state.parental_settings['pin'] = pin
                st.session_state.parental_settings['enabled'] = True
                st.success("✅ Parental controls activated!")
                st.rerun()
        else:
            # PIN verification
            if 'pin_verified' not in st.session_state:
                st.session_state.pin_verified = False
            
            if not st.session_state.pin_verified:
                pin = st.text_input("Enter PIN:", type="password", max_chars=4, key="verify_pin")
                if st.button("Verify"):
                    if self.parental_control.verify_parent_pin(pin):
                        st.session_state.pin_verified = True
                        st.rerun()
                    else:
                        st.error("❌ Incorrect PIN")
                return
            
            # Control Panel
            st.markdown("#### ⚙️ Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.session_state.parental_settings['daily_time_limit'] = st.slider(
                    "Daily Time Limit (minutes):",
                    15, 180, 
                    st.session_state.parental_settings['daily_time_limit'],
                    step=15
                )
                
                st.session_state.parental_settings['safe_mode'] = st.checkbox(
                    "Safe Mode (Age-appropriate content)",
                    st.session_state.parental_settings['safe_mode']
                )
                
                st.session_state.parental_settings['allow_code_execution'] = st.checkbox(
                    "Allow Code Execution",
                    st.session_state.parental_settings['allow_code_execution']
                )
            
            with col2:
                st.session_state.parental_settings['difficulty_level'] = st.selectbox(
                    "Difficulty Level:",
                    ['beginner', 'intermediate', 'advanced'],
                    index=['beginner', 'intermediate', 'advanced'].index(
                        st.session_state.parental_settings['difficulty_level']
                    )
                )
                
                st.session_state.parental_settings['require_quiz_passing'] = st.checkbox(
                    "Require 80% to advance",
                    st.session_state.parental_settings['require_quiz_passing']
                )
            
            # Progress Report
            st.markdown("#### 📊 Progress Report")
            report = self.parental_control.get_progress_report(st.session_state.user_id)
            
            stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
            
            with stat_col1:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{report['completed_modules']}</div>
                    <div class="stat-label">Completed Modules</div>
                </div>
                """, unsafe_allow_html=True)
            
            with stat_col2:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{report['completion_rate']:.0f}%</div>
                    <div class="stat-label">Completion Rate</div>
                </div>
                """, unsafe_allow_html=True)
            
            with stat_col3:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{report['time_spent_today']}</div>
                    <div class="stat-label">Minutes Today</div>
                </div>
                """, unsafe_allow_html=True)
            
            with stat_col4:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-value">{report['streak_days']}</div>
                    <div class="stat-label">Day Streak</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Quick Actions
            st.markdown("#### 🎯 Quick Actions")
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                if st.button("📧 Email Weekly Report"):
                    st.info("Report will be sent to your email!")
            
            with action_col2:
                if st.button("🔄 Reset Daily Timer"):
                    st.session_state.parental_settings['time_used_today'] = 0
                    st.success("Timer reset!")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("Close Dashboard"):
            st.session_state.show_parent_panel = False
            st.session_state.pin_verified = False
            st.rerun()
    
    def check_time_limit_warning(self):
        """Check and display time limit warnings"""
        time_status = self.parental_control.check_time_limit()
        
        if not time_status['allowed']:
            st.markdown("""
            <div class="time-warning">
                ⏰ Time's Up for Today! You've reached your daily limit.
                <br>Great job learning! Come back tomorrow! 🌟
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        # Warning at 10 minutes remaining
        if time_status['time_remaining'] <= 10 and time_status['time_remaining'] > 0:
            st.warning(f"⏰ Only {time_status['time_remaining']} minutes left today!")
    
    def load_modules(self):
        """Load and cache modules from GitHub"""
        if not st.session_state.modules_loaded:
            with st.spinner("🚀 Loading Python lessons... This might take a moment!"):
                try:
                    existing_modules = self.db.get_all_modules()
                    if len(existing_modules) >= 6:
                        st.session_state.modules_loaded = True
                        st.success("✅ Lessons loaded successfully!")
                        return True
                    
                    try:
                        modules = self.github_parser.parse_repository()
                        if len(modules) < 3:
                            modules = self.github_parser.create_fallback_modules()
                    except:
                        modules = self.github_parser.create_fallback_modules()
                    
                    self.db.store_modules(modules)
                    st.session_state.modules_loaded = True
                    st.success(f"✅ {len(modules)} lessons loaded successfully!")
                except Exception as e:
                    st.error(f"❌ Error loading lessons: {str(e)}")
                    return False
        return True
    
    def render_sidebar(self):
        """Render enhanced sidebar with progress and controls"""
        st.sidebar.title("📚 Learning Dashboard")
        
        # Parent Control Button
        self.render_parent_control_button()
        
        # Display Achievements Button
        if st.sidebar.button("🏆 View Achievements"):
            with st.sidebar:
                self.gamification.display_achievements()
        
        st.sidebar.markdown("---")
        
        # Get user progress
        modules = self.db.get_all_modules()
        user_progress = self.db.get_user_progress(st.session_state.user_id)
        
        if modules:
            completed_modules = len([p for p in user_progress if p['completed']])
            total_modules = len(modules)
            progress_percentage = (completed_modules / total_modules) * 100 if total_modules > 0 else 0
            
            st.sidebar.markdown("### 📊 Your Progress")
            st.sidebar.markdown(f"""
            <div class="progress-container">
                <div class="progress-fill" style="width: {progress_percentage}%;">
                    {completed_modules}/{total_modules} Complete
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.sidebar.markdown("### 📖 Available Modules")
            for i, module in enumerate(modules):
                is_basic_module = i <= 2
                is_progression_unlocked = any(p['module_id'] == modules[i-1]['id'] and p['completed'] for p in user_progress) if i > 0 else True
                is_unlocked = is_basic_module or is_progression_unlocked
                
                is_completed = any(p['module_id'] == module['id'] and p['completed'] for p in user_progress)
                is_current = i == st.session_state.current_module
                
                status = "✅" if is_completed else "🔓" if is_unlocked else "🔒"
                
                if st.sidebar.button(f"{status} {module['title']}", key=f"module_{i}", disabled=not is_unlocked):
                    if st.session_state.chat_history and st.session_state.current_module is not None:
                        current_mod = modules[st.session_state.current_module]
                        self.save_current_chat_history(current_mod['id'])
                    
                    st.session_state.current_module = i
                    st.session_state.chat_loaded = False
                    self.load_chat_history_for_module(module['id'])
                    st.session_state.first_visit = len(st.session_state.chat_history) == 0
                    if st.session_state.first_visit:
                        self.add_module_welcome_message(module)
                    st.rerun()

        # Learning mode selector
        st.sidebar.markdown("### 🎯 Learning Mode")
        new_mode = st.sidebar.selectbox(
            "Choose your learning style:",
            ['socratic', 'flashcards', 'quiz', 'explanation', 'coding'],
            format_func=lambda x: {
                'socratic': '🤔 Socratic Method',
                'flashcards': '📚 Flashcards',
                'quiz': '🧪 Quiz Mode',
                'explanation': '💡 Explain Topics',
                'coding': '💻 Code Practice'
            }[x],
            index=['socratic', 'flashcards', 'quiz', 'explanation', 'coding'].index(st.session_state.learning_mode)
        )
        
        if new_mode != st.session_state.learning_mode:
            st.session_state.learning_mode = new_mode
            st.session_state.quiz_active = False
            st.rerun()

        if st.sidebar.button("🔄 Start Fresh Chat"):
            if modules and st.session_state.current_module < len(modules):
                current_mod = modules[st.session_state.current_module]
                self.db.clear_chat_history(st.session_state.user_id, current_mod['id'])
            st.session_state.chat_history = []
            st.session_state.quiz_active = False
            st.rerun()
            
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🛠️ Developer Tools**")
        
        if st.sidebar.button("🔧 Reload All Modules"):
            st.session_state.modules_loaded = False
            try:
                modules = self.github_parser.create_fallback_modules()
                self.db.store_modules(modules)
                st.session_state.modules_loaded = True
                st.sidebar.success(f"✅ Reloaded {len(modules)} modules!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
        
        if st.sidebar.button("🔓 Unlock All Modules"):
            try:
                modules = self.db.get_all_modules()
                for module in modules:
                    self.db.update_user_progress(
                        st.session_state.user_id, 
                        module['id'], 
                        completed=True, 
                        score=100
                    )
                st.sidebar.success("🔓 All modules unlocked!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")

    def render_chat_interface(self):
        """Render the main chat interface"""
        modules = self.db.get_all_modules()
        if not modules:
            st.warning("⚠️ No modules loaded. Please wait for the content to load.")
            return

        current_module = modules[st.session_state.current_module]
        
        st.markdown(f"### 📖 Current Module: {current_module['title']}")
        
        if 'chat_loaded' not in st.session_state:
            self.load_chat_history_for_module(current_module['id'])
            st.session_state.chat_loaded = True
            if not st.session_state.chat_history:
                self.add_module_welcome_message(current_module)
                st.session_state.first_visit = False
        
        elif st.session_state.first_visit and not st.session_state.chat_history:
            self.add_module_welcome_message(current_module)
            st.session_state.first_visit = False
        
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'assistant':
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(message['content'])
                else:
                    with st.chat_message("user", avatar="👨‍🎓"):
                        st.markdown(message['content'])

        if st.session_state.learning_mode == 'quiz' and not st.session_state.quiz_active:
            if st.button("🧪 Start Module Quiz", type="primary"):
                self.start_quiz(current_module)
                
        elif st.session_state.quiz_active:
            self.render_quiz_interface()
            
        elif st.session_state.learning_mode == 'coding':
            self.render_coding_interface(current_module)
            
        elif st.session_state.learning_mode == 'flashcards':
            self.render_flashcard_interface(current_module)
            
        else:
            self.render_regular_chat(current_module)

    def render_regular_chat(self, current_module):
        """Render regular chat interface"""
        if prompt := st.chat_input("Ask me anything about Python! 💬"):
            st.session_state.chat_history.append({
                'role': 'user',
                'content': prompt
            })
            
            self.db.save_chat_message(
                st.session_state.user_id,
                current_module['id'],
                'user',
                prompt,
                st.session_state.learning_mode
            )
            
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking..."):
                    if st.session_state.learning_mode == 'socratic':
                        response = self.socratic_tutor.respond(prompt, current_module, st.session_state.chat_history)
                    elif st.session_state.learning_mode == 'explanation':
                        response = self.socratic_tutor.explain_topic(prompt, current_module)
                    else:
                        response = self.socratic_tutor.respond(prompt, current_module, st.session_state.chat_history)
                
                st.markdown(response or "Sorry, I couldn't generate a response.")
            
            response_content = response or "Sorry, I couldn't generate a response."
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response_content
            })
            
            self.db.save_chat_message(
                st.session_state.user_id,
                current_module['id'],
                'assistant',
                response_content,
                st.session_state.learning_mode
            )
            
            # Award XP for interaction
            self.gamification.award_xp(5, "Asked a question")

    def render_coding_interface(self, current_module):
        """Render coding practice interface"""
        st.markdown("### 💻 Code Practice")
        
        # Check if code execution is allowed
        if not st.session_state.parental_settings['allow_code_execution']:
            st.warning("⚠️ Code execution is disabled by parental controls.")
            return
        
        if 'coding_exercise' not in st.session_state:
            with st.spinner("Generating coding exercise..."):
                st.session_state.coding_exercise = self.code_evaluator.generate_exercise(current_module)
        
        st.markdown(f"**Exercise:** {st.session_state.coding_exercise}")
        
        user_code = st.text_area("Write your Python code here:", height=200, key="code_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏃‍♂️ Run Code"):
                if user_code.strip():
                    result = self.code_evaluator.evaluate_code(user_code, st.session_state.coding_exercise)
                    st.markdown("**Result:**")
                    st.code(result, language="python")
                    
                    # Award XP
                    self.gamification.award_xp(15, "Completed coding exercise")
                    
        with col2:
            if st.button("🔄 New Exercise"):
                del st.session_state.coding_exercise
                st.rerun()

    def render_flashcard_interface(self, current_module):
        """Render flashcard interface"""
        st.markdown("### 📚 Flashcards")
        
        if 'flashcard_data' not in st.session_state:
            with st.spinner("Generating flashcards..."):
                st.session_state.flashcard_data = self.generate_flashcards(current_module)
                st.session_state.flashcard_index = 0
                st.session_state.show_answer = False
        
        if st.session_state.flashcard_data:
            total_cards = len(st.session_state.flashcard_data)
            current_index = st.session_state.flashcard_index
            current_card = st.session_state.flashcard_data[current_index]
            
            st.markdown(f"**Card {current_index + 1} of {total_cards}**")
            st.markdown(f"### {current_card['question']}")
            
            if not st.session_state.show_answer:
                if st.button("🔍 Show Answer"):
                    st.session_state.show_answer = True
                    st.rerun()
            else:
                st.success(f"**Answer:** {current_card['answer']}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("👍 Got it!"):
                        self.gamification.award_xp(3, "Reviewed flashcard")
                        self.next_flashcard()
                with col2:
                    if st.button("👎 Need review"):
                        self.next_flashcard()
                with col3:
                    if st.button("➡️ Next"):
                        self.next_flashcard()

    def generate_flashcards(self, module):
        """Generate flashcards for the current module"""
        module_title = module.get('title', 'Python')
        content = module.get('content', [])
        examples = module.get('code_examples', [])
        
        flashcards = []
        
        if 'introduction' in module_title.lower():
            flashcards = [
                {"question": "What is Python? 🐍", "answer": "Python is a friendly programming language that's perfect for beginners. It's used to build websites, games, apps, and even control robots!"},
                {"question": "Why is Python good for beginners?", "answer": "Python code is easy to read and write - it's almost like writing in English! Plus it's used by companies like Google and NASA."},
                {"question": "What can you build with Python?", "answer": "You can build websites, games, mobile apps, robots, and solve real-world problems! The possibilities are endless! 🚀"}
            ]
        elif 'data types' in module_title.lower():
            flashcards = [
                {"question": "What is a string in Python? 📝", "answer": "A string is text enclosed in quotes, like 'Hello' or \"Python\". It's how we store words and sentences!"},
                {"question": "What is an integer? 🔢", "answer": "An integer is a whole number like 5, 10, or 100. No decimal points allowed!"},
                {"question": "How do you create a variable? 📦", "answer": "Just use: name = 'Alice' or age = 12. Variables are like labeled boxes to store information!"}
            ]
        elif 'function' in module_title.lower():
            flashcards = [
                {"question": "What is a function? ⚙️", "answer": "A function is like a recipe - it takes ingredients (inputs) and makes something (output). Use 'def' to create one!"},
                {"question": "How do you call a function? 📞", "answer": "Just write the function name with parentheses: greet() or add_numbers(5, 3)"},
                {"question": "What does 'return' do? ↩️", "answer": "Return gives back a result from your function, like return x + y gives back the sum!"}
            ]
        else:
            flashcards = [
                {"question": f"What do we learn in {module_title}? 🤔", "answer": f"In {module_title}, we explore important Python concepts that help us become better programmers!"},
                {"question": "How do you print in Python? 🖨️", "answer": "Use print('Hello World') - the print() function displays text on the screen!"},
                {"question": "What makes Python special? ✨", "answer": "Python is easy to read, powerful, and fun to use! It's perfect for learning programming."}
            ]
        
        if examples:
            flashcards.append({
                "question": f"What does this code do? 💻\n{examples[0]}", 
                "answer": "This is an example from our current module. Try running it to see what happens! 🎉"
            })
        
        return flashcards

    def save_current_chat_history(self, module_id: int):
        """Save current chat history to database"""
        pass
    
    def load_chat_history_for_module(self, module_id: int):
        """Load chat history for a specific module"""
        try:
            chat_history = self.db.load_chat_history(st.session_state.user_id, module_id)
            st.session_state.chat_history = [
                {'role': msg['role'], 'content': msg['content']} 
                for msg in chat_history
            ]
        except Exception as e:
            st.error(f"Error loading chat history: {str(e)}")
            st.session_state.chat_history = []
    
    def add_module_welcome_message(self, module):
        """Add welcome message when entering a new module"""
        module_title = module.get('title', 'Python Learning')
        
        welcome_messages = {
            'introduction': """🎉 Welcome to your Python journey! I'm so excited to learn with you!
            
Python is like having a magical language that lets you talk to computers! 🐍✨ Think of it like learning a new language, but instead of talking to people, you're giving instructions to computers.

What would you like to explore first?""",
            'data types': """📊 Time to explore the building blocks of Python - Data Types! 
            
Think of data types like different kinds of LEGO blocks 🧱 - each one has a special purpose!

What's your favorite thing? Is it a word, a number, or maybe something true/false?""",
            'data structures': """🗂️ Welcome to Data Structures!
            
Imagine your backpack 🎒 - you organize things in it, right? That's what data structures do!

What do you like to collect or organize?""",
            'function': """⚙️ Functions are here! These are like having superpowers!
            
Think of functions like recipes 👨‍🍳 - you give ingredients and get a result!

What's your favorite recipe?""",
            'loops': """🔄 Ready for Loops? These let us repeat actions!
            
Loops are like having a helpful robot 🤖 that does repetitive tasks!

What would YOU want a computer to repeat for you?""",
            'file': """📁 File Handling time! Now we can save our work!
            
Think of files like digital notebooks 📓!

What would you like to save in a file?"""
        }
        
        welcome_msg = next(
            (msg for key, msg in welcome_messages.items() if key in module_title.lower()),
            f"""🌟 Welcome to {module_title}! 
            
I'm excited to explore this topic with you!

What questions do you have?"""
        )
        
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': welcome_msg
        })

    def next_flashcard(self):
        """Move to next flashcard"""
        st.session_state.flashcard_index = (st.session_state.flashcard_index + 1) % len(st.session_state.flashcard_data)
        st.session_state.show_answer = False
        st.rerun()

    def start_quiz(self, module):
        """Start a quiz for the current module"""
        with st.spinner("🎯 Creating your personalized quiz..."):
            user_progress = self.db.get_user_progress(st.session_state.user_id)
            difficult_topics = self.db.get_difficult_topics(st.session_state.user_id, module['id'])
            
            quiz_data = self.quiz_generator.generate_quiz(module, difficult_topics)
            st.session_state.quiz_data = quiz_data
            st.session_state.quiz_active = True
            st.session_state.current_question = 0
            st.session_state.user_answers = []
            
            for i in range(10):
                if f'quiz_answer_{i}' in st.session_state:
                    del st.session_state[f'quiz_answer_{i}']
            
            st.rerun()

    def render_quiz_interface(self):
        """Render the quiz interface"""
        quiz = st.session_state.quiz_data
        current_q = st.session_state.current_question
        
        if current_q < len(quiz['questions']):
            question = quiz['questions'][current_q]
            
            st.markdown(f"### 🧪 Question {current_q + 1} of {len(quiz['questions'])}")
            st.markdown(f"**{question['question']}**")
            
            if f'quiz_answer_{current_q}' not in st.session_state:
                st.session_state[f'quiz_answer_{current_q}'] = None
            
            if question['type'] == 'multiple_choice':
                answer = st.radio("Choose your answer:", question['options'], key=f"q_radio_{current_q}")
                
                if answer and st.session_state[f'quiz_answer_{current_q}'] is None:
                    if st.button("Submit Answer", type="primary", key=f"submit_mc_{current_q}"):
                        st.session_state.user_answers.append(answer)
                        st.session_state[f'quiz_answer_{current_q}'] = answer
                        self.gamification.award_xp(10, "Answered quiz question")
                        st.session_state.current_question += 1
                        st.rerun()
                elif st.session_state[f'quiz_answer_{current_q}'] is not None:
                    st.success(f"✅ Answer submitted!")
                    
            else:
                answer = st.text_area("Your answer:", key=f"q_text_{current_q}", height=100)
                
                if answer.strip() and st.session_state[f'quiz_answer_{current_q}'] is None:
                    if st.button("Submit Answer", type="primary", key=f"submit_fr_{current_q}"):
                        st.session_state.user_answers.append(answer.strip())
                        st.session_state[f'quiz_answer_{current_q}'] = answer.strip()
                        self.gamification.award_xp(10, "Answered quiz question")
                        st.session_state.current_question += 1
                        st.rerun()
                elif st.session_state[f'quiz_answer_{current_q}'] is not None:
                    st.success(f"✅ Answer submitted!")
        else:
            self.show_quiz_results()

    def show_quiz_results(self):
        """Display quiz results"""
        quiz = st.session_state.quiz_data
        user_answers = st.session_state.user_answers
        
        score = self.quiz_generator.calculate_score(quiz, user_answers)
        percentage = (score / len(quiz['questions'])) * 100
        
        st.markdown("### 🎉 Quiz Complete!")
        st.markdown(f"**Your Score: {score}/{len(quiz['questions'])} ({percentage:.1f}%)**")
        
        if percentage >= 80:
            st.success("🎊 Congratulations! You passed!")
            st.balloons()
            
            modules = self.db.get_all_modules()
            current_module = modules[st.session_state.current_module]
            self.db.update_user_progress(
                st.session_state.user_id, 
                current_module['id'], 
                completed=True, 
                score=percentage
            )
            
            # Award XP and check achievements
            self.gamification.award_xp(50, "Passed module quiz!")
            self.gamification.check_achievements('module_complete', len([m for m in modules if m.get('completed')]))
            if percentage == 100:
                self.gamification.check_achievements('quiz_score', 100)
            
            if st.session_state.current_module < len(modules) - 1:
                st.info("🔓 Next module unlocked!")
            else:
                st.success("🏆 You've completed all modules! You're a Python pro!")
                
        else:
            st.warning("📚 Keep studying! You need 80% to pass.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📖 Back to Learning"):
                st.session_state.quiz_active = False
                st.session_state.learning_mode = 'socratic'
                st.rerun()
        with col2:
            if percentage < 80 and st.button("🔄 Retake Quiz"):
                st.session_state.quiz_active = False
                st.rerun()

    def run(self):
        """Main application runner"""
        # Check time limit first
        if st.session_state.parental_settings['enabled']:
            self.check_time_limit_warning()
            # Increment session time (simplified - in production use actual timing)
            if 'last_time_check' not in st.session_state:
                st.session_state.last_time_check = datetime.now()
            
            time_diff = (datetime.now() - st.session_state.last_time_check).seconds / 60
            if time_diff >= 1:
                self.parental_control.increment_session_time(1)
                st.session_state.last_time_check = datetime.now()
        
        self.render_header()
        
        # Show parental dashboard if requested
        if st.session_state.show_parent_panel:
            self.render_parental_dashboard()
            return
        
        if not self.load_modules():
            return
            
        self.render_sidebar()
        self.render_chat_interface()


# Main execution
if __name__ == "__main__":
    app = EnhancedStudyBotApp()
    app.run()