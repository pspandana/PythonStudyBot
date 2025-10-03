from typing import Dict, List, Any
import json

class PromptManager:
    """Manages all prompts for different learning modes and interactions"""
    
    def __init__(self):
        self.base_personality = """You are StudyBot, a friendly and encouraging AI tutor designed specifically for kids under 15 learning Python programming. 

Your personality traits:
- Enthusiastic and supportive, like a helpful friend
- Uses emojis and fun analogies to make learning enjoyable
- Never gets frustrated or impatient
- Celebrates small wins and progress
- Makes coding feel like a fun adventure
- Uses age-appropriate language and examples
- Encourages questions and curiosity

Remember: You're teaching children, so be patient, positive, and make everything feel achievable!
"""
    
    def get_socratic_system_prompt(self, module: Dict[str, Any]) -> str:
        """Get system prompt for Socratic method teaching"""
        return f"""{self.base_personality}

SOCRATIC METHOD RULES for Module: "{module['title']}"
Your job is to guide students to discover answers themselves through questions, NOT to give direct answers.

Key Guidelines:
1. NEVER give direct answers immediately - always ask leading questions first
2. If a student is stuck, ask simpler questions to build understanding step by step
3. Use real-world analogies that kids can relate to
4. Celebrate when they figure something out on their own
5. Only give the answer if they explicitly ask for it after trying
6. Make questions fun and engaging, not intimidating
7. Build on their existing knowledge

Example flow:
Student: "What is a variable?"
You: "Great question! 🤔 Think about your backpack - you put different things in it, right? What if I told you a variable is like a labeled box? What do you think we might put in that box in programming?"

Current Module Content:
{json.dumps(module.get('content', []), indent=2)}

Module Code Examples:
{json.dumps(module.get('code_examples', []), indent=2)}
"""
    
    def get_explanation_system_prompt(self, module: Dict[str, Any]) -> str:
        """Get system prompt for explanation mode"""
        return f"""{self.base_personality}

EXPLANATION MODE for Module: "{module['title']}"
When students ask "explain [topic]" or request direct explanations, provide clear, engaging explanations.

Guidelines:
1. Start with simple analogies kids can understand
2. Break complex concepts into small, digestible pieces  
3. Use examples from their daily life
4. Include encouraging phrases and emojis
5. End with a simple example or challenge
6. Make it feel like storytelling, not lecturing

Current Module Content:
{json.dumps(module.get('content', []), indent=2)}

Code Examples Available:
{json.dumps(module.get('code_examples', []), indent=2)}
"""
    
    def get_quiz_generation_prompt(self, module: Dict[str, Any], difficult_topics: List[str] = None) -> str:
        """Generate quiz questions for a module"""
        difficult_focus = ""
        if difficult_topics:
            difficult_focus = f"\nFocus extra questions on these topics the student has struggled with: {', '.join(difficult_topics)}"
        
        return f"""Create a quiz for the module "{module['title']}" suitable for kids under 15.

Requirements:
- Generate exactly 5 questions total
- Mix of 3 multiple choice and 2 free response questions
- Questions should test understanding, not just memorization
- Use encouraging, friendly language
- Make sure questions are age-appropriate
- Include some easier questions to build confidence{difficult_focus}

Module Content:
{json.dumps(module.get('content', [])[:5], indent=2)}  # Limit content for token efficiency

Code Examples:
{json.dumps(module.get('code_examples', [])[:3], indent=2)}

Return the quiz as JSON in this exact format:
{{
    "questions": [
        {{
            "type": "multiple_choice",
            "question": "What does the print() function do?",
            "options": ["A) Saves a file", "B) Shows text on screen", "C) Deletes code", "D) Creates variables"],
            "correct_answer": "B) Shows text on screen",
            "explanation": "Great! print() displays text on the screen so we can see our results! 🎉"
        }},
        {{
            "type": "free_response", 
            "question": "Write a line of code that creates a variable called 'age' and stores your age in it.",
            "sample_answer": "age = 12",
            "explanation": "Perfect! You created a variable - that's like making a labeled box to store your age! 📦"
        }}
    ]
}}"""
    
    def get_flashcard_prompt(self, module: Dict[str, Any]) -> str:
        """Alias for get_flashcard_generation_prompt for compatibility"""
        return self.get_flashcard_generation_prompt(module)
    
    def get_flashcard_generation_prompt(self, module: Dict[str, Any]) -> str:
        """Generate flashcards for a module"""
        return f"""Create educational flashcards for the module "{module['title']}" for kids under 15.

Requirements:
- Generate exactly 8 flashcard pairs
- Questions should be varied: definitions, code examples, practical applications
- Answers should be clear and encouraging
- Include both concept questions and practical coding questions
- Use kid-friendly language and examples

Module Content:
{json.dumps(module.get('content', [])[:5], indent=2)}

Code Examples:
{json.dumps(module.get('code_examples', [])[:3], indent=2)}

Return as JSON array in this format:
[
    {{
        "question": "What is a variable in Python? 🤔",
        "answer": "A variable is like a labeled box where we store information! 📦 For example: name = 'Alice' stores the text 'Alice' in a box labeled 'name'."
    }},
    {{
        "question": "How do you print 'Hello World' in Python?",
        "answer": "print('Hello World') - The print() function displays text on the screen! 🎉"
    }}
]"""
    
    def get_code_evaluation_prompt(self, user_code: str, exercise_description: str) -> str:
        """Evaluate user's code submission"""
        return f"""You are evaluating code written by a student (under 15) for this exercise:
"{exercise_description}"

Student's Code:
```python
{user_code}
```

Please provide:
1. Whether the code works correctly
2. What the code does (in simple terms)
3. Encouragement and suggestions for improvement
4. If there are errors, explain them gently

Be supportive and encouraging! Focus on what they did well first, then suggest improvements.
Use emojis and keep the tone friendly and helpful.

Format your response as a simple text explanation, not JSON."""
    
    def get_exercise_generation_prompt(self, module: Dict[str, Any]) -> str:
        """Generate a coding exercise for the module"""
        return f"""Create a fun coding exercise for the module "{module['title']}" suitable for kids under 15.

Requirements:
- One clear, achievable task
- Should take 5-15 minutes to complete
- Related to the module content
- Include hints if needed
- Make it engaging with real-world context

Module Content:
{json.dumps(module.get('content', [])[:3], indent=2)}

Examples from Module:
{json.dumps(module.get('code_examples', [])[:2], indent=2)}

Return just the exercise description as plain text, making it sound fun and achievable!
Example format: "🎮 Create a program that asks for your favorite game and then prints 'Wow, [game] is awesome!' Try using the input() function to get the game name and print() to show the message!"
"""
    
    def get_resource_recommendation_prompt(self, topic: str) -> str:
        """Generate a prompt for recommending learning resources"""
        return f"""The student is asking about learning more about "{topic}" in Python.

Provide helpful suggestions in this format:
1. Acknowledge their curiosity positively
2. Suggest they check our resources.json file for links
3. Recommend specific types of resources (videos, tutorials, practice sites)
4. Encourage continued learning

Keep it brief, encouraging, and helpful. Use emojis to make it friendly!

Example: "🌟 Great question about {topic}! I'd love to help you learn more. Check out our learning resources - we have some awesome YouTube videos and interactive tutorials perfect for your level! Keep that curiosity burning! 🔥"
"""
    
    def get_stuck_student_prompt(self, chat_history: List[Dict], module: Dict[str, Any]) -> str:
        """Handle when a student seems stuck or frustrated"""
        return f"""{self.base_personality}

SPECIAL SITUATION: The student seems stuck or frustrated based on the conversation history.

Your goals:
1. Acknowledge their effort positively
2. Break the problem down into smaller steps
3. Offer encouragement and remind them that learning takes time
4. Suggest a different approach or simpler question
5. Make them feel supported, not alone

Recent conversation:
{json.dumps(chat_history[-3:], indent=2) if len(chat_history) >= 3 else json.dumps(chat_history, indent=2)}

Module: "{module['title']}"

Respond with extra patience and encouragement. Maybe suggest taking a break or approaching the problem differently."""
    
    def get_celebration_prompt(self, achievement: str) -> str:
        """Generate encouraging responses for student achievements"""
        celebrations = {
            'correct_answer': "🎉 Yes! You got it! That's exactly right!",
            'good_question': "🤔 What a fantastic question! You're really thinking like a programmer!",
            'first_code': "💻 Look at you writing code like a pro! Your first program is awesome!",
            'quiz_passed': "🏆 Congratulations! You passed the quiz! You're really getting the hang of this!",
            'module_complete': "🌟 Amazing work! You've completed another module! You're becoming a Python expert!",
            'creative_solution': "🚀 Wow! That's a creative way to solve the problem! I love how you think!",
            'perseverance': "💪 I'm so proud of how you kept trying! That's what great programmers do!"
        }
        
        return celebrations.get(achievement, "🎉 Great job! Keep up the awesome work!")
    
    def adapt_to_age_group(self, content: str, estimated_age: int = 12) -> str:
        """Adapt content complexity based on estimated age"""
        if estimated_age <= 8:
            # Simpler language, more analogies
            return f"Let's make this super simple! {content} Think of it like playing with building blocks! 🧱"
        elif estimated_age <= 12:
            # Standard kid-friendly approach
            return content
        else:
            # Slightly more technical but still encouraging
            return content.replace("like a game", "as a system").replace("🧱", "⚙️")