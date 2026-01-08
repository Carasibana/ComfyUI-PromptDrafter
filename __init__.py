"""
ComfyUI-PromptDrafter
A custom node pack for drafting and managing prompts with wildcard support.

Nodes:
- Dual Prompt Drafter: Main node with positive/negative prompt fields
- Single Prompt Drafter: Single prompt field for flexible use
- Wildcard: Create and manage wildcard value lists
- Prompt Combiner: Combine multiple strings with smart comma handling
"""

import os
import json
from aiohttp import web
from server import PromptServer

from .nodes.dual_prompt_drafter import DualPromptDrafter, DualPromptDrafterAPI
from .nodes.single_prompt_drafter import SinglePromptDrafter, SinglePromptDrafterAPI
from .nodes.wildcard_node import WildcardNode, WildcardNodeAPI
from .nodes.prompt_combiner import PromptCombiner
from .utils.file_manager import FileManager
from .utils.wildcard_parser import WildcardParser

# Extension directory
EXTENSION_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIRECTORY = os.path.join(EXTENSION_DIR, "js")

# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "DualPromptDrafter": DualPromptDrafter,
    "SinglePromptDrafter": SinglePromptDrafter,
    "Wildcard": WildcardNode,
    "PromptCombiner": PromptCombiner,
}

# Display names for nodes in the UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "DualPromptDrafter": "Dual Prompt Drafter",
    "SinglePromptDrafter": "Single Prompt Drafter",
    "Wildcard": "Wildcard",
    "PromptCombiner": "Prompt Combiner",
}

# Tell ComfyUI where to find the web files
WEB_DIRECTORY = "./js"

# Version info
__version__ = "1.0.0"


# ============================================================================
# API Routes for frontend communication
# ============================================================================

@PromptServer.instance.routes.post("/promptdrafter/dual/save")
async def save_dual_prompt(request):
    """Save a dual prompt combination."""
    try:
        data = await request.json()
        name = data.get("name", "")
        positive = data.get("positive", "")
        negative = data.get("negative", "")
        
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = DualPromptDrafterAPI.save_prompt(name, positive, negative)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.get("/promptdrafter/dual/load/{name}")
async def load_dual_prompt(request):
    """Load a dual prompt combination."""
    try:
        name = request.match_info.get("name", "")
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = DualPromptDrafterAPI.load_prompt(name)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.get("/promptdrafter/dual/list")
async def list_dual_prompts(request):
    """Get list of all saved dual prompts."""
    try:
        result = DualPromptDrafterAPI.list_prompts()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.delete("/promptdrafter/dual/delete/{name}")
async def delete_dual_prompt(request):
    """Delete a saved dual prompt."""
    try:
        name = request.match_info.get("name", "")
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = DualPromptDrafterAPI.delete_prompt(name)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.post("/promptdrafter/single/save")
async def save_single_prompt(request):
    """Save a single prompt."""
    try:
        data = await request.json()
        name = data.get("name", "")
        prompt = data.get("prompt", "")
        
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = SinglePromptDrafterAPI.save_prompt(name, prompt)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.get("/promptdrafter/single/load/{name}")
async def load_single_prompt(request):
    """Load a single prompt."""
    try:
        name = request.match_info.get("name", "")
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = SinglePromptDrafterAPI.load_prompt(name)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.get("/promptdrafter/single/list")
async def list_single_prompts(request):
    """Get list of all saved single prompts."""
    try:
        result = SinglePromptDrafterAPI.list_prompts()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.delete("/promptdrafter/single/delete/{name}")
async def delete_single_prompt(request):
    """Delete a saved single prompt."""
    try:
        name = request.match_info.get("name", "")
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = SinglePromptDrafterAPI.delete_prompt(name)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.post("/promptdrafter/wildcard/save")
async def save_wildcard(request):
    """Save a wildcard list."""
    try:
        data = await request.json()
        name = data.get("name", "")
        raw_text = data.get("raw_text", "")
        
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = WildcardNodeAPI.save_wildcard(name, raw_text)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.get("/promptdrafter/wildcard/load/{name}")
async def load_wildcard(request):
    """Load a wildcard list."""
    try:
        name = request.match_info.get("name", "")
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = WildcardNodeAPI.load_wildcard(name)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.get("/promptdrafter/wildcard/list")
async def list_wildcards(request):
    """Get list of all saved wildcards."""
    try:
        result = WildcardNodeAPI.list_wildcards()
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.delete("/promptdrafter/wildcard/delete/{name}")
async def delete_wildcard(request):
    """Delete a saved wildcard."""
    try:
        name = request.match_info.get("name", "")
        if not name:
            return web.json_response({"success": False, "message": "Name is required"})
        
        result = WildcardNodeAPI.delete_wildcard(name)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.post("/promptdrafter/wildcard/count")
async def get_wildcard_count(request):
    """Get the number of values in wildcard text."""
    try:
        data = await request.json()
        raw_text = data.get("raw_text", "")
        
        result = WildcardNodeAPI.get_value_count(raw_text)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.post("/promptdrafter/wildcard/reset")
async def reset_wildcard_sequential(request):
    """Reset sequential index for a wildcard node."""
    try:
        data = await request.json()
        unique_id = data.get("unique_id", "")
        
        result = WildcardNodeAPI.reset_sequential(unique_id)
        return web.json_response(result)
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


@PromptServer.instance.routes.post("/promptdrafter/parse_wildcards")
async def parse_wildcards_from_text(request):
    """Parse wildcard names from prompt text."""
    try:
        data = await request.json()
        text = data.get("text", "")
        
        wildcards = WildcardParser.extract_wildcard_names(text)
        return web.json_response({
            "success": True,
            "wildcards": wildcards
        })
    except Exception as e:
        return web.json_response({"success": False, "message": str(e)})


print(f"[PromptDrafter] Loaded v{__version__}")
