import json, pyaudio
# import numpy as np
from vosk import Model, KaldiRecognizer
# import tensorflow as tf
# from tensorflow.keras import models, layers
from Interface import App
import traceback
from functions_for_Mita import ints_of_time, ints, programms
from functions_for_Mita import*
# import random
# import time
# import multiprocessing as mp
from sys import stdout, stderr

data_time = list(ints_of_time.keys())
data_int = list(ints.keys())
prog_data = list(programms.keys())
black_list = ["открой","запусти","закрой"]

vocabulary = ["а", "б", "в", "г", "д", "е", "ё", "ж", "з", "и", "й", "к", "л","м", "н", "о",
            "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ь","ы","ъ", "э", "ю", "я"," "]

names = ["мита","митра","митта", "мит", "мид"]

# def change_extensions():
#     global extensions
#     # в список ниже вводишь те расширения, которые тебе нужны
#     # extensions = []
#     pass

def word_to_number(word):
    word = list(word)
    for i in range(len(word)):
        for i2 in range(len(vocabulary)):
            if word[i] == vocabulary[i2]:
                word[i] = i2+1

    return word

def word_for_compare(word):
    word = list(word)
    for i in range(len(word)):
        for i2 in range(len(vocabulary)):
            if word[i] == vocabulary[i2]:
                word[i] = i2+1

    while len(word) < 50:
        word.append(0)

    while len(word) > 50:
        word.pop(-1)

    return word

def text_to_number(text):
    output_text = []
    for word in text:
        word = word_to_number(word)
        for i in range(len(word)):
            output_text.append(word[i])

    for i2 in range(len(output_text)-1):
        try:
            if type(output_text[i2]) == str:
                output_text.pop(i2)
        except:
            print("Error, list index out of range")
    
    while len(output_text) < 512:
        output_text.append(0)

    while len(output_text) > 512:
        output_text.pop(-1)
    
    return output_text

def start_interface():
    app = App()
    app.mainloop()

#loaded_text = "Доброго времени суток."

# Примечание: Вы можете найти все модели по адресу https://huggingface.co/TeraTTS, включая модель GLADOS
# tts = TTS("TeraTTS/natasha-g2p-vits", add_time_to_end=1.0, tokenizer_load_dict=True) # Вы можете настроить 'add_time_to_end' для продолжительности аудио, 'tokenizer_load_dict' можно отключить если используете RUAccent


# 'length_scale' можно использовать для замедления аудио для лучшего звучания (по умолчанию 1.1, указано здесь для примера)
#audio = tts(text, lenght_scale=1.1)  # Создать аудио. Можно добавить ударения, используя '+'
#tts.play_audio(audio)  # Воспроизвести созданное аудио
#tts.save_wav(audio, "./test.wav")  # Сохранить аудио в файл


# Создать аудио и сразу его воспроизвести
#tts(text, play=True, lenght_scale=1.1)
#print("loading models")
#compare_model = tf.keras.models.load_model(
#    'D:\MitaFiles\compare_model/compare_model.keras', custom_objects=None, compile=True, safe_mode=True
#    ) 
#print("compare_model loaded")
#main_model = tf.keras.models.load_model(
#    'D:\MitaFiles\main_model/main_model.keras', custom_objects=None, compile=True, safe_mode=True
#)
#print("main_model loaded")
#print("Main Mita's model is loaded, but disabled")

with vosk_without_logs():
    model = Model(f'{path_of_this_file}/vosk-model-small-ru-0.22')
    rec = KaldiRecognizer(model,16000)
    p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,channels=1,rate=16000,input=True,frames_per_buffer=8000)
stream.start_stream()
print("Vosk загружен")


def listen():
    while True:
        data=stream.read(4000,exception_on_overflow=False)
        if (rec.AcceptWaveform(data)) and (len(data) > 0):
            answer=json.loads(rec.Result())
            if answer['text']:
                yield answer['text']

def Other(data):
    Voice(["Простите, но данной возможности у меня пока ещё нет"])

