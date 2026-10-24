import json
import re
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

BASE_JSON = Path("base_timbres.json")
PASTA_SAIDA = Path("bstar_presets")
JSON_ATUALIZADO = Path("base_timbres_com_nome_bstar.json")

CRIADOR = "Rafael Leal"



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


def valor_0_10_para_127(valor):
    texto = str(valor).replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", texto)

    if not match:
        return 0

    numero = float(match.group())
    numero = max(0, min(10, numero))

    return round((numero / 10) * 127)

def valor_0_10_para_31(valor):
    texto = str(valor).replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", texto)

    if not match:
        return 0

    numero = float(match.group())
    numero = max(0, min(10, numero))

    return round((numero / 10) * 31)

def valor_0_10_para_38(valor):
    texto = str(valor).replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", texto)

    if not match:
        return 0

    numero = float(match.group())
    numero = max(0, min(10, numero))

    return round((numero / 10) * 38)

def extrair_ms(valor):
    if not valor:
        return 0

    texto = str(valor).lower()

    if "desligado" in texto:
        return 0

    match_ms = re.search(r"(\d+)\s*ms", texto)
    if match_ms:
        return int(match_ms.group(1))

    match_bpm = re.search(r"(\d+)\s*bpm", texto)
    if match_bpm:
        bpm = int(match_bpm.group(1))
        return round(60000 / bpm)

    return 400

def limpar_nome_arquivo(nome):
    nome = re.sub(r'[\\/:*?"<>|]', "", nome)
    return nome.strip()[:80]


def pegar_voice(voice):
    texto = str(voice).lower()

    ordem = [
        ("clean warm", 0),
        ("clean bright", 1),
        ("super crunch", 3),
        ("crunch", 2),
        ("od1", 4),
        ("od2", 5),
    ]

    for nome, codigo in ordem:
        if nome in texto:
            return codigo

    return 0


def pegar_tvp(tvp):
    texto = str(tvp).lower()

    for nome, codigo in TVP_MAP.items():
        if nome.lower() == texto:
            return codigo

    return 2


def assinatura_preset(timbre):
    dados = {
        "amplificador": timbre["amplificador"],
        "efeitos": timbre["efeitos"],
    }

    texto = json.dumps(dados, ensure_ascii=False, sort_keys=True)
    return hashlib.md5(texto.encode("utf-8")).hexdigest()


