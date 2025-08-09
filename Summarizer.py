#!/usr/bin/env python3
"""
File Tree Scanner - Generates a markdown file with directory structure and content analysis
Usage: python PROJECT_SCANNER.py [--dir "path/to/directory"]
"""

import os
import argparse
from datetime import datetime
from pathlib import Path
import mimetypes
import re
from collections import defaultdict
import math


# File extensions to analyze with emoji mappings
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.r',
    '.md', '.txt', '.rst', '.asciidoc',
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    '.xml', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
    '.sql', '.dockerfile', '.makefile',
    '.tex', '.latex', '.bib',
    '.vue', '.svelte', '.astro'
}

# Files to skip
SKIP_FILES = {'desktop.ini', 'thumbs.db', '.ds_store'}

# File type emoji mappings
FILE_EMOJIS = {
    '.py': '🐍',
    '.js': '📜',
    '.ts': '📘',
    '.jsx': '⚛️',
    '.tsx': '⚛️',
    '.java': '☕',
    '.c': '🔷',
    '.cpp': '🔷',
    '.cs': '🔷',
    '.go': '🐹',
    '.rs': '🦀',
    '.rb': '💎',
    '.php': '🐘',
    '.swift': '🦉',
    '.kt': '🟣',
    '.r': '📊',
    '.md': '📝',
    '.txt': '📄',
    '.html': '🌐',
    '.htm': '🌐',
    '.css': '🎨',
    '.scss': '🎨',
    '.sass': '🎨',
    '.json': '📊',
    '.xml': '📰',
    '.yaml': '⚙️',
    '.yml': '⚙️',
    '.toml': '⚙️',
    '.ini': '⚙️',
    '.cfg': '⚙️',
    '.conf': '⚙️',
    '.sh': '🐚',
    '.bash': '🐚',
    '.bat': '🖥️',
    '.cmd': '🖥️',
    '.ps1': '💠',
    '.sql': '🗃️',
    '.dockerfile': '🐳',
    '.vue': '💚',
    '.svelte': '🧡',
    '.astro': '🚀',
}


def get_emoji(file_path):
    """Get emoji for file type."""
    ext = file_path.suffix.lower()
    return FILE_EMOJIS.get(ext, '📄')


def should_skip_file(file_path):
    """Check if file should be skipped."""
    name_lower = file_path.name.lower()
    return name_lower in SKIP_FILES or file_path.suffix.lower() == '.lnk'


def should_skip_directory(dir_path):
    """Check if directory should be skipped (starts with dot or exclamation mark)."""
    return dir_path.name.startswith('.') or dir_path.name.startswith('!')


