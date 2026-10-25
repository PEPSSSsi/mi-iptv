import urllib.request
import re
from concurrent.futures import ThreadPoolExecutor

# Fuente: lista de iptv-org con canales que tienen audio en español
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

# Solo países hispanohablantes (código en el tvg-id, ej. "Canal13.cl@SD").
# Evita canales de EE.UU./otros que aparecen en spa.m3u por tener un audio
# secundario en español pero que en la práctica se ven en inglés.
PAISES_HISPANOS = {
    "es", "mx", "ar", "cl", "co", "pe", "ve", "ec", "bo", "py", "uy",
    "cr", "pa", "gt", "hn", "sv", "ni", "do", "cu", "pr", "gq",
}

# Palabras en el nombre que delatan canales en inglés
PALABRAS_INGLES = ["english", "(en)", " en)", "[en]"]

# Descartar canales intermitentes o con bloqueo regional
EXCLUIR = ["[not 24/7]", "[geo-blocked]"]

# Verificación de links
VERIFICAR_LINKS = True
TIMEOUT = 10
HILOS = 40
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def pais_de(extinf):
    m = re.search(r'tvg-id="[^".]*\.([a-z]{2})(?:@[^"]*)?"', extinf, re.I)
    return m.group(1).lower() if m else None


def link_funciona(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            if r.status >= 400:
                return False
            datos = r.read(2048)
            if url.split("?")[0].endswith(".m3u8") or b"#EXTM3U" in datos[:20]:
                return b"#EXT" in datos
            return len(datos) > 0
    except Exception:
        return False


print("Descargando lista en español (spa.m3u)...")
req = urllib.request.Request(URL_ESPANOL, headers={"User-Agent": UA})
with urllib.request.urlopen(req, timeout=60) as response:
    lineas = response.read().decode("utf-8", errors="ignore").splitlines()

candidatos = []  # (bloque, url)
descartados_pais = 0

i = 0
while i < len(lineas):
    linea = lineas[i].strip()
    if linea.startswith("#EXTINF:"):
        bloque = [linea]
        i += 1
        while i < len(lineas) and not lineas[i].strip().startswith("http"):
            if lineas[i].strip():
                bloque.append(lineas[i].strip())
            i += 1

        if i < len(lineas):
            url = lineas[i].strip()
            bloque.append(url)
            texto_lower = linea.lower()

            if any(ex in texto_lower for ex in EXCLUIR):
                i += 1
                continue
            if any(p in texto_lower for p in PALABRAS_INGLES):
                i += 1
                continue
            if pais_de(linea) not in PAISES_HISPANOS:
                descartados_pais += 1
                i += 1
                continue

            match = re.search(r'group-title="([^"]*)"', linea)
            grupos = [g.strip() for g in match.group(1).lower().split(";")] if match else []

            categoria = next((esp for ing, esp in MAPA_CATEGORIAS.items() if ing in grupos), None)
            if categoria:
                bloque[0] = re.sub(r'group-title="[^"]*"', f'group-title="{categoria}"', bloque[0])
                candidatos.append((bloque, url))
    i += 1

print(f"{len(candidatos)} candidatos ({descartados_pais} descartados por país no hispano).")

if VERIFICAR_LINKS:
    print("Verificando links (puede tardar 1-2 minutos)...")
    with ThreadPoolExecutor(max_workers=HILOS) as ex:
        resultados = list(ex.map(lambda c: link_funciona(c[1]), candidatos))
    vivos = [c for c, ok in zip(candidatos, resultados) if ok]
    print(f"{len(vivos)} funcionan, {len(candidatos) - len(vivos)} caídos eliminados.")
else:
    vivos = candidatos

# Ordenar por carpeta y nombre
vivos.sort(key=lambda c: (re.search(r'group-title="([^"]*)"', c[0][0]).group(1), c[0][0].split(",")[-1].lower()))

salida = ["#EXTM3U"]
for bloque, _ in vivos:
    salida.extend(bloque)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(salida) + "\n")

print(f"Listo: {len(vivos)} canales guardados en '{OUTPUT_FILE}'.")
