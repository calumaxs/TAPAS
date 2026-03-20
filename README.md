# TAPAS — Tapping Application for Perception–Action Synchronization

TAPAS is an open-source Android application for individual and joint finger-tapping tasks, developed for single- and multi-person behavioral and neurophysiological (EEG/hyperscanning) research.

## Overview

TAPAS provides a full-screen touch surface that detects tap onsets and emits timestamped events retrievable in real time from the acquisition PC via the Android Debug Bridge (ADB). The application supports both paced tapping paradigms (with an external metronome presented via PsychoPy) and free/dyadic synchronization paradigms (without external pacing). It is designed to interface directly with EEG acquisition systems via hardware triggers.

## Repository Structure

```
TAPAS/
├── src/
│   └── TAPAS/
│       ├── app.py              # Main Android application (Toga/BeeWare)
│       ├── __init__.py
│       ├── __main__.py
│       └── resources/          # Place your tap sound file here (e.g. tap_sound.wav)
├── psychopy_scripts/
│   ├── TAPAS_metronomo.py      # PsychoPy script — paced tapping condition
│   └── TAPAS_syncro.py         # PsychoPy script — dyadic synchronization condition
├── pyproject.toml              # Briefcase build configuration
├── LICENSE
└── README.md
```

## Requirements

### Android Application
- [Python 3.9](https://www.python.org/downloads/release/python-3912/)
- [BeeWare Briefcase 0.3.22](https://beeware.org) — build and packaging
- [Toga 0.5.0](https://toga.readthedocs.io) — GUI framework
- Android device running Android 7.0 (API level 24) or above

### PsychoPy Acquisition Scripts
- [PsychoPy 2025.1.1](https://www.psychopy.org)
- pyserial
- Android Debug Bridge (ADB) installed and available in system PATH
- Two Android devices running TAPAS, connected via USB
- Brain Products TriggerBox (optional — scripts run without it if not connected)

## Building the App

1. Create and activate a virtual environment:
```bash
python -m venv beeware-venv
beeware-venv\Scripts\activate        # Windows
source beeware-venv/bin/activate     # macOS/Linux
```

2. Install dependencies:
```bash
pip install briefcase==0.3.22
pip install toga==0.5.0
```

3. Place your tap feedback sound file (`.wav` or `.mp3`) in `src/TAPAS/resources/` and update the filename in `app.py` accordingly:
```python
sound_path = os.path.join(self.paths.app, "resources", "your_sound_file.wav")
```

4. Build and run:
```bash
briefcase build android
briefcase run android
```

## Using the PsychoPy Scripts

Two acquisition scripts are provided in `psychopy_scripts/`:

- **`TAPAS_metronomo.py`** — for paced tapping conditions. Presents an isochronous metronome via PsychoPy audio and monitors tap events from two tablets simultaneously via ADB. Sends EEG triggers at each metronome onset.
- **`TAPAS_syncro.py`** — for dyadic/free synchronization conditions. No metronome is presented. Monitors tap events from two tablets for a fixed session duration.

Both scripts require two Android devices running TAPAS to be connected via USB and authorized via ADB before launch. Output is saved as semicolon-separated CSV files in `./csv_files/`.

To run:
```bash
python TAPAS_metronomo.py
python TAPAS_syncro.py
```

## Customization

- **Tap sound**: replace the audio file in `src/TAPAS/resources/` and update the filename in `app.py` before building. Different devices can use different sounds.
- **Number of devices**: additional tablets can be monitored by adding ADB logcat subprocesses and corresponding threads in the acquisition scripts.
- **EEG system**: the trigger-sending logic uses standard serial port communication and can be adapted to any EEG system that accepts serial triggers, not just the Brain Products TriggerBox.
- **Session duration**: in `TAPAS_syncro.py`, the session length (default: 360 s) can be modified in the `timer()` function.
- **Metronome**: in `TAPAS_metronomo.py`, the number of beats (`num_sound`) and inter-stimulus interval (`isi`) can be adjusted in the `metronomo()` function.

## Citation

If you use TAPAS in your research, please cite:

> Carraturo G., Matarrelli B., Keller P.E., Bevilacqua V., Sibilano E., Brunetti A., Brattico E.\*, Carlomagno F.\* (in preparation). TAPAS: A Mobile App for Individual and Joint Finger-Tapping in Multi-person Behavioral and Neurophysiological Research. *Royal Society Open Science*. \*shared last authors

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
