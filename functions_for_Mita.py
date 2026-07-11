import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="TypedStorage is deprecated")
try:
    import sys
    from time import time, sleep
    sys.stdout.flush()
    sys.stderr.flush()
    print("Инициализация...", flush=True)
    sleep(0.1)
    import os
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    from sound import Sound
    from voice import Voice
    import webbrowser as webb
    import json
    import screen_brightness_control as sbc
    from bs4 import BeautifulSoup
    from re import sub
    import winreg as reg
    from explorer import Explorer, path_of_this_file, username, GetDisksByJSON
    import threading
    from contextlib import contextmanager
    import socket

    os.system("pip install --upgrade pip > NUL 2>&1")
    os.system("pip install --upgrade selenium > NUL 2>&1")
    from selenium.webdriver import Chrome
    from selenium.webdriver.chrome.options import Options
    print("Установка необходимых зависимостей завершена")
    

    user_processes_dict = {}
    user_files_dict = {}
    reminders = {}
    hive = reg.HKEY_CURRENT_USER
    subKey = r"Software\Microsoft\Windows\CurrentVersion\Run"
    files_learning = False
    disk_usage_bool = True
    

    en_to_ru_alphabet = {".": " точка ", "shch": "щ", "tion": "шн", "sch": "ск", "chr": "хр", "e ": " ", "e-": "-", "e_": "_", "qw": "кв", "dge": "дж", "ch": "ч", "sh": "ш", "pp": "п", "mm": "м", "ee": "и", "ea": "и", "nn": "н", "oo": "у", "ou": "ау", "ss": "с", "ph": "ф", "th": "т", "wh": "в", "wr": "р", "kn": "н", "ck": "к", "ce": "се", "ci": "си", "cy": "си", "ur": "ёр", "ye": "ай", "a": "а", "b": "б", "c": "к", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "х", "i": "и", "j": "дж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п", "q": "кв", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "w": "в", "x": "кс", "y": "и", "z": "з"}#, "Shch": "Щ", "Sch": "Ск", "Qw": "Кв", "Chr": "Хр", "Ch": "Ч", "Sh": "Ш", "Pp": "П", "Mm": "М", "Ee": "И", "Ea": "И", "Nn": "Н", "Oo": "У", "Ss": "С", "Ph": "Ф", "Th": "З", "Wh": "В", "Wr": "Р", "Kn": "Н", "Ck": "К", "Ce": "Се", "Ci": "Си", "Cy": "Си", "A": "Эй", "B": "Би", "C": "Си", "D": "Ди", "E": "И", "F": "Эф", "G": "Джи", "H": "Эйч", "I": "Ай", "J": "Джей", "K": "Кей", "L": "Эл", "M": "Эм", "N": "Эн", "O": "Оу", "P": "Пи", "Q": "Кью", "R": "Ар", "S": "Эс", "T": "ти", "U": "Ю", "V": "Ви", "W": "В", "X": "Икс", "Y": "вай", "Z": "зет"}

    programms = {
        "вартандер":"launcher",
        "тундру":"launcher",
        "телеграмм":"Telegram",
        "телеграм":"Telegram",
        "вскод":"Code",
        "дискорд":"Discord",
        "дс":"Discord",
        "хром":"chrome",
        "яндекс":"yandex",
        "ватсап":"WhatsApp",
        "стим":"steam",
        "захват экрана":"obs64",
        "павэр поинт":"POWERPNT",
        "презентации":"POWERPNT",
        "документы":"WINWORD",
        "калькулятор":"CalculatorApp",
    }

    ints = {
        "максимум": 100,
        "минимум": 0,
        "ноль": 0,
        "нуль": 0,
        "один": 1,
        "одна": 1,
        "одну": 1,
        "два": 2,
        "две": 2,
        "три": 3,
        "четыре": 4,
        "пять": 5,
        "шесть": 6,
        "семь": 7,
        "восемь": 8,
        "девять": 9,
        "десять": 10,
        "одиннадцать": 11,
        "двенадцать": 12,
        "тринадцать": 13,
        "четырнадцать": 14,
        "пятнадцать": 15,
        "шестнадцать": 16,
        "семнадцать": 17,
        "восемнадцать": 18,
        "девятнадцать": 19,
        "двадцать": 20,
        "тридцать": 30,
        "сорок": 40,
        "пятьдесят": 50,
        "шестьдесят": 60,
        "семьдесят": 70,
        "восемьдесят": 80,
        "девяносто": 90,
        "сто": 100,
        "двести": 200,
        "триста": 300,
        "четыреста": 400,
        "пятьсот": 500,
        "шестьсот": 600,
        "семьсот": 700,
        "восемьсот": 800,
        "девятьсот": 900,
        "тысяча": 1000,
        "тысячи": 1000,
        "тысяч": 1000,
        "тыща": 1000,
        "тыщи": 1000,
        "тыщ": 1000,
        "миллион": 1000000,
        "миллиона": 1000000,
        "миллионов": 1000000,
        "миллиард": 1000000000,
        "миллиарда": 1000000000,
        "миллиардов": 1000000000,
        "триллион": 1000000000000,
        "триллиона": 1000000000000,
        "триллионов": 1000000000000
    }

    ints_of_time = {
        "миллисекунда": 0.001,
        "миллисекунды": 0.001,
        "миллисекунд": 0.001,
        "миллисекунду": 0.001,
        "секунда": 1,
        "секунды": 1,
        "секунд": 1,
        "секунду": 1,
        "минута": 60,
        "минуты": 60,
        "минут": 60,
        "минуту": 60,
        "час": 3600,
        "часа": 3600,
        "часов": 3600,
        "день": 86400,
        "дня": 86400,
        "дней": 86400,
        "сутки": 86400,
        "суток": 86400,
        "неделя": 604800,
        "недели": 604800,
        "недель": 604800,
        "неделю": 604800,
        "месяц": 2592000,
        "месяца": 2592000,
        "месяцев": 2592000,
        "полгода": 15811200,
        "год": 31536000,
        "года": 31536000,
        "лет": 31536000
    }


