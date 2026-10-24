import tkinter as tk
from tkinter import ttk
from editor_timbres import open_editor # type: ignore


def start_interface(get_current_song, get_next_song, get_tone,
                     format_tone, extract_ms, base_json, song_bracket, reload_tones):
    def update_interface():
        nonlocal delay_ms, modulation_ms

        name, artist = get_current_song()

        text_tone.delete("1.0", tk.END)

        if not name:
            song_var.set("No song playing")
            artist_var.set("")
            next_var.set("Next: not identified")
            text_tone.insert(tk.END, "Open Spotify and play a song.")
            delay_ms = None
            modulation_ms = None
            return

        song_var.set(name)
        artist_var.set(artist)

        tone = get_tone(name, artist)

        if tone:
            text_tone.insert(tk.END, format_tone(tone))

            if isinstance(tone.get("timbres", tone.get("tones")), dict) and tone.get("timbres", tone.get("tones", {})):
                name_standart = tone.get("standart_tone", tone.get("timbre_padrao", tone.get("tone_standart", "drive")))

                if name_standart not in tone.get("timbres", tone.get("tones", {})):
                    name_standart = next(iter(tone.get("timbres", tone.get("tones", {}))), None)

                fx = tone.get("timbres", tone.get("tones", {})).get(name_standart, {}).get("efeitos", {})
            else:
                fx = tone.get("efeitos", {})

            if fx:
                delay_ms = extract_ms(fx.get("delay", {}).get("tap"))
                modulation_ms = extract_ms(fx.get("modulation", {}).get("tap"))
            else:
                delay_ms = None
                modulation_ms = None

        else:
            text_tone.insert(tk.END, "Tone not registered for this song.")
            delay_ms = None
            modulation_ms = None

        next_name, next_artist = get_next_song()

        if next_name:
            next_var.set(f"Next: {next_name} - {next_artist}")
        else:
            next_var.set("Next: not identified")

    def update_automatically():
        update_interface()
        window.after(5000, update_automatically)

    def blink_led_delay():
        if delay_ms:
            canvas.itemconfig(led_delay, fill="#00ff66")
            window.after(120, lambda: canvas.itemconfig(led_delay, fill="#003d18"))
            window.after(delay_ms, blink_led_delay)
        else:
            canvas.itemconfig(led_delay, fill="#202020")
            window.after(500, blink_led_delay)

    def blink_led_modulation():
        if modulation_ms:
            canvas.itemconfig(led_modulation, fill="#00aaff")
            window.after(120, lambda: canvas.itemconfig(led_modulation, fill="#003344"))
            window.after(modulation_ms, blink_led_modulation)
        else:
            canvas.itemconfig(led_modulation, fill="#202020")
            window.after(500, blink_led_modulation)

    window = tk.Tk()
    window.title("Spotify tone Finder")
    window.geometry("780x700")
    window.configure(bg="#121212")

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Arial", 11), padding=8)

    delay_ms = None
    modulation_ms = None

    title = tk.Label(
        window,
        text="Spotify tone Finder",
        font=("Arial", 22, "bold"),
        bg="#121212",
        fg="#1DB954"
    )
    title.pack(pady=12)

    song_var = tk.StringVar(value="No song detected")
    artist_var = tk.StringVar(value="")
    next_var = tk.StringVar(value="Next: not identified")

    label_song = tk.Label(
        window,
        textvariable=song_var,
        font=("Arial", 16, "bold"),
        bg="#121212",
        fg="white"
    )
    label_song.pack()

    label_artist = tk.Label(
        window,
        textvariable=artist_var,
        font=("Arial", 13),
        bg="#121212",
        fg="#b3b3b3"
    )
    label_artist.pack(pady=3)

    label_next = tk.Label(
        window,
        textvariable=next_var,
        font=("Arial", 11),
        bg="#121212",
        fg="#f5c542"
    )
    label_next.pack(pady=5)

    frame_leds = tk.Frame(window, bg="#121212")
    frame_leds.pack(pady=8)

    canvas = tk.Canvas(frame_leds, width=360, height=55, bg="#121212", highlightthickness=0)
    canvas.pack()

    canvas.create_text(80, 28, text="Delay Tap", fill="white", font=("Arial", 11))
    led_delay = canvas.create_oval(145, 15, 175, 45, fill="#202020", outline="#555555")

    canvas.create_text(245, 28, text="Mod Tap", fill="white", font=("Arial", 11))
    led_modulation = canvas.create_oval(305, 15, 335, 45, fill="#202020", outline="#555555")

    button = ttk.Button(
        window,
        text="Update now",
        command=update_interface
    )
    button.pack(pady=8)

    def open_manager():
        def after_saving():
            reload_tones()
            update_interface()
        open_editor(window, base_json, song_bracket, after_saving)

    ttk.Button(
        window,
        text="Manage songs and tones",
        command=open_manager
    ).pack(pady=5)

    frame_text = tk.Frame(window, bg="#121212")
    frame_text.pack(fill="both", expand=True, padx=20, pady=10)

    text_tone = tk.Text(
        frame_text,
        font=("Consolas", 11),
        bg="#181818",
        fg="white",
        insertbackground="white",
        wrap="word",
        relief="flat",
        padx=15,
        pady=15
    )
    text_tone.pack(fill="both", expand=True)



    update_interface()
    update_automatically()
    blink_led_delay()
    blink_led_modulation()

    window.mainloop()
