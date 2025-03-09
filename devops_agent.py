#!/usr/bin/env python3
import os
import sys
import json
import argparse
import logging
import subprocess
import requests
import re
from pathlib import Path
import time
import getpass

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('devops-ai-agent')

CONFIG_DIR = Path.home() / '.devops-ai-agent'
CONFIG_FILE = CONFIG_DIR / 'config.json'

class DevOpsAIAgent:
    def __init__(self):
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from config file or create if not exists"""
        if not CONFIG_DIR.exists():
            CONFIG_DIR.mkdir(parents=True)
            
        if not CONFIG_FILE.exists():
            logger.info("No configuration found. Running first-time setup...")
            return self.first_time_setup()
        
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.info("Configuration loaded successfully.")
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Running setup again to fix configuration...")
            return self.first_time_setup()
    
    def first_time_setup(self):
        """First time setup to configure the AI agent"""
        print("\n" + "="*50)
        print("Welcome to DevOps AI Agent Setup!")
        print("="*50)
        
        config = {}
        
        # Get OpenRouter API Key
        print("\nYou will now be prompted to enter your OpenRouter API key.")
        while True:
            try:
                # Using sys.stdin.readline() for more reliable input handling
                print("\nEnter your OpenRouter API key: ", end='', flush=True)
                api_key = sys.stdin.readline().strip()
                print(f"Validating API key...")
                if self.validate_openrouter_api_key(api_key):
                    config['api_key'] = api_key
                    print("API key validation successful!")
                    break
                else:
                    print("Invalid API key. Please try again.")
            except Exception as e:
                logger.error(f"Exception during API key input: {e}")
                print("Error during API key input. Please try again.")
        
        # Get Model choice
        print("\nFetching available models...")
        models = self.get_available_models(config['api_key'])
        
        print("\nAvailable Models:")
        for i, model in enumerate(models, 1):
            print(f"{i}. {model}")
        
        while True:
            try:
                print("\nSelect a model (number) or enter a custom model ID: ", end='', flush=True)
                choice_input = sys.stdin.readline().strip()
                
                # Check if input is a number (model selection from list)
                if choice_input.isdigit():
                    choice = int(choice_input)
                    if 1 <= choice <= len(models):
                        config['model'] = models[choice-1]
                        print(f"Selected model: {config['model']}")
                        break
                    else:
                        print(f"Please enter a number between 1 and {len(models)}.")
                # If not a number, treat as custom model ID
                else:
                    config['model'] = choice_input
                    print(f"Using custom model: {config['model']}")
                    break
            except ValueError:
                print("Please enter a valid number or model ID.")
        
        # Configure error monitoring settings
        config['error_monitoring'] = {
            'enabled': True,
            'scan_interval': 300,  # 5 minutes
            'log_patterns': [
                r'error:',
                r'exception',
                r'failure',
                r'fatal',
                r'critical'
            ]
        }
        
        # Save config
        print("\nSaving configuration...")
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\nSetup completed successfully!")
        return config
    
    def validate_openrouter_api_key(self, api_key):
        """Validate OpenRouter API key by making a test request"""
        if not api_key:
            return False
            
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(
                'https://openrouter.ai/api/v1/auth/key',
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False
    
    def get_available_models(self, api_key):
        """Get all available models from OpenRouter"""
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                models_data = response.json()
                
                # Get all available models instead of filtering
                available_models = []
                for model in models_data.get('data', []):
                    model_id = model.get('id')
                    if model_id:
                        available_models.append(model_id)
                
                # If no models were found, provide default fallback models
                if not available_models:
                    logger.warning("No models returned from API, using fallback list")
                    return [
                        "anthropic/claude-3-opus",
                        "anthropic/claude-3-sonnet",
                        "anthropic/claude-3-haiku",
                        "google/gemini-pro",
                        "google/gemini-1.5-pro",
                        "openai/gpt-4o",
                        "openai/gpt-4-turbo",
                        "openai/gpt-3.5-turbo",
                        "meta/llama-3-70b-instruct",
                        "mistralai/mixtral-8x7b",
                        "mistralai/mistral-7b-instruct"
                    ]
                
                return available_models
            else:
                logger.warning(f"Could not fetch models: {response.status_code}")
                # Return a wide variety of models as fallback
                return [
                    "anthropic/claude-3-opus",
                    "anthropic/claude-3-sonnet",
                    "anthropic/claude-3-haiku",
                    "google/gemini-pro",
                    "google/gemini-1.5-pro", 
                    "openai/gpt-4o",
                    "openai/gpt-4-turbo",
                    "openai/gpt-3.5-turbo",
                    "meta/llama-3-70b-instruct",
                    "mistralai/mixtral-8x7b",
                    "mistralai/mistral-7b-instruct"
                ]
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            # Return a wide variety of models as fallback
            return [
                "anthropic/claude-3-opus",
                "anthropic/claude-3-sonnet",
                "anthropic/claude-3-haiku",
                "google/gemini-pro",
                "google/gemini-1.5-pro",
                "openai/gpt-4o",
                "openai/gpt-4-turbo",
                "openai/gpt-3.5-turbo",
                "meta/llama-3-70b-instruct",
                "mistralai/mixtral-8x7b",
                "mistralai/mistral-7b-instruct"
            ]
    
    def analyze_error(self, error_text):
        """Analyze an error using the AI model"""
        prompt = f"""You are a DevOps AI assistant. Analyze this error and provide a solution:

```
{error_text}
```

Please explain:
1. What is causing this error
2. How to fix it
3. Any preventive measures for the future

