import copy
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk, simpledialog
import tkinter as tk

from bstar_numeracao import remove_old_names, renumber_tones # type: ignore
from bstar_export import create_patches # type: ignore

BLACKSTAR_FOLDER = Path.home() / "OneDrive" / "Documentos" / "Blackstar" / "Saved Patches" / "Patches"
VOICES = ["Clean Warm", "Clean Bright", "Crunch", "Super Crunch", "OD1", "OD2"]
TVPS = ["EL84", "6V6", "EL34", "KT66", "6L6", "KT88"]
TYPES = {"modulation": ["Off", "Phaser", "Flanger", "Chorus", "Tremolo"],
         "delay": ["Off", "Linear", "Analogue", "Tape", "Multi"],
         "reverb": ["Off", "Room", "Hall", "Spring", "Plate"]}

def open_editor(window, base_json, bracket_song, when_save):
    base_json = Path(base_json)
    base = json.loads(base_json.read_text(encoding="utf-8"))
    window_ed = tk.Toplevel(window)
    window_ed.title("Manage songs and tones")
    window_ed.geometry("990x780")
    window_ed.transient(window)
    # Black theme for all editing window (including filds and menu).
    BG = "#121212"
    PANEL = "#1d1d1d"
    INPUT = "#282828"
    FG = "#f5f5f5"
    MUTED = "#b3b3b3"
    ACCENT = "#1db954"
    window_ed.configure(bg=BG)
    style = ttk.Style(window_ed)
    style.theme_use("clam")
    style.configure("Editor.TFrame", background=BG)
    style.configure("Editor.TLabelframe", background=PANEL, bordercolor="#444444")
    style.configure("Editor.TLabelframe.Label", background=PANEL, foreground=ACCENT, font=("Arial", 10, "bold"))
    style.configure("Editor.TLabel", background=BG, foreground=FG)
    style.configure("Editor.TEntry", fieldbackground=INPUT, foreground=FG, insertcolor=FG, bordercolor="#444444")
    style.configure("Editor.TCombobox", fieldbackground=INPUT, background=INPUT, foreground=FG, arrowcolor=FG, bordercolor="#444444")
    style.map("Editor.TCombobox", fieldbackground=[("readonly", INPUT)], foreground=[("readonly", FG)], selectbackground=[("readonly", INPUT)], selectforeground=[("readonly", FG)])
    style.configure("Editor.TButton", background="#303030", foreground=FG, padding=7)
    style.map("Editor.TButton", background=[("active", "#404040"), ("pressed", ACCENT)], foreground=[("active", FG)])
    style.configure("Editor.Vertical.TScrollbar", background="#303030", troughcolor=BG, arrowcolor=FG)
    # Colors in the list of the comboboxes (when supported by Tk).
    try:
        window_ed.option_add("*TCombobox*Listbox.background", INPUT)
        window_ed.option_add("*TCombobox*Listbox.foreground", FG)
        window_ed.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        window_ed.option_add("*TCombobox*Listbox.selectForeground", "#000000")
    except tk.TclError:
        pass
    root = ttk.Frame(window_ed, style="Editor.TFrame", padding=12)
    root.pack(fill="both", expand=True)

    search_bar = ttk.Frame(root, style="Editor.TFrame")
    search_bar.pack(fill="x", pady=(0, 8))
    ttk.Label(search_bar, style="Editor.TLabel", text="Search existing song:").pack(side="left")
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_bar, style="Editor.TEntry", textvariable=search_var)
    search_entry.pack(side="left", padx=7, fill="x", expand=True)
    search_count = tk.StringVar()
    ttk.Label(search_bar, style="Editor.TLabel", textvariable=search_count).pack(side="right")

    top = ttk.Frame(root, style="Editor.TFrame")
    top.pack(fill="x")
    ttk.Label(top, style="Editor.TLabel", text="Registered song:").pack(side="left")
    brackets = list(base)
    def display_name(key):
        item = base[key]
        return f'{item.get("musica", item.get("song")) or key.split("|")[0]} — {item.get("artista", item.get("artist")) or key.split("|")[-1]}'
    visible_brackets = list(brackets)
    selection = ttk.Combobox(top, style="Editor.TCombobox", state="readonly", width=62)
    selection.pack(side="left", padx=7, fill="x", expand=True)
    ttk.Button(top, style="Editor.TButton", text="New song", command=lambda: new()).pack(side="left")
    ttk.Button(top, style="Editor.TButton", text="Duplicate tones", command=lambda: duplicate()).pack(side="left", padx=5)

    def filter_songs(*_):
        query = search_var.get().casefold().strip()
        terms = query.split()
        visible_brackets[:] = [key for key in brackets
                               if all(term in display_name(key).casefold() for term in terms)]
        selection["values"] = [display_name(key) for key in visible_brackets]
        search_count.set(f"{len(visible_brackets)} found")
        selected_key = current["bracket"]
        if selected_key not in visible_brackets:
            selection.set("")

    search_var.trace_add("write", filter_songs)

    line = ttk.Frame(root, style="Editor.TFrame")
    line.pack(fill="x", pady=9)
    fields = {}
    for label, field, width in [("Song", "musica", 33), ("Artist", "artista", 28), ("Tuning", "afinacao", 28)]:
        block = ttk.Frame(line, style="Editor.TFrame")
        block.pack(side="left", fill="x", expand=True, padx=3)
        ttk.Label(block, style="Editor.TLabel", text=label).pack(anchor="w")
        ent = ttk.Entry(block, style="Editor.TEntry", width=width)
        ent.pack(fill="x")
        fields[field] = ent

    obs_frame = ttk.Frame(root, style="Editor.TFrame")
    obs_frame.pack(fill="x")
    ttk.Label(obs_frame, style="Editor.TLabel", text="Observations").pack(anchor="w")
    observations = tk.Text(obs_frame, height=3, wrap="word", bg=INPUT, fg=FG, insertbackground=FG, selectbackground="#146d38", relief="flat", padx=8, pady=6)
    observations.pack(fill="x")

    strip = ttk.Frame(root, style="Editor.TFrame")
    strip.pack(fill="x", pady=8)
    ttk.Label(strip, style="Editor.TLabel", text="Tone/variant:").pack(side="left")
    variant = ttk.Combobox(strip, style="Editor.TCombobox", width=24, state="readonly")
    variant.pack(side="left", padx=7)
    ttk.Button(strip, style="Editor.TButton", text="+ Add variant", command=lambda: add_variant()).pack(side="left", padx=5)
    ttk.Button(strip, style="Editor.TButton", text="Remove variant", command=lambda: remove_variant()).pack(side="left", padx=5)

    canvas = tk.Canvas(root, highlightthickness=0, bg=BG)
    bar = ttk.Scrollbar(root, style="Editor.Vertical.TScrollbar", orient="vertical", command=canvas.yview)
    internal = ttk.Frame(canvas, style="Editor.TFrame", padding=(5, 4))
    internal.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=internal, anchor="nw")
    canvas.configure(yscrollcommand=bar.set)
    canvas.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")

    controls = {}
    def section(title, itens):
        frame = ttk.LabelFrame(internal, style="Editor.TLabelframe", text=title, padding=9)
        frame.pack(fill="x", pady=5)
        for i,(path,label,options) in enumerate(itens):
            row, col = divmod(i, 3)
            sub = ttk.Frame(frame, style="Editor.TFrame")
            sub.grid(row=row, column=col, sticky="ew", padx=7, pady=4)
            frame.columnconfigure(col, weight=1)
            ttk.Label(sub, style="Editor.TLabel", text=label).pack(anchor="w")
            widget = ttk.Combobox(sub, style="Editor.TCombobox", values=options, width=25) if options else ttk.Entry(sub, style="Editor.TEntry", width=27)
            widget.pack(fill="x")
            controls[path] = widget

    section("Guitar", [(("guitarra", k), r, None) for k,r in [
        ("captador","Pickup"), ("volume","Volume"), ("tone","Tone")]])
    section("Amplifier", [(("amplificador", k), r, o) for k,r,o in [
        ("voice","Voice",VOICES),("gain","Gain",None),("bass","Bass",None),
        ("middle","Middle",None),("treble","Treble",None),("isf","ISF",None),
        ("tvp","TVP",TVPS)]])
    for group, name, itens in [
        ("modulation","Modulation",["type","depth","mix","speed","tap"]),
        ("delay","Delay",["type","level","feedback","time","tap"]),
        ("reverb","Reverb",["type","level","size"])]:
        section(name, [(("efeitos",group,k),k.title(),TYPES[group] if k=="type" else None) for k in itens])

    ttk.Label(root, style="Editor.TLabel", text=f"JSON will be saved in: {base_json}").pack(anchor="w", pady=(4, 0))

    baseboard = ttk.Frame(window_ed, style="Editor.TFrame", padding=12)
    baseboard.pack(fill="x")
    ttk.Label(baseboard, style="Editor.TLabel", text="Exclusive destination .bstar:").pack(side="left")
    folder = ttk.Entry(baseboard, style="Editor.TEntry")
    folder.insert(0, str(BLACKSTAR_FOLDER))
    folder.pack(side="left", fill="x", expand=True, padx=8)
    ttk.Button(baseboard, style="Editor.TButton", text="Save JSON and create .bstar", command=lambda: save()).pack(side="right")

    current = {"bracket": None, "data": {}, "variant": None, "variants": {}}

    def set_entry(widget, value):
        widget.delete(0, tk.END)
        widget.insert(0, str(value if value is not None else ""))

    def fill_variant(name):
        data = current["variants"].get(name, {})
        for path, widget in controls.items():
            value = data
            for part in path:
                value = value.get(part, {}) if isinstance(value, dict) else {}
            set_entry(widget, value if not isinstance(value, dict) else "")
        current["variant"] = name

    def colect_variant():
        name = current["variant"]
        if name is None:
            return
        data = copy.deepcopy(current["variants"].get(name, {}))
        for path, widget in controls.items():
            target = data
            for part in path[:-1]:
                target = target.setdefault(part, {})
            target[path[-1]] = widget.get().strip()
        current["variants"][name] = data

    def change_variant(event=None):
        colect_variant()
        fill_variant(variant.get())

    def fill_song(bracket):
        current["bracket"] = bracket
        data = copy.deepcopy(base.get(bracket, {})) if bracket else {}
        current["data"] = data
        for name in fields:
            set_entry(fields[name], data.get(name,""))
        observations.delete("1.0",tk.END)
        observations.insert("1.0",data.get("observacoes",""))
        if isinstance(data.get("timbres"),dict) and data["timbres"]:
            current["variants"] = copy.deepcopy(data["timbres"])
        else:
            current["variants"] = {"main":copy.deepcopy(data)}
        variant["values"] = list(current["variants"])
        first = next(iter(current["variants"]))
        variant.set(first)
        current["variant"] = None
        fill_variant(first)

    def choose(event=None):
        i = selection.current()
        if 0 <= i < len(visible_brackets):
            fill_song(visible_brackets[i])

    def new():
        selection.set("")
        fill_song(None)
        for name in fields:
            set_entry(fields[name],"")
        observations.delete("1.0",tk.END)

    def duplicate():
        # Criate a new song copying the settings that are on the editor.
        colect_variant()
        current["bracket"] = None
        selection.set("")
        set_entry(fields["musica"], "")
        set_entry(fields["artista"], "")
        fields["musica"].focus_set()

    def add_variant():
        colect_variant()
        name = simpledialog.askstring("New variant", "Name of the variant (ex.: clean, drive, solo):", parent=window_ed)
        if not name:
            return
        name = name.strip().lower()
        if name in current["variants"]:
            messagebox.showwarning("Existing variant", "This variant already exists.", parent=window_ed)
            return
        current["variants"][name] = copy.deepcopy(current["variants"].get(current["variant"], {}))
        variant["values"] = list(current["variants"])
        variant.set(name)
        fill_variant(name)

    def remove_variant():
        if len(current["variants"]) <= 1:
            messagebox.showwarning("Not permitted","Keep at least one tone.",parent=window_ed)
            return
        name = variant.get()
        if messagebox.askyesno("Remove variant",f"Remove the variant {name}?",parent=window_ed):
            del current["variants"][name]
            first = next(iter(current["variants"]))
            variant["values"] = list(current["variants"])
            variant.set(first)
            current["variant"] = None
            fill_variant(first)

    def save():
        try:
            colect_variant()
            name = fields["musica"].get().strip()
            artist = fields["artista"].get().strip()
            if not name or not artist:
                raise ValueError("Inform song and artist.")
            bracket = bracket_song(name, artist)
            if bracket in base and bracket != current["bracket"]:
                if not messagebox.askyesno("Already registered", "This song already exists. Do you want to overwrite it?", parent=window_ed):
                    return
            register = copy.deepcopy(current["data"])
            register.update(musica=name, artista=artist,
                            afinacao=fields["afinacao"].get().strip(),
                            observacoes=observations.get("1.0",tk.END).strip())
            variants = copy.deepcopy(current["variants"])
            if len(variants)==1 and "main" in variants:
                register.pop("timbres",None)
                register.update({
                    k: copy.deepcopy(variants["main"].get(k, {}))
                    for k in ("guitarra", "amplificador", "efeitos")
                })
                register["observacoes"] = observations.get("1.0",tk.END).strip()
            else:
                register["timbres"] = variants
                register["tipo_timbre"] = "multi"
                register["timbre_padrao"] = register.get("timbre_padrao") if register.get("timbre_padrao") in variants else next(iter(variants))
            for v in variants.values():
                amp = v.get("amplificador",{})
                fx = v.get("efeitos",{})
                if not amp.get("voice") or not amp.get("tvp"):
                    raise ValueError("Fill Voice and TVP in all tones.")
                for group in ("modulation","delay","reverb"):
                    if not fx.get(group,{}).get("type"):
                        raise ValueError(f"Select the {group} type in all tones.")
            new = copy.deepcopy(base)
            if current["bracket"] and current["bracket"] != bracket:
                new.pop(current["bracket"],None)
            new[bracket] = register
            remove_old_names(new) 
            result = renumber_tones(new)
            destination = Path(folder.get().strip()).expanduser()
            if not destination.is_dir():
                raise ValueError(f"Blackstar folder not found:\n{destination}\n\nConfirm the path before saving.")
            if not messagebox.askyesno(
                "Confirm export",
                "The numbering will be recalculated for the entire database. "
                "This can rename old presets and replace .bstar files "
                "in Blackstar folder. A backup will be crated before. Continue?",
                parent=window_ed
            ):
                return
            with tempfile.TemporaryDirectory() as tmp:
                temporary = Path(tmp)
                total = create_patches(new,temporary)
                if not total:
                    raise ValueError("No patch was generated.")
                # Temporary JSON next to the scripts, never on Blackstar folder.
                json_tmp = base_json.with_name(base_json.name + ".new")
                json_tmp.write_text(json.dumps(new,ensure_ascii=False,indent=4),encoding="utf-8")
                # Backup before overwriting the JSON or any existing patch.
                folder_backup = base_json.parent / "backups_timbres" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                folder_backup.mkdir(parents=True,exist_ok=False)
                shutil.copy2(base_json,folder_backup/base_json.name)
                patches_backup = folder_backup/"patches"
                patches_backup.mkdir()
                for file in temporary.glob("*.bstar"):
                    existing = destination/file.name
                    if existing.exists():
                        shutil.copy2(existing,patches_backup/file.name)
                # The runumbering can change the number of old presets.
                # So we export all colection, not only the new ones.
                for file in temporary.glob("*.bstar"):
                    os.replace(file,destination/file.name)
                os.replace(json_tmp,base_json)
            base.clear()
            base.update(new)
            when_save()
            messagebox.showinfo("Finished",
                f"JSON saved.\n{result['musics']} songs processed.\n"
                f"{result['presets_unicos']} unique presets exported.\n"
                f"Backup: {folder_backup}",parent=window_ed)
            window_ed.destroy()
        except Exception as erro:
            messagebox.showerror("Save error",str(erro),parent=window_ed)

    variant.bind("<<ComboboxSelected>>",change_variant)
    selection.bind("<<ComboboxSelected>>", choose)
    search_entry.bind("<Return>", lambda event: select_first_result())
    def select_first_result():
        if visible_brackets:
            selection.current(0)
            choose()
    filter_songs()
    new()
