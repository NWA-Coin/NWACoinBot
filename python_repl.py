#!/usr/bin/env python3
import code
import sys
import traceback
from utils import clear_screen, print_welcome_message, print_help

class EnhancedConsole(code.InteractiveConsole):
    def __init__(self):
        super().__init__()
        self.filename = "<console>"
        print_welcome_message()
        
    def push(self, line):
        """Push a line to the interpreter."""
        try:
            return code.InteractiveConsole.push(self, line)
        except KeyboardInterrupt:
            self.write("\nKeyboardInterrupt\n")
            return False
        except Exception as e:
            self.showtraceback()
            return False

    def raw_input(self, prompt=""):
        """Return the input string with custom prompt."""
        try:
            return input(prompt)
        except KeyboardInterrupt:
            self.write("\n")
            return ""
        except EOFError:
            self.write("\n")
            raise

    def run_file(self, filename):
        """Execute a Python file."""
        try:
            with open(filename, 'r') as file:
                content = file.read()
            self.runcode(compile(content, filename, 'exec'))
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found.")
        except Exception as e:
            print(f"Error executing file: {str(e)}")
            self.showtraceback()

def main():
    console = EnhancedConsole()
    
    # Check if a file was provided as an argument
    if len(sys.argv) > 1:
        console.run_file(sys.argv[1])
        return

    # Interactive mode
    while True:
        try:
            command = console.raw_input(">>> ")
            
            # Handle special commands
            if command.strip() == "exit":
                break
            elif command.strip() == "clear":
                clear_screen()
            elif command.strip() == "help":
                print_help()
            else:
                console.push(command)
                
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            traceback.print_exc()
    
    print("\nGoodbye!")

if __name__ == "__main__":
    main()
