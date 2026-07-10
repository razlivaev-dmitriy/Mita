import os
import pygetwindow as gw
import win32gui
import platform
import winshell
import win32com.client
import pythoncom
import sqlite3
import json
import subprocess
from shutil import move

shell = win32com.client.Dispatch("WScript.Shell")
disks = {}
max_depth = 10

# files_system = {f"C:\\Users\\{username}": []}
black_list = [".vscode", "Microsoft", "Windows"]

def Prepare():
    global path_of_this_file, python_path, recent_files_path, path_learned_files, desktop_path, current_drive
    with open(f"C:/Mita/config.json", 'r', encoding='utf-8') as f:
        install_info = json.load(f)
    username = install_info["active_user"]
    path_of_this_file = install_info["program_path"]
    python_path = "C:/Mita/Python310"
    if platform.release() == "10": desktop_path = f"C:\\Users\\{username}\\Desktop"
    elif platform.release() == "11": desktop_path = f"C:\\Users\\{username}\\OneDrive\\Рабочий стол"
    else: desktop_path = "C:\\"
    recent_files_path = winshell.recent()
    path_learned_files = f"C:\\Users\\{username}"
    current_drive = f"C:\\Users\\{username}"

def GetDisksByJSON():
    global disks
    with open(f"{path_of_this_file}/data/disks.json", "r", encoding="utf-8") as f:
        disks = json.load(f)["Disks"]

class Explorer():
    def __init__(self, current_path):
        self.current_path = current_path
        self.conn = sqlite3.connect(f'{path_of_this_file}/data/files.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
            
    def SearchFilesInDB(self, filename, extension=None):
        try:
            if extension == None:
                self.cursor.execute('''
                    SELECT name, extension, path, disk_id FROM files 
                    WHERE name = ? 
                ''', (filename,))
            else:
                self.cursor.execute('''
                SELECT name, extension, path, disk_id FROM files 
                WHERE name = ? AND extension LIKE ? 
            ''', (filename, f'%{extension}%'))
            results = self.cursor.fetchall()
            existing_files = []
            for result in results:
                for i in range(len(disks[result[3]])):
                    if os.path.exists(disks[result[3]][i][0] + str(result[2])):
                        existing_files.append(disks[result[3]][i][0] + str(result[2]))
            return existing_files
        except Exception as e:
            print(f"Ошибка поиска в базе: {str(e)}")
            return []

    def ChangeCurrentPath(self, new_path: str):
        self.current_path = new_path

    def GetExplorerWindowPath(self, MyHwnd):
        try:
            pythoncom.CoInitialize()
            shell_app = win32com.client.Dispatch("Shell.Application")
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

    def LearnFilePath(self, filename: str, extension: str | None = None):
        print(self.current_path)
        probably_files = []
        probably_files.extend(self.SearchFilesInDB(filename, extension))
        for i in os.listdir(self.current_path):
            if os.path.splitext(os.path.basename(i))[0] == filename:
                if not os.path.isdir(i):
                    if os.path.splitext(os.path.basename(i))[1] == extension or extension == None:
                        probably_files.append(self.current_path + "\\" + i)
                else:
                    self.ChangeCurrentPath(self.current_path + "\\" + i)
                    self.LearnFilePath(filename)
        if probably_files: return probably_files
        for i in os.listdir(desktop_path):
            if os.path.splitext(os.path.basename(i))[0] == filename:
                if not os.path.isdir(i):
                    if os.path.splitext(os.path.basename(i))[1] == extension or extension == None:
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
                            if extension == "lnk" or extension == None:
                                probably_files.append(recent_files_path + "\\" + i)
                        else:
                            self.ChangeCurrentPath(recent_files_path + "\\" + i)
                            self.LearnFilePath(filename)
            except Exception as e: continue
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
        path = self.LearnFilePath(path, "")[0]
        if not path: return "Папкаа не найдена"
        relpath = os.path.dirname(path)
        if not ziph: ziph = os.path.relpath(path, relpath) + ".zip"
        try:
            cwd = os.getcwd()
            os.chdir(path)
            result = subprocess.run(["patool", "create", ziph, "."], capture_output=True, text=True)
            os.chdir(cwd)
            move(path + "\\" + ziph, relpath)
            if result.returncode == 0:
                return f"Папка {ziph[:-4]} успешно заархивирована"
            else:
                return "Произошла ошибка при архивации папки"
        except:
            return "Произошла ошибка при архивации папки"
        
    def UnzippingFiles(self, path_to_ziph: str, outpath: str = "", extension: str | None = None):
        paths_to_ziph = self.LearnFilePath(path_to_ziph, extension)
        if not outpath: outpath = path_to_ziph.rsplit(".")[0]
        for path_to_ziph in paths_to_ziph:
            try:
                os.makedirs(outpath, exist_ok=True)
                cwd = os.getcwd()
                os.chdir(outpath)
                result = subprocess.run(["patool", "extract", path_to_ziph, "--outdir", outpath], capture_output=True, text=True)
                os.chdir(cwd)
                if result.returncode == 0:
                    return "Папка успешно разархивирована"
                else:
                    return "Произошла ошибка при разархивации папки"
            except:
                return "Произошла ошибка при разархивации папки"
            finally:
                self.RemoveFile(path_to_ziph)
        else: 
            return "Архив не найден"
            
    def WatchingZippedFiles(self, path_to_ziph: str, extension: str | None = None):
        paths_to_ziph = self.LearnFilePath(path_to_ziph, extension)
        for path_to_ziph in paths_to_ziph:
            result = subprocess.run(["patool", "list", path_to_ziph], capture_output=True, text=True)
            if result.returncode == 0:
                archive_list = result.stdout.splitlines()
                return archive_list
            else:
                return "Произошла ошибка при просмотре папки"
        else:
            return "Архив не найден"
  
Prepare()      
GetDisksByJSON()
