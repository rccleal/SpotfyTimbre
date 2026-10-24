import json
import hashlib
import shutil
from pathlib import Path

BASE_JSON = Path("base_timbres.json")
BACKUP_JSON = Path("base_timbres_backup_antes_renumeracao.json")
SAIDA_JSON = Path("base_timbres_renumerado.json")


def assinatura_timbre(timbre):
    """
    Cria uma assinatura usando somente amplificador e efeitos.

    Timbres com amplificador e efeitos exatamente iguais
    recebem o mesmo nome_bstar.
    """
    dados = {
        "amplificador": timbre.get("amplificador", {}),
        "efeitos": timbre.get("efeitos", {}),
    }

    texto = json.dumps(
        dados,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()


def remover_nomes_antigos(base):
    """
    Remove todos os nome_bstar antigos antes de renumerar.
    """
    for musica in base.values():

        musica.pop("nome_bstar", None)

        timbres = musica.get("timbres", {})

        for timbre in timbres.values():
            timbre.pop("nome_bstar", None)


def renumerar_timbres(base):
    assinaturas = {}
    proximo_numero = 1

    musicas_processadas = 0
    variantes_processadas = 0

    for musica in base.values():

        timbres = musica.get("timbres")

        # Música com CLEAN / DRIVE / SOLO
        if isinstance(timbres, dict) and timbres:

            for nome_tom, timbre in timbres.items():

                assinatura = assinatura_timbre(timbre)

                if assinatura not in assinaturas:
                    assinaturas[assinatura] = (
                        f"Timbre {proximo_numero:03d}"
                    )
                    proximo_numero += 1

                timbre["nome_bstar"] = assinaturas[assinatura]
                variantes_processadas += 1

        # Música com apenas um timbre
        else:
            assinatura = assinatura_timbre(musica)

            if assinatura not in assinaturas:
                assinaturas[assinatura] = (
                    f"Timbre {proximo_numero:03d}"
                )
                proximo_numero += 1

            musica["nome_bstar"] = assinaturas[assinatura]
            variantes_processadas += 1

        musicas_processadas += 1

    return {
        "musicas": musicas_processadas,
        "variantes": variantes_processadas,
        "presets_unicos": len(assinaturas),
    }


