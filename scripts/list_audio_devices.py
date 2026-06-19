"""List audio devices so you can find BlackHole / your input.

    python3 scripts/list_audio_devices.py
"""
from __future__ import annotations


def main() -> None:
    try:
        import sounddevice as sd
    except ImportError:
        print("sounddevice not installed. Run: pip install sounddevice")
        return
    print(sd.query_devices())
    print("\nLook for 'BlackHole 2ch' (or your Multi-Output) as an input device.")


if __name__ == "__main__":
    main()
