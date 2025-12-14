"""
Custom exceptions for the desktop agent.
"""
from __future__ import annotations


class AgentError(Exception):
    """Base exception for all agent errors."""
    pass


class ModelError(AgentError):
    """Error communicating with the VLM."""
    pass


class ExecutionError(AgentError):
    """Error executing an action."""
    pass
