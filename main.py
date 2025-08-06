# -*- coding: utf-8 -*-
"""
LinkedIn Jobs Skills Analyzer - Main Application
Enhanced version with redesigned class structure and conversation management
"""

import os
import sys
from typing import Optional, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chatbot_class import SkillsAnalyzerChatbot


def display_welcome() -> None:
    """Display welcome message and instructions"""
    print("🤖 LinkedIn Jobs Skills Analyzer - AUTONOMOUS AI AGENT")
    print("=" * 70)
    print("🚀 AUTONOMOUS MODE: The agent will act independently without confirmations")
    print("🧠 THOUGHT PROCESS: The agent will show its ReAct framework thinking")
    print("📊 VISUALIZATION: The agent can now create skill demand plots!")
    print("💾 PERSISTENCE: Conversations are automatically saved and can be resumed")
    print("💡 Ask me anything about job market skills and trends!")
    print()
    print("📋 EXAMPLE QUERIES:")
    print("• 'What are the most in-demand skills?'")
    print("• 'Show me hot AI/ML skills'") 
    print("• 'Plot Python vs JavaScript demand'")
    print("• 'Visualize React skills over the last 6 months'")
    print("• 'Compare programming languages popularity'")
    print("• 'Analyze data science job requirements'")
    print()
    print("🔍 THOUGHT PROCESS INDICATORS:")
    print("   🧠 THOUGHT: Agent's reasoning and planning")
    print("   🛠️ TOOL CALL: Tools being used and parameters")
    print("   � TOOL RESULT: Results from tool execution")
    print("   💬 RESPONSE: Intermediate responses")
    print("   🧠 FINAL RESPONSE: Final answer after all processing")
    print()
    print("⚙️ SPECIAL COMMANDS:")
    print("• 'help' - Show this help message")
    print("• 'new' - Start a new conversation")
    print("• 'stats' - Show current session statistics")
    print("• 'history' - Show conversation history")
    print("• 'list' - List all saved conversations")
    print("• 'load <session_id>' - Load a previous conversation")
    print("• 'verbose on/off' - Toggle verbose mode")
    print("• 'thoughts on/off' - Toggle thought process display")
    print("• 'process' - Show detailed process sequence of last response")
    print("• 'preset <name>' - Set generation preset (creative/balanced/focused/analytical)")
    print("• 'presets' - List available generation presets")
    print("• 'config' - Show current generation configuration")
    print("• 'save' - Force save current conversation")
    print("• 'exit' - Exit the application")
    print("=" * 70)


def handle_special_commands(chatbot: SkillsAnalyzerChatbot, command: str, last_chat_result: Optional[Dict[str, Any]] = None) -> bool:
    """
    Handle special commands that don't require AI processing
    
    Args:
        chatbot: The chatbot instance
        command: User command
        
    Returns:
        True if command was handled, False otherwise
    """
    command = command.lower().strip()
    
    if command == 'help':
        display_welcome()
        return True
    
    elif command == 'new':
        session_id = chatbot.new_chat()
        print(f"🆕 Started new conversation: {session_id}")
        return True
    
    elif command == 'stats':
        stats = chatbot.get_session_stats()
        print("📊 Current Session Statistics:")
        print(f"   Session ID: {stats['session_id']}")
        print(f"   Total Messages: {stats['total_messages']}")
        print(f"   User Messages: {stats['user_messages']}")
        print(f"   Assistant Messages: {stats['assistant_messages']}")
        print(f"   Tool Messages: {stats['tool_messages']}")
        print(f"   Session Duration: {stats['session_duration']}")
        return True
    
    elif command == 'history':
        history = chatbot.get_conversation_history()
        if not history:
            print("📝 No conversation history yet.")
        else:
            print(f"📝 Conversation History ({len(history)} messages):")
            for i, msg in enumerate(history[-10:], 1):  # Show last 10 messages
                role = msg['role'].title()
                content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                timestamp = msg['timestamp'][:19]  # Remove microseconds
                print(f"   {i}. [{timestamp}] {role}: {content}")
        return True
    
    elif command == 'list':
        conversations = chatbot.list_conversations()
        if not conversations:
            print("📚 No saved conversations found.")
        else:
            print(f"📚 Saved Conversations ({len(conversations)}):")
            for i, conv in enumerate(conversations[:10], 1):  # Show last 10
                print(f"   {i}. {conv['session_id']} - {conv['message_count']} messages - {conv['created_at'][:19]}")
        return True
    
    elif command.startswith('load '):
        session_id = command[5:].strip()
        if chatbot.load_conversation(session_id):
            print(f"✅ Loaded conversation: {session_id}")
            stats = chatbot.get_session_stats()
            print(f"📊 Loaded {stats['total_messages']} messages")
        else:
            print(f"❌ Could not load conversation: {session_id}")
        return True
    
    elif command == 'verbose on':
        chatbot.set_verbose_mode(True)
        return True
    
    elif command == 'verbose off':
        chatbot.set_verbose_mode(False)
        return True
    
    elif command == 'thoughts on':
        chatbot.set_thought_process(True)
        return True
    
    elif command == 'thoughts off':
        chatbot.set_thought_process(False)
        return True
    
    elif command == 'process':
        if last_chat_result and "process_sequence" in last_chat_result:
            print("🔍 **DETAILED PROCESS SEQUENCE:**")
            print(f"Total steps: {last_chat_result.get('total_steps', 0)}")
            print(f"Success: {last_chat_result.get('success', False)}")
            print("-" * 60)
            
            for i, step in enumerate(last_chat_result["process_sequence"], 1):
                step_type = step.get("type", "unknown")
                timestamp = step.get("timestamp", "")
                
                if step_type == "thought":
                    print(f"{i}. 🧠 THOUGHT ({timestamp}):")
                    print(f"   Content: {step.get('content', '')}")
                    if step.get('thought_signature'):
                        print(f"   Signature: {step.get('thought_signature')}")
                        
                elif step_type == "tool_call":
                    print(f"{i}. 🛠️ TOOL CALL ({timestamp}):")
                    print(f"   Tool: {step.get('tool_name', '')}")
                    print(f"   Args: {step.get('tool_args', {})}")
                    
                elif step_type == "tool_result":
                    print(f"{i}. 📊 TOOL RESULT ({timestamp}):")
                    print(f"   Tool: {step.get('tool_name', '')}")
                    print(f"   Success: {step.get('success', False)}")
                    result = step.get('result', '')
                    if len(str(result)) > 200:
                        print(f"   Result: {str(result)[:200]}...")
                    else:
                        print(f"   Result: {result}")
                    if not step.get('success', True):
                        print(f"   Error: {step.get('error', '')}")
                        
                elif step_type == "response":
                    print(f"{i}. 💬 RESPONSE ({timestamp}):")
                    content = step.get('content', '')
                    if len(content) > 200:
                        print(f"   Content: {content[:200]}...")
                    else:
                        print(f"   Content: {content}")
                        
                elif step_type == "final_response":
                    print(f"{i}. 🧠 FINAL RESPONSE ({timestamp}):")
                    content = step.get('content', '')
                    if len(content) > 200:
                        print(f"   Content: {content[:200]}...")
                    else:
                        print(f"   Content: {content}")
                        
                elif step_type == "error":
                    print(f"{i}. ❌ ERROR ({timestamp}):")
                    print(f"   Content: {step.get('content', '')}")
                    print(f"   Error: {step.get('error', '')}")
                    
                print()
        else:
            print("❌ No process sequence available. Please run a chat command first.")
        return True
    
    elif command.startswith('preset '):
        preset_name = command[7:].strip()
        chatbot.set_generation_preset(preset_name)
        return True
    
    elif command == 'presets':
        chatbot.list_generation_presets()
        return True
    
    elif command == 'config':
        config = chatbot.get_generation_config()
        print("⚙️ Current Generation Configuration:")
        for key, value in config.items():
            print(f"   {key}: {value}")
        return True
    
    elif command == 'save':
        if chatbot.save_conversation():
            print("💾 Conversation saved successfully!")
        else:
            print("❌ Failed to save conversation.")
        return True
    
    elif command in ['exit', 'quit', 'bye']:
        return 'exit'
    
    return False


