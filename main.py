import os
import sys
import json
import re
import unicodedata
from dotenv import dotenv_values # type: ignore
import spotipy # type: ignore
from spotipy.oauth2 import SpotifyOAuth # type: ignore

import re
import unicodedata


def normalizar(texto):

    texto = str(texto).lower().strip()

    # -------------------------
    # 1. REMOVE ACENTOS
    # -------------------------

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        letra
        for letra in texto
        if unicodedata.category(letra) != "Mn"
    )

    # -------------------------
    # 2. REMOVE PARTICIPAÇÕES
    # -------------------------

    texto = re.sub(
        r"\s*[\(\[]\s*(?:feat\.?|ft\.?|featuring)\s+.*?[\)\]]",
        "",
        texto,
        flags=re.IGNORECASE
    )

    texto = re.sub(
        r"\s*[-–—]\s*(?:feat\.?|ft\.?|featuring)\s+.*$",
        "",
        texto,
        flags=re.IGNORECASE
    )

    # -------------------------
    # 3. REMOVE SUBTÍTULO ESPECÍFICO
    # -------------------------

    texto = re.sub(
        r"\s*[\(\[]\s*take a look at me now\s*[\)\]]",
        "",
        texto,
        flags=re.IGNORECASE
    )

    # -------------------------
    # 4. QUALIFICADORES DO SPOTIFY
    # -------------------------

    qualificadores = (
        r"remaster(?:ed)?"
        r"|remix"
        r"|instrumental"
        r"|acoustic"
        r"|live"
        r"|radio edit"
        r"|edit"
        r"|extended(?: mix| version)?"
        r"|club mix"
        r"|original mix"
        r"|single version"
        r"|album version"
        r"|alternate version"
        r"|alternative version"
        r"|original version"
        r"|demo"
        r"|mono"
        r"|stereo"
        r"|mix"
        r"|version"
        r"|sped up"
        r"|slowed(?: down)?"
        r"|reverb"
        r"|nightcore"
        r"|karaoke"
        r"|ao vivo"
        r"|versao completa"
        r"|studio recording"
    )

    # -------------------------
    # 5. REMOVE VERSÕES ENTRE PARÊNTESES
    # Exemplos:
    # (2011 Remaster)
    # (Single Version)
    # (Original Mix)
    # -------------------------

    texto = re.sub(
        rf"\s*[\(\[][^)\]]*\b(?:{qualificadores})\b[^)\]]*[\)\]]",
        "",
        texto,
        flags=re.IGNORECASE
    )

    # -------------------------
    # 6. REMOVE QUALIFICADORES APÓS HÍFEN
    # Exemplos:
    # - 2011 Remaster
    # - Single Version
    # - Mix
    # - Remastered 2009
    # -------------------------

    texto = re.sub(
        rf"\s+[-–—]\s*"
        rf"(?:(?:\d{{4}})\s+)?"
        rf"(?:{qualificadores})\b.*$",
        "",
        texto,
        flags=re.IGNORECASE
    )

    # Também remove "- 2011 Mix"
    # ou "- 2009 Remastered"
    texto = re.sub(
        rf"\s+[-–—]\s*\d{{4}}\s+"
        rf"(?:{qualificadores})\b.*$",
        "",
        texto,
        flags=re.IGNORECASE
    )

    # -------------------------
    # 7. REMOVE PARÊNTESES RESTANTES
    # Mantém o comportamento original
    # -------------------------

    texto = re.sub(r"\([^)]*\)", "", texto)
    texto = re.sub(r"\[[^\]]*\]", "", texto)

    # -------------------------
    # 8. NORMALIZA PONTUAÇÃO
    # -------------------------

    texto = re.sub(r"[-‐‑‒–—]", " ", texto)

    texto = re.sub(r"[^\w\s]", "", texto)

    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()

def caminho_arquivo(nome):
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), nome)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), nome)

ENV_PATH = caminho_arquivo(".env")
BASE_TIMBRES = caminho_arquivo("base_timbres.json")
CACHE_PATH = caminho_arquivo(".cache")

config = dotenv_values(ENV_PATH)

SPOTIPY_CLIENT_ID = config.get("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = config.get("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = config.get("SPOTIPY_REDIRECT_URI")

if not SPOTIPY_CLIENT_ID:
    raise Exception(f"Não achei SPOTIPY_CLIENT_ID no arquivo: {ENV_PATH}")

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-currently-playing user-read-playback-state",
        cache_path=CACHE_PATH
    )
)

def chave_musica(nome, artista):
    return f"{normalizar(nome)}|{normalizar(artista)}"

with open(BASE_TIMBRES, "r", encoding="utf-8") as arquivo:
    timbres_originais = json.load(arquivo)

