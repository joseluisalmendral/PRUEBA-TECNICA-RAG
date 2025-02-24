# 📘 README - Configuración y Ejecución del Proyecto

## 🛠️ Requisitos Previos
Antes de ejecutar el proyecto, asegúrate de contar con lo siguiente:

### 🔹 Instalación de Dependencias
1. **Python 3.8+** instalado en tu máquina.
2. **Virtualenv** (opcional pero recomendado):
   ```bash
   pip install virtualenv
   ```
3. **Dependencias del proyecto** (instaladas en un entorno virtual):
   ```bash
   python -m venv env
   source env/bin/activate  # Para macOS/Linux
   env\Scripts\activate  # Para Windows
   pip install -r requirements.txt
   ```

---
## ⚙️ Configuración de API Keys (OpenAI y Qdrant)
### 🔹 Creación y Configuración de Claves de API

#### 1️⃣ OpenAI API Key
Si no tienes una cuenta en OpenAI:
1. Regístrate en [OpenAI](https://platform.openai.com/signup/).
2. Ve a la sección de [API Keys](https://platform.openai.com/account/api-keys).
3. Genera una nueva API Key y guárdala en un archivo `.env`:
   ```plaintext
   OPENAI_API_KEY=tu_api_key_de_openai
   ```

#### 2️⃣ Qdrant API Key
Si no tienes una cuenta en Qdrant:
1. Regístrate en [Qdrant Cloud](https://cloud.qdrant.io/).
2. Crea una nueva instancia y copia la URL del endpoint y la API Key.
3. Agrega las siguientes variables en `.env`:
   ```plaintext
   QDRANT_ENDPOINT=tu_endpoint_qdrant
   QDRANT_API_KEY=tu_api_key_qdrant
   ```

---
## 🚀 Ejecución del Proyecto

### 1️⃣ Ejecutar el Servidor
Ejecuta el siguiente comando para iniciar el sistema RAG con Chainlit:

💡 *Nota:* Si es la primera ejecución y no existen ni la documentación ni la colección en Qdrant, se crearán automáticamente antes de lanzar Chainlit.
```bash
chainlit run main.py
```

### 2️⃣ Interactuar con la Aplicación
Una vez iniciado, accede a la interfaz de usuario de Chainlit a través del navegador en la siguiente dirección:
```plaintext
http://localhost:8000
```

---
## 📂 Estructura del Repositorio
```
📁 tu_repositorio/
│-- 📁 chainlit_docs/          # Documentación descargada de Chainlit
│-- 📁 public/                 # Archivos CSS y temas personalizados
│   │-- stylesheet.css         # Personalización de estilos
│   │-- theme.json             # Configuración del tema de Chainlit
│-- 📄 .env                    # Variables de entorno con claves de API
│-- 📄 chainlit.md              # Pantalla de bienvenida de Chainlit
│-- 📄 download_chainlit_docs.py # Script para descargar la documentación
│-- 📄 main.py                  # Script principal con la lógica del sistema RAG
│-- 📄 requirements.txt          # Dependencias necesarias para el entorno
│-- 📄 README.md                # Este archivo con instrucciones detalladas
```

---
## 📢 Notas Adicionales
- Si necesitas cambiar la colección en Qdrant, edita la variable `COLLECTION_NAME` en `main.py`.
- Puedes personalizar el tema de la aplicación modificando `public/theme.json` y `public/stylesheet.css`.
- Para desactivar la pantalla de bienvenida de Chainlit, vacía el contenido de `chainlit.md`.

---
¡Listo! Ahora puedes comenzar a usar el sistema RAG con Chainlit. 🚀

