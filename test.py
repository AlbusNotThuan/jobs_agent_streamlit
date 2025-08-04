# -*- coding: utf-8 -*-
"""
LinkedIn Jobs Skills Analyzer Chatbot
AI-powered chatbot với tích hợp các tool phân tích skills

Usage:
    python AI.py
"""
import os
from datetime import datetime
from typing import Dict, List, Any
from google import genai
from google.genai import types
import pandas as pd
from psycopg_query import query_database
from toolbox import plot_skill_frequency
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

class SkillsAnalyzerChatbot:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.conversation_history = []
        self.session_active = 1  # 1: session active, 0: session ended
        self.max_autonomous_cycles = 10  # Prevent infinite loops
        self.verbose_mode = True  # Set to True to see ReAct thinking process
        self.last_print_message = None  # Store the last message printed by the agent
        self.thought_process_enabled = True  # Enable explicit thought process display


    def display_thought(self, thought: str) -> None:
        """Display the agent's thought process to the user.
        
        Args:
            thought: The thought or reasoning to display
            
        Returns:
            None
        """
        if self.thought_process_enabled:
            print(f"\n🧠 **THOUGHT:** {thought}")
    
    def display_action(self, action: str) -> None:
        """Display the agent's action to the user.
        
        Args:
            action: The action being taken
            
        Returns:
            None
        """
        if self.thought_process_enabled:
            print(f"\n⚡ **ACTION:** {action}")
    
    def display_observation(self, observation: str) -> None:
        """Display the agent's observation to the user.
        
        Args:
            observation: The observation or analysis
            
        Returns:
            None
        """
        if self.thought_process_enabled:
            print(f"\n👁️ **OBSERVATION:** {observation}")


    def set_verbose_mode(self, verbose: bool = True) -> None:
        """Enable/disable verbose mode to see ReAct thinking process.
        
        Args:
            verbose: True to enable verbose output, False to disable
            
        Returns:
            None
        """
        self.verbose_mode = verbose
        if verbose:
            print("🔍 Verbose mode enabled - You'll see the agent's reasoning process")
        else:
            print("🔇 Verbose mode disabled - Only final results will be shown")


    def end_session(self) -> None:
        """Ends the chatbot session by setting session_active to 0.

        Args:
            None

        Returns:
            None
        """
        self.session_active = 0


    def print_message(self, message: str) -> None:
        """Prints a message to the console for the chatbot user.

        Args:
            message: The message string to display.

        Returns:
            None
        """
        print(f"\n📋 {message}")
        self.last_print_message = message  # Store for later eference


    def chat(self, user_message: str) -> str:
        """Main chat function with autonomous tool integration using ReAct framework"""
        
        # Configure tools for Gemini, including print_message and end_session
        # Read system instruction from file
        system_instruction_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_instruction.md")
        try:
            with open(system_instruction_path, "r", encoding="utf-8") as f:
                system_instruction = f.read()
        except Exception as e:
            print(f"⚠️ Could not read system_instruction.md: {e}")
            system_instruction = ""

        config = types.GenerateContentConfig(
            tools=[
                self.print_message,
                self.end_session,
                query_database,
                plot_skill_frequency
            ],
            tool_config={'function_calling_config': {'mode': 'AUTO'}},  # Enable automatic tool calling
            system_instruction=system_instruction
        )
        try:
            # Enhanced prompt for autonomous behavior - let the agent create its own plan
            autonomous_prompt = f"""
AUTONOMOUS AGENT ACTIVATION:
User Request: {user_message}

Instructions: You are now operating as a fully autonomous agent. Follow the ReAct framework and SHOW YOUR THINKING:

CRITICAL: ALWAYS make your thought process visible by using these exact formats:
🧠 **THOUGHT:** [Analyze what the user needs and create your own analysis plan]
⚡ **ACTION:** [Explain what tool you're about to use and why]
👁️ **OBSERVATION:** [Analyze the results and decide next steps]

ReAct Framework Steps:
1. START with "🧠 **THOUGHT:**" - Analyze the user's request and determine what type of job market analysis is needed. Create your own plan based on the request.
2. State "⚡ **ACTION:**" before each tool use - Explain what database query or analysis you're performing
3. After each tool result, use "👁️ **OBSERVATION:**" - Analyze the results and decide if you need more data
4. Continue the cycle until you have complete information to answer the user's question
5. Provide comprehensive analysis and insights based on the data you retrieved
6. IMPORTANT: Always provide a brief summary in your response BEFORE calling end_session
7. Call print_message with your detailed findings, then end_session

AUTONOMY RULES:
- NO predefined categories or keyword matching - interpret the request naturally
- CREATE your own analysis approach based on what the user is asking
- DECIDE what database queries are needed based on the context
- ADAPT your analysis to the specific request, not preset patterns

Remember: NO CONFIRMATIONS NEEDED. Act immediately and autonomously.
SHOW YOUR THINKING PROCESS throughout the entire interaction.
Always include a summary of your findings in your final response text.
"""
            
            # Add conversation context for continuity
            conversation_context = ""
            if self.conversation_history:
                conversation_context = "\n\nPrevious conversation context:\n" + "\n".join(self.conversation_history[-4:])
            
            full_message = autonomous_prompt + conversation_context
            
            if self.verbose_mode:
                print(f"🧠 Sending autonomous prompt to agent...")
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=full_message,
                config=config
            )
            
            # Store conversation for context
            self.conversation_history.append(f"User: {user_message}")
            self.conversation_history.append(f"Agent: {response.text}")
            
            if self.verbose_mode:
                print(f"🤖 Agent raw response: {response.text}")
                
            return response.text
            
        except Exception as e:
            error_msg = f"❌ Autonomous agent error: {str(e)}"
            print(error_msg)
            return error_msg