def get_file_brief(file_path, max_length=50):
    """Generate a brief description of a file based on its content."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(1000)  # Read first 1000 chars for better analysis
            
        # Clean up the content
        content = content.strip()
        if not content:
            return "Empty file"
        
        # Special handling for different file types
        if file_path.suffix == '.py':
            # Look for main purpose in docstring, comments, or main function
            if content.startswith('"""') or content.startswith("'''"):
                match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if not match:
                    match = re.search(r"'''(.*?)'''", content, re.DOTALL)
                if match:
                    brief = match.group(1).strip().split('\n')[0]
                    return truncate_text(brief, max_length)
            
            # Look for first comment that describes purpose
            first_comment = re.search(r'#\s*(.+)', content)
            if first_comment and len(first_comment.group(1)) > 10:
                return truncate_text(first_comment.group(1), max_length)
            
            # Look for main class or function
            if '__main__' in content:
                return "Main script"
            elif 'class ' in content:
                match = re.search(r'class\s+(\w+)', content)
                if match:
                    return f"Defines {match.group(1)} class"
            elif 'def ' in content:
                match = re.search(r'def\s+(\w+)', content)
                if match:
                    return f"Defines {match.group(1)}()"
        
        elif file_path.suffix == '.md':
            # Look for first heading or first meaningful line
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('<!--'):
                    if line.startswith('#'):
                        return truncate_text(line.strip('#').strip(), max_length)
                    elif len(line) > 20:  # Meaningful content
                        return truncate_text(line, max_length)
        
        elif file_path.suffix in ['.html', '.htm']:
            # Look for title or main heading
            match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            if match:
                return truncate_text(match.group(1).strip(), max_length)
            match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
            if match:
                return truncate_text(re.sub(r'<[^>]+>', '', match.group(1)).strip(), max_length)
            return "HTML document"
        
        elif file_path.suffix in ['.json']:
            try:
                import json
                data = json.loads(content)
                if isinstance(data, dict):
                    keys = list(data.keys())[:3]
                    return f"JSON: {', '.join(keys)}..."
                elif isinstance(data, list):
                    return f"JSON array [{len(data)} items]"
            except:
                return "JSON data"
        
        elif file_path.suffix in ['.css', '.scss', '.sass']:
            # Look for main selectors or purpose
            if '/*' in content:
                match = re.search(r'/\*\s*(.+?)\s*\*/', content)
                if match:
                    return truncate_text(match.group(1), max_length)
            selectors = re.findall(r'^([.#]?\w+)\s*{', content, re.MULTILINE)
            if selectors:
                return f"Styles: {', '.join(selectors[:3])}"
        
        elif file_path.suffix in ['.bat', '.cmd']:
            # Look for REM comments or echo statements
            rem_match = re.search(r'(?:REM|rem|::)\s+(.+)', content)
            if rem_match:
                return truncate_text(rem_match.group(1), max_length)
            echo_match = re.search(r'(?:ECHO|echo)\s+(.+)', content)
            if echo_match:
                desc = echo_match.group(1).strip()
                if desc and not desc.startswith('@'):
                    return truncate_text(desc, max_length)
            return "Batch script"
        
        elif file_path.suffix in ['.sh', '.bash']:
            # Look for shebang or first comment
            if content.startswith('#!'):
                lines = content.split('\n')
                for line in lines[1:]:
                    if line.strip().startswith('#') and len(line.strip()) > 2:
                        return truncate_text(line.strip('#').strip(), max_length)
            return "Shell script"
        
        elif file_path.suffix == '.txt':
            # For text files, try to determine purpose from content
            lines = [l.strip() for l in content.split('\n') if l.strip()]
            if lines:
                first_line = lines[0]
                # Check if it's a list, log, readme, etc.
                if 'readme' in first_line.lower():
                    return "Readme file"
                elif 'todo' in first_line.lower() or '- [ ]' in content:
                    return "TODO list"
                elif 'log' in first_line.lower() or re.search(r'\d{4}-\d{2}-\d{2}', first_line):
                    return "Log file"
                elif re.search(r'^\d+\.', first_line) or first_line.startswith('-'):
                    return "List or notes"
                else:
                    return truncate_text(first_line, max_length)
        
        # Default: first meaningful line
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('//') and not line.startswith('/*'):
                return truncate_text(line, max_length)
        
        return "Text file"
        
    except Exception as e:
        return "Error reading"


