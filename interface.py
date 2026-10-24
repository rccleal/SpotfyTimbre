import tkinter as tk
from tkinter import ttk
from editor_timbres import abrir_editor # type: ignore


def iniciar_interface(pegar_musica_atual, pegar_proxima_musica, pegar_timbre,
                     formatar_timbre, extrair_ms, base_json, chave_musica, recarregar_timbres):
    def atualizar_interface():
        nonlocal delay_ms, modulation_ms

        nome, artista = pegar_musica_atual()

        texto_timbre.delete("1.0", tk.END)

        if not nome:
            musica_var.set("Nenhuma música tocando")
            artista_var.set("")
            proxima_var.set("Próxima: não identificada")
            texto_timbre.insert(tk.END, "Abra o Spotify e toque uma música.")
            delay_ms = None
            modulation_ms = None
            return

        musica_var.set(nome)
        artista_var.set(artista)

        timbre = pegar_timbre(nome, artista)

        if timbre:
            texto_timbre.insert(tk.END, formatar_timbre(timbre))

            if "timbres" in timbre:
                nome_padrao = timbre.get("timbre_padrao", "drive")

                if nome_padrao not in timbre["timbres"]:
                    nome_padrao = list(timbre["timbres"].keys())[0]

                fx = timbre["timbres"][nome_padrao].get("efeitos", {})
            else:
                fx = timbre.get("efeitos", {})

            if fx:
                delay_ms = extrair_ms(fx["delay"].get("tap"))
                modulation_ms = extrair_ms(fx["modulation"].get("tap"))
            else:
                delay_ms = None
                modulation_ms = None

        else:
            texto_timbre.insert(tk.END, "Timbre não cadastrado para essa música.")
            delay_ms = None
            modulation_ms = None

        prox_nome, prox_artista = pegar_proxima_musica()

        if prox_nome:
            proxima_var.set(f"Próxima: {prox_nome} - {prox_artista}")
        else:
            proxima_var.set("Próxima: não identificada")

    def atualizar_automaticamente():
        atualizar_interface()
        janela.after(5000, atualizar_automaticamente)

    def piscar_led_delay():
        if delay_ms:
            canvas.itemconfig(led_delay, fill="#00ff66")
            janela.after(120, lambda: canvas.itemconfig(led_delay, fill="#003d18"))
            janela.after(delay_ms, piscar_led_delay)
        else:
            canvas.itemconfig(led_delay, fill="#202020")
            janela.after(500, piscar_led_delay)

    def piscar_led_modulation():
        if modulation_ms:
            canvas.itemconfig(led_modulation, fill="#00aaff")
            janela.after(120, lambda: canvas.itemconfig(led_modulation, fill="#003344"))
            janela.after(modulation_ms, piscar_led_modulation)
        else:
            canvas.itemconfig(led_modulation, fill="#202020")
            janela.after(500, piscar_led_modulation)

    janela = tk.Tk()
    janela.title("Spotify Timbre Finder")
    janela.geometry("780x700")
    janela.configure(bg="#121212")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Arial", 11), padding=8)

    delay_ms = None
    modulation_ms = None

    titulo = tk.Label(
        janela,
        text="Spotify Timbre Finder",
        font=("Arial", 22, "bold"),
        bg="#121212",
        fg="#1DB954"
    )
    titulo.pack(pady=12)

    musica_var = tk.StringVar(value="Nenhuma música detectada")
    artista_var = tk.StringVar(value="")
    proxima_var = tk.StringVar(value="Próxima: não identificada")

    label_musica = tk.Label(
        janela,
        textvariable=musica_var,
        font=("Arial", 16, "bold"),
        bg="#121212",
        fg="white"
    )
    label_musica.pack()

    label_artista = tk.Label(
        janela,
        textvariable=artista_var,
        font=("Arial", 13),
        bg="#121212",
        fg="#b3b3b3"
    )
    label_artista.pack(pady=3)

    label_proxima = tk.Label(
        janela,
        textvariable=proxima_var,
        font=("Arial", 11),
        bg="#121212",
        fg="#f5c542"
    )
    label_proxima.pack(pady=5)

    frame_leds = tk.Frame(janela, bg="#121212")
    frame_leds.pack(pady=8)

    canvas = tk.Canvas(frame_leds, width=360, height=55, bg="#121212", highlightthickness=0)
    canvas.pack()

    canvas.create_text(80, 28, text="Delay Tap", fill="white", font=("Arial", 11))
    led_delay = canvas.create_oval(145, 15, 175, 45, fill="#202020", outline="#555555")

    canvas.create_text(245, 28, text="Mod Tap", fill="white", font=("Arial", 11))
    led_modulation = canvas.create_oval(305, 15, 335, 45, fill="#202020", outline="#555555")

    botao = ttk.Button(
        janela,
        text="Atualizar agora",
        command=atualizar_interface
    )
    botao.pack(pady=8)

    def abrir_gerenciador():
        def apos_salvar():
            recarregar_timbres()
            atualizar_interface()
        abrir_editor(janela, base_json, chave_musica, apos_salvar)

    ttk.Button(
        janela,
        text="Gerenciar músicas e timbres",
        command=abrir_gerenciador
    ).pack(pady=5)

    frame_texto = tk.Frame(janela, bg="#121212")
    frame_texto.pack(fill="both", expand=True, padx=20, pady=10)

    texto_timbre = tk.Text(
        frame_texto,
        font=("Consolas", 11),
        bg="#181818",
        fg="white",
        insertbackground="white",
        wrap="word",
        relief="flat",
        padx=15,
        pady=15
    )
    texto_timbre.pack(fill="both", expand=True)



    atualizar_interface()
    atualizar_automaticamente()
    piscar_led_delay()
    piscar_led_modulation()

    janela.mainloop()
