import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Opcional: instalar html2text si se desea utilizar formato Markdown
try:
    import html2text
except ImportError:
    html2text = None

# Configuración: URL base, directorio de salida, formato deseado ('txt' o 'md') y tiempo de espera (en segundos)
BASE_URL = "https://docs.chainlit.io/"
OUTPUT_DIR = "chainlit_docs"
OUTPUT_FORMAT = "txt"  # Cambia a "md" para Markdown
REQUEST_DELAY = 0.1  # Tiempo de espera entre peticiones en segundos

visited = set()

def sanitize_path(url: str) -> str:
    """
    Convierte una URL en una ruta de archivo segura, asignando la extensión
    correspondiente según el formato de salida.
    """
    parsed = urlparse(url)
    path = parsed.path
    if path.endswith("/"):
        path += "index"
    ext = ".txt" if OUTPUT_FORMAT == "txt" else ".md"
    if not os.path.splitext(path)[1]:
        path += ext
    else:
        path = os.path.splitext(path)[0] + ext
    if path.startswith("/"):
        path = path[1:]
    return os.path.join(OUTPUT_DIR, path)

def convert_content(content: str) -> str:
    """
    Extrae el contenido del div con id 'content-area' y lo convierte
    a plain text o Markdown según se requiera.
    """
    soup = BeautifulSoup(content, "html.parser")
    content_div = soup.find("div", id="content-area")
    if content_div is None:
        print("Advertencia: No se encontró el div con id 'content-area'. Se usará todo el contenido.")
        content_div = soup

    if OUTPUT_FORMAT == "txt":
        return content_div.get_text(separator="\n")
    elif OUTPUT_FORMAT == "md":
        if html2text is None:
            raise ImportError("El módulo html2text es requerido para convertir a Markdown. Instálalo usando: pip install html2text")
        h = html2text.HTML2Text()
        h.ignore_links = False  # Ajusta esta opción según necesites
        h.ignore_images = True
        return h.handle(str(content_div))
    else:
        raise ValueError("Formato de salida no soportado. Usa 'txt' o 'md'.")

def save_page(url: str, content: str):
    """
    Convierte y guarda el contenido descargado (solo lo que está en 'content-area')
    en un archivo cuya ruta se deriva de la URL.
    """
    converted = convert_content(content)
    path = sanitize_path(url)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(converted)
    print(f"Guardado: {url} -> {path}")

def get_internal_links(url: str, content: str) -> set:
    """
    Extrae los enlaces internos que pertenecen al mismo dominio que BASE_URL.
    """
    soup = BeautifulSoup(content, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        absolute_url = urljoin(url, href)
        if urlparse(absolute_url).netloc == urlparse(BASE_URL).netloc:
            cleaned_url = absolute_url.split("#")[0].split("?")[0]
            links.add(cleaned_url)
    return links

def crawl(url: str):
    """
    Función recursiva que descarga la página, guarda el contenido dentro de 'content-area'
    y sigue los enlaces internos, respetando un tiempo de espera entre peticiones.
    """
    if url in visited:
        return
    visited.add(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
        content = response.text
        save_page(url, content)
        # Extraer enlaces internos y recorrerlos
        links = get_internal_links(url, content)
        for link in links:
            if link not in visited:
                time.sleep(REQUEST_DELAY)  # Espera antes de la siguiente petición
                crawl(link)
    except requests.RequestException as e:
        print(f"Error al acceder a {url}: {e}")

if __name__ == "__main__":
    print(f"Iniciando la descarga de la documentación desde {BASE_URL}")
    crawl(BASE_URL)
    print("Descarga completada.")
