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
        """Main chat function with tool integration"""
        # Import tools directly from skills_analyzer
        from skills_analyzer import (
            extract_in_demand_skills,
            get_hot_skills_last_month,
            get_skills_by_category,
            get_trending_skills_comparison,
            get_job_categories_analysis
        )
        # Configure tools for Gemini
        config = types.GenerateContentConfig(
            tools=[
                extract_in_demand_skills,
                get_hot_skills_last_month,
                get_skills_by_category,
                get_trending_skills_comparison,
                get_job_categories_analysis
            ],
            system_instruction="""You are a LinkedIn Jobs Skills Analyzer AI Assistant. Your job is to help users analyze job market trends and skills demand.

Guidelines:
- Always use the available tools to answer user questions if needed. Do not fabricate or make up data.
- You may use multiple tools in combination to provide the most complete and accurate answer.
- Provide insights and recommendations based on the data you retrieve.
- Format responses clearly, using emojis where appropriate.
- Explain trends and what they mean for job seekers.
- Be helpful, concise, and conversational.
"""
        )
        try:
            # Add conversation context
            conversation_context = ""
            if self.conversation_history:
                conversation_context = "\n\nPrevious conversation:\n" + "\n".join(self.conversation_history[-4:])
            full_message = user_message + conversation_context
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_message,
                config=config
            )
            # Store conversation
            self.conversation_history.append(f"User: {user_message}")
            self.conversation_history.append(f"Assistant: {response.text}")
            return response.text
        except Exception as e:
            return f"❌ Error processing your request: {str(e)}"

def main():
    """Main chatbot loop"""
    print("🤖 LinkedIn Jobs Skills Analyzer Chatbot")
    print("=" * 50)
    print("Welcome! I can help you analyze job market skills and trends.")
    print("Ask me questions like:")
    print("• 'What are the most in-demand skills?'")
    print("• 'Show me hot AI/ML skills'") 
    print("• 'What programming languages are trending?'")
    print("• 'Analyze data science job requirements'")
    print("\nType 'exit' to quit, 'help' for more info.")
    print("=" * 50)
    
   
    chatbot = SkillsAnalyzerChatbot()
    
    while True:
        try:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye! Thanks for using the Skills Analyzer Chatbot!")
                break
            
            if user_input.lower() == 'help':
                print("""
🆘 HELP - Available Commands:

📊 General Analysis:
  • "analyze all skills" or "general overview"
  • "most in-demand skills"

🔥 Hot Skills:
  • "hot skills" or "trending this month"
  • "what's popular now"

📂 Skills by Category:
  • "programming skills" or "programming languages"
  • "AI skills" or "machine learning skills"
  • "data science skills"
  • "cloud skills"
  • "web development skills"

📈 Trends:
  • "skills trends" or "analyze trends"
  • "what's trending in the last 30 days"

💼 Job Categories:
  • "job categories analysis"
  • "skills by job type"

🎯 Examples:
  • "What are the most popular programming languages?"
  • "Show me trending AI/ML skills"
  • "What skills do data scientists need?"
  • "Compare skills across different job types"
                """)
                continue
            
            if not user_input:
                print("Please enter a question or type 'help' for assistance.")
                continue
            
            print("\n🤔 Analyzing your request...")
            
            response = chatbot.chat(user_input)
            print(f"\n🤖 Assistant:\n{response}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Thanks for using the Skills Analyzer Chatbot!")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            print("Please try again or type 'help' for assistance.")

if __name__ == "__main__":
    main()