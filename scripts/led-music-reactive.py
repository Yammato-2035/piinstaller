#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LEDs des Freenove Computer Case Kit Pro im Rhythmus der Musik steuern.

Voraussetzungen:
  - I2C aktiviert, User in Gruppe i2c
  - Python-Pakete in einer venv (Raspberry Pi OS blockiert systemweites pip):
    ./scripts/setup-led-music-venv.sh
    Dann starten mit: ./scripts/venv-led-music/bin/python scripts/led-music-reactive.py
  - System: sudo apt install -y python3-smbus  (für I2C)

Audio-Eingabe: Standard-Eingabegerät auf "Monitor of [Standard-Sink]" setzen
  (pavucontrol → Eingabe), damit der abgespielte Ton erfasst wird.

Beenden: Strg+C
"""

import sys
import time
import math
import argparse

# I2C / Freenove-Erweiterungsplatine
I2C_ADDR = 0x21
REG_LED_MODE = 0x03
REG_LED_ALL = 0x02
LED_MODE_OFF = 0
LED_MODE_RGB = 1

# Audio: kleine Blöcke = geringere Latenz, besserer Rhythmus
SAMPLE_RATE = 16000
CHUNK_SIZE = 256
UPDATE_RATE = 45  # mehr Updates pro Sekunde = flüssigerer Beat

# Helligkeit
MIN_LEVEL = 0.01
GAIN = 28.0  # starker Ausschlag
# Attack/Release: Beat = sofort hoch, dann abklingen
ATTACK = 0.18   # Pegel steigt → sehr schnell (82 % neuer Wert pro Schritt)
RELEASE = 0.82  # Pegel fällt → sichtbares Abklingen (18 % neuer Wert)
# Farbdurchlauf (Hue 0..1 pro Sekunde)
COLOR_SPEED = 0.4

# Audio-Eingabegerät: None = Standard, sonst Geräte-Index oder -Name
AUDIO_INPUT_DEVICE = None
_audio_device_error_shown = False


def list_audio_devices():
    """Alle Audio-Geräte ausgeben (Eingabe + Ausgabe, für Fehlerbehebung)."""
    try:
        import sounddevice as sd
    except Exception:
        print("sounddevice nicht verfügbar.", file=sys.stderr)
        return
    try:
        default_in = sd.query_devices(kind="input")
        print("Standard-Eingabegerät:", default_in.get("name", default_in), file=sys.stderr)
    except Exception as e:
        print("Kein gültiges Standard-Eingabegerät:", e, file=sys.stderr)
    # query_devices() liefert DeviceList; per Index zugreifen (Iteration kann DeviceList-Objekte liefern)
    raw = sd.query_devices()
    try:
        n = len(raw)
    except TypeError:
        n = 0
    if n == 0:
        print("Keine Geräte von PortAudio zurückgegeben.", file=sys.stderr)
    print("\nAlle Geräte (Index | Name | Eingänge | Ausgänge | Sample-Rate):", file=sys.stderr)
    has_input = False
    for i in range(n):
        dev = raw[i]
        # Gerät als Dict oder Objekt mit Attributen
        if isinstance(dev, dict):
            inp = dev.get("max_input_channels", 0)
            out = dev.get("max_output_channels", 0)
            name = dev.get("name", "?")
            sr = dev.get("default_samplerate", "?")
        else:
            inp = getattr(dev, "max_input_channels", 0)
            out = getattr(dev, "max_output_channels", 0)
            name = getattr(dev, "name", "?")
            sr = getattr(dev, "default_samplerate", "?")
        if inp > 0:
            has_input = True
        nutzbar = " ← als Eingabe nutzbar" if inp > 0 else ""
        print(f"  {i}: {name} | in: {inp} | out: {out} | sr: {sr}{nutzbar}", file=sys.stderr)
    if not has_input:
        print("\nKein Gerät mit Eingängen gefunden. System prüfen:", file=sys.stderr)
        print("  pactl list sources short   bzw.   wpctl status", file=sys.stderr)
    print("\nLösung: In pavucontrol (oder Einstellungen → Sound) das Standard-EINGABEGERÄT", file=sys.stderr)
    print("auf „Monitor of [Ihr Lautsprecher-Sink]“ setzen.", file=sys.stderr)
    print("Oder dieses Skript mit --device <Index> starten, z.B. --device 0", file=sys.stderr)


def get_expansion_bus():
    """SMBus für I2C 0x21 (Freenove-Erweiterungsplatine) öffnen."""
    try:
        import smbus
        bus = smbus.SMBus(1)
        return bus
    except Exception as e:
        print("I2C/SMBus fehlgeschlagen:", e, file=sys.stderr)
        print("Prüfen: I2C aktiviert? User in Gruppe i2c?", file=sys.stderr)
        if "No module named 'smbus'" in str(e):
            print("Bei venv: venv mit System-Paketen neu anlegen:", file=sys.stderr)
            print("  rm -rf scripts/venv-led-music && ./scripts/setup-led-music-venv.sh", file=sys.stderr)
        return None


def set_led_mode(bus, mode):
    if bus is None:
        return
    try:
        bus.write_byte_data(I2C_ADDR, REG_LED_MODE, mode)
    except Exception:
        pass


def set_all_led_color(bus, r, g, b):
    if bus is None:
        return
    try:
        bus.write_i2c_block_data(I2C_ADDR, REG_LED_ALL, [r, g, b])
    except Exception:
        pass


def get_audio_level():
    """Lautstärke vom Eingabegerät (Standard oder --device) lesen.
    Gibt RMS-Normalwert ~0..1 zurück (oder 0 bei Fehler).
    """
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as e:
        print("Fehlende Abhängigkeit:", e, file=sys.stderr)
        print("Bitte venv einrichten: ./scripts/setup-led-music-venv.sh", file=sys.stderr)
        print("Dann starten mit: ./scripts/venv-led-music/bin/python scripts/led-music-reactive.py", file=sys.stderr)
        return 0.0
    except OSError as e:
        if "PortAudio" in str(e):
            print("PortAudio-Bibliothek fehlt:", e, file=sys.stderr)
            print("Installieren: sudo apt install -y libportaudio2", file=sys.stderr)
        else:
            print("Audio-Fehler:", e, file=sys.stderr)
        return 0.0

    # Kanalzahl vom Gerät übernehmen (manche Geräte nur 1, manche nur 2)
    try:
        if AUDIO_INPUT_DEVICE is not None:
            dev = sd.query_devices(AUDIO_INPUT_DEVICE)
        else:
            dev = sd.query_devices(kind="input")
        channels = dev.get("max_input_channels", 2) if isinstance(dev, dict) else getattr(dev, "max_input_channels", 2)
        channels = max(1, min(int(channels), 8))
    except Exception:
        channels = 2

    kwargs = dict(
        frames=CHUNK_SIZE,
        samplerate=SAMPLE_RATE,
        channels=channels,
        dtype="float32",
        blocking=True,
    )
    if AUDIO_INPUT_DEVICE is not None:
        kwargs["device"] = AUDIO_INPUT_DEVICE

    try:
        block = sd.rec(**kwargs)
        # Peak statt RMS: Schläge (Kick, Snare) erzeugen kurze Spitzen → sichtbarer Rhythmus
        peak = float(np.max(np.abs(block)))
        rms = float(np.sqrt(np.mean(block ** 2)))
        # Überwiegend Peak (Rhythmus), wenig RMS (Grundpegel)
        return 0.88 * peak + 0.12 * rms
    except Exception as e:
        global _audio_device_error_shown
        errmsg = str(e)
        print("Audio lesen fehlgeschlagen:", e, file=sys.stderr)
        if not _audio_device_error_shown and ("device -1" in errmsg or "querying device" in errmsg.lower()):
            _audio_device_error_shown = True
            print("", file=sys.stderr)
            list_audio_devices()
        return 0.0


def level_to_brightness(level):
    """Pegel (0..1) in Helligkeit 0..255 mit Mindest-Schwelle und Verstärkung."""
    if level < MIN_LEVEL:
        return 0
    v = min(1.0, level * GAIN)
    return int(255 * v)


def hue_to_rgb(h):
    """Hue 0..1 → (r, g, b) je 0..1 (S=1, V=1)."""
    h = h % 1.0
    i = int(h * 6) % 6
    f = h * 6 - i
    q = 1 - f
    t = f
    if i == 0:
        return (1, t, 0)
    if i == 1:
        return (q, 1, 0)
    if i == 2:
        return (0, 1, t)
    if i == 3:
        return (0, q, 1)
    if i == 4:
        return (t, 0, 1)
    return (1, 0, q)


def level_and_hue_to_rgb(level, hue):
    """Pegel (0..1) + Hue (0..1) → (r, g, b) je 0..255. Farbe läuft durch, Helligkeit folgt Musik."""
    brightness = level_to_brightness(level) / 255.0
    r, g, b = hue_to_rgb(hue)
    return (
        int(255 * min(1.0, r * brightness)),
        int(255 * min(1.0, g * brightness)),
        int(255 * min(1.0, b * brightness)),
    )


def main():
    global AUDIO_INPUT_DEVICE
    parser = argparse.ArgumentParser(description="LEDs im Rhythmus der Musik (Freenove Case)")
    parser.add_argument(
        "--device", "-d",
        type=lambda x: int(x) if x.isdigit() else x,
        default=None,
        help="Audio-Eingabegerät: Index (Zahl) oder Name. Ohne Angabe: Standard-Eingabe.",
    )
    parser.add_argument(
        "--list-devices", "-l",
        action="store_true",
        help="Eingabegeräte auflisten und beenden.",
    )
    args = parser.parse_args()

    if args.list_devices:
        list_audio_devices()
        sys.exit(0)

    AUDIO_INPUT_DEVICE = args.device

    bus = get_expansion_bus()
    if bus is None:
        sys.exit(1)

    print("LED-Musik-Modus – Beenden mit Strg+C")
    if AUDIO_INPUT_DEVICE is not None:
        print("Audio-Eingabe: Gerät", AUDIO_INPUT_DEVICE)
    else:
        print("Audio-Eingabe: Standard-Eingabegerät (z.B. Monitor of Sink)")
    set_led_mode(bus, LED_MODE_RGB)
    time.sleep(0.05)

    envelope = 0.0
    interval = 1.0 / UPDATE_RATE
    t_start = time.monotonic()

    try:
        while True:
            t0 = time.monotonic()
            level = get_audio_level()
            # Attack/Release: Beats springen schnell, klingen weicher ab
            if level > envelope:
                envelope = ATTACK * envelope + (1.0 - ATTACK) * level
            else:
                envelope = RELEASE * envelope + (1.0 - RELEASE) * level
            # Farbdurchlauf: Hue läuft mit der Zeit
            hue = ((t0 - t_start) * COLOR_SPEED) % 1.0
            r, g, b = level_and_hue_to_rgb(envelope, hue)
            set_all_led_color(bus, r, g, b)
            elapsed = time.monotonic() - t0
            sleep_time = max(0.0, interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    except KeyboardInterrupt:
        pass
    finally:
        set_all_led_color(bus, 0, 0, 0)
        set_led_mode(bus, LED_MODE_OFF)
        try:
            bus.close()
        except Exception:
            pass
        print("Beendet.")


if __name__ == "__main__":
    main()
