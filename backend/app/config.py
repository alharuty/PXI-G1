from langchain_community.llms import Ollama
import requests
import os
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GroqLLM:
    def __init__(self, api_key: str, model: str = "gemma2-9b-it"):  # Cambiado el modelo
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.model = model
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def invoke(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            logger.debug(f"Sending request to Groq API with model: {self.model}")
            response = requests.post(self.endpoint, headers=headers, json=data)
            response.raise_for_status()  # Lanza excepción si hay error HTTP
            
            json_response = response.json()
            logger.debug(f"Groq API response: {json_response}")
            
            if "choices" not in json_response:
                raise ValueError(f"Unexpected API response format: {json_response}")
                
            return json_response["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            logger.error(f"Response content: {response.text if 'response' in locals() else 'No response'}")
            raise RuntimeError(f"Error calling Groq API: {str(e)}")
        except (KeyError, ValueError) as e:
            logger.error(f"Error processing API response: {str(e)}")
            raise

def get_llm(model_name: str = "llama3", provider: str = "groq"):
    # Factory function para crear instancias de LLM
    if provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        return GroqLLM(api_key=api_key)
    else:
        return Ollama(model=model_name)