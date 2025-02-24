import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import deque
from tqdm import tqdm
from colorama import init, Fore, Style

# Inicializar colorama para que los colores se reseteen automáticamente
init(autoreset=True)

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
        print(Fore.YELLOW + "Advertencia: No se encontró el div con id 'content-area'. Se usará todo el contenido.")
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
    print(Fore.BLUE + f"Guardado: {url} -> {path}")

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

def crawl_all(start_url: str):
    """
    Función iterativa que descarga la página, guarda el contenido dentro de 'content-area'
    y sigue los enlaces internos, mostrando una barra de progreso.
    """
    pending = deque([start_url])
    pbar = tqdm(total=1, desc="Progreso", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} urls")
    while pending:
        url = pending.popleft()
        if url in visited:
            continue
        visited.add(url)
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text
            save_page(url, content)
            links = get_internal_links(url, content)
            for link in links:
                if link not in visited and link not in pending:
                    pending.append(link)
                    pbar.total += 1  # Incrementa el total de URLs a procesar
        except requests.RequestException as e:
            print(Fore.RED + f"Error al acceder a {url}: {e}")
        pbar.update(1)
        pbar.refresh()
        time.sleep(REQUEST_DELAY)
    pbar.close()

if __name__ == "__main__":
    # Mensaje de inicio con colores y espacios para resaltar la situación inicial
    print("\n" + Fore.YELLOW + Style.BRIGHT + "==========================================")
    print(Fore.YELLOW + Style.BRIGHT + "¡No se encontró documentación previa!")
    print(Fore.YELLOW + Style.BRIGHT + "Iniciando la descarga de la documentación desde:")
    print(Fore.YELLOW + Style.BRIGHT + f"{BASE_URL}")
    print(Fore.YELLOW + Style.BRIGHT + "==========================================\n")
    
    crawl_all(BASE_URL)
    
    # Mensaje final indicando que la descarga se completó
    print("\n" + Fore.GREEN + Style.BRIGHT + "==========================================")
    print(Fore.GREEN + Style.BRIGHT + "Descarga completada.")
    print(Fore.GREEN + Style.BRIGHT + "==========================================\n")
