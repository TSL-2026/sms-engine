# ============================================================
# File: aviation/client.py
# Version: v1.1.0
#
# Module: OpenRouter API Client Wrapper
# ============================================================

import os
import requests
import json


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

        # Debug logging (remove in production)
        print(f"DEBUG: Sending request to OpenRouter")
        print(f"DEBUG: Model: {model_to_use}")
        print(f"DEBUG: Messages count: {len(messages)}")

        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=30  # Add timeout to prevent hanging
            )

            # Debug response
            print(f"DEBUG: Response status code: {response.status_code}")

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


# Optional: Test the client if run directly
if __name__ == "__main__":
    # Test code
    print("Testing OpenRouter Client...")
    try:
        client = OpenRouterClient()
        print("✓ Client initialized successfully")
        print(f"✓ Default model: {client.default_model}")
        
        # Uncomment to test actual API call (requires API key)
        # response = client.chat_simple(
        #     "Say 'Hello, Aviation Safety System!'",
        #     system_message="You are a helpful assistant."
        # )
        # print(f"✓ API Response: {response}")
        
    except Exception as e:
        print(f"✗ Error: {e}")