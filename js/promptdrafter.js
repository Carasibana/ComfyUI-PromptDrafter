/**
 * ComfyUI-PromptDrafter Frontend
 * Handles custom UI elements, dynamic ports, keyboard shortcuts, and save/load functionality.
 */

import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// ============================================================================
// Constants
// ============================================================================

const COLORS = {
    positive: "#2d5a27",      // Green for positive prompts
    negative: "#5a2727",      // Red for negative prompts
    neutral: "#4a4a4a",       // Silver/gray for single prompts
    wildcard: "#4a2d5a",      // Purple for wildcards
    border: {
        positive: "#4a9f3d",
        negative: "#9f3d3d",
        neutral: "#8a8a8a",
        wildcard: "#8a4a9f"
    }
};

const WILDCARD_PATTERN = /\{wildcard_([a-zA-Z0-9_]+)\}/g;

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Extract wildcard names from text
 */
function extractWildcards(text) {
    const wildcards = new Set();
    let match;
    const pattern = new RegExp(WILDCARD_PATTERN.source, 'g');
    while ((match = pattern.exec(text)) !== null) {
        wildcards.add(`wildcard_${match[1]}`);
    }
    return Array.from(wildcards);
}

/**
 * Debounce function to limit rapid calls
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Get the next wildcard number based on existing wildcards in text
 * Returns {wildcard_01} if none exist, or {wildcard_XX} where XX is next number
 */
function getNextWildcardPlaceholder(text) {
    const matches = text.match(/\{wildcard_(\d+)\}/g) || [];
    if (matches.length === 0) {
        return "{wildcard_01}";
    }
    
    const numbers = matches.map(m => {
        const num = m.match(/\d+/)[0];
        return parseInt(num, 10);
    });
    
    const maxNum = Math.max(...numbers);
    const nextNum = maxNum + 1;
    return `{wildcard_${String(nextNum).padStart(2, '0')}}`;
}

/**
 * Show a notification popup using ComfyUI's notification system
 */
function showNotification(message, type = "info") {
    if (app.ui && app.ui.dialog) {
        app.ui.dialog.show(message);
    } else {
        // Fallback: use console if dialog not available
        console.log(`[${type.toUpperCase()}] ${message}`);
    }
}

// ============================================================================
// API Functions
// ============================================================================

const PromptDrafterAPI = {
    // Dual Prompt API
    async saveDualPrompt(name, positive, negative) {
        const response = await api.fetchApi("/promptdrafter/dual/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, positive, negative })
        });
        return await response.json();
    },

    async loadDualPrompt(name) {
        const response = await api.fetchApi(`/promptdrafter/dual/load/${encodeURIComponent(name)}`);
        return await response.json();
    },

    async listDualPrompts() {
        const response = await api.fetchApi("/promptdrafter/dual/list");
        return await response.json();
    },

    // Single Prompt API
    async saveSinglePrompt(name, prompt) {
        const response = await api.fetchApi("/promptdrafter/single/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, prompt })
        });
        return await response.json();
    },

    async loadSinglePrompt(name) {
        const response = await api.fetchApi(`/promptdrafter/single/load/${encodeURIComponent(name)}`);
        return await response.json();
    },

    async listSinglePrompts() {
        const response = await api.fetchApi("/promptdrafter/single/list");
        return await response.json();
    },

    // Wildcard API
    async saveWildcard(name, rawText) {
        const response = await api.fetchApi("/promptdrafter/wildcard/save", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, raw_text: rawText })
        });
        return await response.json();
    },

    async loadWildcard(name) {
        const response = await api.fetchApi(`/promptdrafter/wildcard/load/${encodeURIComponent(name)}`);
        return await response.json();
    },

    async listWildcards() {
        const response = await api.fetchApi("/promptdrafter/wildcard/list");
        return await response.json();
    },

    async getWildcardCount(rawText) {
        const response = await api.fetchApi("/promptdrafter/wildcard/count", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ raw_text: rawText })
        });
        return await response.json();
    }
};

// ============================================================================
// Dynamic Wildcard Port Management
// ============================================================================

