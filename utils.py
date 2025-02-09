import os
import platform

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def print_welcome_message():
    """Print the welcome message when starting the REPL."""
    welcome = """
Python REPL Environment
----------------------
Type 'help' for commands
Type 'exit' to quit
"""
    print(welcome)

def print_help():
    """Print help information."""
    help_text = """
Available Commands:
------------------
help  - Show this help message
clear - Clear the screen
exit  - Exit the REPL

You can:
1. Execute Python code directly
2. Run Python files by launching with: python python_repl.py <filename>
3. Use standard Python syntax and commands
4. Access all built-in Python functions and modules

Example usage:
>>> print("Hello, World!")
>>> x = 5
>>> y = 10
>>> print(x + y)
"""
    print(help_text)