def main():
    """Main application loop"""
    try:
        # Display welcome message
        display_welcome()
        
        # Initialize chatbot
        print("🔧 Initializing chatbot...")
        chatbot = SkillsAnalyzerChatbot(verbose=True)
        print(f"✅ Chatbot initialized! Session: {chatbot.message_manager.session_id}")
        print("\n💭 Ready for your questions! Type 'help' for commands or start asking about job skills.")
        
        # Track last chat result for process command
        last_chat_result = None
        
        # Main interaction loop
        while True:
            try:
                # Get user input
                user_input = input("\n👤 You: ").strip()
                if not user_input:
                    continue
                # Handle special commands
                command_result = handle_special_commands(chatbot, user_input, last_chat_result)
                if command_result == 'exit':
                    # Final session stats
                    stats = chatbot.get_session_stats()
                    print(f"\n📊 Final session stats: {stats['total_messages']} messages, {stats['session_duration']}")
                    print("👋 Thank you for using Skills Analyzer! Goodbye!")
                    break
                elif command_result:
                    continue  # Command was handled, continue to next input
                # Check if session is active
                if not chatbot.session_active:
                    print("⚠️ Session has ended. Starting a new session...")
                    chatbot.new_chat()
                # Process user message with AI
                print("\n🤖 Assistant:")
                chat_result = chatbot.chat(user_input)
                last_chat_result = chat_result  # Store for process command
                
                # Handle the structured response
                if chat_result["success"]:
                    # Display process summary if verbose mode is off and there were multiple steps
                    if not chatbot.verbose_mode and chat_result["total_steps"] > 1:
                        print(f"📝 Process completed in {chat_result['total_steps']} steps")
                        
                        # Show brief summary of steps
                        thoughts = sum(1 for step in chat_result["process_sequence"] if step["type"] == "thought")
                        tool_calls = sum(1 for step in chat_result["process_sequence"] if step["type"] == "tool_call")
                        
                        if thoughts > 0:
                            print(f"   🧠 Thoughts: {thoughts}")
                        if tool_calls > 0:
                            print(f"   🛠️ Tool calls: {tool_calls}")
                    
                    # The final response is already printed by the chatbot in verbose mode
                    # In non-verbose mode, we should print it here
                    if not chatbot.verbose_mode and chat_result["final_response"]:
                        print(f"\n💬 **Final Response:**")
                        print(chat_result["final_response"])
                        
                else:
                    # Handle error case
                    if "error" in chat_result:
                        print(f"❌ Error: {chat_result['error']}")
                    else:
                        print(f"❌ Failed to process request: {chat_result.get('final_response', 'Unknown error')}")
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupted by user. Saving conversation...")
                chatbot.save_conversation()
                stats = chatbot.get_session_stats()
                print(f"📊 Session stats: {stats['total_messages']} messages, {stats['session_duration']}")
                print("👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error during conversation: {e}")
                print("🔄 Continuing conversation...")
                continue
    
    except Exception as e:
        print(f"❌ Critical error: {e}")
        print("Please check your configuration and try again.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
