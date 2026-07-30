from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from pathlib import Path
import os

client = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY")
)

with open("script.txt", "r", encoding="utf-8") as f:
    text = f.read()

audio = client.text_to_speech.convert(
    voice_id="JBFqnCBsd6RMkjVDRZzb",
    model_id="eleven_multilingual_v2",
    text=text,
    voice_settings=VoiceSettings(
        stability=0.70,
        similarity_boost=0.85,
        style=0.25,
        use_speaker_boost=True
    )
)

output_dir = Path("Outputs/generated_audio")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "skynova_intro.mp3"

with open(output_file, "wb") as file:
    for chunk in audio:
        file.write(chunk)

print(f"Voice generated successfully! Saved to: {output_file.resolve()}")