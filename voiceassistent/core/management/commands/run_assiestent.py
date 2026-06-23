from django.core.management.base import BaseCommand
import speech_recognition as sr
from core.models import Voice_response, App_command
from core.utils.voice_engine import speak_async
import platform
import os

from core.utils.finder import find_app_path
from core.management.commands.add_command import add_new_app_command_voice

class Command(BaseCommand):
    # handle - метод який відповідає за точку входу в програму 
    # *args - позіціонні елементи(передаються по порядку)
    # **options - іменовані параметри(флаги, налаштування та інше)
    def handle(self, *args, **options):
        # self.stdout.write - правильний спосіб виведення тексту в джанго командах
        # self.style.SUCCESS - додає зелений колір до тексту
        self.stdout.write(self.style.SUCCESS("Асистен запущений ..."))
        
        # sr.Recognizer створює об'єкт розпізнавання голосу
        recognizer = sr.Recognizer()
        # sr.Microphone підключає мікрофон як джерело звуку
        mic = sr.Microphone()
        
        # with гарантує правильне відкриття та закриття мікрофону
        # source об'єкт з якого буде слухатись звук
        with mic as source:
            self.stdout.write("Налаштуваня фонового шуму ...")
            # adjust_for_ambient_noise - метод який визначає рівень фонового шуму
            # source - наш мікрофон
            # duration - час на аналіз шуму
            recognizer.adjust_for_ambient_noise(source, duration = 1)
            self.stdout.write(self.style.SUCCESS("Слухаю ..."))
            
            while True:
                try:
                    # recognizer.listen - метод який слухає користувача
                    # timeout = None чекає команду від користувача безліч часу
                    # phrase_time_limit - максимум часу на одну фразу
                    audio = recognizer.listen(source, timeout = None, phrase_time_limit = 5)

                    # recognize_google - метод який відправляє аудіо в гугл апі та отримує текст
                    # language - мова для розпізнання
                    command_text = recognizer.recognize_google(audio, language = "uk-UA")
                    self.stdout.write(f"Ви сказали {command_text}")
                    self.process_command(command_text, source)
                    
                except sr.UnknownValueError:
                    continue
                
                except Exception as err:
                    self.stdout.write(self.style.WARNING(f"Помилка: {err}"))
                    continue
                
    def process_command(self, command_text: str, source):
        command_text = command_text.lower().strip()
        # Якщо в команді нема слова відкрий 

        if "додати команду" in command_text:
            add_new_app_command_voice(source)
            return 

        if "відкрий" not in command_text:
            # Перебираємо всі об'єкти моделі
            # objects.all - отримання всіх об'єктів з моделі
            for resp in Voice_response.objects.all():
                if resp.key_word and resp.key_word.lower() in command_text:
                    speak_async(resp.response)
                    return
            return
        
        found_app = None
        
        for app in App_command.objects.all():
            if app.key_word and app.key_word.lower() in command_text:
                found_app = app
                break

        if not found_app:
            speak_async("Я не знайшла такої команди")
            return
        
        if found_app.path and os.path.exists(found_app.path):
            speak_async(f"Відкриваю {found_app.app_name}")
            self.launch_app(found_app.path)
            return
        
        speak_async(f"Шукаю {found_app.app_name}")
        found_path = find_app_path(found_app.app_name)

        if found_path:
            found_app.path = found_path
            #save() - дозволяє зберегти зміни в базі даних 
            found_app.save()
            speak_async(f"Відкриваю {found_app.app_name}")
            self.launch_app(found_path)
        else:
            speak_async(f"Я не змогла знайти цю програму на компе")
            
    def launch_app(self, path):
        try:
            if platform.system() == "Windows":
                #Стандартний спосіб відкрити програму або файл на Windows
                os.startfile(path)
            else:
                #Виконує команду в терміналі 
                # "open -a" - команда для MacOS чи Linux для вікриття програм
                os.system("open -a" + path)
        except Exception as err:
            self.stdout.write(self.style.ERROR(f"Помилка запуску {err}"))