def main():
    """Main chatbot loop with autonomous agent support"""
    print("🤖 LinkedIn Jobs Skills Analyzer - AUTONOMOUS AI AGENT")
    print("=" * 60)
    print("🚀 AUTONOMOUS MODE: The agent will act independently without confirmations")
    print("🧠 THOUGHT PROCESS: The agent will show its ReAct framework thinking")
    print("📊 VISUALIZATION: The agent can now create skill demand plots!")
    print("💡 Ask me anything about job market skills and trends!")
    print("\nExample queries:")
    print("• 'What are the most in-demand skills?'")
    print("• 'Show me hot AI/ML skills'") 
    print("• 'Plot Python vs JavaScript demand'")
    print("• 'Visualize React skills over the last 6 months'")
    print("• 'Compare programming languages popularity'")
    print("• 'Analyze data science job requirements'")
    print("\n🔍 THOUGHT PROCESS INDICATORS:")
    print("   🧠 THOUGHT: Agent's reasoning and planning")
    print("   ⚡ ACTION: Tools being used and why")
    print("   👁️ OBSERVATION: Analysis of results and next steps")
    print("\n⚡ The agent will automatically query the database and create visualizations")
    print("📋 Special commands: 'help', 'verbose on/off', 'thoughts on/off', 'exit'")
    print("=" * 60)
    
    chatbot = SkillsAnalyzerChatbot()
    
    while True:
        try:
            chatbot.session_active = 1  # Reset session_active for each new user input
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye', 'end']:
                print("👋 Goodbye! Thanks for using the Autonomous Skills Analyzer!")
                break

            if not user_input:
                print("Please enter a question to let the autonomous agent help you.")
                continue
        
            response = chatbot.chat(user_input)
            
            # Check if session was ended by the agent
            if chatbot.session_active == 0:
                print("\n✅ AUTONOMOUS TASK COMPLETED!")
                if chatbot.last_print_message:
                    print("📊 The agent has provided detailed analysis above.")
                else:
                    print("🔍 The agent completed the analysis. Use 'verbose on' to see more details.")
                chatbot.session_active = 1  # Reset for next query
                chatbot.last_print_message = None  # Reset stored message
            else:
                # If session is still active, show the response
                if response and response.strip():
                    print(f"\n🤖 Agent Response:\n{response}")
                else:
                    print("\n🤖 Agent is working... (use 'verbose on' to see details)")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using the Autonomous Skills Analyzer!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print("The autonomous agent will continue. Please try another query.")

if __name__ == "__main__":
    main()