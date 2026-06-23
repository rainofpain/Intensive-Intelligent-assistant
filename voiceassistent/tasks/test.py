import asyncio
import edge_tts

TEXT = 'Привет я другой голос'
VOICE =  'ru-RU-DmitryNeural'

async def main():
    communicate = edge_tts.Communicate(TEXT, VOICE)
    await communicate.save('voice.mp3')

asyncio.run(main())