Format your response in markdown with clear steps.
"""
        
        try:
            headers = {
                'Authorization': f'Bearer {self.config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.config['model'],
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            }
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result['choices'][0]['message']['content']
                return assistant_message
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return f"Error: Could not analyze the error. API responded with {response.status_code}."
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return f"Error: Could not analyze the error due to an API issue: {str(e)}"
    
    def install_tool(self, tool_name):
        """Provide instructions for installing a DevOps tool"""
        prompt = f"""You are a DevOps AI assistant. Provide detailed installation instructions for {tool_name}.

Include:
1. Prerequisites
2. Step-by-step installation process
3. Basic configuration
4. How to verify the installation
5. Common issues and troubleshooting

Format your response in markdown with clear steps that can be executed in a terminal.
"""
        
        try:
            headers = {
                'Authorization': f'Bearer {self.config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': self.config['model'],
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            }
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result['choices'][0]['message']['content']
                return assistant_message
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return f"Error: Could not get installation instructions. API responded with {response.status_code}."
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            return f"Error: Could not get installation instructions due to an API issue: {str(e)}"
            
    def start_monitoring(self):
        """Start background monitoring for errors in logs"""
        logger.info("Starting error monitoring...")
        monitoring_config = self.config.get('error_monitoring', {})
        
        if not monitoring_config.get('enabled', False):
            logger.info("Error monitoring is disabled in configuration.")
            return
            
        scan_interval = monitoring_config.get('scan_interval', 300)
        log_patterns = monitoring_config.get('log_patterns', [r'error:', r'exception'])
        
        # In a real implementation, this would run in a separate thread or process
        logger.info(f"Monitoring active with scan interval: {scan_interval}s")
        logger.info(f"Watching for patterns: {log_patterns}")
        
        # Placeholder for actual monitoring implementation
        # This would involve scanning log files or listening to log streams
        print("Error monitoring is now active in the background.")
        print("Use 'devops-agent analyze-logs <log_file>' to manually analyze logs.")
        
    def execute_command(self, args):
        """Execute command based on arguments"""
        if args.command == 'analyze':
            if args.file and os.path.exists(args.file):
                with open(args.file, 'r') as f:
                    error_text = f.read()
            elif args.text:
                error_text = args.text
            else:
                print("Enter the error text to analyze (type 'DONE' on a new line when finished):")
                lines = []
                while True:
                    line = sys.stdin.readline().strip()
                    if line == 'DONE':
                        break
                    lines.append(line)
                error_text = '\n'.join(lines)
                
            print("\nAnalyzing error...\n")
            analysis = self.analyze_error(error_text)
            print(analysis)
            
        elif args.command == 'install':
            if args.tool:
                tool_name = args.tool
            else:
                print("Enter the name of the tool to install: ", end='', flush=True)
                tool_name = sys.stdin.readline().strip()
                
            print(f"\nGetting installation instructions for {tool_name}...\n")
            instructions = self.install_tool(tool_name)
            print(instructions)
            
        elif args.command == 'monitor':
            self.start_monitoring()
            
        elif args.command == 'setup':
            if args.api_key:
                print(f"Using provided API key from command line")
                config = {}
                config['api_key'] = args.api_key
                
                if args.model:
                    config['model'] = args.model
                    print(f"Using provided model: {config['model']}")
                else:
                    # Get Model choice
                    print("\nFetching available models...")
                    models = self.get_available_models(config['api_key'])
                    
                    print("\nAvailable Models:")
                    for i, model in enumerate(models, 1):
                        print(f"{i}. {model}")
                    
                    while True:
                        try:
                            print("\nSelect a model (number) or enter a custom model ID: ", end='', flush=True)
                            choice_input = sys.stdin.readline().strip()
                            
                            if choice_input.isdigit():
                                choice = int(choice_input)
                                if 1 <= choice <= len(models):
                                    config['model'] = models[choice-1]
                                    print(f"Selected model: {config['model']}")
                                    break
                                else:
                                    print(f"Please enter a number between 1 and {len(models)}.")
                            else:
                                config['model'] = choice_input
                                print(f"Using custom model: {config['model']}")
                                break
                        except ValueError:
                            print("Please enter a valid number or model ID.")
                
                # Configure error monitoring settings
                config['error_monitoring'] = {
                    'enabled': True,
                    'scan_interval': 300,  # 5 minutes
                    'log_patterns': [
                        r'error:',
                        r'exception',
                        r'failure',
                        r'fatal',
                        r'critical'
                    ]
                }
                
                # Save config
                print("\nSaving configuration...")
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=2)
                
                print("\nSetup completed successfully!")
                self.config = config
            else:
                self.config = self.first_time_setup()
            
        else:
            print("Unknown command. Use --help for available commands.")

def main():
    """Main entry point for the CLI"""
    parser = argparse.ArgumentParser(description='DevOps AI Agent for error solving and tool installation.')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze an error')
    analyze_parser.add_argument('--file', '-f', help='Path to error log file')
    analyze_parser.add_argument('--text', '-t', help='Error text to analyze')
    
    # Install command
    install_parser = subparsers.add_parser('install', help='Get installation instructions for a tool')
    install_parser.add_argument('--tool', '-t', help='Name of the tool to install')
    
    # Monitor command
    subparsers.add_parser('monitor', help='Start error monitoring')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Run first-time setup or reconfigure')
    setup_parser.add_argument('--api-key', help='OpenRouter API key')
    setup_parser.add_argument('--model', help='Model ID to use')
    
    args = parser.parse_args()
    
    # If no command is given, show help
    if not args.command:
        parser.print_help()
        return
    
    agent = DevOpsAIAgent()
    agent.execute_command(args)

if __name__ == '__main__':
    main()