# Функции подготовки

    def ExplorerPrepare():
        global exp
        exp = Explorer(f"C:\\Users\\{username}")

    def ParsingPrepare():
        global driver
        # chromedriver_autoinstaller.install()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        # driver_version = os.listdir(f"C:/Users/{username}/.cache/selenium/chromedriver/win32/")[0]
        driver = Chrome(options=chrome_options)

    def VoicingPrepare():
        global voice
        voice = Voice()

    def SoundPrepare():
        global sound
        sound = Sound()
# 


# Общие функции 

    def CheckReminders(rem_dict: dict):
        rem_keys = list(rem_dict.keys())
        current_time = int(time())
        for i in range(len(rem_keys)):
            reminder = rem_dict.get(rem_keys[i])
            if reminder <= current_time:
                # VoicePro('Напоминание: "' + rem_keys[i] + '"')
                # Voice('Напоминание: "' + rem_keys[i] + '"')
                rem_dict.pop(rem_keys[i])
                return rem_keys[i]

    def CheckThread(rem_dict):
        while 1:
            CheckReminders(rem_dict)
            exp.CheckExplorer()
            GetDisksByJSON()
            CheckInternetConnection()
            sys.stdout.flush()
            sys.stderr.flush()
            sleep(10)

    def CheckInternetConnection():
        global connection
        connection = False
        try:
            driver.get("http://google.com")
            connection = True
        except Exception as e:
            print(str(e))
            print("Вы не подключены к интернету")
            connection = False

    def GetProgrammPathByName(programmName: str):
        GetProgramsByLocalhost()
        return user_processes_dict[programms[programmName]]
    
    def GetProgramsByLocalhost():
        global programms, user_processes_dict
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('127.0.0.1', 9999))
            sock.sendall("processes".encode("utf-8"))
            founded_programs = json.loads(sock.recv(16384).decode("utf-8"))
        user_processes_dict.update(founded_programs)
        for fp_name in founded_programs.keys():
            programm_name = fp_name.lower()
            if programm_name not in [i.lower() for i in programms.values()]:
                programm_name = EnToRuNames(programm_name)
                programms.update({programm_name: fp_name})
                
    def GetPCWorkloadByLocalhost():
        global workload_info
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('127.0.0.1', 9999))
            sock.sendall("workload".encode("utf-8"))
            workload_info = json.loads(sock.recv(16384).decode("utf-8"))

    def EnToRuNames(name: str):
        for letter in en_to_ru_alphabet:
            if letter in name:
                name = name.replace(letter, en_to_ru_alphabet[letter])
            if name[-1] == "e":
                name = name[:-1]
        return name

    @contextmanager
    def vosk_without_logs():
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        orig_stdout_fd = os.dup(1)
        orig_stderr_fd = os.dup(2)
        with open(os.devnull, 'w') as devnull:
            sys.stdout = devnull
            sys.stderr = devnull
            os.dup2(devnull.fileno(), 1)
            os.dup2(devnull.fileno(), 2)
        try:
            yield
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            os.dup2(orig_stdout_fd, 1)
            os.dup2(orig_stderr_fd, 2)
            os.close(orig_stdout_fd)
            os.close(orig_stderr_fd)