/**
 * Update dynamic wildcard input ports based on text content
 * Does NOT resize the node - user controls node size
 */
function updateWildcardPorts(node, texts) {
    // Combine all texts and extract wildcards
    const combinedText = Array.isArray(texts) ? texts.join(" ") : texts;
    const requiredWildcards = extractWildcards(combinedText);
    
    // Get current wildcard inputs
    const currentWildcardInputs = [];
    if (node.inputs) {
        for (let i = 0; i < node.inputs.length; i++) {
            const input = node.inputs[i];
            if (input.name.startsWith("wildcard_")) {
                currentWildcardInputs.push(input.name);
            }
        }
    }
    
    // Find wildcards to add and remove
    const toAdd = requiredWildcards.filter(w => !currentWildcardInputs.includes(w));
    const toRemove = currentWildcardInputs.filter(w => !requiredWildcards.includes(w));
    
    // Remove unused wildcard inputs
    for (const name of toRemove) {
        const index = node.inputs.findIndex(i => i.name === name);
        if (index !== -1) {
            node.removeInput(index);
        }
    }
    
    // Add new wildcard inputs
    for (const name of toAdd) {
        node.addInput(name, "STRING");
    }
    
    // Just mark canvas dirty, do NOT resize node
    if (toAdd.length > 0 || toRemove.length > 0) {
        app.graph.setDirtyCanvas(true, true);
    }
}

// ============================================================================
// Node Registration: Dual Prompt Drafter
// ============================================================================

