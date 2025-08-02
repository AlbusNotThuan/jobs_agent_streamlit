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
    

    def analyze_user_request(self, user_message: str) -> Dict[str, Any]:
        """Analyze the user's request and determine what type of analysis is needed.
        
        Args:
            user_message: The user's query
            
        Returns:
            Dictionary with analysis type and suggested approach
        """
        user_lower = user_message.lower()
        analysis_plan = {
            "query_type": "general",
            "needs_database": True,
            "suggested_queries": [],
            "analysis_focus": []
        }
        
        # Analyze what the user is asking for
        if any(word in user_lower for word in ['python', 'java', 'javascript', 'c++', 'programming']):
            analysis_plan["query_type"] = "programming_skills"
            analysis_plan["analysis_focus"].append("programming languages and frameworks")
            analysis_plan["suggested_queries"].append("Query for programming language skills in job postings")
            
        if any(word in user_lower for word in ['ai', 'ml', 'machine learning', 'data science', 'artificial intelligence']):
            analysis_plan["query_type"] = "ai_ml_skills" 
            analysis_plan["analysis_focus"].append("AI/ML and data science skills")
            analysis_plan["suggested_queries"].append("Query for AI/ML related skills and tools")
            
        if any(word in user_lower for word in ['top', 'most', 'popular', 'demand', 'trending']):
            analysis_plan["analysis_focus"].append("most in-demand skills")
            analysis_plan["suggested_queries"].append("Query for top skills by frequency")
            
        if any(word in user_lower for word in ['salary', 'pay', 'compensation', 'wage']):
            analysis_plan["analysis_focus"].append("salary analysis")
            analysis_plan["suggested_queries"].append("Query for salary information by skill")
            
        return analysis_plan

    def display_analysis_plan(self, user_message: str) -> None:
        """Display the analysis plan based on user request."""
        plan = self.analyze_user_request(user_message)
        
        self.display_thought(f"Analyzing the request: '{user_message}'")
        self.display_thought(f"I detect this is a {plan['query_type']} query focusing on: {', '.join(plan['analysis_focus'])}")
        
        if plan['suggested_queries']:
            self.display_thought("My planned approach:")
            for i, query in enumerate(plan['suggested_queries'], 1):
                print(f"   {i}. {query}")
        
        self.display_action("I'll now use the database query tool to gather the necessary data from the job market database.")


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
        # Import tools directly from skills_analyzer
       
        
        # Display detailed analysis of the user's request
        self.display_analysis_plan(user_message)
        
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
                query_database
            ],
            tool_config={'function_calling_config': {'mode': 'AUTO'}},  # Enable automatic tool calling
            system_instruction=system_instruction
        )
        try:
            # Enhanced prompt for autonomous behavior with explicit thought process instructions
            autonomous_prompt = f"""
AUTONOMOUS AGENT ACTIVATION:
User Request: {user_message}

Instructions: You are now operating as a fully autonomous agent. Follow the ReAct framework and SHOW YOUR THINKING:

CRITICAL: ALWAYS make your thought process visible by using these exact formats:
🧠 **THOUGHT:** [Analyze what the user needs and plan your approach]
⚡ **ACTION:** [Explain what tool you're about to use and why]
👁️ **OBSERVATION:** [Analyze the results and decide next steps]

ReAct Framework Steps:
1. START with "🧠 **THOUGHT:**" - Think about what the user needs
2. State "⚡ **ACTION:**" before each tool use - Explain what you're doing
3. After each tool result, use "👁️ **OBSERVATION:**" - Analyze and plan next steps
4. Continue the cycle until you have complete information
5. Provide comprehensive analysis and insights
6. IMPORTANT: Always provide a brief summary in your response BEFORE calling end_session
7. Call print_message with your detailed findings, then end_session

Remember: NO CONFIRMATIONS NEEDED. Act immediately and autonomously.
SHOW YOUR THINKING PROCESS throughout the entire interaction.
Always include a summary of your findings in your final response text.
"""
            
            # Add conversation context for continuity
            conversation_context = ""
            if self.conversation_history:
                conversation_context = "\n\nPrevious conversation context:\n" + "\n".join(self.conversation_history[-4:])
            
            full_message = autonomous_prompt + conversation_context
            
            self.display_action("Sending the request to the AI agent with instructions to work autonomously and query the database as needed.")
            
            self.display_observation("The AI agent is now processing the request. It will analyze what data is needed and automatically query the job market database.")
            
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_message,
                config=config
            )
            
            self.display_observation("Received response from AI agent. Analyzing the results and checking if the task was completed successfully.")
            
            # Store conversation for context
            self.conversation_history.append(f"User: {user_message}")
            self.conversation_history.append(f"Agent: {response.text}")
            
            if self.verbose_mode:
                print(f"🤖 Agent raw response: {response.text}")
            
            # Check if the response contains tool calls or thinking process
            if "THOUGHT:" not in response.text and "ACTION:" not in response.text:
                self.display_observation("The AI agent provided a direct response. For more detailed analysis, it may need to query the database.")
                
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
    print("📊 Ask me anything about job market skills and trends!")
    print("\nExample queries:")
    print("• 'What are the most in-demand skills?'")
    print("• 'Show me hot AI/ML skills'") 
    print("• 'What programming languages are trending?'")
    print("• 'Analyze data science job requirements'")
    print("• 'Compare Python vs JavaScript demand'")
    print("\n🔍 THOUGHT PROCESS INDICATORS:")
    print("   🧠 THOUGHT: Agent's reasoning and planning")
    print("   ⚡ ACTION: Tools being used and why")
    print("   👁️ OBSERVATION: Analysis of results and next steps")
    print("\n⚡ The agent will automatically query the database and provide insights")
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