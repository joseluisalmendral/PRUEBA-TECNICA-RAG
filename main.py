import os
import subprocess
import time
import string
import nltk
from nltk.corpus import stopwords
from typing import List, Dict
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct, VectorParams, Distance
import openai
import chainlit as cl
from colorama import init, Fore, Style

# Inicializar colorama para mensajes de consola con colores
init(autoreset=True)

def ensure_docs_directory(directory: str = "chainlit_docs", timeout: int = 30):
    """
    Verifica la existencia del directorio de documentación. Si no existe, ejecuta
    el script de descarga y espera hasta que se cree o se alcance el timeout.
    """
    if not os.path.exists(directory):
        print(Fore.YELLOW + Style.BRIGHT + f"\nNo se encontró el directorio '{directory}'. Iniciando descarga...\n")
        subprocess.run(["python", "download_chainlit_docs.py"], check=True)
        start_time = time.time()
        while not os.path.exists(directory) and time.time() - start_time < timeout:
            time.sleep(1)
        if not os.path.exists(directory):
            print(Fore.RED + Style.BRIGHT + f"Error: El directorio '{directory}' no se creó tras la descarga. Abortando.")
            exit(1)
        else:
            print(Fore.GREEN + Style.BRIGHT + f"\nDirectorio '{directory}' creado exitosamente.\n")
    else:
        print(Fore.GREEN + Style.BRIGHT + f"\nDirectorio '{directory}' encontrado.\n")

# Cargar variables de entorno, clave de OpenAI y recursos NLTK
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
nltk.download('stopwords')

def process_text(text: str) -> str:
    text = text.lower().translate(str.maketrans('', '', string.punctuation))
    tokens = text.split()
    nltk_stopwords = set(stopwords.words('english'))
    filtered_tokens = [word for word in tokens if word not in nltk_stopwords]
    return ' '.join(filtered_tokens)

def load_documents(directory: str) -> List[Dict]:
    docs = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)
                topic = os.path.basename(os.path.dirname(file_path))
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                docs.append({
                    'topic': topic,
                    'file_name': file,
                    'text': process_text(text)
                })
    return docs

# Configuración e inicialización de Qdrant Cloud
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
QDRANT_ENDPOINT = os.getenv('QDRANT_ENDPOINT')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY')
COLLECTION_NAME = "chainlit_docs"
qdrant_client = QdrantClient(url=QDRANT_ENDPOINT, api_key=QDRANT_API_KEY)

def create_collection_if_not_exists():
    print(Fore.CYAN + Style.BRIGHT + "\nVerificando la existencia de la colección en Qdrant...\n")
    try:
        # Intentar obtener la colección
        qdrant_client.get_collection(collection_name=COLLECTION_NAME)
        print(Fore.GREEN + Style.BRIGHT + f"La colección '{COLLECTION_NAME}' ya existe en Qdrant.\n")
    except Exception:
        print(Fore.YELLOW + Style.BRIGHT + f"La colección '{COLLECTION_NAME}' no existe. Creándola...\n")
        vector_size = embedding_model.get_sentence_embedding_dimension()
        qdrant_client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        print(Fore.GREEN + Style.BRIGHT + f"Colección '{COLLECTION_NAME}' creada exitosamente.\n")

def index_documents(docs: List[Dict]):
    print(Fore.CYAN + Style.BRIGHT + "Iniciando la indexación de documentos...\n")
    points = []
    for i, doc in enumerate(docs):
        embedding = embedding_model.encode(doc['text']).tolist()
        points.append(
            PointStruct(
                id=i,
                vector=embedding,
                payload={
                    'topic': doc['topic'],
                    'file_name': doc['file_name'],
                    'text': doc['text']
                }
            )
        )
    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(Fore.GREEN + Style.BRIGHT + "Indexación completada.\n")

def retrieve_documents(query: str, top_k: int = 5) -> List[Dict]:
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

def generate_response(query: str, context_docs: List[Dict]) -> str:
    context_texts = [doc['payload']['text'] for doc in context_docs]
    combined_context = "\n".join(context_texts)
    prompt = (
        "Utiliza la siguiente información de contexto para responder de manera precisa y concisa a la pregunta. "
        "Evita incluir menciones a usuarios o contenido irrelevante.\n\n"
        f"Contexto:\n{combined_context}\n\n"
        f"Pregunta: {query}\n\n"
        "Respuesta:"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Eres un asistente que solo responde de forma precisa y concisa utilizando únicamente el contexto proporcionado a temas relacionados con la documentacion de chainlit y el contexto proporcionado en el prompt."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=350,
        temperature=0.0,
        n=1,
    )
    return response.choices[0].message['content'].strip()

def setup():
    # Asegurar que exista el directorio de documentación
    ensure_docs_directory("chainlit_docs")
    # Verificar y crear la colección en Qdrant si es necesario
    create_collection_if_not_exists()
    # Cargar e indexar documentos
    docs = load_documents("chainlit_docs")
    index_documents(docs)

# Ejecutar la configuración inicial antes de levantar la aplicación de Chainlit
setup()

# Callback de Chainlit que se ejecuta al iniciar un chat
@cl.on_chat_start
async def on_chat_start():
    await cl.Message(content="¡Bienvenido al sistema RAG para la documentación de Chainlit! ¿En qué puedo ayudarte?").send()

# Callback de Chainlit para procesar mensajes del usuario
@cl.on_message
async def on_message(message: cl.Message):
    user_query = message.content
    results = retrieve_documents(query=user_query, top_k=5)
    answer = generate_response(query=user_query, context_docs=results)
    await cl.Message(content=answer).send()
