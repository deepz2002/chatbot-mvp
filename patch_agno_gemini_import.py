# patch_agno_gemini_import.py
import types
import google.generativeai as genai

# Patch as if google.genai.types exists with all the attributes agno expects
import sys
sys.modules["google.genai.types"] = types.SimpleNamespace(
    GenerationConfig=genai.GenerationConfig,
    Content=genai.types.ContentType,
    Part=genai.types.PartType,
    FunctionDeclaration=genai.types.FunctionDeclaration,
    Tool=genai.types.Tool,
    HarmCategory=genai.types.HarmCategory,
    HarmBlockThreshold=genai.types.HarmBlockThreshold,
)
