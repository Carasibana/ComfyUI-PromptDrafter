"""
Wildcard Parser for ComfyUI-PromptDrafter
Handles parsing of wildcard patterns and value lists.
"""

import re
from typing import List, Set, Tuple


class WildcardParser:
    """Parses wildcard patterns from text and handles value list parsing."""
    
    # Pattern to match {wildcard_name} placeholders
    WILDCARD_PATTERN = re.compile(r'\{wildcard_([a-zA-Z0-9_]+)\}')
    
    @classmethod
    def extract_wildcard_names(cls, text: str) -> List[str]:
        """
        Extract all unique wildcard names from text.
        
        Args:
            text: Text containing {wildcard_name} patterns
            
        Returns:
            List of unique wildcard names (without the 'wildcard_' prefix in the match,
            but we return the full name for port labeling)
        """
        matches = cls.WILDCARD_PATTERN.findall(text)
        # Return unique names while preserving order of first occurrence
        seen: Set[str] = set()
        unique_names: List[str] = []
        for name in matches:
            full_name = f"wildcard_{name}"
            if full_name not in seen:
                seen.add(full_name)
                unique_names.append(full_name)
        return unique_names
    
    @classmethod
    def replace_wildcards(cls, text: str, wildcard_values: dict) -> str:
        """
        Replace wildcard placeholders with their values.
        Any wildcard in the text that doesn't have a value provided will be
        replaced with an empty string.
        
        Args:
            text: Text containing {wildcard_name} patterns
            wildcard_values: Dictionary mapping wildcard names to their values
                            Keys should be like 'wildcard_color' (full name)
            
        Returns:
            Text with wildcards replaced by their values (or empty string)
        """
        result = text
        
        # First, replace wildcards that have values
        for name, value in wildcard_values.items():
            # Handle both 'wildcard_name' and just 'name' formats in the dict
            if name.startswith('wildcard_'):
                pattern = '{' + name + '}'
            else:
                pattern = '{wildcard_' + name + '}'
            result = result.replace(pattern, str(value) if value else "")
        
        # Then, replace any remaining wildcards with empty string
        # This handles wildcards that exist in text but have no value provided
        remaining_wildcards = cls.extract_wildcard_names(result)
        for wc_name in remaining_wildcards:
            pattern = '{' + wc_name + '}'
            result = result.replace(pattern, "")
        
        return result
    
    @classmethod
    def parse_value_list(cls, text: str) -> List[str]:
        """
        Parse a text string into a list of values.
        Supports newline, comma, and pipe delimiters.
        Treats content inside parentheses () or curly braces {} as single entries.
        
        Args:
            text: Text containing values separated by newlines, commas, or pipes
            
        Returns:
            List of parsed values
        """
        if not text or not text.strip():
            return []
        
        # First, protect bracketed content by replacing delimiters inside brackets
        protected_text, replacements = cls._protect_brackets(text)
        
        # Determine the primary delimiter
        # Priority: newline > pipe > comma (if multiple exist, use the most structured one)
        if '\n' in protected_text:
            # Split by newlines, but also handle commas/pipes within lines
            lines = protected_text.split('\n')
            values = []
            for line in lines:
                line = line.strip()
                if line:
                    # Check if line contains pipes or commas (outside brackets)
                    if '|' in line:
                        values.extend([v.strip() for v in line.split('|') if v.strip()])
                    elif ',' in line:
                        values.extend([v.strip() for v in line.split(',') if v.strip()])
                    else:
                        values.append(line)
        elif '|' in protected_text:
            values = [v.strip() for v in protected_text.split('|') if v.strip()]
        elif ',' in protected_text:
            values = [v.strip() for v in protected_text.split(',') if v.strip()]
        else:
            # Single value
            values = [protected_text.strip()] if protected_text.strip() else []
        
        # Restore protected content
        restored_values = []
        for value in values:
            restored = cls._restore_brackets(value, replacements)
            if restored:
                restored_values.append(restored)
        
        return restored_values
    
    @classmethod
    def _protect_brackets(cls, text: str) -> Tuple[str, dict]:
        """
        Replace content inside brackets with placeholders to protect from splitting.
        
        Args:
            text: Original text
            
        Returns:
            Tuple of (protected text, replacement dictionary)
        """
        replacements = {}
        counter = 0
        result = text
        
        # Protect parentheses content: (...)
        paren_pattern = re.compile(r'\([^()]*\)')
        while paren_pattern.search(result):
            match = paren_pattern.search(result)
            if match:
                placeholder = f"__PAREN_{counter}__"
                replacements[placeholder] = match.group(0)
                result = result[:match.start()] + placeholder + result[match.end():]
                counter += 1
        
        # Protect curly brace content: {...}
        # But NOT our wildcard patterns {wildcard_...}
        curly_pattern = re.compile(r'\{(?!wildcard_)[^{}]*\}')
        while curly_pattern.search(result):
            match = curly_pattern.search(result)
            if match:
                placeholder = f"__CURLY_{counter}__"
                replacements[placeholder] = match.group(0)
                result = result[:match.start()] + placeholder + result[match.end():]
                counter += 1
        
        return result, replacements
    
    @classmethod
    def _restore_brackets(cls, text: str, replacements: dict) -> str:
        """
        Restore protected bracket content.
        
        Args:
            text: Text with placeholders
            replacements: Dictionary of placeholder -> original content
            
        Returns:
            Text with original bracket content restored
        """
        result = text
        for placeholder, original in replacements.items():
            result = result.replace(placeholder, original)
        return result
    
    @classmethod
    def format_as_dynamic_prompts(cls, values: List[str]) -> str:
        """
        Format a list of values as Dynamic Prompts syntax.
        
        Args:
            values: List of values
            
        Returns:
            String in format {value1|value2|value3}
        """
        if not values:
            return ""
        if len(values) == 1:
            return values[0]
        return "{" + "|".join(values) + "}"
    
    @classmethod
    def count_values(cls, text: str) -> int:
        """
        Count the number of values in a text string.
        
        Args:
            text: Text containing values
            
        Returns:
            Number of values
        """
        return len(cls.parse_value_list(text))
    
    @classmethod
    def get_value_at_index(cls, text: str, index: int) -> str:
        """
        Get a specific value from a text string by index.
        
        Args:
            text: Text containing values
            index: Zero-based index of the value to get
            
        Returns:
            The value at the specified index, or empty string if out of range
        """
        values = cls.parse_value_list(text)
        if 0 <= index < len(values):
            return values[index]
        return ""
    
    @classmethod
    def validate_wildcard_name(cls, name: str) -> bool:
        """
        Check if a wildcard name is valid.
        
        Args:
            name: The name to validate (without 'wildcard_' prefix)
            
        Returns:
            True if the name is valid
        """
        if not name:
            return False
        # Only allow alphanumeric and underscores
        return bool(re.match(r'^[a-zA-Z0-9_]+$', name))
