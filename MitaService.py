import win32serviceutil, win32service, win32event, win32api, win32process
import sys
import time
from os import path, scandir
import json
import psutil
import ctypes
import threading
import sqlite3
import pythoncom
import wmi
from threading import Event
import socket

Mitapath = ""

def get_downloaded_user():
    with open(f"C:/Mita/config.json", 'r', encoding='utf-8') as f:
        install_info = json.load(f)
    return install_info
        
def get_mita_path():
    global Mitapath
    try:
        Mitapath = get_downloaded_user().get('program_path')
    except Exception as e:
        print(f"Ошибка чтения конфига: {e}")

def install_service():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print("Требуются права администратора!")
            return False
        
        try:
            win32serviceutil.StopService("MitaDataCollectionService")
            win32serviceutil.RemoveService("MitaDataCollectionService")
            time.sleep(2)
        except:
            pass

        script_path = path.abspath(__file__)
        
        win32serviceutil.InstallService(
            pythonClassString=None,
            serviceName="MitaDataCollectionService",
            displayName="Mita Data Collection Service",
            description="Сервис сбора необходимых данных для голосового ассистента Мита",
            startType=win32service.SERVICE_AUTO_START,
            exeName="C:/Mita/Python310/python.exe",
            exeArgs=f'"{script_path}"'
        )
        
        print("Сервис установлен успешно")
        return True
        
    except Exception as e:
        print(f"Ошибка установки: {e}")
        return False
    
