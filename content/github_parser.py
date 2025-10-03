import requests
import re
import json
from typing import List, Dict, Any, Optional
import time
from urllib.parse import urljoin
import base64

class GitHubParser:
    def __init__(self, repo_url: str = "https://api.github.com/repos/Python-Crash-Course/Python101"):
        """Initialize GitHub parser with repository URL"""
        self.repo_url = repo_url
        self.base_raw_url = "https://raw.githubusercontent.com/Python-Crash-Course/Python101/main/"
        self.session = requests.Session()
        # Add headers to avoid rate limiting
        self.session.headers.update({
            'User-Agent': 'StudyBot-Educational-Tool/1.0',
            'Accept': 'application/vnd.github.v3+json'
        })
    
    def get_repo_structure(self) -> List[Dict[str, Any]]:
        """Get the repository structure recursively"""
        try:
            # Get the repository contents
            response = self.session.get(f"{self.repo_url}/contents")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching repository structure: {e}")
            return []
    
    def get_file_content(self, path: str) -> Optional[str]:
        """Get content of a specific file"""
        try:
            # Use raw GitHub URL for better reliability
            raw_url = f"{self.base_raw_url}{path}"
            response = self.session.get(raw_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching file {path}: {e}")
            # Fallback to API method
            try:
                api_url = f"{self.repo_url}/contents/{path}"
                response = self.session.get(api_url)
                response.raise_for_status()
                content_data = response.json()
                if content_data.get('encoding') == 'base64':
                    return base64.b64decode(content_data['content']).decode('utf-8')
                return content_data.get('content', '')
            except:
                return None
    
    def get_directory_contents(self, path: str = "") -> List[Dict[str, Any]]:
        """Get contents of a directory"""
        try:
            url = f"{self.repo_url}/contents/{path}" if path else f"{self.repo_url}/contents"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching directory {path}: {e}")
            return []
    
    def extract_markdown_sections(self, content: str) -> Dict[str, Any]:
        """Extract structured information from markdown content"""
        if not content:
            return {'title': 'Unknown', 'description': '', 'content': [], 'code_examples': [], 'exercises': []}
        
        lines = content.split('\n')
        sections = {
            'title': 'Unknown',
            'description': '',
            'content': [],
            'code_examples': [],
            'exercises': []
        }
        
        current_section = 'content'
        current_content = []
        in_code_block = False
        code_block_content = []
        
        for line in lines:
            line = line.strip()
            
            # Extract title from first H1
            if line.startswith('# ') and sections['title'] == 'Unknown':
                sections['title'] = line[2:].strip()
                continue
            
            # Handle code blocks
            if line.startswith('```'):
                if in_code_block:
                    # End of code block
                    if code_block_content:
                        sections['code_examples'].append('\n'.join(code_block_content))
                    code_block_content = []
                    in_code_block = False
                else:
                    # Start of code block
                    in_code_block = True
                continue
            
            if in_code_block:
                code_block_content.append(line)
                continue
            
            # Section headers
            if line.startswith('## '):
                # Save current section content
                if current_content:
                    if current_section == 'content':
                        sections['content'].extend(current_content)
                    elif current_section == 'exercises':
                        sections['exercises'].extend(current_content)
                
                current_content = []
                header = line[3:].lower().strip()
                
                if any(keyword in header for keyword in ['exercise', 'practice', 'try', 'challenge', 'problem']):
                    current_section = 'exercises'
                else:
                    current_section = 'content'
                
                current_content.append(line)
                continue
            
            # Regular content
            if line:
                current_content.append(line)
        
        # Save final section
        if current_content:
            if current_section == 'content':
                sections['content'].extend(current_content)
            elif current_section == 'exercises':
                sections['exercises'].extend(current_content)
        
        # Generate description from first few content lines
        if sections['content'] and not sections['description']:
            desc_lines = []
            for line in sections['content'][:3]:
                if line and not line.startswith('#'):
                    desc_lines.append(line)
                if len(' '.join(desc_lines)) > 150:
                    break
            sections['description'] = ' '.join(desc_lines)[:200] + ('...' if len(' '.join(desc_lines)) > 200 else '')
        
        return sections
    
    def parse_lesson_directory(self, dir_path: str) -> Optional[Dict[str, Any]]:
        """Parse a lesson directory and extract all relevant content"""
        contents = self.get_directory_contents(dir_path)
        
        lesson_data = {
            'title': dir_path.replace('/', ' ').title(),
            'description': '',
            'content': [],
            'code_examples': [],
            'exercises': [],
            'github_path': dir_path
        }
        
        # Look for main lesson files
        readme_files = [f for f in contents if f['name'].lower() in ['readme.md', 'lesson.md', 'index.md']]
        python_files = [f for f in contents if f['name'].endswith('.py')]
        other_md_files = [f for f in contents if f['name'].endswith('.md') and f not in readme_files]
        
        # Process main README/lesson file
        if readme_files:
            main_file = readme_files[0]
            content = self.get_file_content(main_file['path'])
            if content:
                sections = self.extract_markdown_sections(content)
                lesson_data.update(sections)
        
        # Process additional markdown files
        for md_file in other_md_files:
            content = self.get_file_content(md_file['path'])
            if content:
                sections = self.extract_markdown_sections(content)
                lesson_data['content'].extend(sections['content'])
                lesson_data['code_examples'].extend(sections['code_examples'])
                lesson_data['exercises'].extend(sections['exercises'])
        
        # Process Python files as code examples
        for py_file in python_files:
            content = self.get_file_content(py_file['path'])
            if content:
                # Add file header comment
                code_with_header = f"# File: {py_file['name']}\n{content}"
                lesson_data['code_examples'].append(code_with_header)
        
        return lesson_data if lesson_data['content'] or lesson_data['code_examples'] else None
    
    def identify_learning_modules(self, repo_contents: List[Dict[str, Any]]) -> List[str]:
        """Identify directories that contain learning modules"""
        module_dirs = []
        
        # Common patterns for lesson directories
        lesson_patterns = [
            r'lesson[\s_-]*\d+',
            r'chapter[\s_-]*\d+',
            r'part[\s_-]*\d+',
            r'module[\s_-]*\d+',
            r'week[\s_-]*\d+',
            r'day[\s_-]*\d+',
            r'\d+[\s_-]*(lesson|chapter|part|module)',
            r'^[0-9]{1,2}[\s_-]*'  # Starts with 1-2 digits
        ]
        
        for item in repo_contents:
            if item['type'] == 'dir':
                dir_name = item['name'].lower()
                
                # Check if directory name matches lesson patterns
                if any(re.search(pattern, dir_name) for pattern in lesson_patterns):
                    module_dirs.append(item['path'])
                
                # Also check for common Python topic directories
                python_topics = [
                    'basics', 'variables', 'functions', 'loops', 'conditionals',
                    'data_structures', 'lists', 'dictionaries', 'classes',
                    'file_handling', 'exceptions', 'modules', 'packages'
                ]
                
                if any(topic in dir_name for topic in python_topics):
                    module_dirs.append(item['path'])
        
        # Sort modules to maintain logical order
        return sorted(module_dirs, key=lambda x: self.extract_order_number(x))
    
    def extract_order_number(self, path: str) -> int:
        """Extract order number from path for sorting"""
        # Try to find a number at the beginning or in the path
        match = re.search(r'(\d+)', path)
        return int(match.group(1)) if match else 999
    
    def parse_repository(self) -> List[Dict[str, Any]]:
        """Parse the entire repository and extract learning modules"""
        print("🚀 Starting repository parsing...")
        
        # Get main repository structure
        repo_contents = self.get_repo_structure()
        if not repo_contents:
            # Fallback: create modules from README if repo structure fails
            return self.create_fallback_modules()
        
        # Identify learning modules
        module_paths = self.identify_learning_modules(repo_contents)
        
        if not module_paths:
            # If no structured modules found, try to parse main README
            readme_content = self.get_file_content('README.md')
            if readme_content:
                return [self.extract_markdown_sections(readme_content)]
            else:
                return self.create_fallback_modules()
        
        modules = []
        print(f"📚 Found {len(module_paths)} potential learning modules")
        
        for i, module_path in enumerate(module_paths):
            print(f"📖 Processing module {i+1}: {module_path}")
            
            module_data = self.parse_lesson_directory(module_path)
            if module_data:
                modules.append(module_data)
                print(f"✅ Successfully parsed: {module_data['title']}")
            else:
                print(f"⚠️ Skipped module: {module_path} (no content found)")
            
            # Add delay to respect rate limits
            time.sleep(0.5)
        
        # If no modules were successfully parsed, create fallback
        if not modules:
            print("📝 No modules found, creating fallback content...")
            return self.create_fallback_modules()
        
        print(f"🎉 Successfully parsed {len(modules)} modules!")
        return modules
    
    def create_fallback_modules(self) -> List[Dict[str, Any]]:
        """Create basic Python learning modules as fallback"""
        fallback_modules = [
            {
                'title': 'Introduction to Python',
                'description': 'Learn what Python is and why it\'s awesome for beginners!',
                'content': [
                    '# Welcome to Python! 🐍',
                    'Python is a friendly programming language that\'s perfect for beginners.',
                    'It\'s used to build websites, games, apps, and even control robots!',
                    'Python code is easy to read and write - it\'s almost like writing in English.',
                    '## Why Learn Python?',
                    '- Easy to learn and understand',
                    '- Used by companies like Google, Netflix, and NASA',
                    '- Great for solving real-world problems',
                    '- Fun and creative!',
                ],
                'code_examples': [
                    'print("Hello, World!")',
                    'print("Welcome to Python programming!")',
                    'name = "Python"\nprint(f"I love {name}!")'
                ],
                'exercises': [
                    'Try printing your name',
                    'Create a variable with your age',
                    'Print a welcome message'
                ],
                'github_path': 'intro'
            },
            {
                'title': 'Variables and Data Types',
                'description': 'Learn how to store and work with different types of information.',
                'content': [
                    '# Variables - Your Data Storage! 📦',
                    'Variables are like labeled boxes where we store information.',
                    'In Python, we can store numbers, text, and more!',
                    '## Types of Data',
                    '- **Strings**: Text like "Hello" or "Python"',
                    '- **Integers**: Whole numbers like 5, 10, 100',
                    '- **Floats**: Decimal numbers like 3.14, 2.5',
                    '- **Booleans**: True or False values'
                ],
                'code_examples': [
                    'name = "Alice"\nage = 12\nheight = 4.5\nis_student = True',
                    'favorite_color = "blue"\nprint(f"My favorite color is {favorite_color}")',
                    'x = 10\ny = 5\nresult = x + y\nprint(f"{x} + {y} = {result}")'
                ],
                'exercises': [
                    'Create variables for your name, age, and favorite hobby',
                    'Make a variable for your favorite number and print it',
                    'Try different data types and print them'
                ],
                'github_path': 'variables'
            },
            {
                'title': 'Basic Operations and Math',
                'description': 'Learn how to do math and operations with Python.',
                'content': [
                    '# Python is a Calculator Too! 🧮',
                    'Python can do all kinds of math operations.',
                    'Let\'s explore the basic mathematical operations.',
                    '## Math Operators',
                    '- **+** Addition',
                    '- **-** Subtraction', 
                    '- **\*** Multiplication',
                    '- **/** Division',
                    '- **\*\*** Exponentiation (power)',
                    '- **%** Modulus (remainder)'
                ],
                'code_examples': [
                    'print(5 + 3)  # Addition\nprint(10 - 4)  # Subtraction',
                    'print(6 * 7)  # Multiplication\nprint(15 / 3)  # Division',
                    'print(2 ** 3)  # 2 to the power of 3\nprint(17 % 5)  # Remainder'
                ],
                'exercises': [
                    'Calculate your age in months',
                    'Find the area of a rectangle (length × width)',
                    'Calculate how many weeks are in a year'
                ],
                'github_path': 'math'
            }
        ]
        
        return fallback_modules