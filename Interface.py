import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="pkg_resources is deprecated")
import customtkinter as ctk
import sounddevice as sd
import soundfile as sf
import webbrowser
import tkinter.messagebox as messagebox
import requests
from win10toast import ToastNotifier
import threading
import time
from datetime import datetime


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        try:
            self.data_sound, self.fs_sound = sf.read("ButtonSound.mp3", dtype="float32")
        except Exception as e:
            print(f"Ошибка загрузки аудио: {e}")
            self.sound_enabled = False

        self.title("Menu")
        self.geometry("600x450")
        self.resizable(False, False)

        self.theme_mode = "light"
        self.autoload = False
        self.sound_enabled = True
        self.reminders = []
        self.toaster = ToastNotifier()
        self.settings_window = None
        self.reminders_window = None

        self.theme_colors = {
            "light": {"bg": "#ffffff", "fg": "#000000"},
            "dark": {"bg": "#2b2b2b", "fg": "#ffffff"},
            "colorblind": {"bg": "#ffff00", "fg": "#0000ff"}
        }

        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(expand=True)

        button_width = 180
        button_height = 40
        button_font = ("Arial", 14, "bold")

        buttons = [
            ("Обновление", self.start),
            ("Автозагрузка: ВКЛ", self.toggle_autoload),
            ("Напоминания", self.open_reminders),
            ("Настройки", self.open_settings),
            ("Помощь", self.open_help)
        ]

        for text, command in buttons:
            ctk.CTkButton(self.button_frame, text=text, command=command,
                         width=button_width, height=button_height, font=button_font).pack(pady=10)

        self.version_label = ctk.CTkLabel(self, text="v0.0.7", text_color="gray")
        self.version_label.pack(side="bottom", anchor="se", padx=10, pady=10)

        self.reminder_thread = threading.Thread(target=self.check_reminders, daemon=True)
        self.reminder_thread.start()

        self.update_theme()

    def update_theme(self):
        colors = self.theme_colors[self.theme_mode]
        ctk.set_appearance_mode("dark" if self.theme_mode == "dark" else "light")
        self.configure(fg_color=colors['bg'])
        
        if self.settings_window:
            self.settings_window.update_theme_display()
            self.settings_window.configure(fg_color=colors['bg'])
        if self.reminders_window:
            self.reminders_window.configure(fg_color=colors['bg'])

    def check_reminders(self):
        while True:
            now = datetime.now()
            for reminder in self.reminders[:]:
                reminder_time = datetime.strptime(f"{reminder[0]} {reminder[1]}", "%d.%m.%Y %H:%M")
                if now >= reminder_time:
                    self.show_notification(reminder[2])
                    self.reminders.remove(reminder)
                    if self.reminders_window:
                        self.reminders_window.update_list()
            time.sleep(1)

    def show_notification(self, message):
        self.toaster.show_toast("Напоминание", message, duration=10)

    def play_button_sound(self):
        if self.sound_enabled and hasattr(self, 'data_sound'):
            sd.play(self.data_sound, self.fs_sound)

    def toggle_theme(self):
       modes = ["light", "dark", "colorblind"]
       self.theme_mode = modes[(modes.index(self.theme_mode) + 1) % 3]
       self.update_theme()
       self.play_button_sound()

    def toggle_autoload(self):
        self.autoload = not self.autoload
        status = "ВКЛ" if self.autoload else "ВЫКЛ"
        for child in self.button_frame.winfo_children():
            if isinstance(child, ctk.CTkButton) and "Автозагрузка" in child.cget("text"):
                child.configure(text=f"Автозагрузка: {status}")
        self.play_button_sound()

    def start(self):
        self.play_button_sound()
        local_version = "0.0.7"
        url_version = "https://raw.githubusercontent.com/Zakhar226/Public/main/version.txt"
        url_changelog = "https://raw.githubusercontent.com/Zakhar226/Public/main/changelog.txt"

        try:
            response = requests.get(url_version)
            response.raise_for_status()
            remote_version = response.text.strip()

            if local_version != remote_version:
                changelog = "Нет информации об изменениях"
                try:
                    changelog_response = requests.get(url_changelog)
                    if changelog_response.ok:
                        changelog = changelog_response.text
                except Exception as e:
                    print(f"Ошибка получения changelog: {e}")

                msg = (f"Доступна новая версия {remote_version}!\n\n"
                      f"Изменения в обновлении:\n{changelog}\n\n"
                      "Хотите перейти на внешний ресурс?")
                response = messagebox.askyesno("Обновление", msg)
                if response:
                    webbrowser.open("https://github.com")
            else:
                messagebox.showinfo("Обновление", "У вас установлена актуальная версия приложения")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось проверить версию: {e}")

    def open_help(self):
        self.play_button_sound()
        response = messagebox.askquestion("Помощь", "Вы хотите перейти на внешний ресурс?")
        if response == 'yes':
            webbrowser.open("https://t.me/hellpers24bot")

    def open_settings(self):
        self.play_button_sound()
        if not self.settings_window or not self.settings_window.winfo_exists():
            self.settings_window = SettingsWindow(self)
        else:
            self.settings_window.focus()

    def open_reminders(self):
        self.play_button_sound()
        if not self.reminders_window or not self.reminders_window.winfo_exists():
            self.reminders_window = RemindersWindow(self)
        else:
            self.reminders_window.focus()

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Настройки")
        self.geometry("300x300")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.configure(fg_color=self.parent.theme_colors[self.parent.theme_mode]['bg'])
        
        self.button_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.button_frame.pack(expand=True)

        button_width = 180
        button_height = 40
        button_font = ("Arial", 14, "bold")

        self.theme_button = ctk.CTkButton(
            self.button_frame, 
            text=f"Тема: {self.parent.theme_mode.upper()}", 
            command=self.parent.toggle_theme,
            width=button_width, 
            height=button_height, 
            font=button_font
        )
        self.theme_button.pack(pady=10)

        self.sound_button = ctk.CTkButton(
            self.button_frame, 
            text=f"Звук: {'ВКЛ' if self.parent.sound_enabled else 'ВЫКЛ'}", 
            command=self.toggle_sound,
            width=button_width, 
            height=button_height, 
            font=button_font
        )
        self.sound_button.pack(pady=10)

        self.clear_cache_button = ctk.CTkButton(
            self.button_frame, 
            text="Сброс", 
            command=self.confirm_clear_cache,
            width=button_width, 
            height=button_height, 
            font=button_font
        )
        self.clear_cache_button.pack(pady=10)

    def toggle_sound(self):
        self.parent.sound_enabled = not self.parent.sound_enabled
        self.sound_button.configure(text=f"Звук: {'ВКЛ' if self.parent.sound_enabled else 'ВЫКЛ'}")

    def confirm_clear_cache(self):
        self.parent.play_button_sound()
        response = messagebox.askyesno("Подтверждение", "Вы точно хотите сбросить приложение?")
        if response:
            self.parent.destroy()

    def update_theme_display(self):
        self.theme_button.configure(text=f"Тема: {self.parent.theme_mode.upper()}")
        self.configure(fg_color=self.parent.theme_colors[self.parent.theme_mode]['bg'])

class RemindersWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Напоминания")
        self.geometry("400x400")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        self.configure(fg_color=self.parent.theme_colors[self.parent.theme_mode]['bg'])
        
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(padx=20, pady=20, fill="both", expand=True)

        ctk.CTkLabel(self.main_frame, text="Дата (ДД.ММ.ГГГГ):").pack()
        self.date_entry = ctk.CTkEntry(self.main_frame)
        self.date_entry.pack(pady=5)

        ctk.CTkLabel(self.main_frame, text="Время (ЧЧ:ММ):").pack()
        self.time_entry = ctk.CTkEntry(self.main_frame)
        self.time_entry.pack(pady=5)

        ctk.CTkLabel(self.main_frame, text="Сообщение:").pack()
        self.message_entry = ctk.CTkEntry(self.main_frame)
        self.message_entry.pack(pady=5)

        ctk.CTkButton(
            self.main_frame, 
            text="Добавить напоминание", 
            command=self.add_reminder,
            font=("Arial", 12, "bold")
        ).pack(pady=10)

        self.reminders_list = ctk.CTkTextbox(self.main_frame, height=150)
        self.reminders_list.pack(fill="x")
        self.update_list()

    def add_reminder(self):
        date_str = self.date_entry.get()
        time_str = self.time_entry.get()
        message = self.message_entry.get()
        
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            datetime.strptime(time_str, "%H:%M")
            self.parent.reminders.append((date_str, time_str, message))
            self.update_list()
            self.date_entry.delete(0, "end")
            self.time_entry.delete(0, "end")
            self.message_entry.delete(0, "end")
        except ValueError:
            messagebox.showerror("Ошибка", "Некорректный формат даты или времени!")

    def update_list(self):
        self.reminders_list.delete("1.0", "end")
        for idx, (date, time, msg) in enumerate(self.parent.reminders, 1):
            self.reminders_list.insert("end", f"{idx}. {date} {time} - {msg}\n")

if __name__ == "__main__":
    app = App()
    app.mainloop()