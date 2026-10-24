import json
import re
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

BASE_JSON = Path("base_timbres.json")
file_exit = Path("bstar_presets")
JSON_ATUALIZADO = Path("base_tones_with_bstar_name.json")

CREATOR = "Spotify Timbre Finder"

VOICE_MAP = {
    "Clean Warm": 0,
    "Clean Bright": 1,
    "Crunch": 2,
    "Super Crunch": 3,
    "OD1": 4,
    "OD2": 5,
}

TVP_MAP = {
    "EL84": 0,
    "6V6": 1,
    "EL34": 2,
    "KT66": 3,
    "6L6": 4,
    "KT88": 5,
}

MOD_MAP = {
    "Phaser": 0,
    "Flanger": 1,
    "Chorus": 2,
    "Tremolo": 3,
}

DELAY_MAP = {
    "Linear": 0,
    "Analogue": 1,
    "Analog": 1,
    "Tape": 2,
    "Multi": 3,
}

REVERB_MAP = {
    "Room": 0,
    "Hall": 1,
    "Spring": 2,
    "Plate": 3,
}

VOLUME_POR_VOICE = {
    0: 127,  # Clean Warm
    1: 122,  # Clean Bright
    2: 110,  # Crunch
    3: 102,  # Super Crunch
    4: 92,   # OD1
    5: 88,   # OD2
}


def value_0_10_to_127(value):
    text = str(value).replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)

    if not match:
        return 0

    numero = float(match.group())
    numero = max(0, min(10, numero))

    return round((numero / 10) * 127)

def value_0_10_to_31(value):
    text = str(value).replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)

    if not match:
        return 0

    numero = float(match.group())
    numero = max(0, min(10, numero))

    return round((numero / 10) * 31)

def value_0_10_to_38(value):
    text = str(value).replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)

    if not match:
        return 0

    numero = float(match.group())
    numero = max(0, min(10, numero))

    return round((numero / 10) * 38)

def extract_ms(value):
    if not value:
        return 0

    text = str(value).lower()

    if "off" in text or "desligado" in text:
        return 0

    match_ms = re.search(r"(\d+)\s*ms", text)
    if match_ms:
        return int(match_ms.group(1))

    match_bpm = re.search(r"(\d+)\s*bpm", text)
    if match_bpm:
        bpm = int(match_bpm.group(1))
        return round(60000 / bpm) if bpm else 0 if bpm else 0

    return 400

def clean_name_file(name):
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    return name.strip()[:80]

def get_voice(voice):
    text = str(voice).lower()

    order = [
        ("clean warm", 0),
        ("clean bright", 1),
        ("super crunch", 3),
        ("crunch", 2),
        ("od1", 4),
        ("od2", 5),
    ]

    for name, code in order:
        if name in text:
            return code

    return 0

def get_tvp(tvp):
    text = str(tvp).lower()

    for name, code in TVP_MAP.items():
        if name.lower() == text:
            return code

    return 2

def signature_preset(tone):
    data = {
        "amplifier": tone["amplificador"],
        "efects": tone["efeitos"],
    }

    text = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(text.encode("utf-8")).hexdigest()

