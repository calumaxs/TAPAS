"""
APPTapping_metronomo.py
-----------------------
PsychoPy acquisition script for the PACED TAPPING condition.

This script runs on the stimulation PC and handles:
  - Metronome stimulus presentation via PsychoPy audio engine (pyo backend)
  - Real-time tap event capture from two Android tablets via ADB (USB)
  - EEG trigger sending via Brain Products TriggerBox (serial port)
  - Timestamping of all events using PsychoPy core.Clock()
  - CSV and log file output per subject

Requirements:
  - PsychoPy (v. 2025.1.1 or later)
  - pyserial
  - Android Debug Bridge (ADB) installed and in system PATH
  - Two Android tablets running the APPTapping app, connected via USB
  - Brain Products TriggerBox connected via USB (optional, gracefully skipped if absent)
  - A metronome audio file named 'metronomo.wav' in the same directory as this script

Output files (saved in ./csv_files/ and ./log_files/):
  - Subj_<ID>.csv  : semicolon-separated log with columns: subj; time; event
  - Subj_<ID>.log  : PsychoPy log file

Created on Mon Apr 15 14:15 2025
@author: Francesco Carlomagno — calumaxs@gmail.com
"""

from psychopy import prefs
prefs.hardware['audioLib'] = ['pyo']  # Use pyo audio backend for lower latency
from psychopy import sound, visual, core, event, gui, logging
import subprocess
import threading
import time
import serial
import serial.tools.list_ports
import sys
import os

# ─────────────────────────────────────────────
# DIRECTORY SETUP
# ─────────────────────────────────────────────
logdir = os.getcwd()  # All output files are saved relative to the working directory

if not os.path.exists(logdir + '/csv_files'):
    os.makedirs(logdir + '/csv_files')
    print("Directory csv_files created.")
if not os.path.exists(logdir + '/log_files'):
    os.makedirs(logdir + '/log_files')
    print("Directory log_files created.")

# ─────────────────────────────────────────────
# EEG TRIGGERBOX SETUP
# ─────────────────────────────────────────────
def trova_porta_eeg():
    """
    Scan available serial ports and return the port associated with the
    Brain Products TriggerBox (identified by USB VID:PID=1103:0022).
    Returns None if no TriggerBox is found.
    """
    porte_disponibili = serial.tools.list_ports.comports()
    for porta in porte_disponibili:
        print(f"Device found: {porta.device}, Description: {porta.description}, HW ID: {porta.hwid}")
        if "USB VID:PID=1103:0022" in porta.hwid:
            print(f"TriggerBox found on port: {porta.device}")
            return porta.device
    return None

porta_eeg = trova_porta_eeg()
port = None
if porta_eeg:
    try:
        port = serial.Serial(porta_eeg, baudrate=2000000, timeout=1)
        print(f"Serial connection established on {porta_eeg}")
    except Exception as e:
        print(f"Error connecting to TriggerBox: {e}")

PulseWidth = 0.01  # Trigger pulse duration in seconds (10 ms)

def send_trigger(device, clock=None):
    """
    Send a binary trigger to the EEG amplifier via the TriggerBox.
    Trigger values: 0x01 for tablet_1, 0x02 for tablet_2.
    A reset byte (0x00) is sent after PulseWidth seconds to complete the pulse.
    If clock is provided, logs and returns the timestamp of the trigger.
    """
    trigger_value = 0x01 if device == "tablet_1" else 0x02
    if port:
        try:
            port.write([trigger_value])
            time.sleep(PulseWidth)
            port.write([0x00])  # Reset trigger line
            print(f"Trigger sent for {device}")
            if clock:
                tempo_trigger = clock.getTime()
                print(f"Trigger time {device}: {tempo_trigger:.4f} s")
                return tempo_trigger
        except Exception as e:
            print(f"Error sending trigger: {e}")
    else:
        print(f"Trigger {trigger_value} for {device} (TriggerBox not connected)")
    return None

# ─────────────────────────────────────────────
# ADB DEVICE DETECTION
# ─────────────────────────────────────────────
# Retrieve the ADB device IDs of the two connected Android tablets.
# The script requires exactly two devices to be connected and authorized via ADB.
adb_devices = subprocess.run(["adb", "devices"], capture_output=True, text=True)
righe = adb_devices.stdout.split("\n")
devices = [riga.split("\t")[0] for riga in righe[1:] if "device" in riga]
if len(devices) < 2:
    print("Error: two tablets must be connected via ADB.")
    sys.exit(1)
tablet_1, tablet_2 = devices[:2]
print(f"Tablet 1: {tablet_1}, Tablet 2: {tablet_2}")

# Clear existing logcat buffers on both devices before starting acquisition
subprocess.run(["adb", "-s", tablet_1, "logcat", "-c"], check=True)
subprocess.run(["adb", "-s", tablet_2, "logcat", "-c"], check=True)

tap_num = 0  # Global tap counter across both devices

