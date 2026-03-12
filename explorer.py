import os
import patoolib
import pygetwindow as gw
import win32gui
import comtypes.client
import platform
import winshell
import win32com.client
import pythoncom
import sqlite3
import json
from io import StringIO
from contextlib import redirect_stdout

shell = win32com.client.Dispatch("WScript.Shell")
username = os.getlogin()
path_of_this_file = os.path.dirname((os.path.abspath(__file__)))
if platform.release() == "10": desktop_path = f"C:\\Users\\{username}\\Desktop"
elif platform.release() == "11": desktop_path = f"C:\\Users\\{username}\\OneDrive\\Рабочий стол"
else: desktop_path = "C:\\"
# recent_files_path = f"C:\\Users\\{username}\\AppData\\Roaming\\Microsoft\\Windows\\Recent"
recent_files_path = winshell.recent()
path_learned_files = f"C:\\Users\\{username}"
disks = {}
current_drive = f"C:\\Users\\{username}"
max_depth = 10

# files_system = {f"C:\\Users\\{username}": []}
black_list = [".vscode", "Microsoft", "Windows"]

def getPCWorkload():
    global workload_info, disks
    with open(f'{path_of_this_file}/data/workload.json', 'r', encoding='utf-8') as f:
        workload_info = json.load(f)
    disks = workload_info["Disks"]