# 


# Функции для Миты

    def StartProgramm(data: list[str]):
        if data is None:
            return ["НЗВФАЙЛА"]
        name = data[0]
        print(data)
        os.startfile(GetProgrammPathByName(name))
        return "Программа запущена"
    
    def RequestToBrowser(data: list[str]):
        # if data is None:
        #     return ["ЗАПР"]
        # request = data[0]
        # webb.open(f"https://yandex.ru/search/?text={request}", new=2)
        pass

    def Say(data: list[str]):
        if data is None:
            return ["ТЕКСТДЛЯОЗВ"]
        text = data[0]
        voice.say(f"<speak>{text}</speak>")

    def CloseProgramm(data: list[str]):
        if data is None:
            return ["НЗВФАЙЛА"]
        print(data)
        name = GetProgrammPathByName(data[0])
        for pr_name, pr_path in user_processes_dict.items():
            try:
                if pr_path == name:
                    os.system(f"taskkill /im {pr_name}.exe /f")
            except IndexError:
                print("Такого процесса нет!")
                return "Такого процесса нет"
                # Voice("Файл не найден")
        return "Программа закрыта"
    
    def OpenURL(data: list[str]):
        if data is None:
            return ["ССЫЛ"]
        url = data[0]
        webb.open(url, new=2)
        return "Этот сайт открыт"
    
    def SetReminder(data: list[int, str]):
        if data is None:
            return ["ЧИСЛО", "ТЕКСТ"]
        set_time = data[0]
        text = data[1]
        current_time = int(time())
        true_time = set_time + current_time + 5
        local_list = [text,true_time]
        reminders.update([local_list])
        for key, value in ints.items():
            if value == set_time:
                return f"Я напомню об этом через {key} секунд"
        
    def GetIntByStr(data: list[str]):
        if data is None:
            return ["СТРОКАЧИСЛА"]
        int_str = data[0]
        str_by_int = int_str.split(" ")
        ints_from_str_by_int = []
        multiplicable_int = 0
        rezult = 0
        for i in str_by_int:
            ints_from_str_by_int.append(ints[i])
        len_ints_from_str_by_int = len(ints_from_str_by_int)
        for iii in range(len_ints_from_str_by_int):
            max_ints_from_str_by_int = max(ints_from_str_by_int)
            if ints_from_str_by_int.index(max_ints_from_str_by_int) > 0:
                multiplicable_int += ints_from_str_by_int[0]
            else:
                if multiplicable_int != 0:
                    rezult += (multiplicable_int * max_ints_from_str_by_int)
                    multiplicable_int = 0
                else:
                    rezult += max_ints_from_str_by_int
            ints_from_str_by_int.pop(0)
        return rezult

    def GetTimeByInt(data: list):
        if data is None:
            return ["ЕДВРЕМЯ", "ЧИСЛО"]
        int_of_time = data[0]
        if len(data) > 1: int = data[1]
        else: int = 1
        rezult = 0
        if int_of_time in ints_of_time:
            rezult = int * ints_of_time[int_of_time]
        else:
            # Voice("Я не знаю такой единицы измерения времени")
            return "Я не знаю такой единицы измерения времени"
        return rezult
    
    def QuitComputer(data: list[int]):
        if data is None:
            return ["ЧИСЛО"]
        time = data[0]
        print("quit system")
        os.system(f'shutdown /s /t {time}')
        for key, value in ints.items():
            if value == time:
                return f"Компьютер будет выключен через {key} секунд"

    def RebootComputer(data: list[int]):
        if data is None:
            return ["ЧИСЛО"]
        time = data[0]
        print("reboot system")
        os.system(f'shutdown /r /t {time}')
        for key, value in ints.items():
            if value == time:
                return f"Компьютер будет перезагружен через {key} секунд"
    
    def SetProgrammToAutoStart(data: list[str] = ["StartMita"]):
        if data is None:
            return ["НЗВФАЙЛА"]
        elif data == ["StartMita"]:
            file = "StartMita"
            programm_path = path_of_this_file
        else:
            file = data[0]
            programm_path = os.path.dirname(GetProgrammPathByName(data[0]))
        if programm_path == "":
            programm_path = path_of_this_file
        programm_path = os.path.dirname(programm_path)
        # bat_path = r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup' % username
        # with open(bat_path + '\\' + file + '.bat', "w+") as bat_file:
        #     bat_file.write(f'"{programm_path}\\{file}"')
        hKey = reg.OpenKey(hive, subKey , 0, reg.KEY_ALL_ACCESS)   
        reg.SetValueEx(hKey, file, 0, reg.REG_SZ, "\"" + programm_path + "\\" + file + "\"") 
        reg.CloseKey(hKey) 
        return f"Программа {file} установена на автозапуск"

    def RemoveProgrammFromAutoStart(data: list[str] = ["StartMita"]): 
        if data is None:
            return ["НЗВФАЙЛА"]
        if data[0] == "StartMita":
            programm = data[0]
        else:
            programm = GetProgrammPathByName(data[0])
        try:
            hKey = reg.OpenKey(hive, subKey, 0, reg.KEY_ALL_ACCESS) 
            reg.DeleteValue(hKey, programm)
            reg.CloseKey(hKey) 
        except: pass
        try:
            exp.RemoveFile(r'C:\Users\%s\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\%s.bat' % (username, programm))
        except: pass
        return f"Программа {programm} снята с автозапуска"

    def Parse(data: list[str]):
        if data is None:
            return ["ТЕКСТ"]
        task = data[0]
        task = list(task)
        task[0] = task[0].upper()
        for sym in range(len(task)):
            if task[sym] == " ":
                task[sym] = "_"
                task[sym+1] = task[sym+1].upper()
        task = "".join(task)
        if connection:
            driver.get(f"https://ru.wikipedia.org/wiki/{task}")
            soup = BeautifulSoup(driver.page_source, features = "html.parser")
            answers = soup.find_all("p")
            result = []
            for answer in answers:
                result.append(sub("\\n", "", sub("\\xa0", "", sub("\[[^\]]*\]", "", answer.text))))
            return " ".join(result)
        else:
            return "Вы не подключены к интернету" 
    
