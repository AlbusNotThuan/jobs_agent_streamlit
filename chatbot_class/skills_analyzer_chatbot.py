# -*- coding: utf-8 -*-
"""
LinkedIn Jobs Skills Analyzer Chatbot
AI-powered chatbot với tích hợp các tool phân tích skills
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv
import sys
import os
# Thêm thư mục gốc vào sys.path để import tools
root_dir = os.path.abspath(os.path.dirname(__file__) + '/../')
if root_dir not in sys.path:
    sys.path.append(root_dir)
from tools.psycopg_query import query_database
from tools.recommender_job import recommend_jobs
from tools.toolbox import (
    plot_skill_trend,
    plot_job_trend,
    create_dummy_line_chart,
    get_top_job_expertises,
    get_top_skills,
)
# Local imports
from .message_manager import MessageManager

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")


class SkillsAnalyzerChatbot:
    """
    LinkedIn Jobs Skills Analyzer Chatbot Class
    
    Main chatbot class that handles AI interactions, tool integration,
    and conversation management using the ReAct framework.
    """
    
    def __init__(self, session_id: Optional[str] = None, verbose: bool = True):
        """
        Initialize the Skills Analyzer Chatbot.

        Args:
            session_id (Optional[str]): Optional session ID for conversation continuity.
            verbose (bool): Enable verbose mode to see ReAct thinking process.

        Returns:
            None
        """
        # Initialize Gemini client
        if not API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=API_KEY)
        
        # Initialize message manager
        self.message_manager = MessageManager(session_id=session_id)
        
        # Session control
        self.session_active = True
        
        # Display settings
        self.verbose_mode = verbose
        self.thought_process_enabled = True
        
        # Thinking configuration for ReAct framework
        self.thinking_budget = 4096  # Token budget for thinking process
        
        # Generation parameters (can be configured)
        self.generation_config = {
            'temperature': 0.1,
            'top_p': 0.8,
            'top_k': 40,
            'max_output_tokens': 4096,
            'response_mime_type': 'text/plain'
        }
        
        # Last messages for reference
        self.last_print_message = None
        self.last_user_message = None
        
        # Load system instruction
        self.system_instruction = self._load_system_instruction()
        
        # Initialize tools
        self._setup_tools()
    
    def _load_system_instruction(self) -> str:
        """
        Load system instruction from markdown file.

        Args:
            None

        Returns:
            str: System instruction string.
        """
        system_instruction_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "system_instruction.md"
        )
        
        try:
            with open(system_instruction_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ Could not read system_instruction.md: {e}")
            return "You are a LinkedIn Jobs Skills Analyzer AI Assistant."
    
    def _setup_tools(self) -> None:
        """
        Setup available tools for the chatbot.

        Args:
            None

        Returns:
            None
        """
        # Import tools locally to avoid circular imports
        try:

            
            # Setup core tools for analysis
            self.available_tools = [
                query_database,
                plot_skill_trend,
                plot_job_trend,
                create_dummy_line_chart,
                get_top_job_expertises,
                get_top_skills
            ]
            
            # Create tool function mapping for manual execution
            self.tool_functions = {
                'query_database': query_database,
                'plot_skill_trend': plot_skill_trend,
                'plot_job_trend': plot_job_trend,
                'create_dummy_line_chart': create_dummy_line_chart,
                'get_top_job_expertises': get_top_job_expertises,
                'get_top_skills': get_top_skills
            }
            
            # Optional: Add code execution tool if needed
            self.code_execution_tool = types.Tool(
                code_execution=types.ToolCodeExecution()
            )
            # Uncomment the line below to include code execution tool
            # self.available_tools.append(self.code_execution_tool)
            
        except ImportError as e:
            print(f"⚠️ Warning: Could not import some tools: {e}")
            # Setup basic tools only - empty list, AI will respond directly
            self.available_tools = []
            self.tool_functions = {}
    
    # =============================================================================
    # PUBLIC INTERFACE METHODS
    # =============================================================================
    
    def new_chat(self, session_id: Optional[str] = None) -> str:
        """
        Start a new chat session.

        Args:
            session_id (Optional[str]): Optional custom session ID.

        Returns:
            str: New session ID.
        """
        # Save current session stats if exists
        if self.message_manager.messages:
            stats = self.message_manager.get_stats()
            print(f"📊 Previous session stats: {stats['total_messages']} messages, {stats['session_duration']}")
        
        # Create new message manager
        self.message_manager = MessageManager(session_id=session_id)
        
        # Reset session state
        self.session_active = True
        self.last_print_message = None
        self.last_user_message = None
        
        new_session_id = self.message_manager.session_id
        print(f"🆕 Started new chat session: {new_session_id}")
        
        return new_session_id
    
    def chat(self, user_message: str) -> Dict[str, Any]:
        """
        Main chat function with ReAct framework using Gemini thinking capabilities.
        Uses a while loop to handle tool calling iteratively.

        Args:
            user_message (str): User's input message.

        Returns:
            Dict[str, Any]: Process sequence containing thoughts, tool calls, results, and final response.
        """
        if not self.session_active:
            return {
                "error": "❌ Session has ended. Please start a new chat session.",
                "process_sequence": [],
                "final_response": "",
                "success": False
            }
        
        # Store user message
        self.last_user_message = user_message
        self.message_manager.add_user_message(user_message)
        
        # Initialize process sequence tracking
        process_sequence = []
        
        try:
            # Prepare conversation history
            conversation_history = self._create_autonomous_prompt(user_message)
            
            # Configure generation with thinking and tools
            config = types.GenerateContentConfig(
                # System and tools
                system_instruction=self.system_instruction,
                tools=self.available_tools,
                tool_config={'function_calling_config': {'mode': 'AUTO'}},
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
                # Thinking configuration for ReAct framework
                thinking_config=types.ThinkingConfig(
                    thinking_budget=self.thinking_budget,
                    include_thoughts=True
                ),
                
                # Generation parameters
                temperature=self.generation_config['temperature'],
                top_p=self.generation_config['top_p'],
                top_k=self.generation_config['top_k'],
                max_output_tokens=self.generation_config['max_output_tokens'],
                response_mime_type=self.generation_config['response_mime_type'],
                
                # Safety settings for better tool usage
                safety_settings=[
                    types.SafetySetting(
                        category='HARM_CATEGORY_DANGEROUS_CONTENT',
                        threshold='BLOCK_NONE'
                    )
                ] if hasattr(types, 'SafetySetting') else None
            )
            
            if self.verbose_mode:
                print(f"🧠 Generating response with thinking budget: {self.thinking_budget} tokens...")
            
            # Main loop to handle tool calling
            while True:
                # Generate response with thinking
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=conversation_history,
                    config=config
                )
                
                candidate = response.candidates[0]
                
                # Process and display response parts for thinking/text
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'thought') and part.thought:
                            thought_content = part.text if hasattr(part, 'text') else str(part.thought)
                            thought_signature = getattr(part, 'thought_signature', None)
                            
                            thought_step = {
                                "type": "thought",
                                "content": thought_content,
                                "thought_signature": thought_signature,
                                "timestamp": datetime.now().isoformat()
                            }
                            process_sequence.append(thought_step)
                            
                            if self.verbose_mode:
                                print(f"🧠 **THOUGHT:** {thought_content}")
                                if thought_signature:
                                    print(f"   Signature: {thought_signature}")
                                    
                        elif hasattr(part, 'text') and part.text and not hasattr(part, 'function_call'):
                            response_step = {
                                "type": "response",
                                "content": part.text,
                                "timestamp": datetime.now().isoformat()
                            }
                            process_sequence.append(response_step)
                            
                            if self.verbose_mode:
                                print(f"💬 **RESPONSE:** {part.text}")
                
                # Check if there's a function call
                has_function_call = False
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_call = True
                        function_call = part.function_call
                        tool_name = function_call.name
                        tool_args = dict(function_call.args) if function_call.args else {}
                        
                        # Record tool call step
                        tool_call_step = {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "timestamp": datetime.now().isoformat()
                        }
                        process_sequence.append(tool_call_step)
                        if self.verbose_mode:
                            print(f"🛠️  MODEL YÊU CẦU GỌI TOOL: {tool_name}")
                            print(f"Tham số: {tool_args}")
                        
                        # Add model's function call to conversation history
                        conversation_history.append(candidate.content)
                        
                        # Execute the tool function
                        tool_to_run = self.tool_functions.get(tool_name)
                        if tool_to_run:
                            try:
                                tool_result = tool_to_run(**tool_args)
                                
                                # Record tool result step
                                tool_result_step = {
                                    "type": "tool_result",
                                    "tool_name": tool_name,
                                    "result": str(tool_result),
                                    "success": True,
                                    "timestamp": datetime.now().isoformat()
                                }
                                process_sequence.append(tool_result_step)
                                if self.verbose_mode:
                                    print(f"📊 **Tool result:** {tool_result}")
                                
                                # Add tool result to conversation history
                                conversation_history.append(
                                    types.Content(
                                        role="model",
                                        parts=[
                                            types.Part(
                                                function_response=types.FunctionResponse(
                                                    name=tool_name,
                                                    response={'result': str(tool_result)}
                                                )
                                            )
                                        ]
                                    )
                                )
                            except Exception as e:
                                tool_result = f"Lỗi khi thực thi tool {tool_name}: {str(e)}"
                                
                                # Record tool error step
                                tool_error_step = {
                                    "type": "tool_result",
                                    "tool_name": tool_name,
                                    "result": tool_result,
                                    "success": False,
                                    "error": str(e),
                                    "timestamp": datetime.now().isoformat()
                                }
                                process_sequence.append(tool_error_step)
                                
                                print(f"❌ Tool error: {tool_result}")
                        else:
                            tool_result = f"Lỗi: không tìm thấy tool {tool_name}"
                            
                            # Record tool not found step
                            tool_error_step = {
                                "type": "tool_result",
                                "tool_name": tool_name,
                                "result": tool_result,
                                "success": False,
                                "error": "Tool not found",
                                "timestamp": datetime.now().isoformat()
                            }
                            process_sequence.append(tool_error_step)
                            
                            print(f"❌ {tool_result}")
                        
                        # Send tool result back to model
                        conversation_history.append(
                            types.Content(
                                role="model",
                                parts=[
                                    types.Part(
                                        function_response=types.FunctionResponse(
                                            name=tool_name,
                                            response={'result': str(tool_result)}
                                        )
                                    )
                                ]
                            )
                        )
                        break  # Only handle one function call per iteration
                
                # If no function call, return the final answer and exit
                if not has_function_call:
                    if self.verbose_mode:
                        print("🧠 **FINAL RESPONSE:**")
                        print(response.text)
                    final_response = response.text
                    if not final_response:
                        # Extract text from parts if candidate.text is empty
                        text_parts = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_parts.append(part.text)
                        final_response = "\n\n".join(text_parts)
                    
                    # Record final response step
                    final_step = {
                        "type": "final_response",
                        "content": final_response,
                        "timestamp": datetime.now().isoformat()
                    }
                    process_sequence.append(final_step)
                    
                    # Store assistant response
                    self.message_manager.add_assistant_message(
                        final_response,
                        metadata={
                            "model": "gemini-2.5-flash", 
                            "thinking_enabled": True,
                            "thinking_budget": self.thinking_budget,
                            "process_sequence": process_sequence
                        }
                    )
                    
                    return {
                        "process_sequence": process_sequence,
                        "final_response": final_response if final_response else "🤖 No response generated",
                        "success": True,
                        "total_steps": len(process_sequence),
                        "thinking_budget": self.thinking_budget
                    }
            
        except Exception as e:
            error_msg = f"❌ ReAct agent error: {str(e)}"
            print(error_msg)
            self.message_manager.add_system_message(f"Error: {str(e)}")
            
            error_step = {
                "type": "error",
                "content": error_msg,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            process_sequence.append(error_step)
            
            return {
                "process_sequence": process_sequence,
                "final_response": error_msg,
                "success": False,
                "error": str(e),
                "total_steps": len(process_sequence)
            }
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history.

        Args:
            limit (Optional[int]): Maximum number of recent messages to return.

        Returns:
            List[Dict[str, Any]]: List of message dictionaries.
        """
        return self.message_manager.get_messages(limit)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get current session statistics.

        Args:
            None

        Returns:
            Dict[str, Any]: Dictionary of session statistics.
        """
        return self.message_manager.get_stats()
    
    def save_conversation(self) -> bool:
        """
        Force save current conversation to file.

        Args:
            None

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            self.message_manager._save_to_file()
            return True
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            return False
    
    def load_conversation(self, session_id: str) -> bool:
        """
        Load a previous conversation.

        Args:
            session_id (str): Session ID to load.

        Returns:
            bool: True if successful, False otherwise.
        """
        success = self.message_manager.load_from_file(session_id)
        if success:
            self.session_active = True
            print(f"✅ Loaded conversation: {session_id}")
        return success
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all saved conversations.

        Args:
            None

        Returns:
            List[Dict[str, Any]]: List of conversation summaries.
        """
        return self.message_manager.list_conversations()
    
    # =============================================================================
    # CONFIGURATION METHODS
    # =============================================================================
    
    def set_thinking_budget(self, budget: int) -> None:
        """
        Set the thinking budget for ReAct framework.

        Args:
            budget (int): Token budget for thinking process (0-24576).

        Returns:
            None
        """
        if 0 <= budget <= 24576:
            self.thinking_budget = budget
            print(f"🧠 Thinking budget set to: {budget} tokens")
        else:
            print("❌ Thinking budget must be between 0 and 24576 tokens")
    
    def get_thinking_budget(self) -> int:
        """
        Get current thinking budget.

        Returns:
            int: Current thinking budget in tokens.
        """
        return self.thinking_budget
    
    def set_verbose_mode(self, verbose: bool = True) -> None:
        """
        Enable/disable verbose mode to see ReAct thinking process.

        Args:
            verbose (bool): True to enable verbose output, False to disable.

        Returns:
            None
        """
        self.verbose_mode = verbose
        if verbose:
            print("🔊 Verbose mode enabled - You'll see the agent's thinking process")
        else:
            print("🔇 Verbose mode disabled - Only final responses will be shown")
    
    def set_thought_process(self, enabled: bool = True) -> None:
        """
        Enable/disable thought process display.

        Args:
            enabled (bool): True to show thought process, False to hide.

        Returns:
            None
        """
        self.thought_process_enabled = enabled
        if enabled:
            print("🧠 Thought process display enabled")
        else:
            print("🤫 Thought process display disabled")
    
    def configure_generation(
        self,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        response_mime_type: Optional[str] = None
    ) -> None:
        """
        Configure generation parameters for the AI model.

        Args:
            temperature (Optional[float]): Controls randomness (0.0-1.0). Lower = more focused.
            top_p (Optional[float]): Nucleus sampling threshold (0.0-1.0).
            top_k (Optional[int]): Top-k sampling limit.
            max_output_tokens (Optional[int]): Maximum tokens in response.
            response_mime_type (Optional[str]): MIME type for response format.

        Returns:
            None
        """
        if temperature is not None:
            self.generation_config['temperature'] = temperature
        if top_p is not None:
            self.generation_config['top_p'] = top_p
        if top_k is not None:
            self.generation_config['top_k'] = top_k
        if max_output_tokens is not None:
            self.generation_config['max_output_tokens'] = max_output_tokens
        if response_mime_type is not None:
            self.generation_config['response_mime_type'] = response_mime_type
        
        print(f"🔧 Generation config updated: {self.generation_config}")
    
    def get_generation_config(self) -> Dict[str, Any]:
        """
        Get current generation configuration.

        Args:
            None

        Returns:
            Dict[str, Any]: Current generation configuration.
        """
        return self.generation_config.copy()
    
    def set_generation_preset(self, preset: str) -> None:
        """
        Set generation parameters using predefined presets optimized for thinking and tool usage.

        Args:
            preset (str): Preset name ('creative', 'balanced', 'focused', 'analytical').

        Returns:
            None
        """
        presets = {
            'creative': {
                'temperature': 0.4,
                'top_p': 0.9,
                'top_k': 50,
                'max_output_tokens': 8192,
                'response_mime_type': 'text/plain',
                'thinking_budget': 3072
            },
            'balanced': {
                'temperature': 0.2,
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 8192,
                'response_mime_type': 'text/plain',
                'thinking_budget': 4096
            },
            'focused': {
                'temperature': 0.1,
                'top_p': 0.7,
                'top_k': 20,
                'max_output_tokens': 8192,
                'response_mime_type': 'text/plain',
                'thinking_budget': 6144
            },
            'analytical': {
                'temperature': 0.05,
                'top_p': 0.6,
                'top_k': 10,
                'max_output_tokens': 8192,
                'response_mime_type': 'text/plain',
                'thinking_budget': 8192
            }
        }
        
        if preset.lower() in presets:
            preset_config = presets[preset.lower()]
            # Update generation config
            for key, value in preset_config.items():
                if key == 'thinking_budget':
                    self.thinking_budget = value
                else:
                    self.generation_config[key] = value
            print(f"🎯 Applied '{preset}' preset:")
            print(f"  Generation: {self.generation_config}")
            print(f"  Thinking budget: {self.thinking_budget} tokens")
        else:
            available = ', '.join(presets.keys())
            print(f"❌ Unknown preset '{preset}'. Available: {available}")
    
    def list_generation_presets(self) -> None:
        """
        List available generation presets with descriptions.

        Args:
            None

        Returns:
            None
        """
        presets_info = {
            'creative': 'High creativity, diverse responses, good for brainstorming',
            'balanced': 'Balanced creativity and focus, good for general use',
            'focused': 'Low randomness, consistent responses, good for analysis',
            'analytical': 'Minimal randomness, precise responses, best for technical analysis'
        }
        
        print("🎯 Available Generation Presets:")
        for preset, description in presets_info.items():
            print(f"  • {preset}: {description}")
    
    def enable_code_execution(self, enable: bool = True) -> None:
        """
        Enable or disable code execution tool.

        Args:
            enable (bool): True to enable code execution, False to disable.

        Returns:
            None
        """
        if not hasattr(self, 'code_execution_tool'):
            self.code_execution_tool = types.Tool(
                code_execution=types.ToolCodeExecution()
            )
        
        if enable:
            if self.code_execution_tool not in self.available_tools:
                self.available_tools.append(self.code_execution_tool)
                print("🐍 Code execution tool enabled")
            else:
                print("🐍 Code execution tool is already enabled")
        else:
            if self.code_execution_tool in self.available_tools:
                self.available_tools.remove(self.code_execution_tool)
                print("🚫 Code execution tool disabled")
            else:
                print("🚫 Code execution tool is already disabled")
    
    def is_code_execution_enabled(self) -> bool:
        """
        Check if code execution tool is enabled.

        Returns:
            bool: True if enabled, False otherwise.
        """
        return hasattr(self, 'code_execution_tool') and self.code_execution_tool in self.available_tools
    
    # =============================================================================
    # PRIVATE HELPER METHODS  
    # =============================================================================
    
    
    def _create_autonomous_prompt(self, user_message: str) -> list:
        """
        Create autonomous prompt as a list of types.Content for Gemini SDK (function calling/multi-turn).

        Args:
            user_message (str): User's input message.

        Returns:
            list: List of types.Content objects for Gemini SDK.
        """
        messages = self.message_manager.get_messages()
        # Đảm bảo message cuối cùng là user_message hiện tại
        if not messages or messages[-1]["role"] != "user" or messages[-1]["content"] != user_message:
            messages = messages + [{"role": "user", "content": user_message, "timestamp": datetime.now().isoformat(), "metadata": {}}]
        # Chuyển thành list types.Content (role, parts=[str])
        content_list = []
        for m in messages:
            # role: "user", "model" (Gemini API yêu cầu "model" thay vì "assistant")
            if m["role"] == "assistant":
                role = "model"
            elif m["role"] == "user":
                role = "user"
            else:
                role = "user"  # Default fallback
            content_list.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))
        return content_list
    
    def __str__(self) -> str:
        """
        String representation of the chatbot.

        Args:
            None

        Returns:
            str: String representation.
        """
        stats = self.get_session_stats()
        return f"SkillsAnalyzerChatbot(session={stats['session_id']}, messages={stats['total_messages']}, active={self.session_active})"
    
    def __repr__(self) -> str:
        """
        Detailed representation of the chatbot.

        Args:
            None

        Returns:
            str: String representation.
        """
        return self.__str__()
