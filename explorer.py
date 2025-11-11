import os
import zipfile
import pygetwindow as gw
import win32gui
import comtypes.client
import platform
import winshell
import win32com.client
import wmi
import pythoncom
import sqlite3
from threading import Event

shell = win32com.client.Dispatch("WScript.Shell")
username = os.getlogin()
path_of_this_file = os.path.dirname((os.path.abspath(__file__))) + "\\"
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


class Explorer():
    def __init__(self, current_path):
        self.current_path = current_path
        self.stack = [(current_path, 0)]
        self.stop = Event()
        self.init_database()
        
    def init_database(self):
        self.conn = sqlite3.connect(f'{path_of_this_file}\\files.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.conn.isolation_level = None
        self.cursor.execute('PRAGMA synchronous = OFF')
        self.cursor.execute('PRAGMA journal_mode = MEMORY')
        self.cursor.execute('PRAGMA cache_size = 10000')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                extension TEXT NOT NULL,
                path TEXT NOT NULL,
                disk_id TEXT,
                UNIQUE(name, extension, path, disk_id)
            )
        ''')
        self.conn.commit()

    # @staticmethod
    # def ScanDisk(path = f"C:\\Users\\{username}"):
    #         old_dict = {}
    #         while 1:
    #             # files_system.keys()[files_system.keys().index(files_system.values()[0])]
    #             # files_system.values()[0].values()[0]
                
    #             # right_list = []
    #             # for i in list(files_system):
    #             #     for ii in list(files_system.values()):
    #             #         right_list.append(i)
    #             #         right_list.append(ii[0].keys()[0])
                
    #             # try:
    #             #     if i == 0: next_value = eval("files_system" + ".values()")
    #             #     else: next_value = eval("files_system" + ".values()" + "[0].values()"*(i))
    #             # except Exception as e: 
    #             #     print(str(e))
    #             #     break
    #             # for ii in next_value:
    #             #     try: next_elem = eval("files_system.keys()[files_system.keys().index(files_system" + ".values()[" + ii + "]"*(i+1) + ")]")
    #             #     except Exception as e: 
    #             #         print(str(e))
    #             #         break

    #             dict_deep = 0
    #             tmp = [files_system]

    #             while tmp:
    #                 elem = tmp.pop()
    #                 if type(elem) == dict:
    #                     for obj in elem.values():
    #                         if type(obj) == dict: 
    #                             tmp.append(obj)
    #                     dict_deep += 1

    #             # for root, dirs, files in os.walk(dict):
    #             #     files_system.update({root: [[f'{root}\\{dir}' for dir in dirs], files]})

    #             # for ii in range(dict_deep):
    #             #     if ii == 0: next_value = files_system
    #             #     else: next_value = eval("files_system" + ".values()[0]"*ii)
    #             #     for iii in list(next_value.keys()):
    #             #         for root, dirs, files in os.walk(iii):
    #             #             eval("list(files_system.values())" + "[0]"*ii + "[list(files_system.values())" + "[0]"*ii + ".index(root)]") = {root: [[f'{root}\\{dir}' for dir in dirs], files]}
                
    #             need_paths = [path]


    #             if old_dict == files_system:
    #                 break
    #             old_dict = files_system
    #             print(files_system)
    #         return files_system
    
    @staticmethod
    def GetDisksInfo():
        global disks
        disks.clear()
        summary = [[], [], []]
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            
            for disk in c.Win32_DiskDrive():
                summary[0].append({
                    'model': disk.Model,
                    'interface': disk.InterfaceType,
                    'size_gb': int(disk.Size) // (1024**3) if disk.Size else 0,
                    'serial': (disk.SerialNumber or '').strip(),
                    'drive': disk.DeviceID
                })
            
            for logical in c.Win32_LogicalDisk():
                summary[1].append({
                    'drive': logical.DeviceID,
                    'size_gb': int(logical.Size) // (1024**3) if logical.Size else 0,
                    'free_gb': int(logical.FreeSpace) // (1024**3) if logical.FreeSpace else 0,
                })
            
            for cd in c.Win32_CDROMDrive():
                summary[2].append({
                    'drive': cd.Drive,
                    'model': cd.Model
                })
                
            for i in summary[0]:
                if i["serial"]: disks[i["serial"]] = []
        
            for ph_disk in summary[0]:
                for disk_to_part in c.Win32_DiskDriveToDiskPartition():
                    if disk_to_part.Antecedent.DeviceID == ph_disk["drive"]:
                        partition_id = disk_to_part.Dependent.DeviceID
                        for part_to_logical in c.Win32_LogicalDiskToPartition():
                            if part_to_logical.Antecedent.DeviceID == partition_id:
                                logical_disk_id = part_to_logical.Dependent.DeviceID
                                if ph_disk["serial"]: disks[ph_disk["serial"]].append((logical_disk_id, partition_id))
                                # else: disks[ph_disk["model"]].append((logical_disk_id, partition_id))
                
            return c
        finally:
            pythoncom.CoUninitialize()
    
    def GetDiskByLetter(self, letter):
        for key, value in disks.items():
            try:
                if value[0][0].upper() == letter.upper():
                    return key
            except:
                continue
        
        return ""

    def LearningFiles(self, resume=True):
        iteration_count = 0
        max_iteration_count = 1000 if resume else 10
        batch_size = 1000
        batch_data = []
        while self.stack:
            if iteration_count >= max_iteration_count: 
                if batch_data:
                    self.InsertBatchToDB(batch_data)
                    batch_data.clear()
                return
            if self.stop.is_set(): 
                if batch_data:
                    self.InsertBatchToDB(batch_data)
                    batch_data.clear()
                return
            path, depth = self.stack.pop(0)
            try:
                with os.scandir(path) as elems:
                    for elem in elems:
                        if elem.is_file():
                            filename, extension = os.path.splitext(elem.name)
                            # if extension.lower() not in extensions: continue
                            if not extension: continue
                            letter, path_without_letter = os.path.splitdrive(elem.path)
                            disk_id = self.GetDiskByLetter(letter)
                            if not self.FileExistsInDB(filename, extension, path_without_letter, disk_id):
                                batch_data.append((filename, extension, path_without_letter, disk_id))
                            if len(batch_data) >= batch_size:
                                self.InsertBatchToDB(batch_data)
                                batch_data.clear()
                        elif elem.is_dir():
                            if elem not in black_list and depth < max_depth:
                                self.stack.append((elem.path, depth+1))
            except (PermissionError, OSError):
                continue
            iteration_count += 1
        else:
            self.stop.set()
            
    def InsertBatchToDB(self, batch_data):
        try:
            self.cursor.executemany('''
                INSERT OR IGNORE INTO files (name, extension, path, disk_id)
                VALUES (?, ?, ?, ?)
            ''', batch_data)
            self.conn.commit()
        except Exception as e:
            print(f"Ошибка пакетной записи: {e}")
            
    def CloseDatabase(self):
        if hasattr(self, 'conn'):
            self.conn.close()
            
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
        
    def FileExistsInDB(self, filename, extension, path, disk_id):
        try:
            normalized_path = os.path.normpath(path).lower().replace('\\\\', '\\')
            
            self.cursor.execute('''
                SELECT COUNT(*) FROM files 
                WHERE name = ? AND extension = ? AND disk_id = ?
                AND LOWER(path) = ?
            ''', (filename, extension, disk_id, normalized_path))
            return self.cursor.fetchone()[0] > 0
        except Exception as e:
            print(f"Ошибка проверки файла в базе: {e}")
            return False
       
    @staticmethod
    def GetDiskAction():
        try:
            pythoncom.CoInitialize()
            c = wmi.WMI()
            for disk in c.Win32_PerfFormattedData_PerfDisk_PhysicalDisk():
                if disk.Name[2:] in current_drive and disk.Name[2:]:
                    utilization = float(disk.PercentDiskTime)
                    if utilization > 100.0: utilization = 100.0
                    return utilization
        except Exception as e:
            print(str(e))
        finally:
            pythoncom.CoUninitialize()
            
    # @staticmethod
    # def FindFile(name: str):
    #     return glob.glob(f"C:\\**\\{name}*", recursive=True)

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
        path = self.LearnFilePath(path)
        if ziph == "":
            ziph = os.path.relpath(path, os.path.dirname(path)) + ".zip"
        try:
            with zipfile.ZipFile(os.path.dirname(path) + "\\" + ziph, 'a', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(path):
                    for file in files:
                        print(os.path.join(root, file))
                        zipf.write(os.path.join(root, file), os.path.join(root, file)[len(path):])
            return f"Папка {ziph[:-4]} успешно заархивирована"
        except:
            return f"Произошла ошибка при архивации папки"
        
    def UnzippingFiles(self, path_to_ziph: str):
        path_to_ziph = self.LearnFilePath(path_to_ziph)
        try:
            os.makedirs(path_to_ziph[:-4], True)
            with zipfile.ZipFile(path_to_ziph, 'r') as zipf:
                zipf.extractall(path_to_ziph[:-4])
            return "Папка успешно разархивирована"
        except:
            return "Произошла ошибка при разархивации папки"
        
# exp = Explorer("C:\\Users\\Admin")
# while not stop:
#     exp.GetDisksInfo()
#     exp.LearningFiles()