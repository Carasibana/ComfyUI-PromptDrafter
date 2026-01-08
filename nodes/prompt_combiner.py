"""
Prompt Combiner Node for ComfyUI-PromptDrafter
Combines multiple strings with smart comma handling.
"""

from ..utils.text_processor import TextProcessor


# Maximum number of inputs supported
MAX_INPUTS = 25


class PromptCombiner:
    """
    A node for combining multiple strings with smart comma handling.
    
    Features:
    - Up to 25 optional string inputs
    - Configurable number of visible inputs via input_count widget
    - Smart comma handling (no double commas, proper spacing)
    - Ignores empty/blank inputs
    """
    
    CATEGORY = "PromptDrafter"
    DISPLAY_NAME = "String Combiner - PromptDrafter"
    FUNCTION = "process"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("combined",)
    OUTPUT_NODE = False
    
    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "input_count": ("INT", {
                    "default": 2,
                    "min": 2,
                    "max": MAX_INPUTS,
                    "step": 1,
                    "display": "number"
                }),
            },
            "optional": {}
        }
        
        # Add 25 optional string inputs
        for i in range(1, MAX_INPUTS + 1):
            inputs["optional"][f"string_{i}"] = ("STRING", {
                "forceInput": True,
                "default": ""
            })
        
        return inputs
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always re-execute to ensure fresh output."""
        return float("nan")
    
    def process(self, input_count: int = 2, **kwargs):
        """
        Combine input strings with smart comma handling.
        
        Args:
            input_count: Number of inputs to consider (for UI, backend processes all)
            **kwargs: string_1 through string_25
            
        Returns:
            Tuple containing the combined string
        """
        # Collect all non-empty string inputs
        strings = []
        
        for i in range(1, MAX_INPUTS + 1):
            key = f"string_{i}"
            value = kwargs.get(key, "")
            if value and value.strip():
                strings.append(value)
        
        # Combine using smart comma handling
        result = TextProcessor.combine_strings(*strings)
        
        return (result,)
