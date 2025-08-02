# -*- coding: utf-8 -*-
"""
LinkedIn Jobs Skills Analyzer Chatbot
AI-powered chatbot với tích hợp các tool phân tích skills

Usage:
    python AI.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

from google import genai
from google.genai import types

# Import các functions từ skills_analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from skills_analyzer import (
        extract_in_demand_skills,
        get_hot_skills_last_month,
        get_skills_by_category,
        get_trending_skills_comparison,
        get_job_categories_analysis
    )
    import pandas as pd
except ImportError as e:
    print(f"⚠️ Import error: {e}")
    print("Make sure skills_analyzer.py is in the same directory and pandas is installed")
    sys.exit(1)


# Load environment variables
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

class SkillsAnalyzerChatbot:
    def __init__(self):
        self.client = genai.Client(api_key=API_KEY)
        self.conversation_history = []
        self.session_active = 1  # 1: session active, 0: session ended
        self.max_autonomous_cycles = 10  # Prevent infinite loops
        self.verbose_mode = False  # Set to True to see ReAct thinking process
        self.last_print_message = None  # Store the last message printed by the agent


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
        self.last_print_message = message  # Store for later reference
    
    
    def format_skills_response(self, data: Dict, analysis_type: str) -> str:
        """Format the analysis results for chatbot response"""
        if not data.get("success"):
            return f"❌ {data.get('message', 'Analysis failed')}"
        
        result = data["data"]
        
        if analysis_type == "all_skills":
            response = f"📊 **GENERAL SKILLS ANALYSIS**\n\n"
            response += f"📈 Total jobs analyzed: {result.get('total_jobs', 0)}\n"
            response += f"📋 Jobs with skills info: {result.get('valid_jobs', 0)}\n"
            response += f"🔍 Unique skills found: {result.get('total_unique_skills', 0)}\n\n"
            
            response += "🏆 **TOP SKILLS:**\n"
            for i, skill in enumerate(result.get('top_skills', [])[:10], 1):
                response += f"{i:2d}. {skill['skill']} - {skill['frequency']} jobs ({skill['percentage']}%)\n"
        
        elif analysis_type == "hot_skills":
            response = f"🔥 **HOT SKILLS - LAST MONTH**\n\n"
            response += f"📅 Period: {result.get('period', 'Recent')}\n"
            response += f"📊 Jobs analyzed: {result.get('total_recent_jobs', 0)}\n\n"
            
            response += "🚀 **TOP HOT SKILLS:**\n"
            for i, skill in enumerate(result.get('hot_skills', [])[:10], 1):
                fire_level = "🔥" * min(int(skill['percentage_of_valid'] / 10) + 1, 5)
                response += f"{i:2d}. {skill['skill']} - {skill['frequency']} jobs ({skill['percentage_of_valid']:.1f}%) {fire_level}\n"
        
        elif analysis_type == "category_skills":
            response = f"📂 **SKILLS BY CATEGORY**\n\n"
            for cat_key, cat_info in result.items():
                if cat_info.get('skills'):
                    response += f"🔸 **{cat_info['name']}:**\n"
                    for skill in cat_info['skills'][:5]:
                        response += f"   • {skill['skill']} - {skill['frequency']} jobs\n"
                    response += "\n"
        
        elif analysis_type == "trends":
            response = f"📈 **SKILLS TRENDS ANALYSIS**\n\n"
            response += f"📅 Period: {result.get('analysis_period', 'Recent')}\n"
            response += f"📊 Total jobs: {result.get('total_jobs_in_period', 0)}\n\n"
            
            response += "🏆 **TOP TRENDING SKILLS:**\n"
            for i, (skill, count) in enumerate(result.get('top_skills_overall', [])[:10], 1):
                response += f"{i:2d}. {skill} - {count} mentions\n"
        
        elif analysis_type == "job_categories":
            response = f"💼 **SKILLS BY JOB CATEGORIES**\n\n"
            for category, data in result.items():
                response += f"🔹 **{category}** ({data['job_count']} jobs):\n"
                for skill, count in data['top_skills'][:5]:
                    response += f"   • {skill}: {count}\n"
                response += "\n"
        
        return response
    
    def chat(self, user_message: str) -> str:
        """Main chat function with autonomous tool integration using ReAct framework"""
        # Import tools directly from skills_analyzer
        from skills_analyzer import (
            extract_in_demand_skills,
            get_hot_skills_last_month,
            get_skills_by_category,
            get_trending_skills_comparison,
            get_job_categories_analysis
        )
        from psycopg_query import query_database
        
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
                # extract_in_demand_skills,
                # get_hot_skills_last_month,
                # get_skills_by_category,
                # get_trending_skills_comparison,
                # get_job_categories_analysis,
                self.print_message,
                self.end_session,
                query_database
            ],
            tool_config={'function_calling_config': {'mode': 'AUTO'}},  # Enable automatic tool calling
            system_instruction=system_instruction
        )
        try:
            # Enhanced prompt for autonomous behavior
            autonomous_prompt = f"""
AUTONOMOUS AGENT ACTIVATION:
User Request: {user_message}

Instructions: You are now operating as a fully autonomous agent. Follow the ReAct framework:
1. THINK about what the user needs
2. ACT by using tools immediately without asking permission  
3. OBSERVE the results and continue until complete
4. Provide comprehensive analysis and insights
5. IMPORTANT: Always provide a brief summary in your response BEFORE calling end_session
6. Call print_message with your detailed findings, then end_session

Remember: NO CONFIRMATIONS NEEDED. Act immediately and autonomously.
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
                model="gemini-2.5-flash",
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
    print("📊 Ask me anything about job market skills and trends!")
    print("\nExample queries:")
    print("• 'What are the most in-demand skills?'")
    print("• 'Show me hot AI/ML skills'") 
    print("• 'What programming languages are trending?'")
    print("• 'Analyze data science job requirements'")
    print("• 'Compare Python vs JavaScript demand'")
    print("\n⚡ The agent will automatically query the database and provide insights")
    print("📋 Special commands: 'help', 'verbose on/off', 'exit'")
    print("=" * 60)
    
    chatbot = SkillsAnalyzerChatbot()
    
    while True:
        try:
            chatbot.session_active = 1  # Reset session_active for each new user input
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye', 'end']:
                print("👋 Goodbye! Thanks for using the Autonomous Skills Analyzer!")
                break
            
            # Special commands for autonomous agent
            if user_input.lower() == 'verbose on':
                chatbot.set_verbose_mode(True)
                continue
            elif user_input.lower() == 'verbose off':
                chatbot.set_verbose_mode(False)
                continue
            elif user_input.lower() in ['help', 'commands']:
                print("\n🆘 AUTONOMOUS AGENT COMMANDS:")
                print("• 'verbose on/off' - Toggle detailed ReAct process visibility")
                print("• 'exit' - Quit the application")
                print("• Ask any question about job skills and the agent will work autonomously!")
                continue
            
            if not user_input:
                print("Please enter a question to let the autonomous agent help you.")
                continue
            
            print("\n🤖 AUTONOMOUS AGENT ACTIVATED - Working independently...")
            if not chatbot.verbose_mode:
                print("🔄 Following ReAct framework: Reasoning → Acting → Observing")
            
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