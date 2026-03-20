"""
app.py
------
TAPAS — Tapping Application for Perception–Action Synchronization

Android application built with the BeeWare framework (Briefcase v. 0.3.22, Toga v. 0.5.0).
Targets Android API level 24 (Android 7.0) and above, compiled via the Chaquopy build system.

The application presents a full-screen tap surface. On each touch event:
  - A randomized background color is applied as visual feedback
  - An auditory feedback sound is played via Android's native SoundPool API
  - A TAP_EVENT entry is emitted to the Android system log (logcat),
    which is captured in real time by the acquisition PC via ADB

The auditory feedback sound can be customized by replacing the file in
src/TAPAS/resources/ and updating the filename in load_sound() accordingly.

@author: Francesco Carlomagno — calumaxs@gmail.com
"""

import toga
from toga.style import Pack
from toga.constants import SANS_SERIF, Baseline
import os
import random

# SoundPool is an Android-native API — import is only available at runtime on Android.
# On desktop (e.g. during development/testing), the import will fail gracefully.
try:
    from android.media import AudioManager, SoundPool
    ANDROID = True
except ImportError:
    ANDROID = False


class TAPAS(toga.App):

    def startup(self):
        """Initialize the application UI: a single full-screen canvas widget."""
        self.canvas = toga.Canvas(style=Pack(flex=1, background_color='lightskyblue'))
        self.canvas.on_press = self.on_canvas_press
        self.canvas.on_draw = self.on_canvas_draw

        main_container = toga.Box(style=Pack(flex=1))
        main_container.add(self.canvas)

        self.main_window = toga.MainWindow(title=self.name)
        self.main_window.content = main_container
        self.main_window.show()

        self.load_sound()

    def load_sound(self):
        """
        Load the tap feedback sound using Android's SoundPool API.
        The audio file must be placed in src/TAPAS/resources/ before building.
        To use a different sound, replace 'tap_sound2.wav' with your filename here.
        On non-Android platforms, sound playback is silently skipped.
        """
        if ANDROID:
            sound_path = os.path.join(self.paths.app, "resources", "tap_sound2.wav")
            if os.path.exists(sound_path):
                # SoundPool(maxStreams, streamType, srcQuality)
                self.soundPool = SoundPool(5, AudioManager.STREAM_MUSIC, 0)
                self.soundId = self.soundPool.load(sound_path, 1)
            else:
                print("Audio file not found:", sound_path)
                self.soundPool = None
        else:
            self.soundPool = None

    def play_sound(self):
        """Play the preloaded tap sound. Prints 'Beep!' on desktop for debug purposes."""
        if ANDROID and self.soundPool:
            # play(soundID, leftVolume, rightVolume, priority, loop, rate)
            self.soundPool.play(self.soundId, 1, 1, 0, 0, 1)
        else:
            print("Beep!")  # Desktop fallback for debugging

    def on_canvas_press(self, widget, x, y):
        """
        Handle a tap (touch press) event on the canvas.
        - Randomizes the background color as visual feedback
        - Plays the auditory feedback sound
        - Emits 'TAP_EVENT' to logcat, which is captured by the acquisition PC via ADB
        """
        widget.style.background_color = self.get_random_color()
        widget.refresh()
        self.play_sound()
        print("TAP_EVENT")  # This string is monitored by the ADB logcat reader on the PC

    def get_random_color(self):
        """Generate a random RGB color string for canvas background feedback."""
        r = random.random()
        g = random.random()
        b = random.random()
        return f'rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})'

    def on_canvas_draw(self, canvas, context, draw_text):
        """Redraw the canvas background with the current background color."""
        context.set_source_color(canvas.style.background_color)
        context.rectangle(0, 0, canvas.layout.width, canvas.layout.height)
        context.fill()


def main():
    return TAPAS("TAPAS", app_id="org.example.tapas")


if __name__ == "__main__":
    main().main_loop()