def truncate_text(text, max_length):
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def analyze_file_content(file_path):
    """Analyze file content and return a detailed summary."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        total_lines = len(lines)
        non_empty_lines = len([l for l in lines if l.strip()])
        
        analysis = {
            'path': file_path,
            'lines': total_lines,
            'non_empty_lines': non_empty_lines,
            'size': file_path.stat().st_size,
            'summary': ""
        }
        
        # File-specific analysis
        if file_path.suffix == '.py':
            # Enhanced Python analysis
            summary_parts = []
            
            # Check for main docstring
            if content.strip().startswith('"""') or content.strip().startswith("'''"):
                match = re.search(r'"""(.*?)"""', content, re.DOTALL)
                if not match:
                    match = re.search(r"'''(.*?)'''", content, re.DOTALL)
                if match:
                    docstring = match.group(1).strip()
                    if docstring:
                        summary_parts.append(docstring.split('\n\n')[0])
            
            # Analyze imports to understand purpose
            imports = re.findall(r'^(?:from|import)\s+(\S+)', content, re.MULTILINE)
            if imports:
                unique_imports = list(set(imports))
                if 'flask' in str(imports).lower() or 'django' in str(imports).lower():
                    summary_parts.append("Web application module")
                elif 'numpy' in str(imports).lower() or 'pandas' in str(imports).lower():
                    summary_parts.append("Data analysis module")
                elif 'tensorflow' in str(imports).lower() or 'torch' in str(imports).lower():
                    summary_parts.append("Machine learning module")
                elif 'pytest' in str(imports).lower() or 'unittest' in str(imports).lower():
                    summary_parts.append("Test module")
            
            # Analyze structure
            classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
            
            if '__main__' in content:
                summary_parts.append("Executable script with main entry point")
            
            if classes:
                summary_parts.append(f"Defines {len(classes)} class(es): {', '.join(classes[:5])}")
            
            if functions:
                # Identify key functions
                key_functions = []
                for func in functions:
                    if func.startswith('__init__'):
                        continue
                    elif func.startswith('test_'):
                        if 'test_' not in ' '.join(key_functions):
                            key_functions.append("test functions")
                    elif func in ['main', 'run', 'execute', 'process']:
                        key_functions.append(func)
                    elif len(key_functions) < 5:
                        key_functions.append(func)
                
                if key_functions:
                    summary_parts.append(f"Key functions: {', '.join(key_functions)}")
            
            # Check for specific patterns
            if 'if __name__' in content:
                # Find what happens in main
                main_match = re.search(r'if __name__.*?:\s*\n(.*?)(?:\n\S|\Z)', content, re.DOTALL)
                if main_match:
                    main_content = main_match.group(1)
                    if 'argparse' in main_content or 'ArgumentParser' in main_content:
                        summary_parts.append("Command-line interface with argument parsing")
                    elif 'app.run' in main_content:
                        summary_parts.append("Web server startup")
            
            analysis['summary'] = " ".join(summary_parts) if summary_parts else "Python module"
        
        elif file_path.suffix == '.md':
            # Markdown analysis
            summary_parts = []
            
            # Get main title
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                summary_parts.append(f"Documentation: {title_match.group(1)}")
            
            # Analyze content type
            headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
            
            if 'installation' in content.lower() and 'usage' in content.lower():
                summary_parts.append("Project documentation with setup instructions")
            elif 'todo' in content.lower() or '- [ ]' in content:
                todos = len(re.findall(r'- \[ \]', content))
                done = len(re.findall(r'- \[x\]', content))
                summary_parts.append(f"Task list ({done}/{todos + done} completed)")
            elif 'changelog' in content.lower() or 'release' in content.lower():
                summary_parts.append("Version history/changelog")
            elif headers:
                summary_parts.append(f"Contains {len(headers)} sections")
            
            # Count elements
            links = re.findall(r'\[([^\]]+)\]\([^\)]+\)', content)
            images = re.findall(r'!\[([^\]]*)\]\([^\)]+\)', content)
            code_blocks = re.findall(r'```', content)
            
            elements = []
            if links:
                elements.append(f"{len(links)} links")
            if images:
                elements.append(f"{len(images)} images")
            if code_blocks:
                elements.append(f"{len(code_blocks)//2} code blocks")
            
            if elements:
                summary_parts.append(f"Includes: {', '.join(elements)}")
            
            analysis['summary'] = " ".join(summary_parts) if summary_parts else "Markdown document"
        
        elif file_path.suffix in ['.html', '.htm']:
            # HTML analysis
            summary_parts = []
            
            title = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            if title:
                summary_parts.append(f"Webpage: {title.group(1).strip()}")
            
            # Analyze page type
            if '<form' in content.lower():
                forms = len(re.findall(r'<form', content, re.IGNORECASE))
                summary_parts.append(f"Interactive page with {forms} form(s)")
            
            if 'jquery' in content.lower() or 'react' in content.lower() or 'vue' in content.lower():
                frameworks = []
                if 'jquery' in content.lower():
                    frameworks.append('jQuery')
                if 'react' in content.lower():
                    frameworks.append('React')
                if 'vue' in content.lower():
                    frameworks.append('Vue')
                summary_parts.append(f"Uses: {', '.join(frameworks)}")
            
            # Count major elements
            scripts = len(re.findall(r'<script', content, re.IGNORECASE))
            styles = len(re.findall(r'<style', content, re.IGNORECASE))
            
            if scripts or styles:
                summary_parts.append(f"Contains {scripts} scripts and {styles} inline styles")
            
            analysis['summary'] = " ".join(summary_parts) if summary_parts else "HTML document"
        
        elif file_path.suffix == '.css':
            # CSS analysis
            summary_parts = []
            
            # Check for framework
            if 'bootstrap' in content.lower():
                summary_parts.append("Bootstrap-based styles")
            elif 'tailwind' in content.lower():
                summary_parts.append("Tailwind CSS utilities")
            
            # Analyze selectors
            selectors = re.findall(r'^([.#]?\w+)\s*{', content, re.MULTILINE)
            media_queries = re.findall(r'@media', content)
            animations = re.findall(r'@keyframes\s+(\w+)', content)
            
            if selectors:
                unique_selectors = len(set(selectors))
                summary_parts.append(f"Defines {unique_selectors} unique selectors")
            
            if media_queries:
                summary_parts.append(f"Responsive design with {len(media_queries)} media queries")
            
            if animations:
                summary_parts.append(f"Animations: {', '.join(animations)}")
            
            analysis['summary'] = " ".join(summary_parts) if summary_parts else "Stylesheet"
        
        elif file_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
            # JavaScript/TypeScript analysis
            summary_parts = []
            
            # Detect framework/library
            if 'react' in content.lower():
                if 'component' in content.lower():
                    summary_parts.append("React component")
                else:
                    summary_parts.append("React application code")
            elif 'angular' in content.lower():
                summary_parts.append("Angular module")
            elif 'vue' in content.lower():
                summary_parts.append("Vue.js component")
            elif 'express' in content.lower():
                summary_parts.append("Express.js server code")
            elif 'jquery' in content.lower():
                summary_parts.append("jQuery-based scripts")
            
            # Analyze exports/imports
            imports = re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content)
            exports = re.findall(r'export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)', content)
            
            if exports:
                if 'default' in content:
                    summary_parts.append(f"Exports: {exports[0]} (default)")
                else:
                    summary_parts.append(f"Exports: {', '.join(exports[:3])}")
            
            # Check for specific patterns
            if 'addEventListener' in content or 'onclick' in content:
                summary_parts.append("Event handling and DOM manipulation")
            elif 'fetch(' in content or 'axios' in content:
                summary_parts.append("API integration code")
            elif 'test(' in content or 'describe(' in content:
                summary_parts.append("Test suite")
            
            analysis['summary'] = " ".join(summary_parts) if summary_parts else "JavaScript code"
        
        elif file_path.suffix == '.json':
            # JSON analysis
            try:
                import json
                data = json.loads(content)
                if isinstance(data, dict):
                    keys = list(data.keys())
                    if 'name' in keys and 'version' in keys and 'dependencies' in keys:
                        analysis['summary'] = f"Package manifest: {data.get('name', 'unknown')} v{data.get('version', '?')}"
                    elif 'compilerOptions' in keys:
                        analysis['summary'] = "TypeScript configuration"
                    else:
                        analysis['summary'] = f"Configuration with keys: {', '.join(keys[:5])}"
                elif isinstance(data, list):
                    analysis['summary'] = f"Data array with {len(data)} items"
            except:
                analysis['summary'] = "JSON data file"
        
        elif file_path.suffix in ['.bat', '.cmd']:
            # Batch file analysis
            summary_parts = []
            
            # Look for purpose in comments or echo
            rem_comments = re.findall(r'(?:REM|rem|::)\s+(.+)', content)
            if rem_comments:
                summary_parts.append(rem_comments[0])
            
            # Analyze commands
            if 'npm' in content:
                summary_parts.append("Node.js build/run script")
            elif 'python' in content or 'py' in content:
                summary_parts.append("Python execution script")
            elif 'git' in content:
                summary_parts.append("Git automation script")
            elif 'copy' in content or 'xcopy' in content:
                summary_parts.append("File management script")
            
            analysis['summary'] = " ".join(summary_parts) if summary_parts else "Windows batch script"
        
        elif file_path.suffix in ['.sh', '.bash']:
            # Shell script analysis
            summary_parts = []
            
            # Check shebang
            if content.startswith('#!/'):
                shebang = content.split('\n')[0]
                if 'bash' in shebang:
                    summary_parts.append("Bash script")
                elif 'sh' in shebang:
                    summary_parts.append("Shell script")
            
            # Look for purpose
            if 'docker' in content:
                summary_parts.append("Docker automation")
            elif 'npm' in content or 'yarn' in content:
                summary_parts.append("Node.js build script")
            elif 'pytest' in content or 'unittest' in content:
                summary_parts.append("Test runner script")
            elif 'deploy' in content.lower():
                summary_parts.append("Deployment script")
            
            analysis['summary'] = " ".join(summary_parts) if summary_parts else "Shell script"
        
        elif file_path.suffix == '.txt':
            # Text file analysis
            lines_sample = [l.strip() for l in lines[:10] if l.strip()]
            
            if 'readme' in file_path.name.lower():
                analysis['summary'] = "README text file with project information"
            elif 'license' in file_path.name.lower():
                analysis['summary'] = "License information"
            elif 'todo' in content.lower()[:100]:
                analysis['summary'] = "TODO list or task tracking"
            elif all(re.match(r'^\d{4}-\d{2}-\d{2}', line) for line in lines_sample[:3] if line):
                analysis['summary'] = "Log file with timestamped entries"
            elif len(lines_sample) > 0:
                analysis['summary'] = f"Text document: {lines_sample[0][:100]}"
            else:
                analysis['summary'] = "Text file"
        
        # Add generic info if no specific analysis
        if not analysis['summary']:
            # First few lines of content
            preview_lines = []
            for line in lines[:5]:
                line = line.strip()
                if line and not line.startswith('#'):
                    preview_lines.append(line)
                    break
            if preview_lines:
                analysis['summary'] = preview_lines[0][:150]
            else:
                analysis['summary'] = "Text file"
        
        return analysis
        
    except Exception as e:
        return {
            'path': file_path,
            'lines': 0,
            'non_empty_lines': 0,
            'size': 0,
            'summary': f"Error analyzing file: {str(e)}"
        }


