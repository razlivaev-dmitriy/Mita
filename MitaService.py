import win32serviceutil
import win32service
import win32event
import servicemanager
import sys
import time
from os import path, scandir, makedirs
import json
import psutil
import ctypes
import threading
import sqlite3
import pythoncom
import wmi
from threading import Event

def get_downloaded_user():
    with open(f"C:/ProgramData/Mita/config.json", 'r', encoding='utf-8') as f:
        install_info = json.load(f)
    return install_info
        
Mitapath = f"{get_downloaded_user()['profile_path']}/AppData/Local"

def install_service():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Требуются права администратора!")
            return False
        
        import win32serviceutil
        import win32service
        
        script_path = path.abspath(__file__)
        
        win32serviceutil.InstallService(
            pythonClassString=None,
            serviceName="MitaDataCollectionService",
            displayName="Mita Data Collection Service",
            description="Сервис сбора необходимых данных для голосового ассистента Мита",
            startType=win32service.SERVICE_AUTO_START,
            exeName=sys.executable,
            exeArgs=f'"{script_path}"'
        )
        
        print("Сервис установлен успешно")
        return True
        
    except Exception as e:
        print(f"Ошибка установки: {e}")
        return False
    
class LearnFiles():
    def __init__(self):
        self.current_path = get_downloaded_user()['profile_path']
        self.stack = [(self.current_path, 0)]
        self.stop = Event()
        self.init_database()
        self.disks = {}
        # self.extensions = ['.png', '.jpg', '.jpeg', '.rtf']
        self.black_list = [".vscode", "Microsoft"]
        self.max_depth = 10
        
    def init_database(self):
        self.conn = sqlite3.connect(f'{Mitapath}/data/files.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
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
        
        with open(f"{Mitapath}/data/processes_data.json", "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)

    def GetDisksInfo(self):
        self.disks.clear()
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
                self.disks[i["model"]] = []
        
            for ph_disk in summary[0]:
                for disk_to_part in c.Win32_DiskDriveToDiskPartition():
                    if disk_to_part.Antecedent.DeviceID == ph_disk["drive"]:
                        partition_id = disk_to_part.Dependent.DeviceID
                        for part_to_logical in c.Win32_LogicalDiskToPartition():
                            if part_to_logical.Antecedent.DeviceID == partition_id:
                                logical_disk_id = part_to_logical.Dependent.DeviceID
                                self.disks[ph_disk["model"]].append((logical_disk_id, partition_id))
                
            return c
        finally:
            pythoncom.CoUninitialize()
    
    def GetDiskByLetter(self, letter):
        for key, value in self.disks.items():
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
                with scandir(path) as elems:
                    for elem in elems:
                        if elem.is_file():
                            filename, extension = path.splitext(elem.name)
                            # if extension.lower() not in extensions: continue
                            if not extension: continue
                            letter, path_without_letter = path.splitdrive(elem.path)
                            disk_id = self.GetDiskByLetter(letter)
                            if not self.FileExistsInDB(filename, extension, path_without_letter, disk_id):
                                batch_data.append((filename, extension, path_without_letter, disk_id))
                            if len(batch_data) >= batch_size:
                                self.InsertBatchToDB(batch_data)
                                batch_data.clear()
                        elif elem.is_dir():
                            if elem not in self.black_list and depth < self.max_depth:
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
            
    def FileExistsInDB(self, filename, extension, path, disk_id):
        try:
            normalized_path = path.normpath(path).lower().replace('\\\\', '\\')
            
            self.cursor.execute('''
                SELECT COUNT(*) FROM files 
                WHERE name = ? AND extension = ? AND disk_id = ?
                AND LOWER(path) = ?
            ''', (filename, extension, disk_id, normalized_path))
            return self.cursor.fetchone()[0] > 0
        except Exception as e:
            print(f"Ошибка проверки файла в базе: {e}")
            return False

class MitaDataCollectionService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MitaDataCollectionService"
    _svc_display_name_ = "Mita Data Collection Service"
    _svc_description_ = "Сервис сбора необходимых данных для голосового ассистента Мита"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True
        self.stop_event = threading.Event()
        
        makedirs("C:/ProgramData/Mita", exist_ok=True)
        self.log_file = "C:/ProgramData/Mita/ServiceLog.txt"
        
        self.user_processes = []
        self.current_drive = None
        self.disk_usage_bool = False
        
        self.filesClass = LearnFiles()
        
        self.log("Сервис инициализирован")
        
    def CollectionProcessesData(self):
        while not self.stop_event.is_set():
            user_processes = []
            user_processes_names = []
            user_processes_paths = []

            with open(f"{Mitapath}/data/processes_data.json", "r", encoding="utf-8") as f:
                user_processes_dict = json.load(f)

            try:
                all_processes = psutil.process_iter()
                for p in all_processes:
                    if p.username() == psutil.Process().username():
                        if p.pid >= 1000:
                            if p.status() == psutil.STATUS_RUNNING:
                                for s in range(len(p.exe())):
                                    if s >= 10:
                                        break
                                    if p.exe()[s] == "C:\Windows"[s]:
                                        continue
                                    else:
                                        user_processes.append(p)
                                        break
                
                for i in range(len(user_processes) - 1):
                    if i > 0:
                        for ii in range(i-1, 0, -1):
                            try:
                                if user_processes[i].exe() == user_processes[ii].exe():
                                    break
                            except psutil.NoSuchProcess:
                                pass
                        else:
                            self.user_processes.append(user_processes[i])
                            
                for i in self.user_processes:
                    user_processes_paths.append(i.exe())
                    user_processes_names.append(i.name()[:-4])
                    user_processes_dict[i.name()[:-4]] = i.exe()
            except Exception as e:
                self.log(str(e))

            with open(f"{Mitapath}/data/processes_data.json", "w", encoding="utf-8") as f:
                json.dump(user_processes_dict, f, ensure_ascii=False, indent=4)
                
            self.stop_event.wait(10)
                            
    def CollectionFilesData(self):
        while not self.stop_event.is_set():
            try:
                disks = [get_downloaded_user()['profile_path']] + [d.device for d in psutil.disk_partitions() if d.fstype and d.device != "C:\\"]
                for disk in disks:
                    if not self.disk_usage_bool:
                        self.log(f"Диск {disk} загружен, пропускаем сканирование")
                        continue
                    
                    self.current_drive = disk
                    self.filesСlass.stack = [(disk, 0)]
                    self.filesСlass.stop.clear()
                    self.filesСlass.GetDisksInfo()
                    
                    try:
                        self.filesClass.LearningFiles(resume=True)
                        print("Файлы сохранены в базу данных")
                    except PermissionError as e:
                        self.log(f"Ошибка сканирования диска {disk}: {str(e)}")
                    
                    time.sleep(1)
            except Exception as e:
                self.log(f"Ошибка в collection_files_data: {str(e)}")
                self.stop_event.wait(60)
            
            self.stop_event.wait(3600)
                
    def CheckDiskUsage(self):
        while not self.stop_event.is_set():
            try:
                try:
                    pythoncom.CoInitialize()
                    c = wmi.WMI()
                    for disk in c.Win32_PerfFormattedData_PerfDisk_PhysicalDisk():
                        if disk.Name[2:] in self.current_drive and disk.Name[2:]:
                            utilization = float(disk.PercentDiskTime)
                            if utilization > 100.0: utilization = 100.0
                            return utilization
                except Exception as e:
                    print(str(e))
                finally:
                    pythoncom.CoUninitialize()
                if utilization < 50:
                    self.disk_usage_bool = True
                elif utilization > 90:
                    self.disk_usage_bool = False
            except PermissionError:
                self.disk_usage_bool = False
            
            self.stop_event.wait(60)
            
    def StartThreads(self):
        threads = []
        
        thread1 = threading.Thread(target=self.CollectionProcessesData, daemon=True)
        thread1.start()
        threads.append(thread1)
        
        thread2 = threading.Thread(target=self.CheckDiskUsage, daemon=True)
        thread2.start()
        threads.append(thread2)
        
        thread3 = threading.Thread(target=self.CollectionFilesData, daemon=True)
        thread3.start()
        threads.append(thread3)
        
        self.log("Все потоки запущены")
        return threads
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_alive = False
        self.stop_event.set()
        win32event.SetEvent(self.hWaitStop)
        self.log("Сервис останавливается...")
        
    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.log("Сервис запускается...")
        
        try:
            self.log("Инициализация...")
            
            def start_threads_async():
                self.threads = self.StartThreads()
            
            thread_starter = threading.Thread(target=start_threads_async)
            thread_starter.daemon = True
            thread_starter.start()
            
            self.ReportServiceStatus(win32service.SERVICE_RUNNING)
            self.log("Сервис запущен и работает")

            while self.is_alive:
                result = win32event.WaitForSingleObject(self.hWaitStop, 1000)
                if result == win32event.WAIT_OBJECT_0:
                    break
                for i, thread in enumerate(self.threads):
                    if not thread.is_alive():
                        self.log(f"Поток {i} завершился, перезапускаем...")
                        if i == 0:
                            self.threads[i] = threading.Thread(target=self.collection_processes_data, daemon=True)
                        elif i == 1:
                            self.threads[i] = threading.Thread(target=self.check_disk_usage, daemon=True)
                        elif i == 2:
                            self.threads[i] = threading.Thread(target=self.collection_files_data, daemon=True)
                        self.threads[i].start()
                if int(time.time()) % 30 == 0:
                    self.log("Сервис активен...")
        except Exception as e:
            self.log(f"Критическая ошибка в SvcDoRun: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            
        self.stop_event.set()
        if hasattr(self, 'threads'):
            for thread in self.threads:
                if thread.is_alive():
                    thread.join(timeout=5)
        
        self.filesClass.CloseDatabase()
        self.log("Сервис завершил работу")
    
    def log(self, message):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()}: {message}\n")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            if install_service():
                print("Запускаем сервис...")
                import win32serviceutil
                win32serviceutil.StartService("MitaDataCollectionService")
            elif sys.argv[1] == "debug":
                service = MitaDataCollectionService([])
                service.SvcDoRun()
            else:
                win32serviceutil.HandleCommandLine(MitaDataCollectionService)
    else:
        if len(sys.argv) == 1:
            import servicemanager
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(MitaDataCollectionService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            import win32serviceutil
            win32serviceutil.HandleCommandLine(MitaDataCollectionService)
