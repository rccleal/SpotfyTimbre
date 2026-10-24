import copy
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk

from bstar_numeracao import remover_nomes_antigos, renumerar_timbres # type: ignore
from bstar_export import gerar_patches # type: ignore

PASTA_BLACKSTAR = Path.home() / "OneDrive" / "Documentos" / "Blackstar" / "Saved Patches" / "Patches"
VOICES = ["Clean Warm", "Clean Bright", "Crunch", "Super Crunch", "OD1", "OD2"]
TVPS = ["EL84", "6V6", "EL34", "KT66", "6L6", "KT88"]
TIPOS = {"modulation": ["Desligado", "Phaser", "Flanger", "Chorus", "Tremolo"],
         "delay": ["Desligado", "Linear", "Analogue", "Tape", "Multi"],
         "reverb": ["Desligado", "Room", "Hall", "Spring", "Plate"]}

def abrir_editor(janela, base_json, chave_musica, ao_salvar):
    base_json = Path(base_json)
    base = json.loads(base_json.read_text(encoding="utf-8"))
    janela_ed = tk.Toplevel(janela)
    janela_ed.title("Gerenciar músicas e timbres")
    janela_ed.geometry("990x780")
    janela_ed.transient(janela)
    # Tema escuro para toda a janela de edição (incluindo campos e menus).
    BG = "#121212"
    PANEL = "#1d1d1d"
    INPUT = "#282828"
    FG = "#f5f5f5"
    MUTED = "#b3b3b3"
    ACCENT = "#1db954"
    janela_ed.configure(bg=BG)
    estilo = ttk.Style(janela_ed)
    estilo.theme_use("clam")
    estilo.configure("Editor.TFrame", background=BG)
    estilo.configure("Editor.TLabelframe", background=PANEL, bordercolor="#444444")
    estilo.configure("Editor.TLabelframe.Label", background=PANEL, foreground=ACCENT, font=("Arial", 10, "bold"))
    estilo.configure("Editor.TLabel", background=BG, foreground=FG)
    estilo.configure("Editor.TEntry", fieldbackground=INPUT, foreground=FG, insertcolor=FG, bordercolor="#444444")
    estilo.configure("Editor.TCombobox", fieldbackground=INPUT, background=INPUT, foreground=FG, arrowcolor=FG, bordercolor="#444444")
    estilo.map("Editor.TCombobox", fieldbackground=[("readonly", INPUT)], foreground=[("readonly", FG)], selectbackground=[("readonly", INPUT)], selectforeground=[("readonly", FG)])
    estilo.configure("Editor.TButton", background="#303030", foreground=FG, padding=7)
    estilo.map("Editor.TButton", background=[("active", "#404040"), ("pressed", ACCENT)], foreground=[("active", FG)])
    estilo.configure("Editor.Vertical.TScrollbar", background="#303030", troughcolor=BG, arrowcolor=FG)
    # Cores da lista suspensa nativa dos comboboxes (quando suportadas pelo Tk).
    try:
        janela_ed.option_add("*TCombobox*Listbox.background", INPUT)
        janela_ed.option_add("*TCombobox*Listbox.foreground", FG)
        janela_ed.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        janela_ed.option_add("*TCombobox*Listbox.selectForeground", "#000000")
    except tk.TclError:
        pass
    raiz = ttk.Frame(janela_ed, style="Editor.TFrame", padding=12)
    raiz.pack(fill="both", expand=True)

    topo = ttk.Frame(raiz, style="Editor.TFrame")
    topo.pack(fill="x")
    ttk.Label(topo, style="Editor.TLabel", text="Música cadastrada:").pack(side="left")
    chaves = list(base)
    nomes = [f'{v.get("musica", k.split("|")[0])} — {v.get("artista", k.split("|")[-1])}' for k,v in base.items()]
    selecao = ttk.Combobox(topo, style="Editor.TCombobox", values=nomes, state="readonly", width=62)
    selecao.pack(side="left", padx=7, fill="x", expand=True)
    ttk.Button(topo, style="Editor.TButton", text="Nova música", command=lambda: nova()).pack(side="left")
    ttk.Button(topo, style="Editor.TButton", text="Duplicar timbres", command=lambda: duplicar()).pack(side="left", padx=5)

    linha = ttk.Frame(raiz, style="Editor.TFrame")
    linha.pack(fill="x", pady=9)
    campos = {}
    for label, campo, largura in [("Música", "musica", 33), ("Artista", "artista", 28), ("Afinação", "afinacao", 28)]:
        bloco = ttk.Frame(linha, style="Editor.TFrame")
        bloco.pack(side="left", fill="x", expand=True, padx=3)
        ttk.Label(bloco, style="Editor.TLabel", text=label).pack(anchor="w")
        ent = ttk.Entry(bloco, style="Editor.TEntry", width=largura)
        ent.pack(fill="x")
        campos[campo] = ent

    obs_frame = ttk.Frame(raiz, style="Editor.TFrame")
    obs_frame.pack(fill="x")
    ttk.Label(obs_frame, style="Editor.TLabel", text="Observações").pack(anchor="w")
    observacoes = tk.Text(obs_frame, height=3, wrap="word", bg=INPUT, fg=FG, insertbackground=FG, selectbackground="#146d38", relief="flat", padx=8, pady=6)
    observacoes.pack(fill="x")

    faixa = ttk.Frame(raiz, style="Editor.TFrame")
    faixa.pack(fill="x", pady=8)
    ttk.Label(faixa, style="Editor.TLabel", text="Timbre/variante:").pack(side="left")
    variante = ttk.Combobox(faixa, style="Editor.TCombobox", width=24, state="readonly")
    variante.pack(side="left", padx=7)
    ttk.Button(faixa, style="Editor.TButton", text="+ Adicionar variante", command=lambda: adicionar_variante()).pack(side="left", padx=5)
    ttk.Button(faixa, style="Editor.TButton", text="Excluir variante", command=lambda: excluir_variante()).pack(side="left", padx=5)

    canvas = tk.Canvas(raiz, highlightthickness=0, bg=BG)
    barra = ttk.Scrollbar(raiz, style="Editor.Vertical.TScrollbar", orient="vertical", command=canvas.yview)
    interno = ttk.Frame(canvas, style="Editor.TFrame", padding=(5, 4))
    interno.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0,0), window=interno, anchor="nw")
    canvas.configure(yscrollcommand=barra.set)
    canvas.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")

    controles = {}
    def secao(titulo, itens):
        frame = ttk.LabelFrame(interno, style="Editor.TLabelframe", text=titulo, padding=9)
        frame.pack(fill="x", pady=5)
        for i,(caminho,rotulo,opcoes) in enumerate(itens):
            row, col = divmod(i, 3)
            sub = ttk.Frame(frame, style="Editor.TFrame")
            sub.grid(row=row, column=col, sticky="ew", padx=7, pady=4)
            frame.columnconfigure(col, weight=1)
            ttk.Label(sub, style="Editor.TLabel", text=rotulo).pack(anchor="w")
            widget = ttk.Combobox(sub, style="Editor.TCombobox", values=opcoes, width=25) if opcoes else ttk.Entry(sub, style="Editor.TEntry", width=27)
            widget.pack(fill="x")
            controles[caminho] = widget

    secao("Guitarra", [(("guitarra", k), r, None) for k,r in [
        ("captador","Captador"), ("volume","Volume"), ("tone","Tone")]])
    secao("Amplificador", [(("amplificador", k), r, o) for k,r,o in [
        ("voice","Voice",VOICES),("gain","Gain",None),("bass","Bass",None),
        ("middle","Middle",None),("treble","Treble",None),("isf","ISF",None),
        ("tvp","TVP",TVPS)]])
    for grupo, nome, itens in [
        ("modulation","Modulação",["type","depth","mix","speed","tap"]),
        ("delay","Delay",["type","level","feedback","time","tap"]),
        ("reverb","Reverb",["type","level","size"])]:
        secao(nome, [(("efeitos",grupo,k),k.title(),TIPOS[grupo] if k=="type" else None) for k in itens])

    ttk.Label(raiz, style="Editor.TLabel", text=f"JSON será salvo em: {base_json}").pack(anchor="w", pady=(4, 0))

    rodape = ttk.Frame(janela_ed, style="Editor.TFrame", padding=12)
    rodape.pack(fill="x")
    ttk.Label(rodape, style="Editor.TLabel", text="Destino exclusivo dos .bstar:").pack(side="left")
    pasta = ttk.Entry(rodape, style="Editor.TEntry")
    pasta.insert(0, str(PASTA_BLACKSTAR))
    pasta.pack(side="left", fill="x", expand=True, padx=8)
    ttk.Button(rodape, style="Editor.TButton", text="Salvar JSON e gerar .bstar", command=lambda: salvar()).pack(side="right")

    atual = {"chave": None, "dados": {}, "variante": None, "variantes": {}}

    def set_entry(widget, valor):
        widget.delete(0, tk.END)
        widget.insert(0, str(valor if valor is not None else ""))

    def preencher_variante(nome):
        dados = atual["variantes"].get(nome, {})
        for caminho, widget in controles.items():
            val = dados
            for parte in caminho:
                val = val.get(parte, {}) if isinstance(val, dict) else {}
            set_entry(widget, val if not isinstance(val, dict) else "")
        atual["variante"] = nome

    def recolher_variante():
        nome = atual["variante"]
        if nome is None:
            return
        dados = copy.deepcopy(atual["variantes"].get(nome, {}))
        for caminho, widget in controles.items():
            alvo = dados
            for parte in caminho[:-1]:
                alvo = alvo.setdefault(parte, {})
            alvo[caminho[-1]] = widget.get().strip()
        atual["variantes"][nome] = dados

    def mudar_variante(event=None):
        recolher_variante()
        preencher_variante(variante.get())

    def preencher_musica(chave):
        atual["chave"] = chave
        dados = copy.deepcopy(base.get(chave, {})) if chave else {}
        atual["dados"] = dados
        for nome in campos:
            set_entry(campos[nome], dados.get(nome,""))
        observacoes.delete("1.0",tk.END)
        observacoes.insert("1.0",dados.get("observacoes",""))
        if isinstance(dados.get("timbres"),dict) and dados["timbres"]:
            atual["variantes"] = copy.deepcopy(dados["timbres"])
        else:
            atual["variantes"] = {"principal":copy.deepcopy(dados)}
        variante["values"] = list(atual["variantes"])
        primeiro = next(iter(atual["variantes"]))
        variante.set(primeiro)
        atual["variante"] = None
        preencher_variante(primeiro)

    def escolher(event=None):
        i = selecao.current()
        if i >= 0:
            preencher_musica(chaves[i])

    def nova():
        selecao.set("")
        preencher_musica(None)
        for nome in campos:
            set_entry(campos[nome],"")
        observacoes.delete("1.0",tk.END)

    def duplicar():
        # Cria uma música nova copiando os ajustes que estão no editor.
        recolher_variante()
        atual["chave"] = None
        selecao.set("")
        set_entry(campos["musica"], "")
        set_entry(campos["artista"], "")
        campos["musica"].focus_set()

    def adicionar_variante():
        recolher_variante()
        nome = tk.simpledialog.askstring("Nova variante", "Nome da variante (ex.: clean, drive, solo):", parent=janela_ed)
        if not nome:
            return
        nome = nome.strip().lower()
        if nome in atual["variantes"]:
            messagebox.showwarning("Variante existente", "Essa variante já existe.", parent=janela_ed)
            return
        atual["variantes"][nome] = copy.deepcopy(atual["variantes"].get(atual["variante"], {}))
        variante["values"] = list(atual["variantes"])
        variante.set(nome)
        preencher_variante(nome)

    def excluir_variante():
        if len(atual["variantes"]) <= 1:
            messagebox.showwarning("Não permitido","Mantenha pelo menos um timbre.",parent=janela_ed)
            return
        nome = variante.get()
        if messagebox.askyesno("Excluir variante",f"Excluir a variante {nome}?",parent=janela_ed):
            del atual["variantes"][nome]
            primeiro = next(iter(atual["variantes"]))
            variante["values"] = list(atual["variantes"])
            variante.set(primeiro)
            atual["variante"] = None
            preencher_variante(primeiro)

    def salvar():
        try:
            recolher_variante()
            nome = campos["musica"].get().strip()
            artista = campos["artista"].get().strip()
            if not nome or not artista:
                raise ValueError("Informe música e artista.")
            chave = chave_musica(nome, artista)
            if chave in base and chave != atual["chave"]:
                if not messagebox.askyesno("Já cadastrada", "Essa chave já existe. Deseja sobrescrever?", parent=janela_ed):
                    return
            registro = copy.deepcopy(atual["dados"])
            registro.update(musica=nome, artista=artista,
                            afinacao=campos["afinacao"].get().strip(),
                            observacoes=observacoes.get("1.0",tk.END).strip())
            variantes = copy.deepcopy(atual["variantes"])
            if len(variantes)==1 and "principal" in variantes:
                registro.pop("timbres",None)
                registro.update({
                    k: copy.deepcopy(variantes["principal"].get(k, {}))
                    for k in ("guitarra", "amplificador", "efeitos")
                })
                registro["observacoes"] = observacoes.get("1.0",tk.END).strip()
            else:
                registro["timbres"] = variantes
                registro["tipo_timbre"] = "multi"
                registro["timbre_padrao"] = registro.get("timbre_padrao") if registro.get("timbre_padrao") in variantes else next(iter(variantes))
            for v in variantes.values():
                amp = v.get("amplificador",{})
                fx = v.get("efeitos",{})
                if not amp.get("voice") or not amp.get("tvp"):
                    raise ValueError("Preencha Voice e TVP em todos os timbres.")
                for grupo in ("modulation","delay","reverb"):
                    if not fx.get(grupo,{}).get("type"):
                        raise ValueError(f"Selecione o tipo de {grupo} em todos os timbres.")
            novo = copy.deepcopy(base)
            if atual["chave"] and atual["chave"] != chave:
                novo.pop(atual["chave"],None)
            novo[chave] = registro
            remover_nomes_antigos(novo)
            resultado = renumerar_timbres(novo)
            destino = Path(pasta.get().strip()).expanduser()
            if not destino.is_dir():
                raise ValueError(f"Pasta Blackstar não encontrada:\n{destino}\n\nConfirme o caminho antes de salvar.")
            if not messagebox.askyesno(
                "Confirmar exportação",
                "A numeração será recalculada para toda a base. "
                "Isso pode renomear presets antigos e substituir arquivos .bstar "
                "na pasta Blackstar. Um backup será criado antes. Continuar?",
                parent=janela_ed
            ):
                return
            with tempfile.TemporaryDirectory() as tmp:
                temporaria = Path(tmp)
                total = gerar_patches(novo,temporaria)
                if not total:
                    raise ValueError("Nenhum patch foi gerado.")
                # JSON temporário ao lado dos scripts, nunca na pasta Blackstar.
                json_tmp = base_json.with_name(base_json.name + ".novo")
                json_tmp.write_text(json.dumps(novo,ensure_ascii=False,indent=4),encoding="utf-8")
                # Backup antes de sobrescrever o JSON ou qualquer patch existente.
                pasta_backup = base_json.parent / "backups_timbres" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                pasta_backup.mkdir(parents=True,exist_ok=False)
                shutil.copy2(base_json,pasta_backup/base_json.name)
                patches_backup = pasta_backup/"patches"
                patches_backup.mkdir()
                for arquivo in temporaria.glob("*.bstar"):
                    existente = destino/arquivo.name
                    if existente.exists():
                        shutil.copy2(existente,patches_backup/arquivo.name)
                # A renumeração original pode mudar números de presets antigos.
                # Portanto exportamos a coleção inteira, não só os novos.
                for arquivo in temporaria.glob("*.bstar"):
                    os.replace(arquivo,destino/arquivo.name)
                os.replace(json_tmp,base_json)
            base.clear()
            base.update(novo)
            ao_salvar()
            messagebox.showinfo("Concluído",
                f"JSON salvo.\n{resultado['musicas']} músicas processadas.\n"
                f"{resultado['presets_unicos']} presets únicos exportados.\n"
                f"Backup: {pasta_backup}",parent=janela_ed)
            janela_ed.destroy()
        except Exception as erro:
            messagebox.showerror("Erro ao salvar",str(erro),parent=janela_ed)

    import tkinter.simpledialog
    variante.bind("<<ComboboxSelected>>",mudar_variante)
    selecao.bind("<<ComboboxSelected>>",escolher)
    nova()
