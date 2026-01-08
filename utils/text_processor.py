"""
Text Processor for ComfyUI-PromptDrafter
Handles combining prefix/suffix with prompts and wildcard replacement.
"""

from typing import Optional, Dict
from .wildcard_parser import WildcardParser


class TextProcessor:
    """Processes prompt text with prefix/suffix and wildcard replacement."""
    
    @classmethod
    def _strip_commas(cls, text: str) -> str:
        """
        Strip leading and trailing commas and whitespace from text.
        
        Args:
            text: Text to clean
            
        Returns:
            Text with leading/trailing commas removed
        """
        if not text:
            return ""
        # Strip whitespace first, then commas, then whitespace again
        result = text.strip()
        result = result.strip(',')
        result = result.strip()
        return result
    
    @classmethod
    def combine_prompt(
        cls,
        text: str,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        separator: str = ", "
    ) -> str:
        """
        Combine a prompt with optional prefix and suffix.
        Smart comma handling ensures no double commas and proper spacing.
        
        Args:
            text: The main prompt text
            prefix: Optional text to prepend
            suffix: Optional text to append
            separator: Separator to use between parts (default: ", ")
            
        Returns:
            Combined prompt string
        """
        parts = []
        
        # Clean each part - strip commas from edges to prevent doubling
        if prefix and prefix.strip():
            parts.append(cls._strip_commas(prefix))
        
        if text and text.strip():
            parts.append(cls._strip_commas(text))
        
        if suffix and suffix.strip():
            parts.append(cls._strip_commas(suffix))
        
        return separator.join(parts)
    
    @classmethod
    def combine_strings(cls, *strings: str, separator: str = ", ") -> str:
        """
        Combine multiple strings with smart comma handling.
        Ignores empty/blank strings and ensures proper separator between parts.
        
        Args:
            *strings: Variable number of strings to combine
            separator: Separator to use between parts (default: ", ")
            
        Returns:
            Combined string with proper separators
        """
        parts = []
        
        for s in strings:
            if s and s.strip():
                cleaned = cls._strip_commas(s)
                if cleaned:  # Only add if there's content after cleaning
                    parts.append(cleaned)
        
        return separator.join(parts)
    
    @classmethod
    def process_prompt(
        cls,
        text: str,
        prefix: Optional[str] = None,
        suffix: Optional[str] = None,
        wildcard_values: Optional[Dict[str, str]] = None,
        separator: str = ", "
    ) -> str:
        """
        Fully process a prompt: combine with prefix/suffix and replace wildcards.
        
        Args:
            text: The main prompt text
            prefix: Optional text to prepend
            suffix: Optional text to append
            wildcard_values: Dictionary mapping wildcard names to values
            separator: Separator to use between parts
            
        Returns:
            Fully processed prompt string
        """
        # First combine with prefix/suffix
        combined = cls.combine_prompt(text, prefix, suffix, separator)
        
        # Then replace wildcards if provided
        if wildcard_values:
            combined = WildcardParser.replace_wildcards(combined, wildcard_values)
        
        return combined
    
    @classmethod
    def get_required_wildcards(cls, text: str) -> list:
        """
        Get list of wildcard names required by a prompt.
        
        Args:
            text: Prompt text to analyze
            
        Returns:
            List of wildcard names (e.g., ['wildcard_color', 'wildcard_style'])
        """
        return WildcardParser.extract_wildcard_names(text)
    
    @classmethod
    def get_combined_wildcards(
        cls,
        positive_text: str,
        negative_text: str
    ) -> list:
        """
        Get combined list of unique wildcard names from both positive and negative prompts.
        
        Args:
            positive_text: Positive prompt text
            negative_text: Negative prompt text
            
        Returns:
            List of unique wildcard names from both prompts
        """
        positive_wildcards = set(WildcardParser.extract_wildcard_names(positive_text))
        negative_wildcards = set(WildcardParser.extract_wildcard_names(negative_text))
        
        # Combine and sort for consistent ordering
        all_wildcards = positive_wildcards.union(negative_wildcards)
        return sorted(list(all_wildcards))
    
    @classmethod
    def validate_wildcards(
        cls,
        text: str,
        available_wildcards: Dict[str, str]
    ) -> tuple:
        """
        Check if all wildcards in text have values available.
        
        Args:
            text: Prompt text to check
            available_wildcards: Dictionary of available wildcard values
            
        Returns:
            Tuple of (is_valid, missing_wildcards)
        """
        required = cls.get_required_wildcards(text)
        missing = [w for w in required if w not in available_wildcards]
        return (len(missing) == 0, missing)
    
    @classmethod
    def clean_prompt(cls, text: str) -> str:
        """
        Clean up a prompt by removing extra whitespace and normalizing separators.
        
        Args:
            text: Prompt text to clean
            
        Returns:
            Cleaned prompt text
        """
        if not text:
            return ""
        
        # Replace multiple spaces with single space
        import re
        text = re.sub(r' +', ' ', text)
        
        # Clean up comma spacing
        text = re.sub(r'\s*,\s*', ', ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove trailing comma
        if text.endswith(','):
            text = text[:-1].strip()
        
        return text