## Функции из explorer

    def OpenFile(data: list[str]):
        if data is None:
            return ["НЗВФАЙЛА"]
        name = data[0]
        return exp.OpenFile(name)

    def RenameFile(data: list[str, str]):
        if data is None:
            return ["НЗВФАЙЛА", "ТЕКСТ"]
        old_name = data[0]
        new_name = data[1]
        return exp.RenameFile(old_name, new_name)

    def RemoveFile(data: list[str]):
        if data is None:
            return ["НЗВФАЙЛА"]
        name = data[0]
        return exp.RemoveFile(name)
    
    def ZippingFiles(data: list):
        if data is None:
            return ["НЗВФАЙЛА", "ТЕКСТ"]
        path = data[0]
        if len(data) < 2: ziph = ""
        else: ziph = data[1]
        return exp.ZippingFiles(path, ziph)

    def UnzippingFiles(data: list):
        if data is None:
            return ["НЗВФАЙЛА"]
        path_to_ziph = data[0]
        return exp.UnzippingFiles(path_to_ziph)
##

## Функции для яркости

    def SetScreenBrightness(data: list[int]):
        if data is None:
            return ["ЧИСЛО"]
        level = data[0]
        try:
            if level >= 0 and level < 101:
                sbc.set_brightness(level)
                for key, value in ints.items():
                    if value == level:
                        return f"Яркость экрана установлена на {key}"
            else:
                for key, value in ints.items():
                    if value == level:
                        return f"Я не могу изменить яркость экрана на {key}"
        except:
            return "Я не могу установить яркость экрана на нечисловое значение"
    
    def UpScreenBrightness(data: list[int]):
        if data is None:
            return ["ЧИСЛО"]
        level = sbc.get_brightness()[0] + data[0]
        if level > 100:
            level = 100
        sbc.set_brightness(level)
        for key, value in ints.items():
            if value == level:
                return f"Яркость экрана увеличена на {key}"
    
    def DownScreenBrightness(data: list[int]):
        if data is None:
            return ["ЧИСЛО"]
        level = sbc.get_brightness()[0] - data[0]
        if level < 0:
            level = 0
        sbc.set_brightness(level)
        for key, value in ints.items():
            if value == level:
                return f"Яркость экрана уменьшена на {key}"