def get_file_tree(directory, prefix="", is_last=True, ignore_dirs=None, file_analyses=None):
    """
    Recursively build a file tree structure with content briefs.
    """
    if ignore_dirs is None:
        ignore_dirs = {'__pycache__', 'node_modules', 'venv'}
    
    tree_lines = []
    
    # Get all items in directory
    try:
        items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except PermissionError:
        return [f"{prefix}[Permission Denied]"]
    
    # Filter out ignored directories and files
    items = [item for item in items if not (item.is_dir() and (item.name in ignore_dirs or should_skip_directory(item)))]
    items = [item for item in items if not (item.is_file() and should_skip_file(item))]
    
    for i, item in enumerate(items):
        is_last_item = i == len(items) - 1
        
        # Create the tree branch characters
        if is_last:
            current_prefix = prefix + "└── "
            extension_prefix = prefix + "    "
        else:
            current_prefix = prefix + "├── "
            extension_prefix = prefix + "│   "
        
        if item.is_file():
            # Add file with size and brief
            size = item.stat().st_size
            size_str = format_size(size)
            
            # Check if it's a text file we should analyze
            if item.suffix.lower() in TEXT_EXTENSIONS:
                emoji = get_emoji(item)
                brief = get_file_brief(item)
                tree_lines.append(f"{current_prefix}{emoji} {item.name} ({size_str}) - {brief}")
                
                # Store detailed analysis for later
                if file_analyses is not None:
                    analysis = analyze_file_content(item)
                    file_analyses.append(analysis)
            else:
                # Binary file
                tree_lines.append(f"{current_prefix}{item.name} ({size_str})")
        else:
            # Add directory
            tree_lines.append(f"{current_prefix}📁 {item.name}/")
            # Recursively add subdirectory contents
            subtree = get_file_tree(item, extension_prefix, is_last_item, ignore_dirs, file_analyses)
            tree_lines.extend(subtree)
    
    return tree_lines