TIMBRES = {}

for chave_original, dados in timbres_originais.items():
    nome_json = dados.get("musica", "")
    artista_json = dados.get("artista", "")

    # Primeiro tenta usar os campos internos
    if nome_json and artista_json:
        chave_normalizada = chave_musica(nome_json, artista_json)
        TIMBRES[chave_normalizada] = dados

    # Também registra usando a chave original como segurança
    if "|" in chave_original:
        nome_chave, artista_chave = chave_original.split("|", 1)

        chave_normalizada_original = chave_musica(
            nome_chave,
            artista_chave
        )

        TIMBRES[chave_normalizada_original] = dados


def recarregar_timbres():
    """Recarrega a base após salvar pelo editor, sem reiniciar o aplicativo."""
    global timbres_originais
    with open(BASE_TIMBRES, "r", encoding="utf-8") as arquivo:
        timbres_originais = json.load(arquivo)
    TIMBRES.clear()
    for chave_original, dados in timbres_originais.items():
        nome_json = dados.get("musica", "")
        artista_json = dados.get("artista", "")
        if nome_json and artista_json:
            TIMBRES[chave_musica(nome_json, artista_json)] = dados
        if "|" in chave_original:
            nome_chave, artista_chave = chave_original.split("|", 1)
            TIMBRES[chave_musica(nome_chave, artista_chave)] = dados


def extrair_ms(tap_texto):
    if not tap_texto:
        return None

    texto = tap_texto.lower()

    if "desligado" in texto or "off" in texto:
        return None

    # Caso venha em ms: "380ms", "aprox. 430ms"
    ms = re.search(r"(\d+)\s*ms", texto)
    if ms:
        return int(ms.group(1))

    # Caso venha em BPM: "80 BPM", "aprox. 120 BPM"
    bpm = re.search(r"(\d+)\s*bpm", texto)
    if bpm:
        valor_bpm = int(bpm.group(1))
        return int(60000 / valor_bpm)

    return None

def pegar_timbre(nome, artista):
    chave = chave_musica(nome, artista)

    print("\n=== DIAGNÓSTICO ===")
    print("Música recebida:", repr(nome))
    print("Artista recebido:", repr(artista))
    print("Chave procurada:", repr(chave))
    print("Encontrada no JSON:", chave in TIMBRES)

    return TIMBRES.get(chave)

def pegar_musica_atual():
    tocando = sp.current_user_playing_track()

    if not tocando or not tocando.get("item"):
        return None, None

    item = tocando["item"]
    return item["name"], item["artists"][0]["name"]

def pegar_proxima_musica():
    try:
        fila = sp.queue()
        proximas = fila.get("queue", [])

        if not proximas:
            return None, None

        proxima = proximas[0]

        if proxima.get("type") != "track":
            return None, None

        return proxima["name"], proxima["artists"][0]["name"]

    except Exception:
        return None, None

def formatar_timbre(timbre):

    texto = f"""
AFINAÇÃO
{timbre["afinacao"]}
"""

    if "timbres" in timbre:
        texto += "\n\nTIMBRES PARA SELECIONAR"

        for nome_tom, dados in timbre["timbres"].items():
            guitarra = dados["guitarra"]

            texto += f"""

{nome_tom.upper()} → {dados.get("nome_bstar", "NÃO GERADO")}

GUITARRA
Captador: {guitarra["captador"]}
Volume: {guitarra["volume"]}
Tone: {guitarra["tone"]}
"""

    else:
        guitarra = timbre["guitarra"]

        texto += f"""

TIMBRE PARA SELECIONAR
{timbre.get("nome_bstar", "NÃO GERADO")}

GUITARRA
Captador: {guitarra["captador"]}
Volume: {guitarra["volume"]}
Tone: {guitarra["tone"]}
"""

    texto += f"""

OBSERVAÇÕES
{timbre["observacoes"]}
"""

    return texto.strip()


if __name__ == "__main__":
    from interface import iniciar_interface # type: ignore

    iniciar_interface(
        pegar_musica_atual=pegar_musica_atual,
        pegar_proxima_musica=pegar_proxima_musica,
        pegar_timbre=pegar_timbre,
        formatar_timbre=formatar_timbre,
        extrair_ms=extrair_ms,
        base_json=BASE_TIMBRES,
        chave_musica=chave_musica,
        recarregar_timbres=recarregar_timbres,
    )

#cd E:\programacao\Spotfy
#Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#.\.venv\Scripts\Activate.ps1
#.\.venv\Scripts\python.exe main.py
#.\.venv\Scripts\pyinstaller.exe --noconsole --onedir --name SpotifyTimbreFinder main.py