def criar_xml_bstar(nome_preset, about, timbre):
    amp = timbre["amplificador"]
    fx = timbre["efeitos"]

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
    ET.SubElement(info, "Name").text = nome_preset
    ET.SubElement(info, "Creator").text = CRIADOR
    ET.SubElement(info, "Genre").text = "27"
    ET.SubElement(info, "SubGenre").text = "27"
    ET.SubElement(info, "SearchTags").text = ""
    ET.SubElement(info, "About").text = about

    amplifier = ET.SubElement(sound, "Amplifier")

    voice_codigo = pegar_voice(amp.get("voice"))

    ET.SubElement(amplifier, "Voice").text = str(voice_codigo)
    ET.SubElement(amplifier, "Gain").text = str(valor_0_10_para_127(amp.get("gain")))
    ET.SubElement(amplifier, "Volume").text = str(
        VOLUME_POR_VOICE.get(voice_codigo, 100)
    )
    ET.SubElement(amplifier, "Bass").text = str(valor_0_10_para_127(amp.get("bass")))
    ET.SubElement(amplifier, "Middle").text = str(valor_0_10_para_127(amp.get("middle")))
    ET.SubElement(amplifier, "Treble").text = str(valor_0_10_para_127(amp.get("treble")))
    ET.SubElement(amplifier, "ISF").text = str(valor_0_10_para_127(amp.get("isf")))

    tvp = ET.SubElement(amplifier, "TVP", {"Status": "1"})
    tvp.text = str(pegar_tvp(amp.get("tvp")))

    chain = ET.SubElement(sound, "EffectsChain", {"Focused": "0"})

    delay_status = "0" if delay.get("type") == "Desligado" else "1"
    delay_el = ET.SubElement(chain, "Delay", {"Status": delay_status, "Position": "0"})
    ET.SubElement(
        delay_el,
        "Types",
        {"Linear": "16", "Analogue": "17", "Tape": "21", "Multi": "25"},
    ).text = str(DELAY_MAP.get(delay.get("type"), 1))
    ET.SubElement(delay_el, "Adjust1").text = str(valor_0_10_para_31(delay.get("feedback")))
    ET.SubElement(delay_el, "Adjust2").text = str(valor_0_10_para_127(delay.get("time")))
    ET.SubElement(delay_el, "Level").text = str(valor_0_10_para_127(delay.get("level")))
    ET.SubElement(delay_el, "Tempo").text = str(extrair_ms(delay.get("tap")))

    reverb_status = "0" if reverb.get("type") == "Desligado" else "1"
    reverb_el = ET.SubElement(chain, "Reverb", {"Status": reverb_status, "Position": "0"})
    ET.SubElement(
        reverb_el,
        "Types",
        {"Room": "29", "Hall": "33", "Spring": "37", "Plate": "41"},
    ).text = str(REVERB_MAP.get(reverb.get("type"), 3))
    ET.SubElement(reverb_el, "Adjust1").text = str(valor_0_10_para_31(reverb.get("size")))
    ET.SubElement(reverb_el, "Adjust2").text = "64"
    ET.SubElement(reverb_el, "Level").text = str(valor_0_10_para_127(reverb.get("level")))

    mod_status = "0" if modulation.get("type") == "Desligado" else "1"
    mod_el = ET.SubElement(chain, "Modulation", {"Status": mod_status, "Position": "0"})
    ET.SubElement(
        mod_el,
        "Types",
        {"Phaser": "0", "Flanger": "4", "Chorus": "8", "Tremolo": "12"},
    ).text = str(MOD_MAP.get(modulation.get("type"), 2))
    ET.SubElement(mod_el, "Adjust1").text = str(valor_0_10_para_31(modulation.get("mix")))
    ET.SubElement(mod_el, "Adjust2").text = "0"
    ET.SubElement(mod_el, "Level").text = str(valor_0_10_para_127(modulation.get("depth")))
    ET.SubElement(mod_el, "Rate").text = str(valor_0_10_para_127(modulation.get("speed")))

    ET.SubElement(sound, "Tuner").text = "0"
    ET.SubElement(sound, "Bench").text = "0"

    audio = ET.SubElement(sound, "Audio")
    ET.SubElement(audio, "Metronome", {"Type": "0"}).text = "120"
    ET.SubElement(audio, "Track", {"Repeat": "0"}).text = "NO TRACK"

    xml_bruto = ET.tostring(sound, encoding="utf-8")
    return minidom.parseString(xml_bruto).toprettyxml(indent="  ", encoding="UTF-8")



def gerar_patches(base, pasta_saida):
    """Gera todos os presets, usando o mesmo XML do gerador original."""
    pasta_saida = Path(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)
    presets = {}
    for chave, musica in base.items():
        nome = musica.get("musica", chave.split("|")[0])
        artista = musica.get("artista", chave.split("|")[-1])
        variantes = musica.get("timbres")
        itens = variantes.items() if isinstance(variantes, dict) and variantes else [(None, musica)]
        for variante, timbre in itens:
            assinatura = assinatura_preset(timbre)
            if assinatura not in presets:
                presets[assinatura] = {"nome": timbre["nome_bstar"], "timbre": timbre, "musicas": []}
            descricao = f"{nome} - {artista}" + (f" [{variante.upper()}]" if variante else "")
            presets[assinatura]["musicas"].append(descricao)
    for preset in presets.values():
        about = "Músicas com este timbre:\\n" + "\\n".join(preset["musicas"])
        xml = criar_xml_bstar(preset["nome"], about, preset["timbre"])
        (pasta_saida / (limpar_nome_arquivo(preset["nome"]) + ".bstar")).write_bytes(xml)
    return len(presets)