class LearnFiles():
    def __init__(self):
        self.current_path = get_downloaded_user().get('profile_path')
        self.stack = [(self.current_path, 0)]
        self.stop = Event()
        self.init_database()
        self.disks = {}
        # self.extensions = ['.png', '.jpg', '.jpeg', '.rtf']
        self.black_list = [".vscode", "Microsoft"]
        self.max_depth = 20
        self.letter_to_disk = {}
        self.batch_size = 25000
        
    def init_database(self):
        self.conn = sqlite3.connect(f'{Mitapath}/data/files.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                extension TEXT,
                path TEXT NOT NULL,
                disk_id TEXT,
                UNIQUE(name, extension, path, disk_id)
            )
        ''')
        self.conn.commit()

    def GetDisksInfo(self):
        self.disks.clear()
        self.letter_to_disk.clear()
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
                                self.disks[ph_disk["model"]].append([logical_disk_id, partition_id])

            for disk_model, partitions in self.disks.items():
                for logical_disk, partition_id in partitions:
                    self.letter_to_disk[logical_disk.upper()] = disk_model
                
            return c
        finally:
            pythoncom.CoUninitialize()
    
    def GetDiskByLetter(self, letter):
        return self.letter_to_disk.get(letter.upper(), "")
            
    def LearningFiles(self, resume=True):
        iteration_count = 0
        max_iteration_count = 5000 if resume else 100
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
            localpath, depth = self.stack.pop(0)
            try:
                with scandir(localpath) as elems:
                    for elem in elems:
                        letter, path_without_letter = path.splitdrive(elem.path)
                        disk_id = self.GetDiskByLetter(letter)
                        if elem.is_file():
                            name, extension = path.splitext(elem.name)
                            # if extension.lower() not in extensions: continue
                            if not extension: continue
                            if not self.FileExistsInDB(name, extension, path_without_letter, disk_id):
                                batch_data.append((name, extension, path_without_letter, disk_id))
                            if len(batch_data) >= self.batch_size:
                                self.InsertBatchToDB(batch_data)
                                batch_data.clear()
                        elif elem.is_dir():
                            name = elem.name
                            if not self.FileExistsInDB(name, "", path_without_letter, disk_id):
                                batch_data.append((name, "", path_without_letter, disk_id))
                            if len(batch_data) >= self.batch_size:
                                self.InsertBatchToDB(batch_data)
                                batch_data.clear()
                            if elem not in self.black_list and depth < self.max_depth:
                                self.stack.append((elem.path, depth+1))
            except (PermissionError, OSError) as e:
                print("Ошибка сканирования диска: " + str(e))
                continue
            iteration_count += 1
        else:
            self.stop.set()
            if batch_data:
                self.InsertBatchToDB(batch_data)
                batch_data.clear()
            
    def InsertBatchToDB(self, batch_data):
        try:
            print("Происходит сохранение файлов")
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
            
    def FileExistsInDB(self, filename, extension, localpath, disk_id):
        try:
            normalized_path = path.normpath(localpath).lower().replace('\\\\', '\\')
            
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
        if not args:
            args = [self._svc_name_]
        
        if not "debug" in args:
            win32serviceutil.ServiceFramework.__init__(self, args)
        else:
            self.args = args
            self.ssh = None
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True
        self.stop_scanning_files = threading.Event()
        self.stop_event = threading.Event()
        
        self.log_file = "C:/Mita/ServiceLog.txt"
        self.disks_file = f"{Mitapath}/data/disks.json"
        
        self.cpu_percent = psutil.cpu_percent()
        self.mem_free = 0
        self.disk_usage = 0
        self.workload_info = {}
        
        self.user_processes_dict = {}
        self.current_drive = "C"
        self.disk_usage_bool = True
        self.threads = []
        self.is_scanning_files = False
        
        self.filesClass = LearnFiles()
        self.init_disks_json()
        
        self.listener = None
        self.init_localhost()
        
        self.log("Сервис инициализирован")
        
    def init_disks_json(self):
        with open(self.disks_file, "w", encoding="utf-8") as f:
            f.write("{}")
            
    def init_localhost(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 9999))
        sock.listen()
        self.listener = sock
    
    def collect_processes_data(self):
        user_processes = []
        seen_exes = set()

        try:
            all_processes = psutil.process_iter()
            for p in all_processes:
                process_user = p.username()
                if '\\' in process_user: process_user_name = process_user.split('\\')[-1]
                elif '/' in process_user: process_user_name = process_user.split('/')[-1]
                else: process_user_name = process_user
                
                if process_user_name.lower() != get_downloaded_user()['active_user'].lower():
                    continue
                    
                if p.pid < 1000:
                    continue
                if p.status() != psutil.STATUS_RUNNING:
                    continue
                
                exe_path = p.exe()
                if not exe_path:
                    continue
                
                if exe_path.lower().startswith('c:\\windows'):
                    continue
                
                if exe_path in seen_exes:
                    continue
                seen_exes.add(exe_path)
                
                user_processes.append(p)
        except Exception as e:
            self.log(str(e))
            
        for proc in user_processes:
            try:
                proc_name = proc.name()
                if proc_name.lower().endswith('.exe'):
                    proc_name = proc_name[:-4]
                self.user_processes_dict[proc_name] = proc.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue   
            
    def collect_PC_workload_data(self):
        self.cpu_percent = psutil.cpu_percent()
        self.mem_free = psutil.virtual_memory().available/1024/1024/1024
        drive_letter = self.current_drive[0]
        self.disk_usage = self.get_disk_busy_time_pdh(drive_letter)
        
        self.workload_info = {
            "CPU_percent": self.cpu_percent,
            "Free_RAM": self.mem_free,
            "Disk_usage": self.disk_usage,
        }
        
    def check_disk_usage(self):
        try:
            utilization = self.disk_usage
            
            if utilization < 60:
                self.disk_usage_bool = True
            elif utilization > 90:
                self.disk_usage_bool = False
        except PermissionError as e:
            self.disk_usage_bool = False
            self.log(f"Не удаётся прочитать загрузку диска. Ошибка: {str(e)}")

                            
    def CollectionFilesData(self):
        win32process.SetThreadPriority(win32api.GetCurrentThread(), -1)
        while not self.stop_event.is_set() and not self.stop_scanning_files.is_set():
            try:
                self.is_scanning_files = True
                disks = [get_downloaded_user().get('profile_path')] + [d.device for d in psutil.disk_partitions(all=True) if d.fstype and d.device != "C:\\"]
                for disk in disks:
                    self.collect_PC_workload_data()
                    self.check_disk_usage()
                    if not self.disk_usage_bool:
                        self.log(f"Диск {disk} загружен, пропускаем сканирование")
                        continue
                    
                    if not path.exists(disk):
                        self.log(f"Диск {disk} недоступен, пропускаем сканирование")
                        continue
                    
                    self.current_drive = disk
                    self.filesClass.stack = [(disk, 0)]
                    self.filesClass.stop.clear()
                    self.filesClass.GetDisksInfo()
                    
                    try:
                        self.filesClass.LearningFiles(resume=True)
                        self.log("Файлы сохранены в базу данных")
                    except PermissionError as e:
                        self.log(f"Ошибка сканирования диска {disk}: {str(e)}")
                    
                    time.sleep(1)
                    
                self.is_scanning_files = False
            except Exception as e:
                self.log(f"Ошибка в collection_files_data: {str(e)}")
                self.stop_event.wait(30)
            
            for _ in range(360):
                if self.stop_event.is_set() or self.stop_scanning_files.is_set():
                    self.stop_scanning_files.clear()
                    break
                time.sleep(1)
            
    def CheckDisksJSON(self):
        while not self.stop_event.is_set():
            self.filesClass.GetDisksInfo()
            with open(self.disks_file, "r+", encoding="utf-8") as f:
                old_disks = json.load(f)
                if old_disks:
                    if old_disks["Disks"] != self.filesClass.disks:
                        f.seek(0)
                        json.dump({"Disks": self.filesClass.disks, "Time": time.time()}, f, indent=4, ensure_ascii=False)
                        f.truncate()
                        if not self.is_scanning_files:
                            self.stop_scanning_files.set()
                else:
                    f.seek(0)
                    json.dump({"Disks": self.filesClass.disks, "Time": time.time()}, f, indent=4, ensure_ascii=False)
                    f.truncate()
                    
            self.stop_event.wait(60)
            
    def CheckLocalhost(self):
        win32process.SetThreadPriority(win32api.GetCurrentThread(), 1)
        try:
            while not self.stop_event.is_set():
                try:
                    sock, addr = self.listener.accept()
                    request_data = sock.recv(16384).decode('utf-8')
                    
                    if "processes" in request_data.lower():
                        self.collect_processes_data()
                        sock.sendall(json.dumps(self.user_processes_dict).encode('utf-8'))
                    elif "workload" in request_data.lower():
                        self.collect_PC_workload_data()
                        sock.sendall(json.dumps(self.workload_info).encode('utf-8'))
                    else:
                        self.log("Не удалось распознать запрос")
                    
                    sock.close()
                except WindowsError:
                    pass
                except Exception as e:
                    print(f"Ошибка приёма данных с локального хоста: {e}")
            
                self.stop_event.wait(1)
        finally:
            self.listener.close()
            
    def StartThreads(self):
        threads = []
        
        thread1 = threading.Thread(target=self.CollectionFilesData, daemon=True)
        thread1.start()
        threads.append(thread1)
        
        thread2 = threading.Thread(target=self.CheckDisksJSON, daemon=True)
        thread2.start()
        threads.append(thread2)
        
        thread3 = threading.Thread(target=self.CheckLocalhost, daemon=True)
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
                            self.threads[i] = threading.Thread(target=self.CollectionFilesData, daemon=True)
                        elif i == 1:
                            self.threads[i] = threading.Thread(target=self.CheckDisksJSON, daemon=True)
                        elif i == 2:
                            self.threads[i] = threading.Thread(target=self.CheckLocalhost, daemon=True)
                        self.threads[i].start()
                if int(time.time()) % 3600 == 0:
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
        
    def get_disk_busy_time_pdh(self, drive_letter="C"):
        try:
            import subprocess
            result = subprocess.run(["powershell", "-Command", f'Get-Counter "\Логический диск({drive_letter}:)\% активности диска" -ErrorAction SilentlyContinue'], capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if result.returncode == 0:
                return float("".join(result.stdout.split(":")[-1].split()).replace(",", "."))
        except Exception as e:
            print(f"PowerShell-Counter error: {e}")
            return 0.0
    
    def log(self, message):
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"{time.ctime()}: {message}\n")

if __name__ == '__main__':
    get_mita_path()
    
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1].lower() == 'mitadatacollectionservice'):
        try:
            import servicemanager
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(MitaDataCollectionService)
            servicemanager.StartServiceCtrlDispatcher()
        except Exception as e:
            with open("C:/Mita/StartupError.txt", "w") as f:
                f.write(f"{time.ctime()}: {e}\n")
                import traceback
                f.write(traceback.format_exc())
            raise
    else:
        if sys.argv[1] == "setup":
            if install_service():
                print("Сервис запускается...")
                try:
                    win32serviceutil.StartService("MitaDataCollectionService")
                    print("Сервис запущен")
                except Exception as e:
                    print(f"Ошибка запуска: {e}")
        elif sys.argv[1] == "debug":
            service = MitaDataCollectionService([None, "debug"])
            service.SvcDoRun()
        else:
            win32serviceutil.HandleCommandLine(MitaDataCollectionService)