def criar_xml_bstar(name_preset, about, tone):
    amp = tone["amplificador"]
    fx = tone["efeitos"]

    modulation = fx["modulation"]
    delay = fx["delay"]
    reverb = fx["reverb"]

    sound = ET.Element(
        "Sound",
        {
            "CE": "1",
            "CS": "1",
            "LastModified": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "FirmwareVersion": "1",
        },
    )

    info = ET.SubElement(sound, "Info")
    ET.SubElement(info, "Name").text = name_preset
    ET.SubElement(info, "Creator").text = CREATOR
    ET.SubElement(info, "Genre").text = "27"
    ET.SubElement(info, "SubGenre").text = "27"
    ET.SubElement(info, "SearchTags").text = ""
    ET.SubElement(info, "About").text = about

    amplifier = ET.SubElement(sound, "Amplifier")

    voice_code = get_voice(amp.get("voice"))

    ET.SubElement(amplifier, "Voice").text = str(voice_code)
    ET.SubElement(amplifier, "Gain").text = str(value_0_10_to_127(amp.get("gain")))
    ET.SubElement(amplifier, "Volume").text = str(
        VOLUME_POR_VOICE.get(voice_code, 100)
    )
    ET.SubElement(amplifier, "Bass").text = str(value_0_10_to_127(amp.get("bass")))
    ET.SubElement(amplifier, "Middle").text = str(value_0_10_to_127(amp.get("middle")))
    ET.SubElement(amplifier, "Treble").text = str(value_0_10_to_127(amp.get("treble")))
    ET.SubElement(amplifier, "ISF").text = str(value_0_10_to_127(amp.get("isf")))

    tvp = ET.SubElement(amplifier, "TVP", {"Status": "1"})
    tvp.text = str(get_tvp(amp.get("tvp")))

    chain = ET.SubElement(sound, "EffectsChain", {"Focused": "0"})

    delay_status = "0" if delay.get("type") in ("off", "desligado") else "1"
    delay_el = ET.SubElement(chain, "Delay", {"Status": delay_status, "Position": "0"})
    ET.SubElement(
        delay_el,
        "Types",
        {"Linear": "16", "Analogue": "17", "Tape": "21", "Multi": "25"},
    ).text = str(DELAY_MAP.get(delay.get("type"), 1))
    ET.SubElement(delay_el, "Adjust1").text = str(value_0_10_to_31(delay.get("feedback")))
    ET.SubElement(delay_el, "Adjust2").text = str(value_0_10_to_127(delay.get("time")))
    ET.SubElement(delay_el, "Level").text = str(value_0_10_to_127(delay.get("level")))
    ET.SubElement(delay_el, "Tempo").text = str(extract_ms(delay.get("tap")))

    reverb_status = "0" if reverb.get("type") in ("off", "desligado") else "1"
    reverb_el = ET.SubElement(chain, "Reverb", {"Status": reverb_status, "Position": "0"})
    ET.SubElement(
        reverb_el,
        "Types",
        {"Room": "29", "Hall": "33", "Spring": "37", "Plate": "41"},
    ).text = str(REVERB_MAP.get(reverb.get("type"), 3))
    ET.SubElement(reverb_el, "Adjust1").text = str(value_0_10_to_31(reverb.get("size")))
    ET.SubElement(reverb_el, "Adjust2").text = "64"
    ET.SubElement(reverb_el, "Level").text = str(value_0_10_to_127(reverb.get("level")))

    mod_status = "0" if modulation.get("type") in ("off", "desligado") else "1"
    mod_el = ET.SubElement(chain, "Modulation", {"Status": mod_status, "Position": "0"})
    ET.SubElement(
        mod_el,
        "Types",
        {"Phaser": "0", "Flanger": "4", "Chorus": "8", "Tremolo": "12"},
    ).text = str(MOD_MAP.get(modulation.get("type"), 2))
    ET.SubElement(mod_el, "Adjust1").text = str(value_0_10_to_31(modulation.get("mix")))
    ET.SubElement(mod_el, "Adjust2").text = "0"
    ET.SubElement(mod_el, "Level").text = str(value_0_10_to_127(modulation.get("depth")))
    ET.SubElement(mod_el, "Rate").text = str(value_0_10_to_127(modulation.get("speed")))

    ET.SubElement(sound, "Tuner").text = "0"
    ET.SubElement(sound, "Bench").text = "0"

    audio = ET.SubElement(sound, "Audio")
    ET.SubElement(audio, "Metroname", {"Type": "0"}).text = "120"
    ET.SubElement(audio, "Track", {"Repeat": "0"}).text = "NO TRACK"

    xml_raw = ET.tostring(sound, encoding="utf-8")
    return minidom.parseString(xml_raw).toprettyxml(indent="  ", encoding="UTF-8")

def create_patches(base, file_exit):
    """Create all presets, using the same XML of the original generator."""
    file_exit = Path(file_exit)
    file_exit.mkdir(parents=True, exist_ok=True)
    presets = {}
    for bracket, music in base.items():
        name = music.get("musica", bracket.split("|")[0])
        artista = music.get("artista", bracket.split("|")[-1])
        variants = music.get("timbres")
        itens = variants.items() if isinstance(variants, dict) and variants else [(None, music)]
        for variant, tone in itens:
            signature = signature_preset(tone)
            if signature not in presets:
                presets[signature] = {"name": tone["nome_bstar"], "tone": tone, "musics": []}
            description = f"{name} - {artista}" + (f" [{variant.upper()}]" if variant else "")
            presets[signature]["musics"].append(description)
    for preset in presets.values():
        about = "Songs with this tone:\n" + "\n".join(preset["musics"])
        xml = criar_xml_bstar(preset["name"], about, preset["tone"])
        (file_exit / (clean_name_file(preset["name"]) + ".bstar")).write_bytes(xml)
    return len(presets)