# def split_text(text, max_lenght):
#     length = len(text)
#     parts = length // max_lenght
#     part_size = length // parts
#     result = []
#     for i in range(parts):
#         start = i * part_size
#         # Для последней части берем весь остаток
#         end = (i + 1) * part_size if i < parts - 1 else length
#         result.append(text[start:end])

    # return result

def split_text(text, max_words=40):
    # Разделяем текст на слова
    words = text.split()
    parts = []
    
    # Группируем слова по max_words
    for i in range(0, len(words), max_words):
        part = " ".join(words[i:i + max_words])
        parts.append(part)
    
    return parts

def compare_words(word1, word2):
    max_len = max(len(word1), len(word2))
    matches = 0

    for i in range(max_len):
        # Если одна из строк короче, считаем несовпадение
        if i >= len(word1) or i >= len(word2):
            continue
        # Если буквы совпадают
        if word1[i] == word2[i]:
            matches += 1

    similarity = matches / max_len
    return similarity

#tts(loaded_text,play=True,lenght_scale=2.5)
functions = [StartProgramm,                          # 1
            OpenFile,                                # 2
            RenameFile,                              # 3
            RemoveFile,                              # 4
            RequestToBrowser,                        # 5    (OpenURL)
            CloseProgramm,                           # 6
            QuitComputer,                            # 7
            RebootComputer,                          # 8
            Set_reminder,                            # 9
            SetScreenBrightness,                     # 10
            SetSound,                                # 11
            UpSound,                                 # 12
            DownSound,                               # 13
            MuteSound,                               # 14
            DemuteSound,                             # 15
            SetProgrammToAutoStart,                  # 16
            RemoveProgrammFromAutoStart,             # 17 
            ZippingFiles,                            # 18
            UnzippingFiles,                          # 19
            Parse,                                   # 20
            UpScreenBrightness,                      # 21
            DownScreenBrightness,                    # 22
            Other                                    # 23
            ]

triggers = [["открой", "запусти"],                 # 1
            ["СЛОВОАКТИВАТОР ОТСУТСТВУЕТ"],        # 2
            ["переименуй","переименую"],           # 3
            ["удали"],                             # 4
            ["СЛОВОАКТИВАТОР ОТСУТСТВУЕТ"],        # 5
            ["закрой"],                            # 6
            ["выключи"],                           # 7
            ["перезагрузи","перезагрузить"],       # 8
            ["напомни","напомню"],                 # 9
            ["яркость"],                           # 10
            ["звук", "громкость"],                 # 11
            ["звук выше", "увеличь громкость"],    # 12
            ["звук ниже", "уменьши громкость"],    # 13
            ["заглуши"],                           # 14
            ["включи"],                            # 15
            ["СЛОВОАКТИВАТОР ОТСУТСТВУЕТ"],        # 16
            ["СЛОВОАКТИВАТОР ОТСУТСТВУЕТ"],        # 17
            ["заархивируй","заархивирую"],         # 18
            ["разархивируй","разархивирую"],       # 19
            ["найди", "что такое", "кто такой"],   # 20
            ["увеличь яркость"],                   # 21
            ["уменьши яркость"],                   # 22
            ["поговори"]                           # 23
            ]


