import sounddevice as sd
import numpy as np
import wave
import os
import speech_recognition as sr

def speech_to_text(duration=5, filename="temp.wav"):
    """
    Records audio for 'duration' seconds and converts speech to text.
    """
    # Record audio
    fs = 44100  # Sample rate
    print("🎤 Listening...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()  # Wait until recording is finished

    # Save recording
    wf = wave.open(filename, "wb")
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(fs)
    wf.writeframes(recording.tobytes())
    wf.close()

    # Convert to text using SpeechRecognition
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError:
            return "Speech recognition service is unavailable."