##

## Функции для звука

    def SetSound(data: list[int]):
        if data is None:
            return ["ЧИСЛО"]
        level = data[0]
        sound.volume_set(level)
        for key, value in ints.items():
            if value == level:
                return f"Громкость звука установлена на {key}"
    
    def UpSound(data: list[int]):
        if data is None:
            return ["ЧИСЛО"]
        level = data[0]
        sound.volume_up(level)
        for key, value in ints.items():
            if value == level:
                return f"Громкость звука увеличена на {key}"

    def DownSound(data: list[int]):
        if data is None:
            return ["ЧИСЛО"]
        level = data[0]
        sound.volume_down(level)
        for key, value in ints.items():
            if value == level:
                return f"Громкость звука уменьшена на {key}"
    
    def MuteSound():
        sound.mute()
        return "Звук выключен"
    
    def DemuteSound():
        sound.demute()
        return "Звук включен"
## 

#

    print("Загрузка...")
    ExplorerPrepare()
    print("\r1/8", end="", flush=True)
    VoicingPrepare()
    print("\r2/8", end="", flush=True)
    SoundPrepare()
    print("\r3/8", end="", flush=True)
    ParsingPrepare()
    print("\r4/8", end="", flush=True)
    CheckInternetConnection()
    print("\r5/8", end="", flush=True)
    GetProgramsByLocalhost()
    print("\r6/8", end="", flush=True)
    GetPCWorkloadByLocalhost()
    print("\r7/8", end="", flush=True)
    thread1 = threading.Thread(target=CheckThread, args=(reminders,))
    thread1.start()
    print("\r8/8", end="", flush=True)
    print("\rЗагрузка завершена")

except Exception as e:
    print(str(e))
    input()