if __name__ == "__main__":
    start_interface()
    print("Мита запущена")
    func = None
    for text in listen():
        print(text)
        text = list(text)
        for letter in range(len(text)-1):
            try:
                if text[letter] == "-":
                    text.pop(letter)
            except:
                pass

        text = "".join(text)
        data_out = []
        text_spl = text.split(" ")
        probability = 0
        
        # functions = ["StartFile", "RenameFile", "RemoveFile", "OpenURL", "RequestToBrowser", "CloseProgramm", "QuitComputer", "RebootComputer", "Set_reminder",
        # "Check_reminders", "SetScreenBrightness", "ChangeSound", "SetProgrammToAutoStart", "RemoveProgrammFromAutoStart", "ZippingFiles", "UnzippingFiles","Other"]
        for i in range(len(functions)):
            for ii in range(len(text_spl)):
                if type(i) != int:
                        break
                
                for iii in range(len(triggers[i])):
                    if len(text_spl) <= 0:
                        break

                    if type(i) != int:
                        break
                    
                    if len(text_spl) > ii:
                        if text_spl[ii] in names:
                            text_spl = text_spl[ii+1:]
                            print("обрезанный text: ", text_spl)

                    if triggers[i][iii] in text: # if main_output[0][i] >= 0.75: # После тестов вернуть обратно
                        LearnPathsLaunchedProcesses()
                        #print(main_output[i], i)
                        len_trigger = triggers[i][iii].split(" ")

                        for iv in range(len(len_trigger)):
                            if len(text_spl) > 0:
                                text_spl.pop(0)


                        print(functions[i])
                        func = functions[i]
                        #func = StartProgramm
                        data_in = func(None) # Запуск функции в режиме запроса данных
                        print(data_in)
                        # Сюда типы данных
                        # data types: "НЗВФАЙЛА","ЗАПР","ЧИСЛО","ТЕКСТ","ЕДВРЕМЯ"

                        # Поиск нужных файлов
                        for data in data_in:
                            if data == "НЗВФАЙЛА":
                                print("Поиск названия файла")
                                for i4 in text_spl:
                                    for i5 in prog_data:
                                        #word = word_for_compare(i4)
                                        #word2 = list(i5)
                                        #ord2 = [x for x in word2 if x in vocabulary]
                                        #word2 = ''.join(word2)
                                        #prog = word_for_compare(word2)

                                        #print(i4)
                                        #print(i5)
                                        #text_in = []
                                        #text_in.extend(word)
                                        #text_in.extend([0,0,0,0,0])
                                        #text_in.extend(prog)
                                        #text_in = np.array(text_in)

                                        #text_in = text_in.reshape((-1, 105, 1))
                                        #output = compare_model.predict(text_in)
                                        output = compare_words(i4, i5)
                                        #print(f"Результат сравнения {output}")

                                        if i4 in prog_data:
                                            arg = i4
                                            data_out.append(arg)
                                            print(arg)
                                            while len(data_out) > len(data_in):
                                                data_out.pop(0)

                                        if output >= 0.75 and len(data_out) < len(data_in):
                                            arg = i5
                                            data_out.append(arg)
                                            print(arg)

                                        data_delete = [x for x in data_out if x in black_list]
                                        for block in data_out:
                                            for del_word in range(len(data_delete)):
                                                if block == data_delete[del_word]:
                                                    data_out.pop(del_word)
                                        if len(data_out) >= len(data_in):
                                            print("Набрано достачное кол-во данных")
                                            break


                            if data == "ЗАПР":
                                pass # Вообще не знаю как такое проверять, сюда только с допиленными нейросетями

                            if data == "ССЫЛ":
                                pass # Вообще не знаю как такое проверять, сюда только с допиленными нейросетями

                            if data == "ЧИСЛО":
                                print("Поиск чисел")
                                for i in text_spl:
                                    for i2 in data_int:
                                        if i == i2:
                                            arg = ints.get(i)
                                            data_out.append(arg)

                            if data == "ЕДВРЕМЯ":
                                print("Поиск единиц времени")
                                for i in text_spl: 
                                    for i2 in data_time:
                                        if i == i2:
                                            arg = ints_of_time.get(i)
                                            data_out.append(arg)

                            if data == "ТЕКСТ":
                                arg = '_'.join(text_spl)

                                data_out.append(arg)
                        try:
                            print("data:", data_out)
                            # func_output = func(data_out)
                            # print(func_output)
                            # func_output = str(func_output)
                            func_text = split_text(str(func(data_out)),25)
                            data_out.clear()
                            for part in func_text:
                                Voice([part])
                                data_out.clear()
                            break
                        except Exception as e:
                            print(f"Critical error {e}")
                            traceback.print_exc()  # Вывод полной трассировки стека
                            print("Похоже я неправильно вас поняла :(  попробуйте перефразировать свой запрос")
        stdout.flush()
        stderr.flush()
