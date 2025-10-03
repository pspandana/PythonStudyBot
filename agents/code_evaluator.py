from typing import Dict, List, Any, Optional
import re
import ast
from utils.openai_client import OpenAIClient

class CodeEvaluator:
    """AI agent for evaluating and providing feedback on student code"""
    
    def __init__(self, openai_client: OpenAIClient):
        self.client = openai_client
        
        # Safe built-ins for code execution
        self.safe_builtins = {
            'print': print,
            'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
            'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
            'range': range, 'enumerate': enumerate, 'zip': zip,
            'sum': sum, 'max': max, 'min': min, 'abs': abs, 'round': round,
            'type': type, 'isinstance': isinstance, 'sorted': sorted,
            'reversed': reversed, 'all': all, 'any': any
        }
        
        # Exercise templates for different difficulty levels
        self.exercise_templates = {
            'beginner': [
                "🎯 Create a program that prints your name and age!",
                "🌟 Make variables for your favorite color and food, then print them!",
                "🎮 Write code that calculates and prints the sum of two numbers!",
                "📚 Create a variable with your favorite book title and print a message about it!",
                "🐍 Print 'Hello Python!' three times using a simple approach!"
            ],
            'intermediate': [
                "🔢 Create a program that prints numbers from 1 to 5 using a loop!",
                "📝 Make a list of your three favorite animals and print each one!",
                "🎯 Write a function that takes a name and returns 'Hello, [name]!'",
                "🧮 Create a program that calculates the area of a rectangle!",
                "🎨 Make a program that asks for your age and tells you if you're a teenager!"
            ],
            'advanced': [
                "🏆 Create a simple calculator that can add, subtract, multiply, and divide!",
                "📊 Write a program that finds the largest number in a list!",
                "🎲 Create a guessing game where the computer picks a number!",
                "📚 Make a program that counts how many words are in a sentence!",
                "🔄 Write a function that reverses a string without using built-in reverse!"
            ]
        }
    
    def generate_exercise(self, module: Dict[str, Any], difficulty: str = "beginner") -> str:
        """Generate a coding exercise based on module content"""
        
        # Try to generate with AI first
        ai_exercise = self.generate_ai_exercise(module, difficulty)
        if ai_exercise:
            return ai_exercise
        
        # Fallback to templates
        templates = self.exercise_templates.get(difficulty, self.exercise_templates['beginner'])
        
        # Try to customize based on module content
        module_title = module.get('title', '').lower()
        
        if 'variable' in module_title:
            return "📦 Create three variables: your name, age, and favorite hobby. Then print them in a sentence!"
        elif 'function' in module_title:
            return "🔧 Write a function called 'greet_friend' that takes a name and prints 'Hi there, [name]!'"
        elif 'loop' in module_title:
            return "🔄 Use a loop to print your favorite emoji 5 times!"
        elif 'list' in module_title:
            return "📋 Create a list of your favorite foods and print each one with a number!"
        else:
            import random
            return random.choice(templates)
    
    def generate_ai_exercise(self, module: Dict[str, Any], difficulty: str) -> Optional[str]:
        """Generate exercise using AI based on module content"""
        
        prompt = f"""
        Create a fun coding exercise for kids learning Python, based on this module:
        
        Module: "{module.get('title', '')}"
        Content highlights: {str(module.get('content', [])[:3])}
        
        Requirements:
        - Difficulty: {difficulty}
        - Should take 5-10 minutes
        - Be engaging and fun for kids under 15
        - Focus on concepts from this module
        - Include clear instructions
        - Start with an emoji
        
        Return just the exercise description as plain text.
        """
        
        try:
            exercise = self.client.generate_response(prompt, temperature=0.8, max_tokens=200)
            if exercise and len(exercise) > 20 and not exercise.startswith("❌"):
                return exercise
        except:
            pass
        
        return None
    
    def evaluate_code(self, user_code: str, exercise_description: str) -> str:
        """Evaluate user's code and provide feedback"""
        
        # Safety check first
        if not self.is_code_safe(user_code):
            return "⚠️ This code contains some operations that aren't allowed in our safe environment. Try using basic Python operations like print(), variables, and simple calculations!"
        
        # Try to run the code safely
        execution_result = self.execute_code_safely(user_code)
        
        # Get AI feedback
        ai_feedback = self.get_ai_feedback(user_code, exercise_description, execution_result)
        
        # Combine execution result with AI feedback
        return self.format_evaluation_response(execution_result, ai_feedback)
    
    def is_code_safe(self, code: str) -> bool:
        """Check if code is safe to execute"""
        
        # List of dangerous operations
        dangerous_keywords = [
            'import os', 'import sys', 'import subprocess', 'import shutil',
            'exec(', 'eval(', '__import__', 'compile(',
            'open(', 'file(', 'input(', 'raw_input(',
            'delete', 'remove', 'unlink', 'rmdir',
            'while True:', 'for i in range(1000'
        ]
        
        code_lower = code.lower().replace(' ', '')
        
        for keyword in dangerous_keywords:
            if keyword.replace(' ', '') in code_lower:
                return False
        
        # Check code length (prevent very long programs)
        if len(code) > 2000:
            return False
        
        # Try to parse as valid Python
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return True  # Allow syntax errors for learning
        except:
            return False
    
    def execute_code_safely(self, code: str) -> Dict[str, Any]:
        """Safely execute Python code and capture results"""
        
        try:
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            
            # Capture output
            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()
            
            # Create safe execution environment
            safe_globals = {
                '__builtins__': self.safe_builtins,
                '__name__': '__main__'
            }
            safe_locals = {}
            
            # Execute code with output capture
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, safe_globals, safe_locals)
            
            output = stdout_buffer.getvalue()
            errors = stderr_buffer.getvalue()
            
            return {
                'success': True,
                'output': output,
                'errors': errors if errors else None,
                'variables': {k: str(v) for k, v in safe_locals.items() if not k.startswith('_')}
            }
            
        except SyntaxError as e:
            return {
                'success': False,
                'output': '',
                'errors': f"Syntax Error: {str(e)}",
                'error_type': 'syntax'
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'errors': str(e),
                'error_type': 'runtime'
            }
    
    def get_ai_feedback(self, user_code: str, exercise_description: str, 
                       execution_result: Dict[str, Any]) -> str:
        """Get AI-powered feedback on the code"""
        
        prompt = f"""
        A student (under 15) wrote this Python code for the exercise: "{exercise_description}"
        
        Student's Code:
        ```python
        {user_code}
        ```
        
        Execution Result:
        - Success: {execution_result.get('success')}
        - Output: {execution_result.get('output', 'None')}
        - Errors: {execution_result.get('errors', 'None')}
        
        Please provide encouraging feedback that:
        1. Starts with something positive they did well
        2. Explains what their code does in simple terms
        3. If there are errors, explain them gently and suggest fixes
        4. Gives encouragement to keep coding
        5. Uses emojis and kid-friendly language
        
        Keep it concise but supportive!
        """
        
        try:
            feedback = self.client.generate_response(prompt, temperature=0.7, max_tokens=400)
            if feedback and not feedback.startswith("❌"):
                return feedback
        except:
            pass
        
        # Fallback feedback
        if execution_result.get('success'):
            return "🎉 Great job! Your code ran successfully! Keep up the awesome work! 🚀"
        else:
            return "💪 Good try! There's a small issue with your code, but that's how we learn! Keep experimenting! 🌟"
    
    def format_evaluation_response(self, execution_result: Dict[str, Any], ai_feedback: str) -> str:
        """Format the complete evaluation response"""
        
        response_parts = []
        
        # Add execution status
        if execution_result.get('success'):
            response_parts.append("✅ **Your code ran successfully!**")
        else:
            response_parts.append("⚠️ **There was an issue with your code**")
        
        # Add output if available
        output = execution_result.get('output', '').strip()
        if output:
            response_parts.append(f"📺 **Output:**\n```\n{output}\n```")
        
        # Add variables if created
        variables = execution_result.get('variables', {})
        if variables:
            var_list = [f"{k} = {v}" for k, v in variables.items()]
            response_parts.append(f"📦 **Variables created:** {', '.join(var_list[:3])}")  # Show max 3 variables
        
        # Add error information if any
        errors = execution_result.get('errors')
        if errors:
            response_parts.append(f"🐛 **Error:** {errors}")
            
            # Add helpful error explanations
            error_help = self.get_error_help(errors)
            if error_help:
                response_parts.append(f"💡 **Tip:** {error_help}")
        
        # Add AI feedback
        if ai_feedback:
            response_parts.append(f"🤖 **Feedback:** {ai_feedback}")
        
        return "\n\n".join(response_parts)
    
    def get_error_help(self, error_message: str) -> str:
        """Provide kid-friendly explanations for common errors"""
        
        error_lower = error_message.lower()
        
        if "syntax error" in error_lower or "invalid syntax" in error_lower:
            return "Check your spelling and make sure you have the right symbols like (), [], and quotes!"
        
        elif "name" in error_lower and "not defined" in error_lower:
            return "Make sure you've created all your variables before using them!"
        
        elif "indentation" in error_lower:
            return "Python is picky about spaces! Make sure your code lines up correctly."
        
        elif "type error" in error_lower:
            return "You might be mixing different types of data. Check if you're trying to add numbers and text!"
        
        elif "index error" in error_lower:
            return "You're trying to access something that doesn't exist in your list. Check your list size!"
        
        elif "zero" in error_lower and "division" in error_lower:
            return "Oops! You can't divide by zero - that would break math! 😅"
        
        else:
            return "Don't worry about errors - they're part of learning! Try reading the error message for clues."
    
    def analyze_code_quality(self, code: str) -> Dict[str, Any]:
        """Analyze code quality and provide suggestions"""
        
        analysis = {
            'complexity': 'simple',
            'suggestions': [],
            'good_practices': [],
            'areas_to_improve': []
        }
        
        lines = code.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        # Analyze complexity
        if len(non_empty_lines) > 15:
            analysis['complexity'] = 'complex'
        elif len(non_empty_lines) > 8:
            analysis['complexity'] = 'moderate'
        
        # Check for good practices
        if any('def ' in line for line in non_empty_lines):
            analysis['good_practices'].append("Great job using functions!")
        
        if any('#' in line for line in non_empty_lines):
            analysis['good_practices'].append("Nice comments to explain your code!")
        
        if any('print(' in line for line in non_empty_lines):
            analysis['good_practices'].append("Good use of print() to show results!")
        
        # Suggest improvements
        if not any('print(' in line for line in non_empty_lines):
            analysis['suggestions'].append("Try adding print() statements to see your results!")
        
        if len(set(var for line in non_empty_lines for var in re.findall(r'\b[a-zA-Z_]\w*\s*=', line))) > 5:
            analysis['suggestions'].append("You're using lots of variables - great for organizing data!")
        
        return analysis
    
    def get_code_hints(self, exercise_description: str, user_code: str = "") -> List[str]:
        """Provide hints for coding exercises"""
        
        hints = []
        exercise_lower = exercise_description.lower()
        
        # General hints based on exercise type
        if "variable" in exercise_lower:
            hints.append("💡 Remember: variable_name = value")
            hints.append("🔤 Use quotes for text: name = 'Alice'")
        
        if "print" in exercise_lower:
            hints.append("📺 Use print() to display things: print('Hello!')")
            hints.append("🔗 You can print variables: print(my_variable)")
        
        if "loop" in exercise_lower or "repeat" in exercise_lower:
            hints.append("🔄 Try: for i in range(5): print('Hello')")
            hints.append("📝 Don't forget to indent code inside loops!")
        
        if "function" in exercise_lower:
            hints.append("🔧 Start with: def my_function():")
            hints.append("↩️ Remember to indent function code!")
        
        if "list" in exercise_lower:
            hints.append("📋 Create lists with: my_list = ['item1', 'item2']")
            hints.append("🔍 Access items with: my_list[0]")
        
        # Add encouragement
        hints.append("🌟 Take your time and experiment!")
        hints.append("💪 Every programmer makes mistakes - that's how we learn!")
        
        return hints[:3]  # Return max 3 hints to avoid overwhelming