def format_size(size_bytes):
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"


def count_items(directory, ignore_dirs=None):
    """Count files and directories recursively."""
    if ignore_dirs is None:
        ignore_dirs = {'__pycache__', 'node_modules', 'venv'}
    
    file_count = 0
    dir_count = 0
    text_file_count = 0
    file_type_counts = defaultdict(int)
    
    for root, dirs, files in os.walk(directory):
        # Remove ignored directories from the walk (including dot directories)
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
        
        dir_count += len(dirs)
        
        for file in files:
            file_path = Path(file)
            if should_skip_file(file_path):
                continue
            
            file_count += 1
            ext = file_path.suffix.lower()
            
            if ext in TEXT_EXTENSIONS:
                text_file_count += 1
                file_type_counts[ext] += 1
    
    return file_count, dir_count, text_file_count, file_type_counts


def create_text_pie_chart(data, width=40):
    """Create a text-based pie chart."""
    total = sum(data.values())
    if total == 0:
        return []
    
    # Sort by count
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    
    chart_lines = []
    chart_lines.append("File Type Distribution:")
    chart_lines.append("")
    
    # Create bar chart representation
    for ext, count in sorted_data[:10]:  # Top 10 file types
        percentage = (count / total) * 100
        bar_length = int((count / total) * width)
        bar = "█" * bar_length
        
        emoji = FILE_EMOJIS.get(ext, '📄')
        label = f"{emoji} {ext}"
        chart_lines.append(f"{label:12} {bar} {count:3d} ({percentage:4.1f}%)")
    
    # Add others if more than 10 types
    if len(sorted_data) > 10:
        others_count = sum(count for _, count in sorted_data[10:])
        percentage = (others_count / total) * 100
        bar_length = int((others_count / total) * width)
        bar = "█" * bar_length
        chart_lines.append(f"{'📦 others':12} {bar} {others_count:3d} ({percentage:4.1f}%)")
    
    chart_lines.append("")
    chart_lines.append(f"Total files analyzed: {total}")
    
    return chart_lines


