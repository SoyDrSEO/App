import streamlit as st
import subprocess
import sys
import requests
from PIL import Image
from io import BytesIO
import time
from tenacity import retry, stop_after_attempt, wait_random_exponential

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Instalar dependencias
install("streamlit")
install("groq")
install("requests")
install("pillow")
install("tenacity")
install("openai")

from groq import Groq
import openai

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def verificar_api_together(api_key):
    openai.api_key = api_key
    openai.api_base = "https://api.together.xyz/v1"
    try:
        openai.ChatCompletion.create(
            model="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=10
        )
        return True
    except Exception as e:
        st.error(f"Error al verificar API de Together: {str(e)}")
        return False

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def verificar_api_groq(api_key):
    client = Groq(api_key=api_key)
    try:
        client.chat.completions.create(
            messages=[{"role": "user", "content": "Test"}],
            model="llama3-groq-70b-8192-tool-use-preview",
            max_tokens=10
        )
        return True
    except Exception as e:
        st.error(f"Error al verificar API de Groq: {str(e)}")
        return False

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def reescribir_titulo(titulo, api_tipo, modelo, api_key):
    prompt = f"Reescribe este título en formato H1 en español de manera pegajosa y que cree duda para seguir leyendo el artículo. Proporciona solo un título reescrito sin explicaciones adicionales: {titulo}"
    try:
        if api_tipo == "Together":
            openai.api_key = api_key
            openai.api_base = "https://api.together.xyz/v1"
            respuesta = openai.ChatCompletion.create(
                model=modelo,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.7
            )
            return respuesta.choices[0].message.content.strip()
        elif api_tipo == "Groq":
            client = Groq(api_key=api_key)
            respuesta = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=modelo,
                temperature=0.7,
                max_tokens=50,
            )
            return respuesta.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error al reescribir título: {str(e)}")
        return titulo  # Devuelve el título original si hay un error

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def generar_articulo(titulo, prompt, api_tipo, modelo, api_key):
    prompt_completo = f"{prompt}\n\nTítulo: {titulo}\n\nRecuerda:\n1. El artículo debe tener entre 3 y 5 secciones.\n2. El total de palabras debe estar entre 1800 y 2100.\n3. En los primeros párrafos, responde a la intención de búsqueda implícita en el título.\n4. Asegúrate de que cada H2 o H3 esté completo y bien desarrollado.\n5. Incluye listas y tablas para hacer el texto más dinámico y fácil de leer.\n6. Las respuestas a las preguntas frecuentes deben ser extensas y detalladas, con al menos 5 párrafos cada una."
    try:
        if api_tipo == "Together":
            openai.api_key = api_key
            openai.api_base = "https://api.together.xyz/v1"
            respuesta = openai.ChatCompletion.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": "Eres un redactor experto en SEO."},
                    {"role": "user", "content": prompt_completo}
                ],
                max_tokens=8000,
                temperature=0.7
            )
            return respuesta.choices[0].message.content
        elif api_tipo == "Groq":
            client = Groq(api_key=api_key)
            respuesta = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Eres un redactor experto en SEO."},
                    {"role": "user", "content": prompt_completo}
                ],
                model=modelo,
                temperature=0.7,
                max_tokens=8000,
            )
            return respuesta.choices[0].message.content
    except Exception as e:
        st.error(f"Error al generar artículo: {str(e)}")
        return f"No se pudo generar el artículo debido a un error: {str(e)}"

