from typing import Dict, List, Any, Optional
import json
import re
from utils.openai_client import OpenAIClient
from content.prompts import PromptManager

class SocraticTutor:
    """AI tutor that uses the Socratic method to guide student learning"""
    
    def __init__(self, openai_client: OpenAIClient, prompt_manager: PromptManager):
        self.client = openai_client
        self.prompts = prompt_manager
        self.conversation_context = {}  # Track conversation context per user
        
        # Load learning resources
        self.resources = self.load_resources()
    
    def load_resources(self) -> Dict[str, List[str]]:
        """Load learning resources from JSON file"""
        try:
            import os
            resources_path = os.path.join(os.path.dirname(__file__), '..', 'content', 'resources.json')
            if os.path.exists(resources_path):
                with open(resources_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        # Fallback resources
        return {
            "python_basics": [
                "https://www.python.org/about/gettingstarted/",
                "https://www.codecademy.com/learn/learn-python-3",
                "https://python.org/",
            ],
            "python_videos": [
                "Python for Beginners - Programming with Mosh",
                "Learn Python - Full Course for Beginners - freeCodeCamp",
                "Python Tutorial - Python for Beginners - Programming with Mosh"
            ],
            "practice_sites": [
                "https://codingbat.com/python",
                "https://www.hackerrank.com/domains/python",
                "https://python.org/shell/"
            ],
            "python_games": [
                "https://reeborg.ca/reeborg.html",
                "https://checkio.org/",
                "https://codecombat.com/"
            ]
        }
    
    def respond(self, user_input: str, module: Dict[str, Any], 
                chat_history: List[Dict[str, str]]) -> str:
        """Generate a Socratic response to user input"""
        
        # Check if user is asking for resources
        if self.is_asking_for_resources(user_input):
            return self.provide_resources(user_input)
        
        # Check if user explicitly asks for the answer
        if self.is_asking_for_direct_answer(user_input):
            return self.provide_direct_answer(user_input, module, chat_history)
        
        # Check if user seems stuck or frustrated
        if self.detect_frustration(user_input, chat_history):
            return self.handle_stuck_student(user_input, module, chat_history)
        
        # Generate Socratic response
        return self.generate_socratic_response(user_input, module, chat_history)
    
    def is_asking_for_resources(self, user_input: str) -> bool:
        """Detect if user is asking for learning resources"""
        resource_keywords = [
            'where can i learn', 'learn more about', 'resources', 'links',
            'youtube', 'videos', 'tutorials', 'websites', 'practice',
            'more information', 'study materials'
        ]
        
        return any(keyword in user_input.lower() for keyword in resource_keywords)
    
    def provide_resources(self, user_input: str) -> str:
        """Provide learning resources based on user request"""
        # Extract topic from user input
        topic = self.extract_topic_from_query(user_input)
        
        resource_response = f"🌟 Great question! I love that you want to learn more about {topic}! "
        
        # Suggest relevant resources
        if any(word in user_input.lower() for word in ['video', 'youtube', 'watch']):
            resource_response += "\n\n📺 **Awesome Video Resources:**\n"
            for video in self.resources.get('python_videos', [])[:3]:
                resource_response += f"• {video}\n"
        
        if any(word in user_input.lower() for word in ['practice', 'exercise', 'code']):
            resource_response += "\n\n💻 **Cool Practice Sites:**\n"
            for site in self.resources.get('practice_sites', [])[:3]:
                resource_response += f"• {site}\n"
        
        if any(word in user_input.lower() for word in ['game', 'fun', 'play']):
            resource_response += "\n\n🎮 **Fun Learning Games:**\n"
            for game in self.resources.get('python_games', [])[:3]:
                resource_response += f"• {game}\n"
        
        # Always include basic resources
        if "Video Resources" not in resource_response:
            resource_response += "\n\n📚 **Great Learning Resources:**\n"
            for resource in self.resources.get('python_basics', [])[:3]:
                resource_response += f"• {resource}\n"
        
        resource_response += "\n\nKeep that curiosity burning! 🔥 Learning never stops being awesome! 🚀"
        
        return resource_response
    
    def extract_topic_from_query(self, user_input: str) -> str:
        """Extract the main topic from user's resource request"""
        # Simple extraction - could be improved with NLP
        common_topics = [
            'python', 'variables', 'functions', 'loops', 'lists', 
            'dictionaries', 'conditionals', 'classes', 'modules'
        ]
        
        user_lower = user_input.lower()
        for topic in common_topics:
            if topic in user_lower:
                return topic
        
        return "Python programming"
    
    def is_asking_for_direct_answer(self, user_input: str) -> bool:
        """Detect if user is explicitly asking for the answer"""
        direct_answer_phrases = [
            'just tell me', 'give me the answer', 'what is the answer',
            'i give up', 'i need the answer', 'just show me',
            'can you tell me', 'please tell me'
        ]
        
        return any(phrase in user_input.lower() for phrase in direct_answer_phrases)
    
    def provide_direct_answer(self, user_input: str, module: Dict[str, Any], 
                            chat_history: List[Dict[str, str]]) -> str:
        """Provide direct answer when explicitly requested"""
        # First acknowledge their request positively
        acknowledgment = "🌟 Of course! I can see you've been thinking hard about this. "
        
        # Get the explanation
        system_prompt = self.prompts.get_explanation_system_prompt(module)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please explain this directly: {user_input}"}
        ]
        
        explanation = self.client.generate_chat_response(messages, temperature=0.3)
        
        # Add encouragement
        encouragement = "\n\n💪 Now that you know the answer, do you want to try a related question to practice? Learning is all about trying, making mistakes, and growing! 🌱"
        
        return acknowledgment + explanation + encouragement
    
    def detect_frustration(self, user_input: str, chat_history: List[Dict[str, str]]) -> bool:
        """Detect if student seems frustrated or stuck"""
        frustration_indicators = [
            'i don\'t understand', 'this is hard', 'i\'m confused',
            'i don\'t get it', 'this makes no sense', 'i\'m stuck',
            'i can\'t do this', 'this is too difficult', 'help me',
            'i\'m lost', 'what does this mean'
        ]
        
        recent_responses = [msg['content'].lower() for msg in chat_history[-3:] if msg['role'] == 'user']
        
        # Check current input
        if any(phrase in user_input.lower() for phrase in frustration_indicators):
            return True
        
        # Check for repeated similar questions
        if len(recent_responses) >= 2:
            current_lower = user_input.lower()
            for response in recent_responses:
                if len(current_lower) > 10 and current_lower in response:
                    return True
        
        return False
    
    def handle_stuck_student(self, user_input: str, module: Dict[str, Any], 
                           chat_history: List[Dict[str, str]]) -> str:
        """Handle when student appears stuck or frustrated"""
        system_prompt = self.prompts.get_stuck_student_prompt(chat_history, module)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        return self.client.generate_chat_response(messages, temperature=0.8)
    
    def generate_socratic_response(self, user_input: str, module: Dict[str, Any], 
                                 chat_history: List[Dict[str, str]]) -> str:
        """Generate a Socratic method response"""
        # Check if OpenAI client is available
        if not self.client.client:
            return self.generate_fallback_response(user_input, module)
        
        system_prompt = self.prompts.get_socratic_system_prompt(module)
        
        # Build conversation context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent chat history for context (limit to avoid token overflow)
        recent_history = chat_history[-6:] if len(chat_history) > 6 else chat_history
        for msg in recent_history:
            messages.append({"role": msg['role'], "content": msg['content']})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        response = self.client.generate_chat_response(messages, temperature=0.7)
        
        # If OpenAI response is empty or error, use fallback
        if not response or response.startswith("❌") or response.startswith("🤖 I'd love to chat"):
            return self.generate_fallback_response(user_input, module)
        
        return response
    
    def generate_fallback_response(self, user_input: str, module: Dict[str, Any]) -> str:
        """Generate helpful responses without AI"""
        user_input_lower = user_input.lower()
        module_title = module.get('title', 'this topic')
        
        # Handle common questions about the current module
        if any(word in user_input_lower for word in ['what', 'how', 'explain', 'help']):
            if 'python' in user_input_lower:
                return f"🐍 Great question about Python! Python is a friendly programming language that's perfect for beginners. It's used to build websites, games, apps, and even control robots! Python code is easy to read and write - it's almost like writing in English. What would you like to know more about?"
            
            elif any(word in user_input_lower for word in ['function', 'loop', 'variable', 'list', 'dict']):
                return f"🤔 That's a fantastic question about programming concepts! In {module_title}, we cover this topic. Try looking at the code examples in this module - they'll show you exactly how it works! Want to try writing some code? Switch to 'Code Practice' mode!"
        
        # Handle greetings
        elif any(word in user_input_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
            return f"👋 Hello there! Welcome to {module_title}! I'm excited to help you learn Python. What would you like to explore today? You can ask me about Python concepts, request explanations, or even ask for coding challenges!"
        
        # Handle encouragement requests
        elif any(word in user_input_lower for word in ['hard', 'difficult', 'stuck', 'confused', 'don\'t understand']):
            return f"💪 Hey, learning programming can be challenging, but you're doing great! Remember: Every expert was once a beginner. Python is designed to be friendly! Try breaking down the problem into smaller steps, and don't hesitate to experiment with the code examples in this module."
        
        # Handle examples requests
        elif any(word in user_input_lower for word in ['example', 'show me', 'demonstrate']):
            examples = module.get('code_examples', [])
            if examples:
                return f"📋 Here's a cool example from {module_title}: {examples[0]} - Try running this code! What do you think it will do?"
            else:
                return f"💻 Great idea to look for examples! Check out the code examples section in {module_title} - there are some awesome snippets to try!"
        
        # Default response with proactive teaching
        return f"🤖 That's an interesting question about {module_title}! Let me help you explore this step by step. Instead of just giving you the answer, let's discover it together! What do you think might happen if we tried a simple example? For instance, what would you expect from this basic Python code: print('Hello')? This will help us understand the concepts better! 🎯"
    
    def explain_topic(self, topic: str, module: Dict[str, Any]) -> str:
        """Provide explanation for a specific topic"""
        if not self.client.client:
            return self.generate_explanation_fallback(topic, module)
        
        system_prompt = self.prompts.get_explanation_system_prompt(module)
        prompt = f"Please explain '{topic}' in a clear, engaging way for kids."
        
        response = self.client.generate_response(prompt, system_prompt, temperature=0.5)
        
        # If OpenAI response is empty or error, use fallback
        if not response or response.startswith("❌") or response.startswith("🤖"):
            return self.generate_explanation_fallback(topic, module)
        
        return response
    
    def generate_explanation_fallback(self, topic: str, module: Dict[str, Any]) -> str:
        """Generate explanation without AI"""
        module_title = module.get('title', 'this module')
        content = module.get('content', [])
        examples = module.get('code_examples', [])
        
        response = f"📖 Great question about '{topic}'! In {module_title}, "
        
        # Look for relevant content
        relevant_content = [item for item in content if topic.lower() in item.lower()]
        if relevant_content:
            response += f"we learn that {relevant_content[0]} "
        
        # Add code examples if available
        if examples:
            response += f"Here's a code example: {examples[0]} "
        
        response += f"Want to learn more? Try exploring the '{module_title}' content or switch to 'Code Practice' mode to experiment!"
        
        return response
    
    def check_understanding(self, user_response: str, expected_concept: str) -> Dict[str, Any]:
        """Check if user understands a concept based on their response"""
        
        # Use OpenAI to evaluate understanding
        evaluation_prompt = f"""
        Evaluate if the student understands the concept of "{expected_concept}" based on their response: "{user_response}"
        
        Rate understanding on a scale of 1-5:
        1 - No understanding
        2 - Minimal understanding  
        3 - Partial understanding
        4 - Good understanding
        5 - Excellent understanding
        
        Return JSON format:
        {{
            "understanding_level": 3,
            "explanation": "Student shows partial understanding but needs clarification on...",
            "next_question": "Can you tell me more about...?"
        }}
        """
        
        result = self.client.generate_json_response(evaluation_prompt)
        
        if result:
            return result
        else:
            # Fallback evaluation
            return {
                "understanding_level": 3,
                "explanation": "I can see you're thinking about this! 🤔",
                "next_question": "Can you tell me more about what you think?"
            }
    
    def generate_follow_up_question(self, user_response: str, topic: str) -> str:
        """Generate an appropriate follow-up question"""
        
        follow_up_prompt = f"""
        The student said: "{user_response}" about the topic "{topic}".
        
        Generate an encouraging follow-up question that:
        1. Builds on what they said
        2. Guides them deeper into understanding
        3. Uses the Socratic method
        4. Is appropriate for kids under 15
        5. Includes encouragement and emojis
        
        Make it engaging and not intimidating!
        """
        
        return self.client.generate_response(follow_up_prompt, temperature=0.8)
    
    def celebrate_progress(self, achievement_type: str = "general") -> str:
        """Generate celebratory response for student progress"""
        return self.prompts.get_celebration_prompt(achievement_type)
    
    def adapt_difficulty(self, user_performance: Dict[str, Any], current_topic: str) -> str:
        """Adapt question difficulty based on user performance"""
        
        if user_performance.get('understanding_level', 3) >= 4:
            # Student is doing well, can handle more complexity
            prompt = f"Generate a slightly more challenging question about {current_topic} for a student who understands the basics well."
        elif user_performance.get('understanding_level', 3) <= 2:
            # Student is struggling, simplify
            prompt = f"Generate a simpler, more basic question about {current_topic} to help build confidence."
        else:
            # Student is at appropriate level
            prompt = f"Generate an appropriate follow-up question about {current_topic} at the current difficulty level."
        
        return self.client.generate_response(prompt, temperature=0.7)