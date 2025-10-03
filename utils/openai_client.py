import openai
import os
import time
from typing import Optional, Dict, List, Any
import json
import streamlit as st
from dotenv import load_dotenv    # For loading .env files

class OpenAIClient:
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = None
        self.model = "gpt-3.5-turbo"
        self.max_retries = 3
        self.retry_delay = 2
        self.setup_client()
    
    def setup_client(self):
        """Setup OpenAI client with API key"""
        load_dotenv()

        try:
            # Try to get API key from environment or Streamlit secrets
            api_key = os.getenv("OPENAI_API_KEY")
            
            # if not api_key and hasattr(st, 'secrets'):
            #     try:
            #         api_key = st.secrets["OPENAI_API_KEY"]
            #     except:
            #         pass
            
            if not api_key:
                st.warning("⚠️ OpenAI API key not found. AI features will be limited. Set OPENAI_API_KEY to enable full functionality.")
                self.client = None
                return False
            
            # Create OpenAI client with minimal parameters
            self.client = openai.OpenAI(api_key=api_key)
            return True
            
        except Exception as e:
            st.warning(f"⚠️ Could not initialize OpenAI client: {str(e)}. AI features will be limited.")
            self.client = None
            return False
    
    def generate_response(self, prompt: str, system_prompt: str = "", 
                         temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """Generate a response using OpenAI API"""
        if not self.client:
            return "🤖 Hi! I'm StudyBot, but I need an OpenAI API key to provide personalized responses. For now, you can explore the learning modules and practice coding exercises. To enable AI features, please set your OPENAI_API_KEY environment variable."
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=30
                )
                
                return response.choices[0].message.content.strip()
                
            except openai.RateLimitError:
                if attempt < self.max_retries - 1:
                    wait_time = (attempt + 1) * 2  # Exponential backoff
                    st.warning(f"⏳ Rate limit reached. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                return "⏳ I'm getting too many requests right now. Please try again in a moment!"
                
            except openai.APITimeoutError:
                if attempt < self.max_retries - 1:
                    st.warning(f"⏳ Request timeout. Retrying... (attempt {attempt + 1})")
                    time.sleep(self.retry_delay)
                    continue
                return "⏳ The response is taking too long. Please try again!"
                
            except openai.APIError as e:
                st.error(f"❌ OpenAI API error: {str(e)}")
                return "❌ Sorry, I'm having trouble connecting to my brain right now. Please try again!"
                
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                return "❌ Oops! Something unexpected happened. Please try again!"
        
        return "❌ I tried several times but couldn't generate a response. Please try again!"
    
    def generate_chat_response(self, messages: List[Dict[str, str]], 
                              temperature: float = 0.7, max_tokens: int = 800) -> str:
        """Generate response from a conversation history"""
        if not self.client:
            return "🤖 I'd love to chat with you about Python! However, I need an OpenAI API key to provide intelligent responses. You can still use the learning modules, practice exercises, and flashcards while we work on getting the AI features set up."
        
        # Limit conversation history to last 10 messages to stay within token limits
        limited_messages = messages[-10:] if len(messages) > 10 else messages
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=limited_messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=30
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                st.error(f"Error generating chat response: {str(e)}")
                return "❌ I'm having trouble responding right now. Please try again!"
        
        return "❌ Sorry, I couldn't generate a response. Please try again!"
    
    def generate_json_response(self, prompt: str, system_prompt: str = "", 
                              temperature: float = 0.3) -> Optional[Dict]:
        """Generate a JSON response and parse it"""
        response_text = self.generate_response(
            prompt, system_prompt, temperature, max_tokens=1500
        )
        
        if response_text.startswith("❌") or response_text.startswith("⏳"):
            return None
        
        try:
            # Try to extract JSON from the response
            # Look for JSON blocks first
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to parse the entire response as JSON
            if response_text.strip().startswith('{') or response_text.strip().startswith('['):
                return json.loads(response_text.strip())
            
            # Look for JSON-like content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_content = response_text[json_start:json_end]
                return json.loads(json_content)
            
            # If all else fails, return None
            st.warning("⚠️ Couldn't parse JSON response from AI. Using fallback content.")
            return None
            
        except json.JSONDecodeError as e:
            st.warning(f"⚠️ JSON parsing error: {str(e)}. Using fallback content.")
            return None
        except Exception as e:
            st.error(f"❌ Error processing JSON response: {str(e)}")
            return None
    
    def evaluate_code_safety(self, code: str) -> bool:
        """Basic safety check for user code"""
        dangerous_patterns = [
            'import os', 'import sys', 'import subprocess',
            'exec(', 'eval(', '__import__',
            'open(', 'file(', 'input(', 'raw_input(',
            'delete', 'remove', 'rm ', 'format',
            'while True:', 'for i in range(999'
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                return False
        
        # Check for excessively long code
        if len(code) > 2000:
            return False
        
        return True
    
    def execute_code_safely(self, code: str) -> Dict[str, Any]:
        """Safely execute Python code and return results"""
        if not self.evaluate_code_safety(code):
            return {
                'success': False,
                'error': 'Code contains potentially unsafe operations',
                'output': ''
            }
        
        try:
            # Capture stdout
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            # Create a restricted environment
            safe_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'set': set,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'sum': sum,
                    'max': max,
                    'min': min,
                    'abs': abs,
                    'round': round,
                    'type': type,
                    'isinstance': isinstance,
                }
            }
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, safe_globals, {})
            
            output = stdout_capture.getvalue()
            error = stderr_capture.getvalue()
            
            return {
                'success': True,
                'output': output,
                'error': error if error else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': ''
            }
    
    def set_model(self, model: str):
        """Set the OpenAI model to use"""
        valid_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
        if model in valid_models:
            self.model = model
        else:
            st.warning(f"⚠️ Model {model} not recognized. Using {self.model}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            'model': self.model,
            'max_tokens': 4096 if 'gpt-4' in self.model else 4096,
            'available': self.client is not None
        }