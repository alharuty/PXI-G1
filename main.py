import streamlit as st
from agents import generate_content

st.set_page_config(
    page_title="Generador de contenido", layout="centered")
st.title("📝 Generador de Contenido IA (offline y gratuito)")

st.markdown("Crea tweets, posts de LinkedIn, emails, descripciones de productos, etc.")

tipo = st.selectbox("Selecciona el tipo de contenido:", ("tweet", "linkedin", "email", "descripcion"))
tema = st.text_area("Tema del contenido", placeholder="Ej: rebajas de verano en zapatillas", height=100)

if st.button("Generar contenido"):
    if not tema.strip():
        st.warning("Por favor, ingresa un tema para generar el contenido.")
    else:
        resultado = generate_content(tipo, tema)
        st.subheader("✍️ Resultado generado:")
        st.write(resultado)