app.registerExtension({
    name: "PromptDrafter.DualPromptDrafter",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "DualPromptDrafter") return;
        
        // Override node display name
        nodeData.display_name = "Dual Prompts - PromptDrafter";
        if (nodeType.prototype) {
            nodeType.prototype.title = "Dual Prompts - PromptDrafter";
        }
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            if (onNodeCreated) {
                onNodeCreated.apply(this, arguments);
            }
            
            const node = this;
            
            // Find text widgets
            const positiveWidget = node.widgets.find(w => w.name === "positive_prompt");
            const negativeWidget = node.widgets.find(w => w.name === "negative_prompt");
            const nameWidget = node.widgets.find(w => w.name === "prompt_name");
            const loadWidget = node.widgets.find(w => w.name === "load_prompt");
            
            // Set border colors for drawing
            if (positiveWidget) positiveWidget.borderColor = COLORS.border.positive;
            if (negativeWidget) negativeWidget.borderColor = COLORS.border.negative;
            
            // Debounced wildcard port update (no resize)
            const debouncedUpdatePorts = debounce(() => {
                const positiveText = positiveWidget ? positiveWidget.value : "";
                const negativeText = negativeWidget ? negativeWidget.value : "";
                updateWildcardPorts(node, [positiveText, negativeText]);
            }, 300);
            
            // Text change handler
            node.onTextChange = (name, value) => {
                debouncedUpdatePorts();
            };
            
            // Override widget callbacks to trigger port updates
            if (positiveWidget) {
                const originalCallback = positiveWidget.callback;
                positiveWidget.callback = (value) => {
                    if (originalCallback) originalCallback(value);
                    node.onTextChange("positive_prompt", value);
                };
            }
            
            if (negativeWidget) {
                const originalCallback = negativeWidget.callback;
                negativeWidget.callback = (value) => {
                    if (originalCallback) originalCallback(value);
                    node.onTextChange("negative_prompt", value);
                };
            }
            
            // Add "Add Wildcard" button for positive prompt (after positive_prompt widget)
            if (positiveWidget) {
                const positiveIndex = node.widgets.indexOf(positiveWidget);
                const addPosBtn = node.addWidget("button", "add_pos_wildcard_btn", "Add Wildcard to Prompt", () => {
                    if (positiveWidget) {
                        const nextWildcard = getNextWildcardPlaceholder(positiveWidget.value);
                        positiveWidget.value += (positiveWidget.value ? " " : "") + nextWildcard;
                        if (positiveWidget.callback) {
                            positiveWidget.callback(positiveWidget.value);
                        }
                        debouncedUpdatePorts();
                    }
                });
                if (addPosBtn) {
                    addPosBtn.label = "Add Wildcard to Prompt";
                }
                // Move button to after positive widget
                if (positiveIndex >= 0) {
                    node.widgets.splice(node.widgets.length - 1, 1);
                    node.widgets.splice(positiveIndex + 1, 0, addPosBtn);
                }
            }
            
            // Add "Add Wildcard" button for negative prompt (after negative_prompt widget)
            if (negativeWidget) {
                const negativeIndex = node.widgets.indexOf(negativeWidget);
                const addNegBtn = node.addWidget("button", "add_neg_wildcard_btn", "Add Wildcard to Prompt", () => {
                    if (negativeWidget) {
                        const nextWildcard = getNextWildcardPlaceholder(negativeWidget.value);
                        negativeWidget.value += (negativeWidget.value ? " " : "") + nextWildcard;
                        if (negativeWidget.callback) {
                            negativeWidget.callback(negativeWidget.value);
                        }
                        debouncedUpdatePorts();
                    }
                });
                if (addNegBtn) {
                    addNegBtn.label = "Add Wildcard to Prompt";
                }
                // Move button to after negative widget
                if (negativeIndex >= 0) {
                    node.widgets.splice(node.widgets.length - 1, 1);
                    node.widgets.splice(negativeIndex + 1, 0, addNegBtn);
                }
            }
            
            // Add Save button
            const saveBtn = node.addWidget("button", "save_prompt_btn", "Save Prompts", async () => {
                const name = nameWidget ? nameWidget.value : "";
                if (!name) {
                    showNotification("Please enter a name to save the prompts");
                    return;
                }
                
                const positive = positiveWidget ? positiveWidget.value : "";
                const negative = negativeWidget ? negativeWidget.value : "";
                
                const result = await PromptDrafterAPI.saveDualPrompt(name, positive, negative);
                if (result.success) {
                    // Refresh the load dropdown silently
                    await refreshDualPromptList(node);
                }
            });
            if (saveBtn) {
                saveBtn.label = "Save Prompts";
            }
            
            // Handle load dropdown change
            if (loadWidget) {
                const originalCallback = loadWidget.callback;
                loadWidget.callback = async (value) => {
                    if (originalCallback) originalCallback(value);
                    
                    if (value) {
                        const result = await PromptDrafterAPI.loadDualPrompt(value);
                        if (result.success && result.data) {
                            if (positiveWidget) positiveWidget.value = result.data.positive || "";
                            if (negativeWidget) negativeWidget.value = result.data.negative || "";
                            if (nameWidget) nameWidget.value = result.data.name || value;
                            
                            // Update wildcard ports (no resize)
                            debouncedUpdatePorts();
                        }
                    }
                };
            }
            
            // Initial port update
            setTimeout(debouncedUpdatePorts, 100);
        };
        
        // Custom drawing for colored borders (DualPromptDrafter)
        const onDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function(ctx) {
            if (onDrawForeground) {
                onDrawForeground.apply(this, arguments);
            }
            
            // Draw colored borders around text widgets that have borderColor set
            for (const widget of this.widgets || []) {
                if (widget.borderColor) {
                    // Get widget position
                    let widgetY = widget.last_y;
                    if (widgetY === undefined || widgetY === null) continue;
                    
                    // Use actual computed height with 6px margins on all sides
                    const widgetHeight = Math.max(20, (widget.computedHeight || 40) - 12);
                    const widgetX = 6;
                    const widgetWidth = this.size[0] - 12;
                    
                    ctx.save();
                    ctx.strokeStyle = widget.borderColor;
                    ctx.lineWidth = 3;
                    ctx.strokeRect(widgetX, widgetY + 6, widgetWidth, widgetHeight);
                    ctx.restore();
                }
            }
        };
    }
});

/**
 * Refresh the dual prompt load dropdown
 */
async function refreshDualPromptList(node) {
    const loadWidget = node.widgets.find(w => w.name === "load_prompt");
    if (loadWidget) {
        const result = await PromptDrafterAPI.listDualPrompts();
        if (result.success) {
            loadWidget.options.values = ["", ...result.prompts];
        }
    }
}

