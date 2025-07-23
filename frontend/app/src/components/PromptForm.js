import React, { useState } from 'react';
import axios from 'axios';

function PromptForm() {
  const [prompt, setPrompt] = useState('');
  const [language, setLanguage] = useState('es');
  const [response, setResponse] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/generate', {
        prompt,
        language,
      });
      setResponse(res.data.response);
    } catch (error) {
      console.error('Error al generar respuesta:', error);
      setResponse('Ocurrió un error al procesar tu solicitud.');
    }
  };

  return (
    <div style={{ padding: '1rem' }}>
      <form onSubmit={handleSubmit}>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Escribe tu consulta sobre el mercado financiero"
          rows={6}
          cols={60}
        />
        <br />
        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="en">Inglés</option>
          <option value="es">Español</option>
          <option value="fr">Francés</option>
          <option value="it">Italiano</option>
        </select>
        <br />
        <button type="submit">Enviar</button>
      </form>

      <div style={{ marginTop: '1rem' }}>
        <h3>Respuesta del Agente:</h3>
        <p>{response}</p>
      </div>
    </div>
  );
}

export default PromptForm;