def group_analyses_by_type(analyses):
    """Group file analyses by file type."""
    grouped = defaultdict(list)
    for analysis in analyses:
        ext = analysis['path'].suffix.lower()
        grouped[ext].append(analysis)
    return grouped


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate a file tree structure with content analysis in markdown format'
    )
    parser.add_argument(
        '--dir',
        type=str,
        default='.',
        help='Directory to scan (default: current directory)'
    )
    parser.add_argument(
        '--ignore',
        type=str,
        nargs='*',
        help='Additional directories to ignore'
    )
    parser.add_argument(
        '--no-content',
        action='store_true',
        help='Skip content analysis (faster, only show tree)'
    )
    
    args = parser.parse_args()
    
    # Get the directory path
    scan_dir = Path(args.dir).resolve()
    
    if not scan_dir.exists():
        print(f"Error: Directory '{scan_dir}' does not exist.")
        return 1
    
    if not scan_dir.is_dir():
        print(f"Error: '{scan_dir}' is not a directory.")
        return 1
    
    # Set up ignore directories - now only includes non-dot directories by default
    ignore_dirs = {'__pycache__', 'node_modules', 'venv'}
    if args.ignore:
        ignore_dirs.update(args.ignore)
    
    # Generate timestamp
    now = datetime.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    
    # Create output filename
    output_file = f"ARCHITECTURE-{date_str}-{time_str}.md"
    
    print(f"Scanning directory: {scan_dir}")
    print(f"Ignoring dot directories: All directories starting with '.'")
    print(f"Ignoring exclamation directories: All directories starting with '!'")
    print(f"Ignoring other directories: {', '.join(sorted(ignore_dirs))}")
    if not args.no_content:
        print("Analyzing file contents...")
    
    # Count items
    file_count, dir_count, text_file_count, file_type_counts = count_items(scan_dir, ignore_dirs)
    
    # Generate the tree with analyses
    file_analyses = [] if not args.no_content else None
    tree_lines = get_file_tree(scan_dir, "", True, ignore_dirs, file_analyses)
    
    # Create the markdown content
    md_content = [
        f"# Project Architecture",
        f"",
        f"**Generated on:** {now.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Root Directory:** `{scan_dir}`  ",
        f"**Total Files:** {file_count}  ",
        f"**Total Directories:** {dir_count}  ",
        f"**Text Files Analyzed:** {text_file_count}  ",
        f""
    ]
    
    # Add file type distribution chart
    if file_type_counts:
        md_content.append("## File Type Distribution")
        md_content.append("")
        md_content.append("```")
        chart_lines = create_text_pie_chart(file_type_counts)
        md_content.extend(chart_lines)
        md_content.append("```")
        md_content.append("")
    
    # Add directory structure
    md_content.extend([
        f"## Directory Structure",
        f"",
        f"```",
        f"{scan_dir.name}/",
    ])
    
    md_content.extend(tree_lines)
    md_content.append("```")
    
    # Add file content analysis section
    if file_analyses:
        md_content.extend([
            "",
            "## File Content Analysis",
            "",
            "Detailed analysis of text files found in the project:",
            ""
        ])
        
        # Group analyses by file type
        grouped = group_analyses_by_type(file_analyses)
        
        for ext, analyses in sorted(grouped.items()):
            # File type header with emoji
            emoji = FILE_EMOJIS.get(ext, '📄')
            file_type = {
                '.py': 'Python Files',
                '.js': 'JavaScript Files',
                '.ts': 'TypeScript Files',
                '.jsx': 'JSX Files',
                '.tsx': 'TSX Files',
                '.md': 'Markdown Files',
                '.html': 'HTML Files',
                '.css': 'CSS Files',
                '.json': 'JSON Files',
                '.yml': 'YAML Files',
                '.yaml': 'YAML Files',
                '.txt': 'Text Files',
                '.bat': 'Batch Files',
                '.sh': 'Shell Scripts',
                '.sql': 'SQL Files',
            }.get(ext, f'{ext.upper()} Files')
            
            md_content.extend([
                f"### {emoji} {file_type}",
                ""
            ])
            
            # Sort by file path
            for analysis in sorted(analyses, key=lambda x: x['path']):
                rel_path = analysis['path'].relative_to(scan_dir)
                
                # Create table for file stats
                md_content.extend([
                    f"#### `{rel_path}`",
                    "",
                    "| Lines | Non-Empty | Size |",
                    "|-------|-----------|------|",
                    f"| {analysis['lines']} | {analysis['non_empty_lines']} | {format_size(analysis['size'])} |",
                    "",
                    f"**Summary:** {analysis['summary']}",
                    ""
                ])
    
    # Add summary section
    md_content.extend([
        "",
        "## Summary",
        "",
        f"- **Files scanned:** {file_count}",
        f"- **Directories scanned:** {dir_count}",
        f"- **Text files analyzed:** {text_file_count}",
        f"- **Ignored dot directories:** All directories starting with '.'",
        f"- **Ignored exclamation directories:** All directories starting with '!'",
        f"- **Ignored other directories:** {', '.join(sorted(ignore_dirs)) if ignore_dirs else 'None'}",
        f"- **Excluded files:** desktop.ini, *.lnk",
    ])
    
    # Write to file
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    print(f"\nFile tree generated successfully!")
    print(f"Output saved to: {output_path.resolve()}")
    print(f"Total items: {file_count} files, {dir_count} directories")
    if not args.no_content:
        print(f"Analyzed {text_file_count} text files")
    
    return 0


if __name__ == "__main__":
    exit(main())