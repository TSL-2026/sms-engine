# ============================================================
# File: aviation/client.py
# Version: v1.1.0
#
# Module: OpenRouter API Client Wrapper
# ============================================================

import os
import logging
import requests
import json

logger = logging.getLogger("sms.aviation.client")


class OpenRouterClient:
    """
    Simple wrapper for OpenRouter Chat Completion API.
    """

    def __init__(self, model: str = None):
        """
        Initialize OpenRouter client
        
        Args:
            model: Optional model name (defaults to OPENROUTER_MODEL env or gpt-3.5-turbo)
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")

        # Get model from parameter, then env var, then default
        self.default_model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
        
        self.url = "https://openrouter.ai/api/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # Optional: Add your site/app info for OpenRouter rankings
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Aviation Safety System"
        }

    def chat(self, messages, model=None):
        """
        Send chat completion request to OpenRouter
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Optional model override (uses default if not provided)
        
        Returns:
            API response as dict
        """
        # Use provided model or fall back to default
        model_to_use = model or self.default_model
        
        payload = {
            "model": model_to_use,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 500
        }

        logger.debug("Sending request to OpenRouter — model=%s, messages=%d", model_to_use, len(messages))

        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=30  # Add timeout to prevent hanging
            )

            logger.debug("OpenRouter response status=%d", response.status_code)

            # Handle non-200 responses
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('error', {}).get('message', error_detail)
                except:
                    pass
                
                raise Exception(f"OpenRouter API error ({response.status_code}): {error_detail}")

            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("OpenRouter API request timed out after 30 seconds")
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to connect to OpenRouter API - check your internet connection")
        except Exception as e:
            raise Exception(f"OpenRouter API request failed: {str(e)}")

    def chat_simple(self, user_message, system_message=None, model=None):
        """
        Simplified chat method for single-turn conversations
        
        Args:
            user_message: The user's message string
            system_message: Optional system prompt
            model: Optional model override
        
        Returns:
            Response content string
        """
        messages = []
        
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": user_message})
        
        response = self.chat(messages, model)
        
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected API response format: {str(e)}")


class SmartAIClient:
    """Select optimal AI model based on scenario complexity"""

    SIMPLE_PATTERNS = ['vfr', 'day', 'clear weather', 'rested', 'familiar', 'short', 'direct']
    COMPLEX_PATTERNS = ['imc', 'night', 'mountain', 'emergency', 'fatigue', 'mechanical',
                        'icing', 'wind shear', 'crosswind', 'low fuel', 'maintenance',
                        'deferred', 'pressure', 'illness', 'medication', 'alcohol', 'stress']

    def __init__(self, base_client: OpenRouterClient = None):
        self.client = base_client or OpenRouterClient()

    def select_model(self, scenario: str) -> str:
        scenario_lower = scenario.lower()

        if any(p in scenario_lower for p in self.SIMPLE_PATTERNS):
            return "claude-3-haiku-20240307"

        complexity = sum(p in scenario_lower for p in self.COMPLEX_PATTERNS)
        if complexity >= 3:
            return "claude-3-sonnet-20240229"
        if complexity >= 1:
            return "claude-3-haiku-20240307"

        return "claude-3-haiku-20240307"

    def get_assessment(self, scenario: str) -> str:
        model = self.select_model(scenario)
        system_prompt = (
            "You are an aviation safety expert. Analyze the flight scenario and "
            "provide a concise risk assessment. Include: hazards identified, "
            "risk level, and recommended mitigations."
        )
        return self.client.chat_simple(scenario, system_message=system_prompt, model=model)


# Optional: Test the client if run directly
if __name__ == "__main__":
    import sys

    def test_model_selection():
        client = SmartAIClient.__new__(SmartAIClient)

        assert client.select_model("Day VFR, familiar airport") == "claude-3-haiku-20240307"
        assert client.select_model("Night IMC, mountain terrain, low fuel") == "claude-3-sonnet-20240229"
        assert client.select_model("Clear weather, short flight") == "claude-3-haiku-20240307"
        assert client.select_model("Emergency descent, engine failure, night, IMC") == "claude-3-sonnet-20240229"
        print("All model selection tests passed!")

    print("Testing SmartAIClient...")
    try:
        test_model_selection()
        client = OpenRouterClient()
        print(f"✓ Base client: {client.default_model}")
        smart = SmartAIClient(client)
        scenario = "Day VFR, pilot rested"
        model = smart.select_model(scenario)
        print(f"✓ Scenario: '{scenario}' → {model}")
        scenario2 = "Night IMC, mountain, low fuel, mechanical issue"
        model2 = smart.select_model(scenario2)
        print(f"✓ Scenario: '{scenario2}' → {model2}")
        print("✓ All tests passed!")
    except Exception as e:
        print(f"✗ Error: {e}")