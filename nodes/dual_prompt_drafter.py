"""
Dual Prompt Drafter Node for ComfyUI-PromptDrafter
Main node with positive and negative prompt fields.
"""

from ..utils.file_manager import FileManager
from ..utils.wildcard_parser import WildcardParser
from ..utils.text_processor import TextProcessor


class DualPromptDrafter:
    """
    A node for drafting both positive and negative prompts with wildcard support.
    
    Features:
    - Dual text fields for positive (green) and negative (red) prompts
    - Optional prefix and suffix inputs for both prompts
    - Dynamic wildcard ports based on {wildcard_name} patterns in text
    - Save/Load functionality for prompt combinations
    """
    
    CATEGORY = "PromptDrafter"
    DISPLAY_NAME = "Dual Prompts - PromptDrafter"
    FUNCTION = "process"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt")
    OUTPUT_NODE = False
    
    # Class variable to track sequential wildcard indices (memory-based, resets on restart)
    _wildcard_indices = {}
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get list of saved prompts for the dropdown
        saved_prompts = FileManager.list_dual_prompts()
        saved_prompts_list = [""] + saved_prompts if saved_prompts else [""]
        
        return {
            "required": {
                "positive_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter positive prompt...\nUse {wildcard_name} for wildcards"
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter negative prompt...\nUse {wildcard_name} for wildcards"
                }),
            },
            "optional": {
                "positive_prefix": ("STRING", {
                    "forceInput": True,
                    "default": ""
                }),
                "positive_suffix": ("STRING", {
                    "forceInput": True,
                    "default": ""
                }),
                "negative_prefix": ("STRING", {
                    "forceInput": True,
                    "default": ""
                }),
                "negative_suffix": ("STRING", {
                    "forceInput": True,
                    "default": ""
                }),
                "prompt_name": ("STRING", {
                    "default": "",
                    "placeholder": "Name for saving/loading"
                }),
                "load_prompt": (saved_prompts_list, {
                    "default": ""
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID"
            }
        }
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Force re-execution when inputs change."""
        return float("nan")
    
    def process(
        self,
        positive_prompt: str,
        negative_prompt: str,
        positive_prefix: str = "",
        positive_suffix: str = "",
        negative_prefix: str = "",
        negative_suffix: str = "",
        prompt_name: str = "",
        load_prompt: str = "",
        unique_id: str = "",
        **kwargs  # Catch dynamic wildcard inputs
    ):
        """
        Process the prompts with prefix/suffix and wildcard replacement.
        
        Args:
            positive_prompt: The positive prompt text
            negative_prompt: The negative prompt text
            positive_prefix: Optional prefix for positive prompt
            positive_suffix: Optional suffix for positive prompt
            negative_prefix: Optional prefix for negative prompt
            negative_suffix: Optional suffix for negative prompt
            prompt_name: Name for saving the prompt combination
            load_prompt: Name of prompt to load (handled by frontend)
            unique_id: Unique node ID for tracking
            **kwargs: Dynamic wildcard inputs (wildcard_name -> value)
            
        Returns:
            Tuple of (processed_positive, processed_negative)
        """
        # Collect wildcard values from kwargs
        wildcard_values = {}
        for key, value in kwargs.items():
            if key.startswith("wildcard_"):
                wildcard_values[key] = value
        
        # Process positive prompt
        processed_positive = TextProcessor.process_prompt(
            text=positive_prompt,
            prefix=positive_prefix,
            suffix=positive_suffix,
            wildcard_values=wildcard_values
        )
        
        # Process negative prompt
        processed_negative = TextProcessor.process_prompt(
            text=negative_prompt,
            prefix=negative_prefix,
            suffix=negative_suffix,
            wildcard_values=wildcard_values
        )
        
        # Clean up the prompts
        processed_positive = TextProcessor.clean_prompt(processed_positive)
        processed_negative = TextProcessor.clean_prompt(processed_negative)
        
        return (processed_positive, processed_negative)
    
    @classmethod
    def get_wildcards_from_text(cls, positive_text: str, negative_text: str) -> list:
        """
        Get list of wildcard names from both prompt texts.
        Used by frontend to create dynamic ports.
        
        Args:
            positive_text: Positive prompt text
            negative_text: Negative prompt text
            
        Returns:
            List of unique wildcard names
        """
        return TextProcessor.get_combined_wildcards(positive_text, negative_text)


# API endpoints for frontend communication
class DualPromptDrafterAPI:
    """API methods for frontend save/load operations."""
    
    @staticmethod
    def save_prompt(name: str, positive: str, negative: str) -> dict:
        """Save a dual prompt combination."""
        success = FileManager.save_dual_prompt(name, positive, negative)
        return {
            "success": success,
            "message": f"Saved prompt '{name}'" if success else f"Failed to save prompt '{name}'"
        }
    
    @staticmethod
    def load_prompt(name: str) -> dict:
        """Load a dual prompt combination."""
        data = FileManager.load_dual_prompt(name)
        if data:
            return {
                "success": True,
                "data": data
            }
        return {
            "success": False,
            "message": f"Failed to load prompt '{name}'"
        }
    
    @staticmethod
    def list_prompts() -> dict:
        """Get list of all saved dual prompts."""
        prompts = FileManager.list_dual_prompts()
        return {
            "success": True,
            "prompts": prompts
        }
    
    @staticmethod
    def delete_prompt(name: str) -> dict:
        """Delete a saved dual prompt."""
        success = FileManager.delete_dual_prompt(name)
        return {
            "success": success,
            "message": f"Deleted prompt '{name}'" if success else f"Failed to delete prompt '{name}'"
        }