# ─────────────────────────────────────────────
# LOGCAT READER (runs in a dedicated thread per device)
# ─────────────────────────────────────────────
def leggi_logcat(device_id, device_name, process, clock=None):
    """
    Continuously reads the ADB logcat stream from a single device.
    When a 'TAP_EVENT' line is detected, the current PsychoPy clock time
    is recorded and written to the CSV log file.

    This function is designed to run in a separate thread for each device,
    enabling simultaneous monitoring of multiple tablets without blocking.

    Parameters:
        device_id   : ADB device serial string (unused here, kept for extensibility)
        device_name : Human-readable label ('tablet_1' or 'tablet_2')
        process     : subprocess.Popen object for the ADB logcat stream
        clock       : PsychoPy core.Clock() instance for timestamping
    """
    global tap_num
    while True:
        line = process.stdout.readline()
        if not line:
            break
        if "TAP_EVENT" in line:
            tap_num += 1
            print(f"{device_name} sent tap #{tap_num}!")
            tempo_risposta = clock.getTime()
            if clock and tempo_risposta is not None:
                print(f"Tap time {device_name}: {tempo_risposta:.4f} s")
                logfile.write(f"{subID};{tempo_risposta:.4f};Risposta_{device_name}\n")

# ─────────────────────────────────────────────
# METRONOME THREAD
# ─────────────────────────────────────────────
def metronomo(clock=None):
    """
    Presents a fixed sequence of isochronous metronome beats using PsychoPy audio.
    At each beat onset:
      - Sends a trigger (0x01) to the EEG amplifier
      - Plays the metronome sound
      - Logs the onset timestamp to the CSV file

    The metronome audio file ('metronomo.wav') must be located in the working directory.
    Stimulus parameters (number of beats, ISI) can be adjusted via num_sound and isi.

    After all beats are presented, this function closes all open resources and exits.
    """
    num_sound = 20      # Total number of metronome beats to present
    isi = 0.450         # Inter-stimulus interval in seconds (450 ms, ~133 BPM)
    stim = sound.Sound(os.path.join(logdir, "metronomo.wav"), volume=1)
    trial_num = 0

    for i in range(num_sound):
        # Send EEG trigger at metronome onset
        try:
            trigger = 0x01
            port.write([trigger])
            time.sleep(PulseWidth)
            port.write([0x00])
        except Exception as e:
            print(f"Error sending metronome trigger: {e}")

        stim.play()
        print(f"Metronome beat #{trial_num}")

        if clock:
            tempo_metronomo = clock.getTime()
            print(f"Metronome time: {tempo_metronomo:.4f} s")
            logfile.write(f"{subID};{tempo_metronomo:.4f};Metronomo\n")

        core.wait(stim.getDuration() + isi)
        trial_num += 1

        if event.getKeys(["escape"]):
            break

    # Close all resources after metronome sequence completes
    logfile.close()
    if port:
        port.close()
    process_1.terminate()
    process_2.terminate()
    print("ADB processes and serial port closed.")
    sys.exit(0)

# ─────────────────────────────────────────────
# LAUNCH ADB LOGCAT SUBPROCESSES AND THREADS
# ─────────────────────────────────────────────
# Each device gets its own subprocess (logcat stream) and a dedicated reader thread.
# thread_3 manages the metronome presentation.
process_1 = subprocess.Popen(["adb", "-s", tablet_1, "logcat"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, bufsize=1)
clock = core.Clock()
thread_1 = threading.Thread(target=leggi_logcat, args=(tablet_1, "tablet_1", process_1, clock))

process_2 = subprocess.Popen(["adb", "-s", tablet_2, "logcat"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, bufsize=1)
thread_2 = threading.Thread(target=leggi_logcat, args=(tablet_2, "tablet_2", process_2, clock))
thread_3 = threading.Thread(target=metronomo, args=(clock,))

thread_1.start()
thread_2.start()

# ─────────────────────────────────────────────
# SUBJECT ID DIALOG AND FILE INITIALIZATION
# ─────────────────────────────────────────────
ID = gui.Dlg(title='Subject ID')
ID.addField('ID: ')
response = ID.show()
subID = response[0].strip()

filename = logdir + f'/csv_files/Subj_{subID}.csv'
print(f"Output file: {filename}")

if os.path.exists(filename):
    err = gui.Dlg(title='Attention')
    err.addText(f'FILE Subj_{subID}.csv ALREADY EXISTS!')
    err.show()
    core.quit()
else:
    logfile = open(filename, 'w')
    logfile.write("subj;time;event\n")
    block_time = core.Clock()
    logging.setDefaultClock(block_time)
    filename_log = f"{logdir}/log_files/Subj_{subID}.log"
    logging.LogFile(filename_log, level=logging.INFO, filemode='a')

if not subID:
    core.quit()

# ─────────────────────────────────────────────
# START EXPERIMENT
# ─────────────────────────────────────────────
core.wait(1)        # Brief pause before starting
thread_3.start()    # Start metronome thread
clock.reset()       # Reset clock to t=0 at experiment onset

# Keep main thread alive until experiment ends or KeyboardInterrupt
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nInterrupted. Closing ADB and serial port.")
    if port:
        port.close()
    logfile.close()
    sys.exit(0)
