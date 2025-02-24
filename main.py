import os
import string
import nltk
from nltk.corpus import stopwords
from typing import List, Dict
from dotenv import load_dotenv

# Cargar las variables desde el archivo .env
load_dotenv()

# Descargar stopwords de NLTK (solo la primera vez)
nltk.download('stopwords')

##########################################
# PARTE 1: INGESTA Y PROCESAMIENTO DE DATOS
##########################################

def process_text(text: str) -> str:
    """
    Procesa el texto: lo convierte a minúsculas, elimina signos de puntuación 
    y filtra las stop words en inglés.
    """
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = text.split()
    nltk_stopwords = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in nltk_stopwords]
    return ' '.join(filtered_tokens)

def load_documents(directory: str) -> List[Dict]:
    """
    Recorre recursivamente el directorio 'chainlit_docs' para cargar los archivos TXT.
    Cada documento se almacena con metadata: 'topic' (nombre de la carpeta), 
    'file_name' y 'text' (procesado).
    """
    docs = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                # Se asume que el nombre del tema es el nombre de la carpeta
                topic = os.path.basename(os.path.dirname(file_path))
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                processed_text = process_text(text)
                docs.append({
                    'topic': topic,
                    'file_name': file,
                    'text': processed_text
                })
    return docs

##########################################
# PARTE 2: INDEXACIÓN CON QDRANT CLOUD
##########################################

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance

# Cargamos un modelo de embeddings gratuito
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Configuración de Qdrant Cloud (reemplaza con tus credenciales)
QDRANT_ENDPOINT = os.getenv('QDRANT_ENDPOINT')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
COLLECTION_NAME = "chainlit_docs"

# Inicialización del cliente de Qdrant
qdrant_client = QdrantClient(url=QDRANT_ENDPOINT, api_key=QDRANT_API_KEY)

def create_collection_if_not_exists():
    """
    Verifica si la colección existe en Qdrant; de lo contrario, la crea 
    usando la dimensión del vector del modelo y la distancia COSINE.
    """
    try:
        qdrant_client.get_collection(collection_name=COLLECTION_NAME)
    except Exception:
        vector_size = embedding_model.get_sentence_embedding_dimension()
        qdrant_client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )

def index_documents(docs: List[Dict]):
    """
    Para cada documento, se genera su embedding y se indexa en Qdrant junto con su metadata.
    """
    points = []
    for i, doc in enumerate(docs):
        embedding = embedding_model.encode(doc['text']).tolist()
        point = PointStruct(
            id=i,
            vector=embedding,
            payload={
                'topic': doc['topic'],
                'file_name': doc['file_name'],
                'text': doc['text']
            }
        )
        points.append(point)
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)

##########################################
# PARTE 3: RECUPERACIÓN DE INFORMACIÓN
##########################################

def retrieve_documents(query: str, top_k: int = 5) -> List[Dict]:
    """
    Genera el embedding de la consulta y realiza una búsqueda en Qdrant usando
    similitud coseno, devolviendo los documentos más relevantes.
    """
    query_embedding = embedding_model.encode(query).tolist()
    search_result = qdrant_client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k
    )
    results = []
    for point in search_result:
        results.append({
            'id': point.id,
            'score': point.score,
            'payload': point.payload
        })
    return results

##########################################
# PARTE 4: GENERACIÓN DE RESPUESTAS CON LLM
##########################################

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Selecciona un modelo open-source para generación (ejemplo: gpt2; puedes cambiarlo)
LLM_MODEL_NAME = "gpt2"
tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(LLM_MODEL_NAME)

# Configuramos la pipeline de generación con temperatura 0.10
generator = pipeline("text-generation", model=model, tokenizer=tokenizer, 
                     config={"temperature": 0.1})

def generate_response(query: str, context_docs: List[Dict]) -> str:
    """
    Combina el contexto obtenido (documentos recuperados) y la consulta para 
    formar un prompt y generar una respuesta usando el LLM.
    """
    # Se extrae el texto de cada documento
    context_texts = [doc['payload']['text'] for doc in context_docs]
    combined_context = "\n".join(context_texts)
    
    prompt = f"Contexto:\n{combined_context}\n\nPregunta: {query}\nRespuesta:"
    
    output = generator(prompt, max_length=200, num_return_sequences=1)
    # Se extrae la respuesta eliminando el prompt del output
    answer = output[0]['generated_text'][len(prompt):].strip()
    return answer

##########################################
# PARTE 5: FRONTEND CON CHAINLIT
##########################################

import chainlit as cl

@cl.on_chat_start
def start():
    cl.send_message("¡Bienvenido al sistema RAG para la documentación de Chainlit! Por favor, ingresa tu consulta sobre Chainlit.")

@cl.on_message
async def main(message: str):
    """
    Al recibir una consulta, se recuperan los documentos relevantes y se 
    genera una respuesta que se envía al usuario.
    """
    # Se recuperan los documentos más relevantes (se asume que la consulta está relacionada con Chainlit)
    results = retrieve_documents(query=message, top_k=5)
    answer = generate_response(query=message, context_docs=results)
    cl.send_message(answer)

##########################################
# EJECUCIÓN PRINCIPAL
##########################################

if __name__ == "__main__":
    # Esta parte se ejecuta una única vez para indexar los documentos. 
    # Asegúrate de que los documentos de 'chainlit_docs' estén correctamente ubicados.
    create_collection_if_not_exists()
    docs = load_documents("chainlit_docs")
    index_documents(docs)
    
    # Inicia la aplicación Chainlit.
    # Ejecuta este script con: chainlit run nombre_del_script.py
    cl.run()