import streamlit as st
import os
from datetime import datetime, timedelta
import json
from typing import Optional, Dict, List
# Add after existing imports
from auth.auth_handler import AuthHandler
# Import custom modules
from database.db_handler import DatabaseHandler
from content.github_parser import GitHubParser
from content.prompts import PromptManager
from agents.socratic_tutor import SocraticTutor
from agents.quiz_generator import QuizGenerator
from agents.code_evaluator import CodeEvaluator
from utils.openai_client import OpenAIClient
# Create persistent user ID
USER_ID_FILE = '.studybot_data/current_user.txt'
os.makedirs('.studybot_data', exist_ok=True)

def get_or_create_user_id():
    if os.path.exists(USER_ID_FILE):
        with open(USER_ID_FILE, 'r') as f:
            return f.read().strip()
    else:
        user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with open(USER_ID_FILE, 'w') as f:
            f.write(user_id)
        return user_id
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
# Fun, kid-friendly CSS design with animations!
st.markdown("""
<style>
/* Fun Color Palette for Kids */
:root {
    --primary: #667eea;
    --secondary: #764ba2;
    --success: #48bb78;
    --warning: #f6ad55;
    --danger: #fc8181;
    --info: #4299e1;
}

/* Animated Space Background */
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
    background-size: 400% 400%;
    animation: spaceGradient 15s ease infinite;
}

@keyframes spaceGradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Main Container with fun styling */
.main .block-container {
    padding: 2rem;
    padding-bottom: 150px !important;
    max-width: 1400px;
    position: relative;
    z-index: 1;
}

/* Make sure all content is visible */
.main .block-container > div {
    position: relative;
    z-index: 2;
}

/* Chat Messages - Fun bubbles! */
.stChatMessage {
    font-size: 16px !important;
    line-height: 1.7 !important;
    padding: 1.2rem !important;
    border-radius: 20px !important;
    margin: 0.8rem 0 !important;
    animation: popIn 0.4s ease;
    box-shadow: 0 6px 15px rgba(0,0,0,0.12);
    position: relative;
    z-index: 5;
}

@keyframes popIn {
    0% { transform: scale(0.9) translateY(10px); opacity: 0; }
    100% { transform: scale(1) translateY(0); opacity: 1; }
}

/* Bot messages - Purple gradient with emoji */
div[data-testid="stChatMessage-assistant"] {
    background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%) !important;
    border-left: 5px solid #667eea !important;
    border-top: 3px solid rgba(255,255,255,0.5);
}

/* User messages - Pink/Blue gradient */
div[data-testid="stChatMessage-user"] {
    background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%) !important;
    border-left: 5px solid #fd79a8 !important;
    border-top: 3px solid rgba(255,255,255,0.5);
}

/* Chat Input - Fun colorful border */
.stChatInput textarea {
    font-size: 18px !important;
    border-radius: 25px !important;
    border: 3px solid #48bb78 !important;
    padding: 15px 20px !important;
    min-height: 60px !important;
    box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
    position: relative;
    z-index: 10;
}

.stChatInput textarea:focus {
    border-color: #667eea !important;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.5) !important;
}

/* Buttons - Fun and bouncy! */
.stButton > button {
    border-radius: 15px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 600 !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.05);
    box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5) !important;
}

/* Progress Bar - Animated rainbow! */
.progress-container {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    height: 36px;
    margin: 1rem 0;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    border: 2px solid rgba(255,255,255,0.3);
    position: relative;
    overflow: visible;
}

.progress-fill {
    background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #667eea);
    background-size: 200%;
    height: 100%;
    border-radius: 18px;
    animation: shimmer 3s linear infinite;
    position: absolute;
    top: 0;
    left: 0;
}

/* Progress text overlay - always visible */
.progress-container::after {
    content: attr(data-progress);
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: #2c3e50;
    font-weight: bold;
    font-size: 0.95rem;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    z-index: 2;
    pointer-events: none;
}

@keyframes shimmer {
    0% { background-position: 0%; }
    100% { background-position: 200%; }
}

/* Sidebar - Colorful Space Theme! */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
    position: relative;
    z-index: 100;
    box-shadow: 4px 0 20px rgba(0,0,0,0.3);
    border-right: 2px solid rgba(255,255,255,0.2);
}

[data-testid="stSidebar"] h1 {
    font-size: 1.2rem !important;
    font-weight: 700;
    color: white !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 0.5rem !important;
    padding: 0.5rem 0 !important;
}

[data-testid="stSidebar"] h3 {
    font-size: 0.95rem !important;
    font-weight: 600;
    color: #ffeaa7 !important;
    margin-top: 0.8rem !important;
    margin-bottom: 0.4rem !important;
    text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    padding: 0.2rem 0 !important;
    overflow: visible !important;
    white-space: normal !important;
}

[data-testid="stSidebar"] .stButton > button {
    font-size: 0.85rem !important;
    padding: 0.4rem 0.7rem !important;
    min-height: 35px !important;
    margin: 0.2rem 0 !important;
    background: rgba(255,255,255,0.2) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    transition: all 0.3s ease !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.3) !important;
    transform: translateX(5px) !important;
    border-color: rgba(255,255,255,0.5) !important;
}

[data-testid="stSidebar"] p {
    font-size: 0.85rem !important;
    margin: 0.25rem 0 !important;
    color: rgba(255,255,255,0.95) !important;
}

/* Sidebar selectbox - colorful */
[data-testid="stSidebar"] .stSelectbox {
    font-size: 0.85rem !important;
}

[data-testid="stSidebar"] .stSelectbox label {
    font-size: 0.85rem !important;
    margin-bottom: 0.2rem !important;
    color: white !important;
}

[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
    background: rgba(255,255,255,0.2) !important;
    border-color: rgba(255,255,255,0.3) !important;
}

/* Compact markdown in sidebar */
[data-testid="stSidebar"] .stMarkdown {
    margin: 0.25rem 0 !important;
    color: white !important;
}

[data-testid="stSidebar"] hr {
    margin: 0.6rem 0 !important;
    border-color: rgba(255,255,255,0.3) !important;
}

/* Stats Cards - Colorful! */
.stat-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 20px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    animation: floatUp 3s ease-in-out infinite;
}

@keyframes floatUp {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

.stat-value {
    font-size: 2.5rem;
    font-weight: bold;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Achievement Badges - Bouncy! */
.achievement-badge {
    display: inline-block;
    background: linear-gradient(135deg, #f6ad55, #fc8181);
    color: white;
    padding: 0.6rem 1.2rem;
    border-radius: 25px;
    margin: 0.3rem;
    font-weight: bold;
    box-shadow: 0 4px 15px rgba(252, 129, 129, 0.4);
    animation: bounce 2s infinite;
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

/* Streak Badge - Fire animation! */
.streak-badge {
    display: inline-flex;
    align-items: center;
    background: linear-gradient(135deg, #fc8181 0%, #f6ad55 100%);
    color: white;
    padding: 0.8rem 1.5rem;
    border-radius: 30px;
    font-weight: bold;
    font-size: 1.1rem;
    box-shadow: 0 4px 20px rgba(252, 129, 129, 0.5);
    animation: fireGlow 1.5s infinite;
}

@keyframes fireGlow {
    0%, 100% { transform: scale(1); box-shadow: 0 4px 20px rgba(252, 129, 129, 0.5); }
    50% { transform: scale(1.05); box-shadow: 0 6px 30px rgba(252, 129, 129, 0.8); }
}

/* XP Bar - Sparkling! */
.xp-fill {
    background: linear-gradient(90deg, #f6ad55, #fc8181, #f093fb);
    background-size: 200%;
    animation: sparkleMove 2s linear infinite;
}

@keyframes sparkleMove {
    0% { background-position: 0%; }
    100% { background-position: 200%; }
}

/* Success/Info/Warning Messages - Colorful! */
.stSuccess {
    background: linear-gradient(135deg, #b7f8db 0%, #50d890 100%) !important;
    border-radius: 15px !important;
    padding: 1rem !important;
    border-left: 5px solid #27ae60 !important;
    box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3) !important;
    animation: slideIn 0.4s ease !important;
}

.stInfo {
    background: linear-gradient(135deg, #d4f1f4 0%, #75d7f0 100%) !important;
    border-radius: 15px !important;
    padding: 1rem !important;
    border-left: 5px solid #3498db !important;
    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.3) !important;
    animation: slideIn 0.4s ease !important;
}

.stWarning {
    background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%) !important;
    border-radius: 15px !important;
    padding: 1rem !important;
    border-left: 5px solid #f39c12 !important;
    box-shadow: 0 4px 15px rgba(243, 156, 18, 0.3) !important;
    animation: slideIn 0.4s ease !important;
}

.stError {
    background: linear-gradient(135deg, #fab1a0 0%, #ff7675 100%) !important;
    border-radius: 15px !important;
    padding: 1rem !important;
    border-left: 5px solid #e74c3c !important;
    box-shadow: 0 4px 15px rgba(231, 76, 60, 0.3) !important;
    animation: slideIn 0.4s ease !important;
}

@keyframes slideIn {
    0% { transform: translateX(-20px); opacity: 0; }
    100% { transform: translateX(0); opacity: 1; }
}

/* Ensure notifications are visible */
div[data-baseweb="notification"] {
    background: rgba(255, 255, 255, 0.98) !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
}

/* Mobile Responsive */
@media (max-width: 768px) {
    .main .block-container {
        padding: 1rem !important;
        padding-bottom: 180px !important;
    }
}
</style>
""", unsafe_allow_html=True)






