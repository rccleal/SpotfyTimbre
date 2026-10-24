import os
import sys
import json
import re
import unicodedata
from dotenv import dotenv_values # type: ignore
import spotipy # type: ignore
from spotipy.oauth2 import SpotifyOAuth # type: ignore



def normalize(text):

    text = str(text).lower().strip()

    # -------------------
    # 1. REMOVE ACCENTS
    # -------------------

    text = unicodedata.normalize("NFD", text)

    text = "".join(
        letter
        for letter in text
        if unicodedata.category(letter) != "Mn"
    )

    # -----------------
    # 2. REMOVE FEATS
    # -----------------

    text = re.sub(
        r"\s*[\(\[]\s*(?:feat\.?|ft\.?|featuring)\s+.*?[\)\]]",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*[-–—]\s*(?:feat\.?|ft\.?|featuring)\s+.*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------
    # 3. REMOVE SPECIFIC SUBTITLE 
    # -----------------------------

    text = re.sub(
        r"\s*[\(\[]\s*take a look at me now\s*[\)\]]",
        "",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------
    # 4. SPOTIFY QUALIFIERS
    # Add more if you need
    # -----------------------

    qualifiers = (
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

    # -----------------------------------
    # 5. REMOVE VERSIONS IN PARENTHESES
    # Examples:
    # (2011 Remaster)
    # (Single Version)
    # (Original Mix)
    # ------------------------------------

    text = re.sub(
        rf"\s*[\(\[][^)\]]*\b(?:{qualifiers})\b[^)\]]*[\)\]]",
        "",
        text,
        flags=re.IGNORECASE
    )

    # -----------------------------------
    # 6. REMOVE QUALIFIERS AFTER HYPHEN
    # Examples:
    # - 2011 Remaster
    # - Single Version
    # - Mix
    # - Remastered 2009
    # -----------------------------------

    text = re.sub(
        rf"\s+[-–—]\s*"
        rf"(?:(?:\d{{4}})\s+)?"
        rf"(?:{qualifiers})\b.*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Also remove "- 2011 Mix"
    # or "- 2009 Remastered"
    text = re.sub(
        rf"\s+[-–—]\s*\d{{4}}\s+"
        rf"(?:{qualifiers})\b.*$",
        "",
        text,
        flags=re.IGNORECASE
    )

    # ---------------------------------
    # 7. REMOVE REMAINING PARENTHESES
    # Keep the original behavior
    # ---------------------------------

    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)

    # --------------------------
    # 8. NORMALIZE PUNCTUATION 
    # --------------------------

    text = re.sub(r"[-‐‑‒–—]", " ", text)

    text = re.sub(r"[^\w\s]", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()

def file_path(name):
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), name)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

ENV_PATH = file_path(".env")
BASE_TONES = file_path("base_timbres.json")
CACHE_PATH = file_path(".cache")

config = dotenv_values(ENV_PATH)

SPOTIPY_CLIENT_ID = config.get("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = config.get("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = config.get("SPOTIPY_REDIRECT_URI")

if not SPOTIPY_CLIENT_ID:
    raise Exception(f"SPOTIPY_CLIENT_ID not found in the file: {ENV_PATH}")

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope="user-read-currently-playing user-read-playback-state",
        cache_path=CACHE_PATH
    )
)

def song_bracket(name, artist):
    return f"{normalize(name)}|{normalize(artist)}"

with open(BASE_TONES, "r", encoding="utf-8") as arquivo:
    original_tones = json.load(arquivo)

TONES = {}

for original_bracket, datas in original_tones.items():
    name_json = datas.get("musica", datas.get("song", ""))
    artist_json = datas.get("artista", datas.get("artist", ""))

    # Try to use the internal filds first
    if name_json and artist_json:
        normalized_bracket = song_bracket(name_json, artist_json)
        TONES[normalized_bracket] = datas

    # Registers the original bracket for safety
    if "|" in original_bracket:
        name_bracket, artist_bracket = original_bracket.split("|", 1)

        original_normalized_bracket = song_bracket(
            name_bracket,
            artist_bracket
        )

        TONES[original_normalized_bracket] = datas


def reload_tones():
    """Recarrega a base após salvar pelo editor, sem reiniciar o aplicativo."""
    global original_tones
    with open(BASE_TONES, "r", encoding="utf-8") as arquivo:
        original_tones = json.load(arquivo)
    TONES.clear()
    for original_bracket, datas in original_tones.items():
        name_json = datas.get("musica", datas.get("song", ""))
        artist_json = datas.get("artista", datas.get("artist", ""))
        if name_json and artist_json:
            TONES[song_bracket(name_json, artist_json)] = datas
        if "|" in original_bracket:
            name_bracket, artist_bracket = original_bracket.split("|", 1)
            TONES[song_bracket(name_bracket, artist_bracket)] = datas


def extract_ms(tap_text):
    if not tap_text:
        return None

    text = tap_text.lower()

    if "off" in text or "desligado" in text:
        return None

    # If it comes in ms: "380ms", "aprox. 430ms"
    ms = re.search(r"(\d+)\s*ms", text)
    if ms:
        return int(ms.group(1))

    # If it comes in BPM: "80 BPM", "aprox. 120 BPM"
    bpm = re.search(r"(\d+)\s*bpm", text)
    if bpm:
        value_bpm = int(bpm.group(1))
        return int(60000 / value_bpm) if value_bpm else None if value_bpm else None

    return None

def get_tone(name, artist):
    bracket = song_bracket(name, artist)

    print("\n=== DIAGNÓSTICO ===")
    print("Song received:", repr(name))
    print("Artist received:", repr(artist))
    print("Bracket surched:", repr(bracket))
    print("Found in JSON:", bracket in TONES)

    return TONES.get(bracket)

def get_current_song():
    playing = sp.current_user_playing_track()

    if not playing or not playing.get("item"):
        return None, None

    item = playing["item"]
    return item["name"], item["artists"][0]["name"]

def get_next_song():
    try:
        queue = sp.queue()
        next = queue.get("queue", [])

        if not next:
            return None, None

        next = next[0]

        if next.get("type") != "track":
            return None, None

        return next["name"], next["artists"][0]["name"]

    except Exception:
        return None, None

def format_tone(tone):
    """Format both single-tone and multi-variant records."""
    lines = ["TUNING", str(tone.get("afinacao", tone.get("tuning", "")))]
    variants = tone.get("timbres", tone.get("tones"))
    if not isinstance(variants, dict) or not variants:
        variants = {"main": tone}
    lines.append("\nTONES TO SELECT")
    for variant_name, data in variants.items():
        guitar = data.get("guitarra", data.get("guitar", {}))
        lines.extend([
            "", f"{variant_name.upper()} → {data.get('nome_bstar', data.get('name_bstar', 'NOT GENERATED'))}",
            "GUITAR", f"Pickup: {guitar.get('captador', guitar.get('pickup', ''))}",
            f"Volume: {guitar.get('volume', '')}", f"Tone: {guitar.get('tone', '')}"
        ])
    lines.extend(["", "OBSERVATIONS", str(tone.get("observacoes", tone.get("observations", "")))])
    return "\n".join(lines).strip()


if __name__ == "__main__":
    from interface import start_interface # type: ignore

    start_interface(
        get_current_song=get_current_song,
        get_next_song=get_next_song,
        get_tone=get_tone,
        format_tone=format_tone,
        extract_ms=extract_ms,
        base_json=BASE_TONES,
        song_bracket=song_bracket,
        reload_tones=reload_tones,
    )

#cd E:\programacao\Spotfy
#Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#.\.venv\Scripts\Activate.ps1
#.\.venv\Scripts\python.exe main.py
#.\.venv\Scripts\pyinstaller.exe --noconsole --onedir --name SpotifytoneFinder main.py