// ============================================================================
// Node Registration: Single Prompt Drafter
// ============================================================================

app.registerExtension({
    name: "PromptDrafter.SinglePromptDrafter",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "SinglePromptDrafter") return;
        
        // Override node display name
        nodeData.display_name = "Single Prompt - PromptDrafter";
        if (nodeType.prototype) {
            nodeType.prototype.title = "Single Prompt - PromptDrafter";
        }
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            if (onNodeCreated) {
                onNodeCreated.apply(this, arguments);
            }
            
            const node = this;
            
            // Find widgets
            const promptWidget = node.widgets.find(w => w.name === "prompt");
            const nameWidget = node.widgets.find(w => w.name === "prompt_name");
            const loadWidget = node.widgets.find(w => w.name === "load_prompt");
            
            // Set border color (neutral silver)
            if (promptWidget) promptWidget.borderColor = COLORS.border.neutral;
            
            // Debounced wildcard port update (no resize)
            const debouncedUpdatePorts = debounce(() => {
                const text = promptWidget ? promptWidget.value : "";
                updateWildcardPorts(node, text);
            }, 300);
            
            // Text change handler
            node.onTextChange = (name, value) => {
                debouncedUpdatePorts();
            };
            
            // Override widget callback
            if (promptWidget) {
                const originalCallback = promptWidget.callback;
                promptWidget.callback = (value) => {
                    if (originalCallback) originalCallback(value);
                    node.onTextChange("prompt", value);
                };
            }
            
            // Add "Add Wildcard" button (after prompt widget)
            if (promptWidget) {
                const promptIndex = node.widgets.indexOf(promptWidget);
                const addWildcardBtn = node.addWidget("button", "add_prompt_wildcard_btn", "Add Wildcard to Prompt", () => {
                    if (promptWidget) {
                        const nextWildcard = getNextWildcardPlaceholder(promptWidget.value);
                        promptWidget.value += (promptWidget.value ? " " : "") + nextWildcard;
                        if (promptWidget.callback) {
                            promptWidget.callback(promptWidget.value);
                        }
                        debouncedUpdatePorts();
                    }
                });
                if (addWildcardBtn) {
                    addWildcardBtn.label = "Add Wildcard to Prompt";
                }
                // Move button to after prompt widget
                if (promptIndex >= 0) {
                    node.widgets.splice(node.widgets.length - 1, 1);
                    node.widgets.splice(promptIndex + 1, 0, addWildcardBtn);
                }
            }
            
            // Add Save button
            const saveBtn = node.addWidget("button", "save_prompt_btn", "Save Prompt", async () => {
                const name = nameWidget ? nameWidget.value : "";
                if (!name) {
                    showNotification("Please enter a name to save the prompt");
                    return;
                }
                
                const prompt = promptWidget ? promptWidget.value : "";
                
                const result = await PromptDrafterAPI.saveSinglePrompt(name, prompt);
                if (result.success) {
                    await refreshSinglePromptList(node);
                }
            });
            if (saveBtn) {
                saveBtn.label = "Save Prompt";
            }
            
            // Handle load dropdown change
            if (loadWidget) {
                const originalCallback = loadWidget.callback;
                loadWidget.callback = async (value) => {
                    if (originalCallback) originalCallback(value);
                    
                    if (value) {
                        const result = await PromptDrafterAPI.loadSinglePrompt(value);
                        if (result.success && result.data) {
                            if (promptWidget) promptWidget.value = result.data.prompt || "";
                            if (nameWidget) nameWidget.value = result.data.name || value;
                            
                            debouncedUpdatePorts();
                        }
                    }
                };
            }
            
            // Initial port update
            setTimeout(debouncedUpdatePorts, 100);
        };
        
        // Custom drawing for colored border (SinglePromptDrafter)
        const onDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function(ctx) {
            if (onDrawForeground) {
                onDrawForeground.apply(this, arguments);
            }
            
            for (const widget of this.widgets || []) {
                if (widget.borderColor) {
                    let widgetY = widget.last_y;
                    if (widgetY === undefined || widgetY === null) continue;
                    
                    // Use actual computed height with 6px margins on all sides
                    const widgetHeight = Math.max(20, (widget.computedHeight || 40) - 12);
                    const widgetX = 6;
                    const widgetWidth = this.size[0] - 12;
                    
                    ctx.save();
                    ctx.strokeStyle = widget.borderColor;
                    ctx.lineWidth = 3;
                    ctx.strokeRect(widgetX, widgetY + 6, widgetWidth, widgetHeight);
                    ctx.restore();
                }
            }
        };
    }
});

