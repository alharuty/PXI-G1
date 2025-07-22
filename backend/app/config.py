from langchain_community.llms import Ollama

def get_llm(model_name: str = "llama3") -> Ollama:
    return Ollama(model=model_name)
