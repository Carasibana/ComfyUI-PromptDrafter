"""
Wildcard Node for ComfyUI-PromptDrafter
Node for creating and managing wildcard value lists.
"""

import random

from ..utils.file_manager import FileManager
from ..utils.wildcard_parser import WildcardParser


class WildcardNode:
    """
    A node for creating wildcard value lists.
    
    Features:
    - Text field with purple outline for entering wildcard values
    - Supports newline, comma, and pipe delimiters
    - Bracket grouping: (a, b) or {a|b} treated as single entries
    - Output modes: Sequential, Random, Fixed, Dynamic Prompts
    - Save/Load functionality for wildcard lists
    """
    
    CATEGORY = "PromptDrafter"
    DISPLAY_NAME = "Wildcards - PromptDrafter"
    FUNCTION = "process"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("wildcard_value",)
    OUTPUT_NODE = False
    
    # Output mode options
    # "Dynamic Prompts" is the standard name for the {opt1|opt2|opt3} format
    OUTPUT_MODES = ["random", "sequential", "fixed", "dynamic_prompts", "list (csv)"]
    
    # Class variable to track sequential indices (memory-based, resets on ComfyUI restart)
    _sequential_indices = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get list of saved wildcards for the dropdown
        saved_wildcards = FileManager.list_wildcards()
        saved_wildcards_list = [""] + saved_wildcards if saved_wildcards else [""]
        
        return {
            "required": {
                "wildcard_values": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter values separated by newline, comma, or |\nUse (a, b) or {a|b} to group values"
                }),
                "output_mode": (cls.OUTPUT_MODES, {
                    "default": "random"
                }),
            },
            "optional": {
                "fixed_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 9999,
                    "step": 1,
                    "display": "number"
                }),
                "wildcard_name": ("STRING", {
                    "default": "",
                    "placeholder": "Name for saving/loading"
                }),
                "load_wildcard": (saved_wildcards_list, {
                    "default": ""
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }
    
    @classmethod
    def IS_CHANGED(cls, output_mode, **kwargs):
        """
        Control when the node re-executes.
        Random and sequential modes should always re-execute.
        """
        if output_mode in ["random", "sequential"]:
            return float("nan")  # Always re-execute
        return ""  # Use default caching for fixed and dynamic_prompts
    
    def process(
        self,
        wildcard_values: str,
        output_mode: str,
        fixed_index: int = 0,
        wildcard_name: str = "",
        load_wildcard: str = "",
        unique_id: str = ""
    ):
        """
        Process the wildcard values and return based on output mode.
        
        Args:
            wildcard_values: Text containing wildcard values
            output_mode: One of 'random', 'sequential', 'fixed', 'dynamic_prompts', 'list'
            fixed_index: Index to use when output_mode is 'fixed'
            wildcard_name: Name for saving the wildcard
            load_wildcard: Name of wildcard to load (handled by frontend)
            unique_id: Unique node ID for tracking sequential state
            
        Returns:
            Tuple containing the selected/formatted wildcard value
        """
        # Parse the values
        values = WildcardParser.parse_value_list(wildcard_values)
        
        if not values:
            return ("",)
        
        # Process based on output mode
        if output_mode == "list (csv)":
            # Return as comma-separated list
            result = ", ".join(values)
            return (result,)
        
        elif output_mode == "dynamic_prompts":
            # Return in Dynamic Prompts format: {opt1|opt2|opt3}
            result = WildcardParser.format_as_dynamic_prompts(values)
            return (result,)
        
        elif output_mode == "fixed":
            # Return value at specific index (clamped to valid range)
            index = max(0, min(fixed_index, len(values) - 1))
            return (values[index],)
        
        elif output_mode == "sequential":
            # Get next value in sequence
            node_key = f"wildcard_{unique_id}"
            
            if node_key not in WildcardNode._sequential_indices:
                WildcardNode._sequential_indices[node_key] = 0
            
            index = WildcardNode._sequential_indices[node_key] % len(values)
            result = values[index]
            
            # Increment for next execution
            WildcardNode._sequential_indices[node_key] = (index + 1) % len(values)
            
            return (result,)
        
        else:  # random (default)
            # Randomly select a value
            result = random.choice(values)
            return (result,)
    
    @classmethod
    def get_value_count(cls, wildcard_values: str) -> int:
        """
        Get the number of values in the wildcard text.
        Used by frontend to set fixed_index range.
        
        Args:
            wildcard_values: Text containing wildcard values
            
        Returns:
            Number of parsed values
        """
        return WildcardParser.count_values(wildcard_values)
    
    @classmethod
    def reset_sequential_index(cls, unique_id: str):
        """
        Reset the sequential index for a specific node.
        
        Args:
            unique_id: The node's unique ID
        """
        node_key = f"wildcard_{unique_id}"
        if node_key in cls._sequential_indices:
            cls._sequential_indices[node_key] = 0
    
    @classmethod
    def reset_all_sequential_indices(cls):
        """Reset all sequential indices."""
        cls._sequential_indices.clear()


# API endpoints for frontend communication
class WildcardNodeAPI:
    """API methods for frontend save/load operations."""
    
    @staticmethod
    def save_wildcard(name: str, raw_text: str) -> dict:
        """Save a wildcard list."""
        values = WildcardParser.parse_value_list(raw_text)
        success = FileManager.save_wildcard(name, raw_text, values)
        return {
            "success": success,
            "message": f"Saved wildcard '{name}'" if success else f"Failed to save wildcard '{name}'"
        }
    
    @staticmethod
    def load_wildcard(name: str) -> dict:
        """Load a wildcard list."""
        data = FileManager.load_wildcard(name)
        if data:
            return {
                "success": True,
                "data": data
            }
        return {
            "success": False,
            "message": f"Failed to load wildcard '{name}'"
        }
    
    @staticmethod
    def list_wildcards() -> dict:
        """Get list of all saved wildcards."""
        wildcards = FileManager.list_wildcards()
        return {
            "success": True,
            "wildcards": wildcards
        }
    
    @staticmethod
    def delete_wildcard(name: str) -> dict:
        """Delete a saved wildcard."""
        success = FileManager.delete_wildcard(name)
        return {
            "success": success,
            "message": f"Deleted wildcard '{name}'" if success else f"Failed to delete wildcard '{name}'"
        }
    
    @staticmethod
    def get_value_count(raw_text: str) -> dict:
        """Get the number of values in wildcard text."""
        count = WildcardParser.count_values(raw_text)
        return {
            "success": True,
            "count": count
        }
    
    @staticmethod
    def reset_sequential(unique_id: str) -> dict:
        """Reset sequential index for a node."""
        WildcardNode.reset_sequential_index(unique_id)
        return {
            "success": True,
            "message": "Sequential index reset"
        }
