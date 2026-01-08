"""
Single Prompt Drafter Node for ComfyUI-PromptDrafter
Single text field node for either positive or negative prompts.
"""

from ..utils.file_manager import FileManager
from ..utils.wildcard_parser import WildcardParser
from ..utils.text_processor import TextProcessor


class SinglePromptDrafter:
    """
    A node for drafting a single prompt with wildcard support.
    
    Features:
    - Single text field with neutral silver outline
    - Optional prefix and suffix inputs
    - Dynamic wildcard ports based on {wildcard_name} patterns in text
    - Save/Load functionality for prompts
    """
    
    CATEGORY = "PromptDrafter"
    DISPLAY_NAME = "Single Prompt - PromptDrafter"
    FUNCTION = "process"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    OUTPUT_NODE = False
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get list of saved prompts for the dropdown
        saved_prompts = FileManager.list_single_prompts()
        saved_prompts_list = [""] + saved_prompts if saved_prompts else [""]
        
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter prompt...\nUse {wildcard_name} for wildcards"
                }),
            },
            "optional": {
                "prefix": ("STRING", {
                    "forceInput": True,
                    "default": ""
                }),
                "suffix": ("STRING", {
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
        prompt: str,
        prefix: str = "",
        suffix: str = "",
        prompt_name: str = "",
        load_prompt: str = "",
        unique_id: str = "",
        **kwargs  # Catch dynamic wildcard inputs
    ):
        """
        Process the prompt with prefix/suffix and wildcard replacement.
        
        Args:
            prompt: The prompt text
            prefix: Optional prefix for prompt
            suffix: Optional suffix for prompt
            prompt_name: Name for saving the prompt
            load_prompt: Name of prompt to load (handled by frontend)
            unique_id: Unique node ID for tracking
            **kwargs: Dynamic wildcard inputs (wildcard_name -> value)
            
        Returns:
            Tuple containing the processed prompt
        """
        # Collect wildcard values from kwargs
        wildcard_values = {}
        for key, value in kwargs.items():
            if key.startswith("wildcard_"):
                wildcard_values[key] = value
        
        # Process prompt
        processed = TextProcessor.process_prompt(
            text=prompt,
            prefix=prefix,
            suffix=suffix,
            wildcard_values=wildcard_values
        )
        
        # Clean up the prompt
        processed = TextProcessor.clean_prompt(processed)
        
        return (processed,)
    
    @classmethod
    def get_wildcards_from_text(cls, text: str) -> list:
        """
        Get list of wildcard names from prompt text.
        Used by frontend to create dynamic ports.
        
        Args:
            text: Prompt text
            
        Returns:
            List of unique wildcard names
        """
        return TextProcessor.get_required_wildcards(text)


# API endpoints for frontend communication
class SinglePromptDrafterAPI:
    """API methods for frontend save/load operations."""
    
    @staticmethod
    def save_prompt(name: str, prompt: str) -> dict:
        """Save a single prompt."""
        success = FileManager.save_single_prompt(name, prompt)
        return {
            "success": success,
            "message": f"Saved prompt '{name}'" if success else f"Failed to save prompt '{name}'"
        }
    
    @staticmethod
    def load_prompt(name: str) -> dict:
        """Load a single prompt."""
        data = FileManager.load_single_prompt(name)
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
        """Get list of all saved single prompts."""
        prompts = FileManager.list_single_prompts()
        return {
            "success": True,
            "prompts": prompts
        }
    
    @staticmethod
    def delete_prompt(name: str) -> dict:
        """Delete a saved single prompt."""
        success = FileManager.delete_single_prompt(name)
        return {
            "success": success,
            "message": f"Deleted prompt '{name}'" if success else f"Failed to delete prompt '{name}'"
        }
