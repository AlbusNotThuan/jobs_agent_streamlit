# -*- coding: utf-8 -*-
"""
Message Manager for Skills Analyzer Chatbot
Handles conversation history and message persistence
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


class MessageManager:
    """Manages conversation history and message persistence for the chatbot"""
    
    def __init__(self, session_id: Optional[str] = None, save_to_file: bool = True):
        """
        Initialize the message manager.

        Args:
            session_id (Optional[str]): Unique identifier for the chat session.
            save_to_file (bool): Whether to save messages to file automatically.

        Returns:
            None
        """
        self.session_id = session_id or self._generate_session_id()
        self.save_to_file = save_to_file
        self.messages: List[Dict[str, Any]] = []
        self.conversations_dir = "conversations"
        
        if self.save_to_file:
            self._ensure_conversations_dir()
    
    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID based on timestamp.

        Args:
            None

        Returns:
            str: Generated session ID string.
        """
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _ensure_conversations_dir(self) -> None:
        """
        Ensure the conversations directory exists.

        Args:
            None

        Returns:
            None
        """
        if not os.path.exists(self.conversations_dir):
            os.makedirs(self.conversations_dir)
    
    def add_message(
        self, 
        role: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the conversation history.

        Args:
            role (str): Role of the message sender ('user', 'assistant', 'system', 'tool').
            content (str): Content of the message.
            metadata (Optional[Dict[str, Any]]): Optional metadata (tool calls, thinking process, etc.).

        Returns:
            None
        """
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        
        self.messages.append(message)
        
        if self.save_to_file:
            self._save_to_file()
    
    def add_user_message(self, content: str) -> None:
        """
        Add a user message.

        Args:
            content (str): Content of the user message.

        Returns:
            None
        """
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add an assistant message.

        Args:
            content (str): Content of the assistant message.
            metadata (Optional[Dict[str, Any]]): Optional metadata for the message.

        Returns:
            None
        """
        self.add_message("assistant", content, metadata)
    
    def add_system_message(self, content: str) -> None:
        """
        Add a system message.

        Args:
            content (str): Content of the system message.

        Returns:
            None
        """
        self.add_message("system", content)
    
    def add_tool_message(self, tool_name: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a tool execution message.

        Args:
            tool_name (str): Name of the tool used.
            content (str): Content of the tool message.
            metadata (Optional[Dict[str, Any]]): Optional metadata for the tool message.

        Returns:
            None
        """
        tool_metadata = {"tool_name": tool_name}
        if metadata:
            tool_metadata.update(metadata)
        self.add_message("tool", content, tool_metadata)
    
    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation messages.

        Args:
            limit (Optional[int]): Maximum number of recent messages to return.

        Returns:
            List[Dict[str, Any]]: List of message dictionaries.
        """
        if limit:
            return self.messages[-limit:]
        return self.messages.copy()
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent conversation messages.
        
        Args:
            limit (int): Maximum number of recent messages to return.
            
        Returns:
            List[Dict[str, Any]]: List of recent message dictionaries.
        """
        return self.messages[-limit:] if self.messages else []
    
    def get_conversation_context(self, limit: int = 10) -> str:
        """
        Get formatted conversation context for the AI model.

        Args:
            limit (int): Maximum number of recent messages to include.

        Returns:
            str: Formatted conversation string.
        """
        recent_messages = self.get_messages(limit)
        context_lines = []
        for msg in recent_messages:
            role = msg["role"].title()
            content = msg["content"]
            context_lines.append(f"{role}: {content}")
        return "\n".join(context_lines)
    
    def clear_messages(self) -> None:
        """
        Clear all messages from the current session.

        Args:
            None

        Returns:
            None
        """
        self.messages.clear()
        if self.save_to_file:
            self._save_to_file()
    
    def _save_to_file(self) -> None:
        """
        Save messages to file.

        Args:
            None

        Returns:
            None
        """
        filename = f"{self.session_id}.json"
        filepath = os.path.join(self.conversations_dir, filename)
        conversation_data = {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "message_count": len(self.messages),
            "messages": self.messages
        }
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Warning: Could not save conversation to file: {e}")
    
    def load_from_file(self, session_id: str) -> bool:
        """
        Load conversation from file.

        Args:
            session_id (str): Session ID to load.

        Returns:
            bool: True if successful, False otherwise.
        """
        filename = f"{session_id}.json"
        filepath = os.path.join(self.conversations_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.session_id = data["session_id"]
                self.messages = data["messages"]
                return True
        except Exception as e:
            print(f"❌ Error loading conversation: {e}")
            return False
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all saved conversations.

        Args:
            None

        Returns:
            List[Dict[str, Any]]: List of conversation summaries.
        """
        if not os.path.exists(self.conversations_dir):
            return []
        conversations = []
        for filename in os.listdir(self.conversations_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.conversations_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        summary = {
                            "session_id": data["session_id"],
                            "created_at": data["created_at"],
                            "message_count": data["message_count"],
                            "filename": filename
                        }
                        conversations.append(summary)
                except Exception:
                    continue
        # Sort by creation date, newest first
        conversations.sort(key=lambda x: x["created_at"], reverse=True)
        return conversations
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get conversation statistics.

        Args:
            None

        Returns:
            Dict[str, Any]: Dictionary of conversation statistics.
        """
        user_messages = sum(1 for msg in self.messages if msg["role"] == "user")
        assistant_messages = sum(1 for msg in self.messages if msg["role"] == "assistant")
        tool_messages = sum(1 for msg in self.messages if msg["role"] == "tool")
        
        return {
            "session_id": self.session_id,
            "total_messages": len(self.messages),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "tool_messages": tool_messages,
            "session_duration": self._calculate_session_duration()
        }
    
    def _calculate_session_duration(self) -> str:
        """Calculate session duration"""
        if not self.messages:
            return "0 minutes"
        
        first_msg = datetime.fromisoformat(self.messages[0]["timestamp"])
        last_msg = datetime.fromisoformat(self.messages[-1]["timestamp"])
        duration = last_msg - first_msg
        
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} minutes"