/**
 * Refresh the single prompt load dropdown
 */
async function refreshSinglePromptList(node) {
    const loadWidget = node.widgets.find(w => w.name === "load_prompt");
    if (loadWidget) {
        const result = await PromptDrafterAPI.listSinglePrompts();
        if (result.success) {
            loadWidget.options.values = ["", ...result.prompts];
        }
    }
}

// ============================================================================
// Node Registration: Wildcard Node
// ============================================================================

app.registerExtension({
    name: "PromptDrafter.Wildcard",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "Wildcard") return;
        
        // Override node display name
        nodeData.display_name = "Wildcards - PromptDrafter";
        if (nodeType.prototype) {
            nodeType.prototype.title = "Wildcards - PromptDrafter";
        }
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            if (onNodeCreated) {
                onNodeCreated.apply(this, arguments);
            }
            
            const node = this;
            
            // Find widgets
            const valuesWidget = node.widgets.find(w => w.name === "wildcard_values");
            const modeWidget = node.widgets.find(w => w.name === "output_mode");
            const fixedIndexWidget = node.widgets.find(w => w.name === "fixed_index");
            const nameWidget = node.widgets.find(w => w.name === "wildcard_name");
            const loadWidget = node.widgets.find(w => w.name === "load_wildcard");
            
            // Set border color (purple)
            if (valuesWidget) valuesWidget.borderColor = COLORS.border.wildcard;
            
            // Update fixed_index visibility based on mode
            const updateFixedIndexVisibility = () => {
                if (fixedIndexWidget && modeWidget) {
                    fixedIndexWidget.disabled = modeWidget.value !== "fixed";
                }
            };
            
            // Update fixed_index max based on value count
            const updateFixedIndexRange = async () => {
                if (fixedIndexWidget && valuesWidget) {
                    const result = await PromptDrafterAPI.getWildcardCount(valuesWidget.value);
                    if (result.success && result.count > 0) {
                        fixedIndexWidget.options.max = result.count - 1;
                        if (fixedIndexWidget.value >= result.count) {
                            fixedIndexWidget.value = result.count - 1;
                        }
                    }
                }
            };
            
            // Mode change handler
            if (modeWidget) {
                const originalCallback = modeWidget.callback;
                modeWidget.callback = (value) => {
                    if (originalCallback) originalCallback(value);
                    updateFixedIndexVisibility();
                };
            }
            
            // Values change handler
            if (valuesWidget) {
                const originalCallback = valuesWidget.callback;
                valuesWidget.callback = (value) => {
                    if (originalCallback) originalCallback(value);
                    updateFixedIndexRange();
                };
            }
            
            // Add Save button
            const saveBtn = node.addWidget("button", "save_wildcard_btn", "Save Wildcards", async () => {
                const name = nameWidget ? nameWidget.value : "";
                if (!name) {
                    showNotification("Please enter a name to save the wildcards");
                    return;
                }
                
                const rawText = valuesWidget ? valuesWidget.value : "";
                
                const result = await PromptDrafterAPI.saveWildcard(name, rawText);
                if (result.success) {
                    await refreshWildcardList(node);
                }
            });
            if (saveBtn) {
                saveBtn.label = "Save Wildcards";
            }
            
            // Handle load dropdown change
            if (loadWidget) {
                const originalCallback = loadWidget.callback;
                loadWidget.callback = async (value) => {
                    if (originalCallback) originalCallback(value);
                    
                    if (value) {
                        const result = await PromptDrafterAPI.loadWildcard(value);
                        if (result.success && result.data) {
                            if (valuesWidget) valuesWidget.value = result.data.raw_text || "";
                            if (nameWidget) nameWidget.value = result.data.name || value;
                            
                            updateFixedIndexRange();
                        }
                    }
                };
            }
            
            // Initial setup
            updateFixedIndexVisibility();
            setTimeout(updateFixedIndexRange, 100);
        };
        
        // Custom drawing for colored border (Wildcard)
        const onDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function(ctx) {
            if (onDrawForeground) {
                onDrawForeground.apply(this, arguments);
            }
            
            for (const widget of this.widgets || []) {
                if (widget.borderColor) {
                    let widgetY = widget.last_y;
                    if (widgetY === undefined || widgetY === null) continue;
                    
                    // Use actual computed height with 6px margins on all sides
                    const widgetHeight = Math.max(20, (widget.computedHeight || 40) - 12);
                    const widgetX = 6;
                    const widgetWidth = this.size[0] - 12;
                    
                    ctx.save();
                    ctx.strokeStyle = widget.borderColor;
                    ctx.lineWidth = 3;
                    ctx.strokeRect(widgetX, widgetY + 6, widgetWidth, widgetHeight);
                    ctx.restore();
                }
            }
        };
    }
});

