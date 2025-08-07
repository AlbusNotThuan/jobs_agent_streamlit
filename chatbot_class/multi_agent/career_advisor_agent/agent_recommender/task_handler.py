# -*- coding: utf-8 -*-
"""
Task Handler for Agent Recommender
Handles input/output task format for integration with other agents
"""

from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import json
import os


class TaskHandler:
    """
    Handles task input/output format for agent integration
    
    Input Task Format:
    {
        "sessionId": str | None,  # Optional session ID for conversation continuity
        "message": List[Dict],    # List of message dicts with role/content
                                  # Supported roles: 'user', 'assistant', 'system', 'tool', 'model'
        "metadata": Dict          # Additional options like images (base64), urls, etc.
    }
    
    Output Task Format:
    {
        "start_time": str,        # ISO format timestamp
        "end_time": str,          # ISO format timestamp  
        "sessionId": str,         # Session ID (existing or newly created)
        "state": str,             # "completed", "failed", "input-required"
        "process_sequence": List, # List of processing steps
        "final_response": str,    # Final response or error/requirement message
        "metadata": Dict          # Additional options
    }
    """
    
    def __init__(self, conversations_dir: str = "conversations"):
        """
        Initialize task handler.
        
        Args:
            conversations_dir: Directory to store conversation sessions
        """
        self.conversations_dir = conversations_dir
        self._ensure_conversations_dir()
    
    def _ensure_conversations_dir(self) -> None:
        """Ensure the conversations directory exists."""
        if not os.path.exists(self.conversations_dir):
            os.makedirs(self.conversations_dir)
    
    def validate_input_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate input task format and return validation result.
        
        Args:
            task: Input task dictionary
            
        Returns:
            Dict with 'valid' boolean and 'errors' list
        """
        errors = []
        
        # Check required fields
        if 'message' not in task:
            errors.append("Required field 'message' is missing")
        elif not isinstance(task['message'], list):
            errors.append("Field 'message' must be a list")
        else:
            # Validate message format
            for i, msg in enumerate(task['message']):
                if not isinstance(msg, dict):
                    errors.append(f"Message {i} must be a dictionary")
                    continue
                if 'role' not in msg:
                    errors.append(f"Message {i} missing 'role' field")
                if 'content' not in msg:
                    errors.append(f"Message {i} missing 'content' field")
                if msg.get('role') not in ['user', 'assistant', 'system', 'tool', 'model']:
                    errors.append(f"Message {i} has invalid role: {msg.get('role')}")
        
        # Validate optional fields
        if 'sessionId' in task and task['sessionId'] is not None:
            if not isinstance(task['sessionId'], str):
                errors.append("Field 'sessionId' must be a string or null")
        
        if 'metadata' in task and not isinstance(task['metadata'], dict):
            errors.append("Field 'metadata' must be a dictionary")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def check_session_exists(self, session_id: str) -> bool:
        """
        Check if a session ID exists in the conversations directory.
        
        Args:
            session_id: Session ID to check
            
        Returns:
            Boolean indicating if session exists
        """
        if not session_id:
            return False
        
        filename = f"{session_id}.json"
        filepath = os.path.join(self.conversations_dir, filename)
        return os.path.exists(filepath)
    
    def create_output_task(
        self,
        start_time: datetime,
        end_time: datetime,
        session_id: str,
        state: str,
        process_sequence: List[Dict[str, Any]],
        final_response: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create standardized output task.
        
        Args:
            start_time: Task start time
            end_time: Task end time  
            session_id: Session identifier
            state: Task state (completed/failed/input-required)
            process_sequence: List of processing steps
            final_response: Final response text
            metadata: Optional additional metadata
            error: Optional error message
            
        Returns:
            Formatted output task dictionary
        """
        output_task = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "sessionId": session_id,
            "state": state,
            "process_sequence": process_sequence,
            "final_response": final_response,
            "metadata": metadata or {}
        }
        
        # Add error info if provided
        if error:
            output_task["metadata"]["error"] = error
        
        # Add execution time
        execution_time = (end_time - start_time).total_seconds()
        output_task["metadata"]["execution_time_seconds"] = execution_time
        
        return output_task
    
    def create_failed_task(
        self,
        start_time: datetime,
        reason: str,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a failed task response.
        
        Args:
            start_time: Task start time
            reason: Failure reason
            session_id: Optional session ID
            metadata: Optional metadata
            
        Returns:
            Failed task dictionary
        """
        end_time = datetime.now()
        return self.create_output_task(
            start_time=start_time,
            end_time=end_time,
            session_id=session_id or "failed_session",
            state="failed",
            process_sequence=[{
                "type": "error",
                "content": reason,
                "timestamp": end_time.isoformat()
            }],
            final_response=f"Task failed: {reason}",
            metadata=metadata,
            error=reason
        )
    
    def extract_user_query(self, messages: List[Dict[str, Any]]) -> str:
        """
        Extract the main user query from message list.
        Prioritizes the last user message.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            User query string
        """
        # Find the last user message
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                return msg.get('content', '')
        
        # If no user message found, join all content
        return ' '.join([msg.get('content', '') for msg in messages if msg.get('content')])
    
    def format_conversation_history(self, messages: List[Dict[str, Any]]) -> str:
        """
        Format message history for context.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Formatted conversation string
        """
        formatted_lines = []
        for msg in messages:
            role = msg.get('role', 'unknown').title()
            content = msg.get('content', '')
            formatted_lines.append(f"{role}: {content}")
        
        return '\n'.join(formatted_lines)
