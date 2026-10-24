import json
import hashlib
import shutil
from pathlib import Path

BASE_JSON = Path("base_tones.json")
BACKUP_JSON = Path("base_tones_backup_before_renumbering.json")
SAIDA_JSON = Path("base_tones_renumbered.json")

def assinatura_tone(tone):
    """
    Create a signature using only amp and efects.

    Tones with amp and effects exactly the same
    receive the same name_bstar.
    """
    data = {
        "amplifier": tone.get("amplificador", {}),
        "efects": tone.get("efeitos", {}),
    }

    text = json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()

def remove_old_names(base):
    """
    Remove all of the name_bstar before renumbering.
    """
    for music in base.values():

        music.pop("nome_bstar", None)

        tones = music.get("timbres", {})

        for tone in tones.values():
            tone.pop("nome_bstar", None)

def renumber_tones(base):
    signatures = {}
    next_number = 1

    musics_processed = 0
    variants_processed = 0

    for music in base.values():

        tones = music.get("timbres")

        # Songs with CLEAN / DRIVE / SOLO
        if isinstance(tones, dict) and tones:

            for name_tom, tone in tones.items():

                signature = assinatura_tone(tone)

                if signature not in signatures:
                    signatures[signature] = (
                        f"tone {next_number:03d}"
                    )
                    next_number += 1

                tone["nome_bstar"] = signatures[signature]
                variants_processed += 1

        # Música com apenas um tone
        else:
            signature = assinatura_tone(music)

            if signature not in signatures:
                signatures[signature] = (
                    f"tone {next_number:03d}"
                )
                next_number += 1

            music["nome_bstar"] = signatures[signature]
            variants_processed += 1

        musics_processed += 1

    return {
        "musics": musics_processed,
        "variants": variants_processed,
        "presets_unicos": len(signatures),
    }
