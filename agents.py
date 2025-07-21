from langchain.llms import ollama
from langchain.prompts import PromptTemplate
from prompts import content_templates

#Uso de modelo mistral en local
llm = ollama.Ollama(model="mistral")

def generate_content(tipo: str, tema: str) -> str:
    if tipo not in content_templates:
        return "Tipo de contenido no válido"
    
    template = content_templates[tipo]
    prompt = PromptTemplate.from_template(template)
    final_prompt = prompt.format(topic=tema)
    
    return llm.predict(final_prompt)