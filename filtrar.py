import urllib.request
import re

# Fuente: lista de iptv-org que YA está 100% en español
URL_ESPANOL = "https://iptv-org.github.io/iptv/languages/spa.m3u"
OUTPUT_FILE = "espanol_filtrado.m3u"

# Categorías a conservar y nombre de carpeta en SS IPTV
MAPA_CATEGORIAS = {
    "movies": "Cine y Películas",
    "series": "Series",
    "sports": "Deportes",
    "animation": "Animación y Anime",
    "music": "Música",
    "documentary": "Documentales",
    "science": "Ciencia",
    "entertainment": "Entretenimiento",
    "general": "TV Abierta / General",
    "comedy": "Comedia",
}

# Descartar canales intermitentes o con bloqueo regional
EXCLUIR = ["[not 24/7]", "[geo-blocked]"]

print("Descargando lista en español (spa.m3u)...")
req = urllib.request.Request(URL_ESPANOL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=60) as response:
    lineas = response.read().decode("utf-8", errors="ignore").splitlines()

canales_filtrados = ["#EXTM3U"]
guardados = 0

i = 0
while i < len(lineas):
    linea = lineas[i].strip()
    if linea.startswith("#EXTINF:"):
        bloque = [linea]
        i += 1
        # Conservar líneas intermedias (#EXTVLCOPT, etc.) hasta la URL
        while i < len(lineas) and not lineas[i].strip().startswith("http"):
            if lineas[i].strip():
                bloque.append(lineas[i].strip())
            i += 1

        if i < len(lineas):
            bloque.append(lineas[i].strip())
            texto_lower = linea.lower()

            if not any(ex in texto_lower for ex in EXCLUIR):
                match = re.search(r'group-title="([^"]*)"', linea)
                grupos_canal = [g.strip() for g in match.group(1).lower().split(";")] if match else []

                categoria_traducida = None
                for cat_ing, cat_esp in MAPA_CATEGORIAS.items():
                    if cat_ing in grupos_canal:
                        categoria_traducida = cat_esp
                        break

                if categoria_traducida:
                    bloque[0] = re.sub(
                        r'group-title="[^"]*"',
                        f'group-title="{categoria_traducida}"',
                        bloque[0],
                    )
                    canales_filtrados.extend(bloque)
                    guardados += 1
    i += 1

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(canales_filtrados) + "\n")

print(f"Listo: {guardados} canales en español guardados en '{OUTPUT_FILE}'.")
