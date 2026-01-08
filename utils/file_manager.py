"""
File Manager for ComfyUI-PromptDrafter
Handles saving and loading of prompts and wildcards as JSON files.
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Get the directory where this file is located
EXTENSION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(EXTENSION_DIR, "config.json")


class FileManager:
    """Manages file operations for saving/loading prompts and wildcards."""
    
    _config_cache: Optional[Dict[str, Any]] = None
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Load and cache the configuration file."""
        if cls._config_cache is None:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    cls._config_cache = json.load(f)
            else:
                # Default configuration
                cls._config_cache = {
                    "save_paths": {
                        "dual_prompts": "saved/dual_prompts",
                        "single_prompts": "saved/single_prompts",
                        "wildcards": "saved/wildcards"
                    },
                    "settings": {
                        "auto_save": False,
                        "default_wildcard_mode": "random"
                    }
                }
        return cls._config_cache
    
    @classmethod
    def reload_config(cls) -> Dict[str, Any]:
        """Force reload the configuration file."""
        cls._config_cache = None
        return cls.get_config()
    
    @classmethod
    def get_save_path(cls, category: str) -> str:
        """
        Get the full save path for a category.
        
        Args:
            category: One of 'dual_prompts', 'single_prompts', 'wildcards'
            
        Returns:
            Full path to the save directory
        """
        config = cls.get_config()
        relative_path = config.get("save_paths", {}).get(category, f"saved/{category}")
        
        # If path is relative, make it relative to extension directory
        if not os.path.isabs(relative_path):
            return os.path.join(EXTENSION_DIR, relative_path)
        return relative_path
    
    @classmethod
    def ensure_directory(cls, category: str) -> str:
        """Ensure the save directory exists and return its path."""
        path = cls.get_save_path(category)
        os.makedirs(path, exist_ok=True)
        return path
    
    @classmethod
    def save_dual_prompt(cls, name: str, positive: str, negative: str) -> bool:
        """
        Save a dual prompt combination.
        
        Args:
            name: Name for the prompt combination
            positive: Positive prompt text
            negative: Negative prompt text
            
        Returns:
            True if save was successful
        """
        try:
            directory = cls.ensure_directory("dual_prompts")
            filename = cls._sanitize_filename(name) + ".json"
            filepath = os.path.join(directory, filename)
            
            data = {
                "name": name,
                "positive": positive,
                "negative": negative,
                "created": datetime.now().isoformat(),
                "type": "dual_prompt"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"[PromptDrafter] Error saving dual prompt: {e}")
            return False
    
    @classmethod
    def load_dual_prompt(cls, name: str) -> Optional[Dict[str, str]]:
        """
        Load a dual prompt combination.
        
        Args:
            name: Name of the prompt combination to load
            
        Returns:
            Dictionary with 'positive' and 'negative' keys, or None if not found
        """
        try:
            directory = cls.get_save_path("dual_prompts")
            filename = cls._sanitize_filename(name) + ".json"
            filepath = os.path.join(directory, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "name": data.get("name", name),
                "positive": data.get("positive", ""),
                "negative": data.get("negative", "")
            }
        except Exception as e:
            print(f"[PromptDrafter] Error loading dual prompt: {e}")
            return None
    
    @classmethod
    def list_dual_prompts(cls) -> List[str]:
        """Get list of all saved dual prompt names."""
        return cls._list_saves("dual_prompts")
    
    @classmethod
    def delete_dual_prompt(cls, name: str) -> bool:
        """Delete a saved dual prompt."""
        return cls._delete_save("dual_prompts", name)
    
    @classmethod
    def save_single_prompt(cls, name: str, prompt: str) -> bool:
        """
        Save a single prompt.
        
        Args:
            name: Name for the prompt
            prompt: Prompt text
            
        Returns:
            True if save was successful
        """
        try:
            directory = cls.ensure_directory("single_prompts")
            filename = cls._sanitize_filename(name) + ".json"
            filepath = os.path.join(directory, filename)
            
            data = {
                "name": name,
                "prompt": prompt,
                "created": datetime.now().isoformat(),
                "type": "single_prompt"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"[PromptDrafter] Error saving single prompt: {e}")
            return False
    
    @classmethod
    def load_single_prompt(cls, name: str) -> Optional[Dict[str, str]]:
        """
        Load a single prompt.
        
        Args:
            name: Name of the prompt to load
            
        Returns:
            Dictionary with 'prompt' key, or None if not found
        """
        try:
            directory = cls.get_save_path("single_prompts")
            filename = cls._sanitize_filename(name) + ".json"
            filepath = os.path.join(directory, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "name": data.get("name", name),
                "prompt": data.get("prompt", "")
            }
        except Exception as e:
            print(f"[PromptDrafter] Error loading single prompt: {e}")
            return None
    
    @classmethod
    def list_single_prompts(cls) -> List[str]:
        """Get list of all saved single prompt names."""
        return cls._list_saves("single_prompts")
    
    @classmethod
    def delete_single_prompt(cls, name: str) -> bool:
        """Delete a saved single prompt."""
        return cls._delete_save("single_prompts", name)
    
    @classmethod
    def save_wildcard(cls, name: str, raw_text: str, values: List[str]) -> bool:
        """
        Save a wildcard list.
        
        Args:
            name: Name for the wildcard
            raw_text: Original text as entered by user
            values: Parsed list of values
            
        Returns:
            True if save was successful
        """
        try:
            directory = cls.ensure_directory("wildcards")
            filename = cls._sanitize_filename(name) + ".json"
            filepath = os.path.join(directory, filename)
            
            data = {
                "name": name,
                "raw_text": raw_text,
                "values": values,
                "created": datetime.now().isoformat(),
                "type": "wildcard"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"[PromptDrafter] Error saving wildcard: {e}")
            return False
    
    @classmethod
    def load_wildcard(cls, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a wildcard list.
        
        Args:
            name: Name of the wildcard to load
            
        Returns:
            Dictionary with 'raw_text' and 'values' keys, or None if not found
        """
        try:
            directory = cls.get_save_path("wildcards")
            filename = cls._sanitize_filename(name) + ".json"
            filepath = os.path.join(directory, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                "name": data.get("name", name),
                "raw_text": data.get("raw_text", ""),
                "values": data.get("values", [])
            }
        except Exception as e:
            print(f"[PromptDrafter] Error loading wildcard: {e}")
            return None
    
    @classmethod
    def list_wildcards(cls) -> List[str]:
        """Get list of all saved wildcard names."""
        return cls._list_saves("wildcards")
    
    @classmethod
    def delete_wildcard(cls, name: str) -> bool:
        """Delete a saved wildcard."""
        return cls._delete_save("wildcards", name)
    
    @classmethod
    def _list_saves(cls, category: str) -> List[str]:
        """Get list of all saved items in a category."""
        try:
            directory = cls.get_save_path(category)
            if not os.path.exists(directory):
                return []
            
            names = []
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    # Try to read the name from the file
                    try:
                        filepath = os.path.join(directory, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        names.append(data.get("name", filename[:-5]))
                    except:
                        # Fall back to filename without extension
                        names.append(filename[:-5])
            
            return sorted(names)
        except Exception as e:
            print(f"[PromptDrafter] Error listing {category}: {e}")
            return []
    
    @classmethod
    def _delete_save(cls, category: str, name: str) -> bool:
        """Delete a saved item."""
        try:
            directory = cls.get_save_path(category)
            filename = cls._sanitize_filename(name) + ".json"
            filepath = os.path.join(directory, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"[PromptDrafter] Error deleting {category}/{name}: {e}")
            return False
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """
        Sanitize a name for use as a filename.
        
        Args:
            name: The name to sanitize
            
        Returns:
            A safe filename string
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        result = name
        for char in invalid_chars:
            result = result.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        result = result.strip(' .')
        
        # Ensure it's not empty
        if not result:
            result = "unnamed"
        
        return result