class ParentalControlManager:
    """Manages parental controls and monitoring - FIX: Now saves to database"""
    
    def __init__(self, db: DatabaseHandler):
        self.db = db
        
    def initialize_parental_settings(self, user_id: str):
        """Initialize parental control settings - Load from DB if exists"""
        if 'parental_settings' not in st.session_state:
            # Try to load from database first
            saved_settings = self.load_parental_settings(user_id)
            if saved_settings:
                st.session_state.parental_settings = saved_settings
            else:
                # Create new settings
                st.session_state.parental_settings = {
                    'enabled': False,
                    'pin': None,
                    'daily_time_limit': 60,
                    'time_used_today': 0,
                    'last_reset': datetime.now().date().isoformat(),
                    'safe_mode': True,
                    'difficulty_level': 'beginner',
                    'allow_code_execution': True,
                    'require_quiz_passing': True,
                    'email_reports': False,
                    'parent_email': None
                }
    
    def save_parental_settings(self, user_id: str):
        """Save parental settings to database"""
        settings = st.session_state.parental_settings
        settings_json = json.dumps(settings, default=str)
        
        try:
            self.db.save_user_settings(user_id, 'parental_settings', settings_json)
        except Exception as e:
            print(f"Error saving parental settings to database: {e}")
            # Fallback to file if database fails
            os.makedirs('.studybot_data', exist_ok=True)
            with open(f'.studybot_data/{user_id}_parental.json', 'w') as f:
                json.dump(settings, f, default=str)
    
    def load_parental_settings(self, user_id: str) -> Optional[Dict]:
        """Load parental settings from database"""
        try:
            settings_json = self.db.get_user_settings(user_id, 'parental_settings')
            if settings_json:
                settings = json.loads(settings_json)
                # Convert date string back to date object if needed
                if 'last_reset' in settings and isinstance(settings['last_reset'], str):
                    settings['last_reset'] = datetime.fromisoformat(settings['last_reset']).date()
                return settings
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error loading parental settings from database: {e}")
        
        # Fallback to file if database fails
        try:
            with open(f'.studybot_data/{user_id}_parental.json', 'r') as f:
                settings = json.load(f)
                if 'last_reset' in settings and isinstance(settings['last_reset'], str):
                    settings['last_reset'] = datetime.fromisoformat(settings['last_reset']).date()
                return settings
        except FileNotFoundError:
            pass
        
        return None
    
    def check_time_limit(self) -> Dict[str, any]:
        """Check if student has exceeded daily time limit"""
        settings = st.session_state.parental_settings
        
        # Convert string to date if needed
        if isinstance(settings['last_reset'], str):
            settings['last_reset'] = datetime.fromisoformat(settings['last_reset']).date()
        
        # Reset timer if it's a new day
        if settings['last_reset'] != datetime.now().date():
            settings['time_used_today'] = 0
            settings['last_reset'] = datetime.now().date()
            # SAVE TO DATABASE when resetting
            self.save_parental_settings(st.session_state.user_id)
        
        time_remaining = settings['daily_time_limit'] - settings['time_used_today']
        
        return {
            'allowed': time_remaining > 0 or not settings['enabled'],
            'time_remaining': time_remaining,
            'time_used': settings['time_used_today'],
            'limit': settings['daily_time_limit']
        }
    
    def increment_session_time(self, minutes: int = 1):
        """Increment time used in current session - UPDATED: Now saves to database"""
        if st.session_state.parental_settings['enabled']:
            st.session_state.parental_settings['time_used_today'] += minutes
            # SAVE TO DATABASE every time we increment
            self.save_parental_settings(st.session_state.user_id)
    
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
            st.info("Start learning to unlock achievements!")
            return
        
        cols = st.columns(3)
        for idx, achievement in enumerate(st.session_state.achievements):
            with cols[idx % 3]:
                st.markdown(f'<div class="achievement-badge">{achievement.replace("_", " ").title()}</div>', 
                          unsafe_allow_html=True)


