Objetivo de la Prueba
Evaluar la capacidad del candidato para diseñar, implementar y optimizar un sistema RAG utilizando técnicas modernas de recuperación y generación de texto.


Parte 1: Ingesta y Procesamiento de Datos

Obtención de datos:
Tarea: Descarga un conjunto de documentos de una fuente abierta (puede ser un conjunto de artículos, documentación técnica o cualquier dataset textual).
Procesa los datos eliminando ruido y asegurando que sean utilizables en un sistema de búsqueda.
En mi caso: tengo descargada documentación entera de la librería Chainlit. Para reducir el tamaño del texto más adelante (teniendo en cuenta que el texto está en inglés), no estaría mal eliminar las stop words o algo para reducir el tamaño del texto pero no perder contexto ni lo importante.


Base de datos vectorial:
Tarea: Usa una base de datos vectorial (ej. FAISS, Elasticsearch, Weaviate o ChromaDB) para indexar los documentos con embeddings generados por un modelo de lenguaje (ej. OpenAI, Hugging Face, etc.).
En mi caso: voy a usar Qdrant Cloud como base de datos vectorial. Para generar los embeddings quiero utilizar algún modelo gratis de la librería transformers.


Parte 2: Recuperación de Información
Consulta y Recuperación:
Tarea: Implementa un mecanismo para recuperar los documentos más relevantes según una consulta dada.
En mi caso: lo haré mediante Qdrant con la similitud del coseno, pero si consideras que puede funcionar mejor, podemos utilizar la distancia euclidiana.


Parte 3: Generación de Respuestas
Integración con LLM:
Tarea: Implementa un modelo de lenguaje para generar respuestas utilizando los documentos recuperados como contexto.
Puedes usar modelos como GPT-4, Llama, Mistral o cualquier modelo open-source compatible.
En mi caso: ayudame a implementar algún modelo open-source compatible como pueden ser deep-seekk o alguno de la librería transformers pero con la temperatura al 0.10 para que responda en base al contexto que obtenga sin alucinar.


Parte 4: Creación de un frontend
Tarea: Streamlit / Gradio / Chainlit:
En mi caso: Voy a utilizar Chainlit.