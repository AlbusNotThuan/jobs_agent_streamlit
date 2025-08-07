# -*- coding: utf-8 -*-
"""
Test Career Advisor Mode with Conversation History
"""

import sys
import os
from dotenv import load_dotenv

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from chatbot_class.skills_analyzer_chatbot import SkillsAnalyzerChatbot

def test_career_advisor_mode():
    """Test career advisor mode with conversation history"""
    
    print("🧪 Testing Career Advisor Mode with Conversation History")
    print("=" * 60)
    
    # Initialize chatbot
    try:
        chatbot = SkillsAnalyzerChatbot(verbose=True)
        print("✅ Chatbot initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize chatbot: {e}")
        return
    
    # Test 1: Check career advisor availability
    print(f"\n🔍 Career advisor available: {chatbot.career_advisor_available}")
    
    # Test 2: Switch to career advisor mode
    print("\n🎯 Switching to career advisor mode...")
    success = chatbot.toggle_career_advisor_mode(True)
    print(f"Mode switched: {success}")
    print(f"Current mode: {chatbot.get_current_mode()}")
    
    # Test 3: Have a conversation to build history
    print("\n💬 Building conversation history...")
    
    # First message - user background
    response1 = chatbot.chat("Xin chào, tôi là một sinh viên năm cuối ngành Khoa học máy tính.")
    print(f"Response 1 success: {response1.get('success', False)}")
    
    # Second message - user interest
    response2 = chatbot.chat("Tôi đang quan tâm đến lĩnh vực AI và Machine Learning.")
    print(f"Response 2 success: {response2.get('success', False)}")
    
    # Third message - career question (should trigger career advisor with full history)
    print("\n🎯 Testing career advisor with full context...")
    response3 = chatbot.chat("Tôi muốn xin lời khuyên về career path trong AI/ML. Bạn có thể tư vấn cho tôi không?")
    print(f"Response 3 success: {response3.get('success', False)}")
    
    # Print conversation history
    print("\n📋 Conversation History:")
    history = chatbot.get_conversation_history()
    for i, msg in enumerate(history):
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')[:100] + "..." if len(msg.get('content', '')) > 100 else msg.get('content', '')
        print(f"  {i+1}. [{role}] {content}")
    
    # Check process sequence of last response
    if 'process_sequence' in response3:
        print(f"\n🔄 Process sequence length: {len(response3['process_sequence'])}")
        for step in response3['process_sequence']:
            step_type = step.get('type', 'unknown')
            if step_type == 'tool_call':
                tool_name = step.get('tool_name', 'unknown')
                tool_args = step.get('tool_args', {})
                print(f"  Tool called: {tool_name}")
                if tool_name == 'get_career_advice':
                    # Check if task parameter contains conversation history
                    if 'task' in tool_args and isinstance(tool_args['task'], dict):
                        task = tool_args['task']
                        messages = task.get('message', [])
                        print(f"    Conversation history provided: {len(messages)} messages")
                        print(f"    Session ID: {task.get('sessionId', 'None')}")
                    else:
                        print(f"    ❌ No proper task format provided to get_career_advice")
                else:
                    print(f"    Other tool args: {tool_args}")
    
    print("\n✅ Test completed")

if __name__ == "__main__":
    load_dotenv()
    test_career_advisor_mode()