class Explorer():
    def __init__(self, current_path):
        self.current_path = current_path
        self.conn = sqlite3.connect(f'{path_of_this_file}/data/files.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
            
    def SearchFilesInDB(self, filename):
        try:
            self.cursor.execute('''
                SELECT name, extension, path, disk_id FROM files 
                WHERE name LIKE ? 
            ''', (f'%{filename}%',))
            results = self.cursor.fetchall()
            for result in results:
                if not os.path.exists(disks[result[3]][1] + str(result[2])):
                    results.remove(result)
            return results
        except Exception as e:
            print(f"Ошибка поиска в базе: {e}")
            return []

    def ChangeCurrentPath(self, new_path: str):
        self.current_path = new_path

    def GetExplorerWindowPath(self, MyHwnd):
        try:
            pythoncom.CoInitialize()
            shell_app = comtypes.client.CreateObject("Shell.Application")
            windows = shell_app.Windows()
            for i in range(windows.Count):
                explorer_window = windows.Item(i)
                if explorer_window is None:
                    continue
                if explorer_window.hwnd == MyHwnd:
                    path = os.path.basename(explorer_window.FullName)
                    if path.lower() == "explorer.exe":
                        explore_path = explorer_window.Document.Folder.Items().Item().Path
                        return explore_path
        finally: 
            shell_app = None
            pythoncom.CoUninitialize()

    def CheckExplorer(self):
        try:
            windows = gw.getAllWindows()
            for window in windows:
                if win32gui.GetClassName(window._hWnd) == "CabinetWClass":
                    hwnd = window._hWnd
                    current_path = self.GetExplorerWindowPath(hwnd)
                    if current_path: self.ChangeCurrentPath(current_path)
                    else: return "Не удалось получить текущий путь к папке в проводнике."
        except Exception as e:
            print(str(e))
            return "Не удалось получить текущий путь к папке в проводнике."

    def LearnFilePath(self, filename: str):
        print(self.current_path)
        probably_files = []
        for i in os.listdir(self.current_path):
            if os.path.splitext(os.path.basename(i))[0] == filename:
                if not os.path.isdir(i):
                    probably_files.append(self.current_path + "\\" + i)
                else:
                    self.ChangeCurrentPath(self.current_path + "\\" + i)
                    self.LearnFilePath(filename)
        if probably_files: return probably_files
        for i in os.listdir(desktop_path):
            if os.path.splitext(os.path.basename(i))[0] == filename:
                if not os.path.isdir(i):
                    probably_files.append(desktop_path + "\\" + i)
                else:
                    self.ChangeCurrentPath(desktop_path + "\\" + i)
                    self.LearnFilePath(filename)
        if probably_files: return probably_files
        for i in os.listdir(recent_files_path):
            try:
                target_name = os.path.splitext(os.path.basename(winshell.Shortcut(recent_files_path + "\\" + i).path))[0]
                if target_name:
                    if target_name == filename:
                        if not os.path.isdir(target_name):
                            probably_files.append(recent_files_path + "\\" + i)
                        else:
                            self.ChangeCurrentPath(recent_files_path + "\\" + i)
                            self.LearnFilePath(filename)
            except Exception as e: continue
        self.SearchFilesInDB(filename)
        if probably_files: return probably_files
        # return self.FindFile(filename)
        return []
    
    def ChooseFile(self, name: str):
        if "\\\\" in name or "\\" in name or "/" in name:
            return name
        else:
            names_list = self.LearnFilePath(self, name)
            if not names_list:
                return [0]
            if len(names_list) > 1:
                return [1, names_list]
            else:
                return names_list[0]
    
    def OpenFile(self, name: str):
        file = self.ChooseFile(name)
        if file[0] == 0:
            return "Файл не найден"
        elif file[0] == 1:
            return ["ФАЙЛ", file[1]]
        else:
            os.startfile(file)
        return "Файл запущен"

    def RenameFile(self, old_name: str, new_name: str):
        file = self.ChooseFile(old_name)
        if file[0] == 0:
            return "Файл не найден"
        elif file[0] == 1:
            return ["ФАЙЛ", file[1]]
        else:
            os.rename(file, os.path.dirname(file) + "/" + new_name)
        return "Файл переименован"

    def RemoveFile(self, path = str):
        file = self.ChooseFile(path)
        if file[0] == 0:
            return "Файл не найден"
        elif file[0] == 1:
            return ["ФАЙЛ", file[1]]
        else:
            os.remove(file)
        return "Файл удалён"
    
    def ZippingFiles(self, path: str, ziph: str = ""):
        # path = self.LearnFilePath(path)
        if not ziph: ziph = os.path.relpath(path, os.path.dirname(path)) + ".zip"
        try:
            cwd = os.getcwd()
            os.chdir(path)
            patoolib.create_archive(ziph, os.listdir('.'))
            os.chdir(cwd)
            return f"Папка {ziph[:-4]} успешно заархивирована"
        except:
            return "Произошла ошибка при архивации папки"
        
    def UnzippingFiles(self, path_to_ziph: str, outpath: str = ""):
        # path_to_ziph = self.LearnFilePath(path_to_ziph)
        if not outpath: outpath = path_to_ziph.rsplit(".")[0]
        try:
            os.makedirs(outpath, exist_ok=True)
            cwd = os.getcwd()
            os.chdir(outpath)
            patoolib.extract_archive(path_to_ziph, outdir=outpath)
            os.chdir(cwd)
            return "Папка успешно разархивирована"
        except:
            return "Произошла ошибка при разархивации папки"
        finally:
            self.RemoveFile(path_to_ziph)
            
    def WatchingZippedFiles(self, path_to_ziph: str):
        # path_to_ziph = self.LearnFilePath(path_to_ziph)
        try:
            archive_redirect = StringIO()
            with redirect_stdout(archive_redirect):
                patoolib.list_archive(path_to_ziph)
            archive_list = archive_redirect.getvalue()
            return archive_list
        except:
            return "Произошла ошибка при просмотре папки"
        
# exp = Explorer("C:\\Users\\Admin")

# print(exp.ZippingFiles(r"D:\From desktop\мои файлы\Большие вызовы\2026", r"F:\Загрузки\test.zip"))
# print(exp.WatchingZippedFiles(r"F:\Загрузки\test.zip"))
# print(exp.UnzippingFiles(r"F:\Загрузки\test.zip"))