/**
 * Refresh the wildcard load dropdown
 */
async function refreshWildcardList(node) {
    const loadWidget = node.widgets.find(w => w.name === "load_wildcard");
    if (loadWidget) {
        const result = await PromptDrafterAPI.listWildcards();
        if (result.success) {
            loadWidget.options.values = ["", ...result.wildcards];
        }
    }
}

// ============================================================================
// Node Registration: Prompt Combiner
// ============================================================================

const MAX_COMBINER_INPUTS = 25;

app.registerExtension({
    name: "PromptDrafter.PromptCombiner",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "PromptCombiner") return;
        
        // Override node display name
        nodeData.display_name = "String Combiner - PromptDrafter";
        if (nodeType.prototype) {
            nodeType.prototype.title = "String Combiner - PromptDrafter";
        }
        
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function() {
            if (onNodeCreated) {
                onNodeCreated.apply(this, arguments);
            }
            
            const node = this;
            
            // Find the input_count widget
            const inputCountWidget = node.widgets.find(w => w.name === "input_count");
            let lastInputCount = inputCountWidget ? parseInt(inputCountWidget.value) : 2;
            let isInitialized = false;
            
            /**
             * Update which inputs are shown based on input_count
             * We remove inputs beyond count and add them back when needed
             */
            const updateInputs = () => {
                const count = inputCountWidget ? parseInt(inputCountWidget.value) : 2;
                
                if (!node.inputs) return;
                
                // On first load or when count changes, update the inputs
                if (!isInitialized || count !== lastInputCount) {
                    isInitialized = true;
                    lastInputCount = count;
                    
                    // Remove all string inputs first
                    for (let i = node.inputs.length - 1; i >= 0; i--) {
                        const input = node.inputs[i];
                        if (input.name.match(/^string_(\d+)$/)) {
                            node.removeInput(i);
                        }
                    }
                    
                    // Add back only the inputs we need (1 to count)
                    for (let i = 1; i <= count; i++) {
                        const inputName = `string_${i}`;
                        node.addInput(inputName, "STRING");
                    }
                    
                    node.setDirtyCanvas(true, true);
                    app.graph.setDirtyCanvas(true, true);
                }
            };
            
            // Override input_count widget callback to always fire
            if (inputCountWidget) {
                const originalCallback = inputCountWidget.callback;
                inputCountWidget.callback = (value) => {
                    if (originalCallback) originalCallback(value);
                    // Always call updateInputs, don't wait for requestAnimationFrame
                    setTimeout(updateInputs, 10);
                };
            }
            
            // Periodic check in case callback doesn't fire
            const checkInterval = setInterval(() => {
                if (node.inputs) {
                    updateInputs();
                }
            }, 200);
            
            // Store interval ID so it can be cleaned up if needed
            node._combinerCheckInterval = checkInterval;
            
            // Initial setup - remove extra inputs
            updateInputs();
        };
    }
});

console.log("[PromptDrafter] Frontend loaded");
