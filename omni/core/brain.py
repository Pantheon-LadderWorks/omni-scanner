"""
Omni Brain - The Intelligence Layer
====================================
Transforms Omni from "eyes that see" to "Science Officer that understands."

Pattern: Scan → Analyze → Synthesize → Explain
Architecture: Client of the Federation (uses Constitution Pillar for model selection)
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Import The Law (Constitution Client)
# This ensures Omni respects the same rules as the Council
try:
    from federation_heart.clients.constitution import get_model_client, get_env_client
    FEDERATION_ACTIVE = True
except ImportError:
    FEDERATION_ACTIVE = False
    logging.warning("⚠️ Federation Heart not found. Brain functions offline.")

logger = logging.getLogger("omni.core.brain")


class OmniBrain:
    """
    The Intelligence Layer for the Tricorder.
    
    Leverages Federation Constitution for model selection and auth.
    This is NOT a hardcoded LLM - it's a Constitutional Client.
    
    Pattern: "Ask the Constitution which model to use, then use it."
    """
    
    def __init__(self):
        """Initialize Brain by connecting to Constitution Pillar."""
        self.model_client = get_model_client() if FEDERATION_ACTIVE else None
        self.env_client = get_env_client() if FEDERATION_ACTIVE else None
        self._federation_active = FEDERATION_ACTIVE
        
    def analyze(self, scan_result: Dict[str, Any], prompt: str = None) -> str:
        """
        Analyze a scan result using the Federation's preferred model.
        
        Args:
            scan_result: Census/scan data from Omni scanners
            prompt: Optional custom analysis prompt
            
        Returns:
            AI-generated analysis of the scan data
        """
        if not self._federation_active:
            return (
                "❌ Federation Heart not found. Brain functions offline.\n"
                "Install federation_heart package to enable AI analysis."
            )

        # 1. Select Model (The Diamond Fallback)
        # We prefer Flash models for high-volume scan analysis
        model_id = self._select_model()
        if not model_id:
            return "❌ No suitable model found in Constitution configuration"
        
        # 2. Get Credentials
        api_key = self._get_api_key(model_id)
        if not api_key:
            return f"❌ Missing API Key for model {model_id}"

        # 3. Construct Context (The 'Prompt Engineering' part)
        context_str = self._build_context(scan_result)
        
        system_prompt = (
            "You are OMNI, the Federation's Science Officer.\n"
            "Analyze the following infrastructure scan data.\n"
            "Identify patterns, risks, and architectural anomalies.\n"
            "Be precise, technical, and concise."
        )
        
        user_message = prompt if prompt else "Provide a structural analysis of this scan."

        # 4. Inference (The Spark)
        logger.info(f"🧠 Thinking with {model_id}...")
        
        try:
            response = self._call_model(model_id, api_key, system_prompt, context_str, user_message)
            return response
        except Exception as e:
            logger.error(f"Brain inference failed: {e}")
            return f"❌ Analysis failed: {str(e)}"
    
    def _select_model(self) -> Optional[str]:
        """
        Select best model for scan analysis.
        
        Pattern: Diamond Fallback (prefer Flash for high-volume analysis)
        """
        if not self.model_client:
            return None
            
        # Try to resolve preferred model with fallback chain
        try:
            model_id = self.model_client.resolve(
                "gemini-2.0-flash-thinking-exp-1219",
                fallback_chain=[
                    "gemini-2.0-flash-exp",
                    "gemini-exp-1206",
                    "gemini-1.5-flash-latest"
                ]
            )
            return model_id
        except Exception as e:
            logger.error(f"Model selection failed: {e}")
            return None
    
    def _get_api_key(self, model_id: str) -> Optional[str]:
        """Get API key for selected model from Constitution."""
        if not self.model_client or not self.env_client:
            return None
            
        try:
            model_info = self.model_client.get_model(model_id)
            if not model_info:
                return None
                
            # Map provider to key (e.g., GOOGLE → GOOGLE_API_KEY)
            provider = model_info.provider.value.upper()
            api_key_name = f"{provider}_API_KEY"
            api_key = self.env_client.get(api_key_name)
            
            if not api_key:
                logger.warning(f"Missing API Key: {api_key_name}")
                
            return api_key
        except Exception as e:
            logger.error(f"Failed to get API key: {e}")
            return None
    
    def _build_context(self, scan_result: Dict[str, Any]) -> str:
        """
        Build context string from scan result.
        
        Truncates if too large (avoid token overflow).
        """
        context_str = json.dumps(scan_result, indent=2)
        
        # Truncate if over 100KB (approximately 25k tokens)
        if len(context_str) > 100000:
            context_str = context_str[:100000] + "\n...[TRUNCATED]..."
            logger.warning("Context truncated to 100KB")
            
        return context_str
    
    def _call_model(
        self, 
        model_id: str, 
        api_key: str, 
        system_prompt: str, 
        context: str, 
        user_message: str
    ) -> str:
        """
        Call the LLM with constructed prompt.
        
        NOTE: This is currently a STUB. To activate:
        1. Install: pip install google-generativeai
        2. Uncomment implementation below
        3. Or use litellm for provider-agnostic calls
        """
        
        # --- STUB FOR ACTUAL API CALL ---
        # This is where the real inference happens
        
        logger.info(f"Would call {model_id} with:")
        logger.info(f"  System: {system_prompt[:100]}...")
        logger.info(f"  Context: {len(context)} chars")
        logger.info(f"  User: {user_message}")
        
        # MOCK RESPONSE
        return (
            f"[MOCK ANALYSIS via {model_id}]\n"
            f"Analysis of {len(context)} bytes of scan data.\n"
            f"System appears nominal.\n\n"
            f"To activate real AI analysis:\n"
            f"1. pip install google-generativeai\n"
            f"2. Uncomment implementation in omni/core/brain.py\n"
            f"3. Ensure GOOGLE_API_KEY in federation_heart/.env"
        )
        
        # --- REAL IMPLEMENTATION (UNCOMMENT TO ACTIVATE) ---
        """
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_id)
        
        # Construct full prompt
        full_prompt = f"{system_prompt}\n\n{context}\n\n{user_message}"
        
        response = model.generate_content(full_prompt)
        return response.text
        """


# Singleton
_brain = None


def get_brain() -> OmniBrain:
    """Get singleton Brain instance."""
    global _brain
    if _brain is None:
        _brain = OmniBrain()
    return _brain
