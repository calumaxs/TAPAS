import toga
from toga.style import Pack
from toga.style.pack import COLUMN, CENTER
import os
import random

try:
    from android.media import AudioManager, SoundPool
    from os.path import join
    ANDROID = True
except ImportError:
    ANDROID = False


class APPTapping(toga.App):
    def startup(self):
        """ Inizializza l'interfaccia utente di Toga. """
        self.main_box = toga.Box(style=Pack(direction=COLUMN, alignment=CENTER, flex=1))

        # Crea il pulsante di tapping a schermo intero
        self.tap_button = toga.Button(
            "🎵 TAP! 🎵",
            on_press=self.on_button_press,
            style=Pack(
                flex=1,  # Occupa tutto lo spazio disponibile
                font_size=50,  # Font grande
                text_align=CENTER,
                color="white",  # Testo bianco
                background_color="#FF69B4",  # Rosa vivace
                padding=20,
                width=550, 
                height=800
            )
        )
        self.main_box.add(self.tap_button)

        # Inizializza la finestra principale
        self.main_window = toga.MainWindow(title="Tapping Task")
        self.main_window.content = self.main_box
        self.main_window.show()

        # Carica il suono
        self.load_sound()

    def load_sound(self):
        """ Carica il suono in memoria per l'uso su Android. """
        if ANDROID:
            sound_path = os.path.join(self.paths.app, "resources", "tap_sound.mp3")
            if os.path.exists(sound_path):
                self.soundPool = SoundPool(5, AudioManager.STREAM_MUSIC, 0)
                self.soundId = self.soundPool.load(sound_path, 1)
            else:
                self.soundPool = None
        else:
            self.soundPool = None

    def play_sound(self):
        """ Riproduce un suono su Android o usa un fallback per desktop. """
        if ANDROID and self.soundPool:
            self.soundPool.play(self.soundId, 1, 1, 0, 0, 1)
        else:
            print("Beep!")  # Fallback su desktop

    def on_button_press(self, widget):
        """ Cambia colore e riproduce il suono al tap. """
        # Cambia colore a caso
        random_color = "#{:02x}{:02x}{:02x}".format(
            random.randint(100, 255),
            random.randint(100, 255),
            random.randint(100, 255)
        )
        widget.style.background_color = random_color

        # Riproduce il suono
        self.play_sound()



def main():
    return APPTapping("Tapping Task", app_id="org.example.tapping")


if __name__ == "__main__":
    main().main_loop()