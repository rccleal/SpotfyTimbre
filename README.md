# Spotify Timbre Finder

A Python/Tkinter desktop application that detects the currently playing Spotify track and displays guitar tone settings from a local JSON database. It includes a dark-themed tone editor and can export `.bstar` presets for compatible Blackstar amplifiers.

## Requirements

- Windows (recommended for Blackstar patch integration)
- Python 3.10 or newer
- A Spotify account and an application registered in the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- Dependencies in `requirements.txt`

## Installation

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and enter your Spotify application credentials. Register the **exact same Redirect URI** in the Spotify Developer Dashboard. The example URI is illustrative; adjust it if required by Spotify's current rules.

```powershell
python main.py
```

Spotify may open a browser window to request permission to read your playback state. OAuth tokens are stored locally in `.cache`; **never commit this file**.

## Project files

| File | Purpose |
| --- | --- |
| `main.py` | Spotify API integration, database loading, and tone lookup |
| `interface.py` | Main Tkinter window |
| `editor_timbres.py` | Song and guitar tone editor |
| `bstar_export.py` | `.bstar` preset generation |
| `bstar_numeracao.py` | Preset organization and numbering |
| `base_timbres.json` | Included tone database |
| `.env.example` | Safe credentials template (no secrets) |

## Blackstar presets

By default, the editor exports presets to `~/OneDrive/Documentos/Blackstar/Saved Patches/Patches` on Windows. If your Blackstar software uses another directory, change `PASTA_BLACKSTAR` in `editor_timbres.py` or update the destination field in the editor. Compatibility with other amplifier models has not been verified.

## Language and data compatibility

The application interface and documentation are in English. Existing song titles, artist names, tone variants, tuning descriptions, and notes in `base_timbres.json` are intentionally preserved in their original language to avoid altering user data. The editor accepts both the legacy `Desligado` effect value and the English `Off` value.

## Security

- Never commit `.env`, `.cache`, passwords, access tokens, or generated files in `dist/`.
- Check `git status` before every commit.
- Avoid publishing account information or authentication screenshots.

## Notes

The app requires Spotify playback and API access. Tone settings are reference values and may need adjustment for your guitar, pickups, and amplifier.

Independent project; not affiliated with Spotify or Blackstar.