class EnhancedStudyBotApp:
    def __init__(self):
        self.db = DatabaseHandler()
        self.auth = AuthHandler()  # NEW: Add auth handler
        self.github_parser = GitHubParser()
        self.prompt_manager = PromptManager()
        self.openai_client = OpenAIClient()
        self.socratic_tutor = SocraticTutor(self.openai_client, self.prompt_manager)
        self.quiz_generator = QuizGenerator(self.openai_client, self.prompt_manager)
        self.code_evaluator = CodeEvaluator(self.openai_client)
        
        self.parental_control = ParentalControlManager(self.db)
        self.gamification = GamificationManager()
        
        self.init_session_state()
        
    def init_session_state(self):
        """Initialize all session state variables"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = get_or_create_user_id()
        
        if 'current_module' not in st.session_state:
            st.session_state.current_module = 0
            
        if 'chat_history' not in st.session_state:
    # LOAD CHAT HISTORY FROM DATABASE
            if hasattr(self, 'db') and st.session_state.get('current_module') is not None:
                saved_history = self.db.load_chat_history(
                    st.session_state.user_id, 
                    st.session_state.current_module
                )
                st.session_state.chat_history = saved_history if saved_history else []
            else:
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
        
        self.parental_control.initialize_parental_settings(st.session_state.user_id)
        self.gamification.initialize_gamification()
    
    def render_header(self):
        """Render fun, compact header for kids!"""
        xp_info = self.gamification.get_xp_for_next_level()
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(240,247,255,0.95) 100%); padding: 0.8rem 1.5rem; border-radius: 20px; margin-bottom: 1rem; box-shadow: 0 6px 20px rgba(0,0,0,0.15); border: 3px solid rgba(255,255,255,0.5);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem;">
                <div style="flex: 1; min-width: 200px;">
                    <h2 style="margin: 0; font-size: 1.4rem; color: #667eea; font-weight: 700;">
                        🤖 StudyBot <span style="font-size: 0.8rem; color: #999;">| Python Adventure 🐍</span>
                    </h2>
                </div>
                <div style="flex: 1; min-width: 250px; text-align: center;">
                    <div style="display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(102,126,234,0.1); padding: 0.4rem 1rem; border-radius: 15px;">
                        <span style="font-size: 1.1rem; font-weight: 700; color: #667eea;">⭐ Level {st.session_state.level}</span>
                        <span style="color: #666;">|</span>
                        <span style="font-size: 0.9rem; color: #666;">{int(xp_info['current'])}/{int(xp_info['needed'])} XP</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.8); border-radius: 10px; height: 8px; margin-top: 0.4rem; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #667eea, #764ba2, #f093fb); height: 100%; width: {xp_info['percentage']}%; transition: width 0.5s ease;"></div>
                    </div>
                </div>
                <div style="flex: 0; text-align: right;">
                    <span style="display: inline-flex; align-items: center; background: linear-gradient(135deg, #fc8181 0%, #f6ad55 100%); color: white; padding: 0.5rem 0.8rem; border-radius: 20px; font-weight: 700; font-size: 0.95rem; box-shadow: 0 4px 15px rgba(252,129,129,0.4);">
                        🔥 {st.session_state.streak} Day Streak!
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    def render_parent_control_button(self):
        """Render parent control access button"""
        if st.sidebar.button("👨‍👩‍👧 Parent Dashboard", key="parent_btn"):
            st.session_state.show_parent_panel = not st.session_state.show_parent_panel
            st.rerun()
    
    def render_parental_dashboard(self):
        """Render parental control dashboard - FIX: Now saves PIN"""
        st.markdown('<div class="parent-panel">', unsafe_allow_html=True)
        st.markdown("### 👨‍👩‍👧 Parental Control Dashboard")
        
        if not st.session_state.parental_settings.get('pin'):
            st.info("Set up parental controls with a 4-digit PIN")
            pin = st.text_input("Create PIN:", type="password", max_chars=4, key="setup_pin")
            if st.button("Set PIN") and len(pin) == 4:
                st.session_state.parental_settings['pin'] = pin
                st.session_state.parental_settings['enabled'] = True
                # SAVE TO DATABASE
                self.parental_control.save_parental_settings(st.session_state.user_id)
                st.success("✅ Parental controls activated and saved!")
                st.rerun()
        else:
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
            
            st.markdown("#### ⚙️ Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                new_limit = st.slider(
                    "Daily Time Limit (minutes):",
                    15, 180, 
                    st.session_state.parental_settings['daily_time_limit'],
                    step=15
                )
                if new_limit != st.session_state.parental_settings['daily_time_limit']:
                    st.session_state.parental_settings['daily_time_limit'] = new_limit
                    self.parental_control.save_parental_settings(st.session_state.user_id)
                
                new_safe_mode = st.checkbox(
                    "Safe Mode (Age-appropriate content)",
                    st.session_state.parental_settings['safe_mode']
                )
                if new_safe_mode != st.session_state.parental_settings['safe_mode']:
                    st.session_state.parental_settings['safe_mode'] = new_safe_mode
                    self.parental_control.save_parental_settings(st.session_state.user_id)
                
                new_code_exec = st.checkbox(
                    "Allow Code Execution",
                    st.session_state.parental_settings['allow_code_execution']
                )
                if new_code_exec != st.session_state.parental_settings['allow_code_execution']:
                    st.session_state.parental_settings['allow_code_execution'] = new_code_exec
                    self.parental_control.save_parental_settings(st.session_state.user_id)
            
            with col2:
                new_difficulty = st.selectbox(
                    "Difficulty Level:",
                    ['beginner', 'intermediate', 'advanced'],
                    index=['beginner', 'intermediate', 'advanced'].index(
                        st.session_state.parental_settings['difficulty_level']
                    )
                )
                if new_difficulty != st.session_state.parental_settings['difficulty_level']:
                    st.session_state.parental_settings['difficulty_level'] = new_difficulty
                    self.parental_control.save_parental_settings(st.session_state.user_id)
                
                new_quiz_passing = st.checkbox(
                    "Require 80% to advance",
                    st.session_state.parental_settings['require_quiz_passing']
                )
                if new_quiz_passing != st.session_state.parental_settings['require_quiz_passing']:
                    st.session_state.parental_settings['require_quiz_passing'] = new_quiz_passing
                    self.parental_control.save_parental_settings(st.session_state.user_id)
            
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
                    self.parental_control.save_parental_settings(st.session_state.user_id)
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
        
        self.render_parent_control_button()
        
        if st.sidebar.button("🏆 View Achievements"):
            with st.sidebar:
                self.gamification.display_achievements()
        
        st.sidebar.markdown("---")
        
        modules = self.db.get_all_modules()
        user_progress = self.db.get_user_progress(st.session_state.user_id)
        
        if modules:
            completed_modules = len([p for p in user_progress if p['completed']])
            total_modules = len(modules)
            progress_percentage = (completed_modules / total_modules) * 100 if total_modules > 0 else 0
            
            st.sidebar.markdown("### 📊 Your Progress")
            st.sidebar.markdown(f"""
            <div class="progress-container" data-progress="{completed_modules}/{total_modules} Complete">
                <div class="progress-fill" style="width: {progress_percentage}%;"></div>
            </div>
            """, unsafe_allow_html=True)
            
            st.sidebar.markdown("### 📖 Available Modules")
            for i, module in enumerate(modules):
                is_basic_module = i <= 2
                is_progression_unlocked = any(p['module_id'] == modules[i-1]['id'] and p['completed'] for p in user_progress) if i > 0 else True
                is_unlocked = is_basic_module or is_progression_unlocked
                
                is_completed = any(p['module_id'] == module['id'] and p['completed'] for p in user_progress)
                
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
                    with st.chat_message("user", avatar="👦"):
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
            
            self.gamification.award_xp(5, "Asked a question")

    def render_coding_interface(self, current_module):
        """Render coding practice interface"""
        st.markdown("### 💻 Code Practice")
        
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
        
        flashcards = []
        
        if 'introduction' in module_title.lower():
            flashcards = [
                {"question": "What is Python?", "answer": "Python is a friendly programming language that's perfect for beginners. It's used to build websites, games, apps, and even control robots!"},
                {"question": "Why is Python good for beginners?", "answer": "Python code is easy to read and write - it's almost like writing in English! Plus it's used by companies like Google and NASA."},
                {"question": "What can you build with Python?", "answer": "You can build websites, games, mobile apps, robots, and solve real-world problems! The possibilities are endless!"}
            ]
        elif 'data types' in module_title.lower():
            flashcards = [
                {"question": "What is a string in Python?", "answer": "A string is text enclosed in quotes, like 'Hello' or \"Python\". It's how we store words and sentences!"},
                {"question": "What is an integer?", "answer": "An integer is a whole number like 5, 10, or 100. No decimal points allowed!"},
                {"question": "How do you create a variable?", "answer": "Just use: name = 'Alice' or age = 12. Variables are like labeled boxes to store information!"}
            ]
        elif 'function' in module_title.lower():
            flashcards = [
                {"question": "What is a function?", "answer": "A function is like a recipe - it takes ingredients (inputs) and makes something (output). Use 'def' to create one!"},
                {"question": "How do you call a function?", "answer": "Just write the function name with parentheses: greet() or add_numbers(5, 3)"},
                {"question": "What does 'return' do?", "answer": "Return gives back a result from your function, like return x + y gives back the sum!"}
            ]
        else:
            flashcards = [
                {"question": f"What do we learn in {module_title}?", "answer": f"In {module_title}, we explore important Python concepts that help us become better programmers!"},
                {"question": "How do you print in Python?", "answer": "Use print('Hello World') - the print() function displays text on the screen!"},
                {"question": "What makes Python special?", "answer": "Python is easy to read, powerful, and fun to use! It's perfect for learning programming."}
            ]
        
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
            'introduction': "Welcome to your Python journey! I'm so excited to learn with you!\n\nPython is like having a magical language that lets you talk to computers! What would you like to explore first?",
            'data types': "Time to explore the building blocks of Python - Data Types!\n\nThink of data types like different kinds of LEGO blocks - each one has a special purpose!\n\nWhat's your favorite thing? Is it a word, a number, or maybe something true/false?",
            'data structures': "Welcome to Data Structures!\n\nImagine your backpack - you organize things in it, right? That's what data structures do!\n\nWhat do you like to collect or organize?",
            'function': "Functions are here! These are like having superpowers!\n\nThink of functions like recipes - you give ingredients and get a result!\n\nWhat's your favorite recipe?",
            'loops': "Ready for Loops? These let us repeat actions!\n\nLoops are like having a helpful robot that does repetitive tasks!\n\nWhat would YOU want a computer to repeat for you?",
            'file': "File Handling time! Now we can save our work!\n\nThink of files like digital notebooks!\n\nWhat would you like to save in a file?"
        }
        
        welcome_msg = next(
            (msg for key, msg in welcome_messages.items() if key in module_title.lower()),
            f"Welcome to {module_title}!\n\nI'm excited to explore this topic with you!\n\nWhat questions do you have?"
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
    def save_chat_message_to_db(self, role: str, content: str):
        """Save individual chat messages to database for persistence"""
        if hasattr(self, 'db') and 'current_module' in st.session_state:
            self.db.save_chat_message(
                st.session_state.user_id,
                st.session_state.current_module,
                role,
                content
            )

    def load_chat_history_from_db(self):
        """Load chat history from database when switching modules"""
        if hasattr(self, 'db') and 'current_module' in st.session_state:
            saved_history = self.db.load_chat_history(
                st.session_state.user_id,
                st.session_state.current_module
            )
            if saved_history:
                st.session_state.chat_history = saved_history
                return True
        return False
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
                    st.success("✅ Answer submitted!")
                    
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
                    st.success("✅ Answer submitted!")
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
    def check_authentication(self) -> bool:
        """Check if user is authenticated"""
        # Initialize authentication state
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        
        # Check for existing session token
        if 'session_token' in st.session_state:
            user_info = self.auth.validate_session(st.session_state.session_token)
            if user_info:
                st.session_state.authenticated = True
                st.session_state.user_id = f"user_{user_info['user_id']}"
                st.session_state.username = user_info['username']
                st.session_state.display_name = user_info['display_name']
                st.session_state.role = user_info['role']
                st.session_state.db_user_id = user_info['user_id']  # Store numeric ID for DB
                return True
            else:
                st.session_state.authenticated = False
                return False
        
        return st.session_state.authenticated

    def render_login_screen(self):
        """Render login/signup screen"""
        # Center the content
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 40px 0 20px 0;">
                <h1 style="font-size: 3rem; margin: 0;">🤖 StudyBot</h1>
                <p style="font-size: 1.3rem; color: #667eea; margin-top: 10px;">
                    Your AI-Powered Python Learning Journey
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Tabs for Login and Sign Up
            tab1, tab2 = st.tabs(["🔑 Login", "✨ Create Account"])
            
            with tab1:
                st.markdown("### Welcome Back!")
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input(
                        "Username",
                        key="login_username",
                        placeholder="Enter your username"
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        key="login_password",
                        placeholder="Enter your password"
                    )
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        submit = st.form_submit_button(
                            "Login",
                            use_container_width=True,
                            type="primary"
                        )
                    with col_btn2:
                        demo = st.form_submit_button(
                            "Try Demo",
                            use_container_width=True
                        )
                    
                    if submit:
                        if username and password:
                            with st.spinner("Logging in..."):
                                result = self.auth.authenticate_user(username, password)
                            
                            if result['success']:
                                st.session_state.authenticated = True
                                st.session_state.user_id = f"user_{result['user_id']}"
                                st.session_state.username = result['username']
                                st.session_state.display_name = result['display_name']
                                st.session_state.role = result['role']
                                st.session_state.session_token = result['session_token']
                                st.session_state.db_user_id = result['user_id']
                                st.rerun()
                            else:
                                st.error(result['message'])
                        else:
                            st.error("Please enter both username and password")
                    
                    if demo:
                        # Create/login demo user
                        demo_username = "demo_student"
                        demo_password = "demo123"
                        
                        # Try to login first
                        result = self.auth.authenticate_user(demo_username, demo_password)
                        
                        if not result['success']:
                            # Create demo user if doesn't exist
                            create_result = self.auth.create_user(
                                username=demo_username,
                                password=demo_password,
                                display_name="Demo Student",
                                role="student"
                            )
                            if create_result['success']:
                                result = self.auth.authenticate_user(demo_username, demo_password)
                        
                        if result['success']:
                            st.session_state.authenticated = True
                            st.session_state.user_id = f"user_{result['user_id']}"
                            st.session_state.username = result['username']
                            st.session_state.display_name = result['display_name']
                            st.session_state.role = result['role']
                            st.session_state.session_token = result['session_token']
                            st.session_state.db_user_id = result['user_id']
                            st.rerun()
            
            with tab2:
                st.markdown("### Join StudyBot!")
                with st.form("signup_form", clear_on_submit=False):
                    new_username = st.text_input(
                        "Username*",
                        key="signup_username",
                        placeholder="Choose a username (min 3 characters)",
                        help="Letters, numbers, _ and - only"
                    )
                    new_display_name = st.text_input(
                        "Display Name",
                        key="signup_display_name",
                        placeholder="What should we call you?"
                    )
                    new_email = st.text_input(
                        "Email (optional)",
                        key="signup_email",
                        placeholder="your.email@example.com"
                    )
                    new_password = st.text_input(
                        "Password*",
                        type="password",
                        key="signup_password",
                        placeholder="Create a password (min 6 characters)"
                    )
                    confirm_password = st.text_input(
                        "Confirm Password*",
                        type="password",
                        key="signup_confirm",
                        placeholder="Type password again"
                    )
                    
                    role = st.selectbox(
                        "I am a:",
                        ["student", "parent", "teacher"],
                        help="Choose your role"
                    )
                    
                    submit = st.form_submit_button(
                        "Create Account",
                        use_container_width=True,
                        type="primary"
                    )
                    
                    if submit:
                        if new_username and new_password:
                            if new_password != confirm_password:
                                st.error("❌ Passwords don't match!")
                            else:
                                with st.spinner("Creating your account..."):
                                    result = self.auth.create_user(
                                        username=new_username,
                                        password=new_password,
                                        email=new_email if new_email else None,
                                        role=role,
                                        display_name=new_display_name if new_display_name else new_username
                                    )
                                
                                if result['success']:
                                    st.success(result['message'])
                                    st.info("✨ Please login with your new account!")
                                    # Switch to login tab
                                else:
                                    st.error(result['message'])
                        else:
                            st.error("❌ Please fill in username and password")
            
            # Footer
            st.markdown("""
            <div style="text-align: center; margin-top: 40px; padding: 20px; color: #666;">
                <p>🐍 Learn Python through AI-powered Socratic tutoring</p>
                <p style="font-size: 0.9rem;">🎮 Gamification • 📚 Flashcards • 🧪 Quizzes • 💻 Code Practice</p>
            </div>
            """, unsafe_allow_html=True)

    def render_user_sidebar(self):
        """Render user info and logout in sidebar"""
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**👤 {st.session_state.display_name}**")
            st.caption(f"@{st.session_state.username} • {st.session_state.role}")
            
            if st.button("🚪 Logout", use_container_width=True):
                if 'session_token' in st.session_state:
                    self.auth.logout(st.session_state.session_token)
                
                # Clear all session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                
                st.rerun()
    
    def run(self):
        """Main application runner with authentication"""
        
        # CHECK AUTHENTICATION FIRST
        if not self.check_authentication():
            self.render_login_screen()
            return
        
        # Initialize/ensure parental settings exist for this user
        if 'parental_settings' not in st.session_state:
            self.parental_control.initialize_parental_settings(st.session_state.user_id)
        
        # Show user info in sidebar
        self.render_user_sidebar()
        
        # Check time limits if parental controls enabled
        if st.session_state.parental_settings['enabled']:
            self.check_time_limit_warning()
            if 'last_time_check' not in st.session_state:
                st.session_state.last_time_check = datetime.now()
            
            time_diff = (datetime.now() - st.session_state.last_time_check).seconds / 60
            if time_diff >= 1:
                self.parental_control.increment_session_time(1)
                st.session_state.last_time_check = datetime.now()
        
        self.render_header()
        
        if st.session_state.show_parent_panel:
            self.render_parental_dashboard()
            return
        
        if not self.load_modules():
            return
            
        self.render_sidebar()
        self.render_chat_interface()
if __name__ == "__main__":
    app = EnhancedStudyBotApp()
    app.run()