def generar_html(titulo, contenido):
    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{titulo}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #444; margin-top: 30px; }}
            p {{ margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <h1>{titulo}</h1>
        {contenido}
        <p>No olvides dejar tu comentario y leer más en nuestro blog.</p>
    </body>
    </html>
    """
    return html

# Configuración de la página
st.set_page_config(page_title="Generador de Artículos IA", layout="wide", initial_sidebar_state="expanded")

# Estilos personalizados
st.markdown("""
<style>
    body { color: #000080; background-color: white; }
    .stApp { background-color: white; }
    .main { padding: 2rem; }
    .stButton>button { color: white; background-color: #000080; border: none; border-radius: 5px; padding: 0.5rem 1rem; font-weight: bold; transition: all 0.3s; }
    .stButton>button:hover { background-color: #F2522E; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { border-color: #000080; border-radius: 5px; }
    .stSelectbox>div>div>select { border-color: #000080; border-radius: 5px; }
    h1, h2, h3 { color: #000080; }
    .stAlert { background-color: rgba(0, 0, 128, 0.1); color: #000080; }
    .sidebar .sidebar-content { background-color: #f0f2f6; }
    .css-1d391kg { padding-top: 3.5rem; }
</style>
""", unsafe_allow_html=True)

# Cargar y mostrar el logotipo con enlace
logo_url = "https://momentumimpulse.com/wp-content/uploads/2024/08/Momentum-Impulse-1.png"
website_url = "https://momentumimpulse.com"
st.markdown(f'<a href="{website_url}" target="_blank"><img src="{logo_url}" width="500"></a>', unsafe_allow_html=True)

st.title("🤖 Generador de Artículos con IA")

col1, col2 = st.columns([2,1])

with col1:
    st.markdown("## 📝 Ingreso de Títulos")
    
    # Añadir un botón de ayuda
    titulo_help = st.button("❓ Cómo ingresar títulos")
    if titulo_help:
        st.info("Ingresa cada título en una línea separada. Puedes ingresar múltiples títulos para generar varios artículos a la vez.")
    
    titulos = st.text_area("Ingresa los títulos (uno por línea)", height=150)

with col2:
    st.markdown("## ⚙️ Configuración")
    api_tipo = st.selectbox("Selecciona el tipo de API", ["Together", "Groq"])

    # Simplificación de los modelos
    modelo_options = {
        "Together": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "Groq": "llama3-groq-70b-8192-tool-use-preview",
    }

    modelo = modelo_options[api_tipo]

    api_key = st.text_input("Ingresa tu API Key", type="password")

    if api_key:
        if api_tipo == "Together":
            if verificar_api_together(api_key):
                st.success("✅ API Key de Together verificada")
            else:
                st.error("❌ API Key de Together inválida")
        elif api_tipo == "Groq":
            if verificar_api_groq(api_key):
                st.success("✅ API Key de Groq verificada")
            else:
                st.error("❌ API Key de Groq inválida")

st.markdown("## 🖋️ Configuración del Prompt")
usar_prompt_default = st.checkbox("Usar prompt predeterminado", value=True)
if not usar_prompt_default:
    prompt = st.text_area("Ingresa tu prompt personalizado")
else:
    prompt = """
    Eres un redactor nativo en español y escribes de manera neutral solo en español. Para el título H1 proporcionado, crea un artículo orientado al SEO siguiendo estas instrucciones:

    1. Escribe una introducción de 2-3 párrafos basada en el título H1, respondiendo a la intención de búsqueda implícita (NO USAR LA PALABRA INTRODUCCION).
    2. Genera 5 subtítulos H2 relacionados con el tema principal. Coloca cada subtítulo en etiquetas HTML <h2></h2>.
    3. Desarrolla cada subtítulo H2 con 5 párrafos de contenido detallado, asegurándote de que cada sección esté completa.
    4. Utiliza etiquetas HTML <strong></strong> para resaltar las frases más características o importantes en cada sección.
    5. Incluye al menos una lista con viñetas <ul><li> y una tabla <table> para hacer el contenido más dinámico.
    6. Crea 7 Preguntas Frecuentes en español (no usar otro idioma) relacionadas con el tema. Formatea cada pregunta como subtítulo H3 en HTML <h3></h3> y responde inmediatamente después con al menos 5 párrafos extensos y detallados.
    7. No incluyas saludos, conclusiones o texto adicional fuera de lo solicitado.
    8. Escribe todo el contenido en español, sin usar otros idiomas.
    9. Asegúrate de que el artículo tenga una longitud total de 1800 a 2100 palabras.

    Asegúrate de que el contenido sea informativo, bien estructurado y optimizado para SEO.
    """

reescribir_titulos = st.checkbox("Reescribir títulos", value=False)

if st.button("🚀 Generar Artículos"):
    if api_key and titulos:
        titulos_lista = [titulo.strip() for titulo in titulos.split("\n") if titulo.strip()]
        if not titulos_lista:
            st.warning("Por favor, ingresa al menos un título.")
        else:
            progress_bar = st.progress(0)
            for i, titulo in enumerate(titulos_lista):
                with st.spinner(f"Generando artículo {i+1} de {len(titulos_lista)}: {titulo}"):
                    try:
                        if reescribir_titulos:
                            titulo = reescribir_titulo(titulo, api_tipo, modelo, api_key)
                        
                        contenido = generar_articulo(titulo, prompt, api_tipo, modelo, api_key)
                        contenido += "\n\n<p>No olvides dejar tu comentario y leer más en nuestro blog.</p>"
                        html_contenido = generar_html(titulo, contenido)
                        
                        st.subheader(f"📄 {titulo}")
                        st.markdown(contenido, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label=f"📥 Descargar HTML",
                                data=html_contenido,
                                file_name=f"{titulo.replace(' ', '_')}.html",
                                mime="text/html"
                            )
                        with col2:
                            st.download_button(
                                label=f"📥 Descargar Markdown",
                                data=contenido,
                                file_name=f"{titulo.replace(' ', '_')}.md",
                                mime="text/markdown"
                            )
                        
                        st.markdown("---")
                    except Exception as e:
                        st.error(f"Error al generar el artículo '{titulo}': {str(e)}")
                progress_bar.progress((i + 1) / len(titulos_lista))
            
            st.success("¡Proceso de generación de artículos completado!")
    else:
        st.warning("Por favor, asegúrate de ingresar una API Key válida y al menos un título.")

# Información de los modelos
st.sidebar.markdown("### Modelos utilizados")
# Información en el lateral
st.sidebar.markdown("### Acerca de")
st.sidebar.markdown("[🌟 Web App desarrollada por Momentum Impulse](https://momentumimpulse.com)")
st.sidebar.markdown("Para poder usar, requieres tener una API de:")
st.sidebar.markdown("- [Together.ai](https://api.together.xyz/settings/api-keys)")
st.sidebar.markdown("- [Groq](https://groq.com/)")

# Información de los modelos
st.sidebar.markdown("### Modelos utilizados")
st.sidebar.markdown("- Together usa Meta Llama 3.1-70B")
st.sidebar.markdown("- Groq usa llama3-groq-70b-8192-tool-use-preview")

if __name__ == "__main__":
    pass