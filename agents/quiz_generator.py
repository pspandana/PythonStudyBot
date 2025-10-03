from typing import Dict, List, Any, Optional
import json
import random
from utils.openai_client import OpenAIClient
from content.prompts import PromptManager

class QuizGenerator:
    """AI agent that generates dynamic quizzes based on module content and student performance"""
    
    def __init__(self, openai_client, prompt_manager):
        self.client = openai_client
        self.prompts = prompt_manager
        
        # Fallback quiz templates for when AI generation fails
        self.fallback_templates = {
            'python_basics': [
                {
                    'type': 'multiple_choice',
                    'question': 'What does the print() function do? 🤔',
                    'options': [
                        'A) Saves a file',
                        'B) Shows text on screen',
                        'C) Deletes code',
                        'D) Creates variables'
                    ],
                    'correct_answer': 'B) Shows text on screen',
                    'explanation': 'Great! print() displays text on the screen so we can see our results! 🎉'
                },
                {
                    'type': 'free_response',
                    'question': 'Write code that creates a variable called "age" and stores your age in it.',
                    'sample_answer': 'age = 12',
                    'explanation': (
                        "Perfect! You created a variable — that's like making a labeled box "
                        "to store your age! 📦"
                    )
                }
            ]
        }
    
    def generate_quiz(self, module: Dict[str, Any], difficult_topics: List[str] = None) -> Dict[str, Any]:
        """Generate a complete quiz for a module"""
        
        # Try to generate quiz using AI
        ai_quiz = self.generate_ai_quiz(module, difficult_topics)
        
        if ai_quiz and self.validate_quiz(ai_quiz):
            return ai_quiz
        
        # Fallback to template-based quiz
        return self.generate_fallback_quiz(module, difficult_topics)
    
    def generate_ai_quiz(self, module: Dict[str, Any], difficult_topics: List[str] = None) -> Optional[Dict[str, Any]]:
        """Generate quiz using AI"""
        try:
            prompt = self.prompts.get_quiz_generation_prompt(module, difficult_topics)
            quiz_response = self.client.generate_json_response(prompt, temperature=0.3)
            
            if quiz_response and 'questions' in quiz_response:
                return quiz_response
        except Exception as e:
            print(f"AI quiz generation failed: {e}")
        
        return None
    
    def generate_fallback_quiz(self, module: Dict[str, Any], difficult_topics: List[str] = None) -> Dict[str, Any]:
        """Generate fallback quiz when AI generation fails"""
        
        questions = []
        
        # Use basic templates and customize them
        base_questions = self.fallback_templates.get('python_basics', [])
        
        # Customize questions based on module content
        if module.get('content'):
            questions.extend(self.create_content_based_questions(module))
        
        # Add code example questions
        if module.get('code_examples'):
            questions.extend(self.create_code_example_questions(module))
        
        # If we still don't have enough questions, use templates
        while len(questions) < 5:
            questions.extend(base_questions)
            if len(questions) >= 5:
                break
        
        # Take first 5 questions and shuffle for variety
        questions = questions[:5]
        random.shuffle(questions)
        
        return {
            'questions': questions,
            'module_id': module.get('id'),
            'module_title': module.get('title'),
            'total_questions': len(questions),
            'difficulty_focus': difficult_topics or [],
            'generation_method': 'fallback'
        }
    
    def create_content_based_questions(self, module: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create questions based on module content"""
        questions = []
        content = module.get('content', [])
        
        # Extract key concepts from content
        concepts = self.extract_key_concepts(content)
        
        for i, concept in enumerate(concepts[:2]):  # Limit to 2 content-based questions
            if i % 2 == 0:
                # Multiple choice question
                questions.append({
                    'type': 'multiple_choice',
                    'question': f'What is the main idea about {concept}? 🤔',
                    'options': [
                        f'A) {concept} is used for calculations',
                        f'B) {concept} is a Python concept we learned',
                        f'C) {concept} is not important',
                        f'D) {concept} is only for experts'
                    ],
                    'correct_answer': f'B) {concept} is a Python concept we learned',
                    'explanation': f'Exactly! {concept} is an important concept in Python! Great job! 🌟'
                })
            else:
                # Free response question
                questions.append({
                    'type': 'free_response',
                    'question': f'Can you explain what {concept} means to you?',
                    'sample_answer': f'{concept} is a Python concept that helps us write better code.',
                    'explanation': f'Nice thinking about {concept}! You\'re really understanding these concepts! 🎉'
                })
        
        return questions
    
    def create_code_example_questions(self, module: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create questions based on code examples"""
        questions = []
        code_examples = module.get('code_examples', [])
        
        for i, code in enumerate(code_examples[:2]):  # Limit to 2 code questions
            # Simple code understanding question
            simplified_code = code.split('\n')[0] if '\n' in code else code
            
            questions.append({
                'type': 'multiple_choice',
                'question': f'What does this code do?\npython\n{simplified_code}\n\n💻',
                'options': [
                    'A) It creates an error',
                    'B) It runs a Python command',
                    'C) It deletes files',
                    'D) It does nothing'
                ],
                'correct_answer': 'B) It runs a Python command',
                'explanation': 'Great! You can read Python code! That\'s awesome! 🚀'
            })
        
        return questions
    
    def extract_key_concepts(self, content: List[str]) -> List[str]:
        """Extract key concepts from module content"""
        concepts = []
        
        for line in content:
            if not isinstance(line, str):
                continue
                
            # Look for headers and important terms
            if line.startswith('#'):
                concept = line.strip('#').strip()
                if 0 < len(concept) < 50:
                    concepts.append(concept)
            elif line.startswith('') and line.endswith(''):
                concept = line.strip('*').strip()
                if 0 < len(concept) < 50:
                    concepts.append(concept)
            elif line.startswith('') and line.endswith(''):
                concept = line.strip('*').strip()
                if 0 < len(concept) < 50:
                    concepts.append(concept)
        
        # Remove duplicates and limit
        unique_concepts = list(dict.fromkeys(concepts))  # Preserves order while removing duplicates
        return unique_concepts[:5]  # Limit to 5 concepts
    
    def validate_quiz(self, quiz: Dict[str, Any]) -> bool:
        """Validate that a quiz has the required structure"""
        try:
            if not isinstance(quiz, dict):
                return False
            
            if 'questions' not in quiz:
                return False
            
            questions = quiz['questions']
            if not isinstance(questions, list) or len(questions) == 0:
                return False
            
            # Validate each question
            for question in questions:
                if not isinstance(question, dict):
                    return False
                
                required_fields = ['type', 'question', 'explanation']
                if not all(field in question for field in required_fields):
                    return False
                
                # Validate specific question types
                if question['type'] == 'multiple_choice':
                    if not all(field in question for field in ['options', 'correct_answer']):
                        return False
                elif question['type'] == 'free_response':
                    if 'sample_answer' not in question:
                        return False
            
            return True
            
        except Exception as e:
            print(f"Quiz validation error: {e}")
            return False
    
    def customize_quiz_for_performance(self, base_quiz: Dict[str, Any], 
                                     student_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Customize quiz based on student's past performance"""
        
        if not student_performance:
            return base_quiz
        
        # Get topics student struggled with
        weak_topics = student_performance.get('weak_topics', [])
        strong_topics = student_performance.get('strong_topics', [])
        
        # Adjust question difficulty and focus
        customized_questions = []
        
        for question in base_quiz.get('questions', []):
            # Add more questions on weak topics
            question_topic = self.extract_topic_from_question(question)
            
            if question_topic in weak_topics:
                # Make question easier or add more context
                question['difficulty'] = 'easy'
                question['extra_hint'] = True
                customized_questions.append(question)
            elif question_topic not in strong_topics:
                # Keep normal questions for topics not mastered
                customized_questions.append(question)
        
        # Ensure we have enough questions
        if len(customized_questions) < 3:
            customized_questions.extend(base_quiz['questions'][:3])
        
        return {
            **base_quiz,
            'questions': customized_questions[:5],
            'personalized': True,
            'focus_areas': weak_topics
        }
    
    def extract_topic_from_question(self, question: Dict[str, Any]) -> str:
        """Extract the main topic from a question"""
        question_text = question.get('question', '').lower()
        
        # Simple keyword matching for topics
        topics = {
            'variables': ['variable', 'age', 'name', 'store'],
            'print': ['print', 'display', 'output', 'screen'],
            'functions': ['function', 'def', 'call', 'return'],
            'loops': ['loop', 'for', 'while', 'repeat'],
            'conditions': ['if', 'else', 'condition', 'compare']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in question_text for keyword in keywords):
                return topic
        
        return 'general'
    
    def calculate_score(self, quiz: Dict[str, Any], user_answers: List[str]) -> int:
        """Calculate the score based on user answers"""
        if not quiz or 'questions' not in quiz:
            return 0
        
        questions = quiz['questions']
        score = 0
        
        for i, question in enumerate(questions):
            if i >= len(user_answers):
                break
                
            user_answer = user_answers[i]
            
            if question['type'] == 'multiple_choice':
                # For multiple choice, check exact match
                correct_answer = question.get('correct_answer', '')
                if user_answer == correct_answer:
                    score += 1
            elif question['type'] == 'free_response':
                # For free response, simple keyword matching
                sample_answer = question.get('sample_answer', '').lower()
                user_answer_lower = user_answer.lower()
                
                # Check if key concepts are mentioned
                if any(word in user_answer_lower for word in sample_answer.split() if len(word) > 3):
                    score += 1
        
        return score