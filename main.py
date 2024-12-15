import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import serial
import json

# Folder z obrazami
IMAGES_FOLDER = "./images"

# Funkcja do ładowania obrazów
def load_images():
    """Ładuje obrazy z folderu i przechowuje je w słowniku."""
    images = {}
    for i in range(1, 100):  # Przyjmujemy, że maksymalnie będzie 99 obrazów
        file_path = os.path.join(IMAGES_FOLDER, f"image{i}.png")
        if os.path.exists(file_path):
            try:
                img = Image.open(file_path)
                img_resized = img.resize((50, 50))  # Zmień rozmiar, jeśli konieczne
                images[i] = ImageTk.PhotoImage(img_resized)
            except Exception as e:
                print(f"Nie udało się załadować obrazu {file_path}: {e}")
    return images

# Funkcja do odświeżania tabeli z danymi JSON
def update_table(data):
    """Odświeża tabelę na podstawie nowych danych JSON."""
    for widget in image_column.winfo_children():
        widget.destroy()

    for row in table.get_children():
        table.delete(row)

    for idx, entry in enumerate(data["lastMessageTimes"], start=1):
        node_id = entry["node"]
        time_since = entry["timeSinceLastMessage"]
        alarm = entry.get("alarm", False)  # Pobieramy flagę alarmową (domyślnie False)

        # Pobieranie obrazu na podstawie indeksu
        img = images.get(idx, None)

        # Tworzenie wiersza z obrazem w osobnej kolumnie
        if img:
            img_label = tk.Label(image_column, image=img)
            img_label.grid(row=idx, column=0, padx=5, pady=5)
            text_label = tk.Label(image_column, text=f"Węzeł \n{node_id}", font=("Arial", 12))
            text_label.grid(row=idx, column=1, padx=5, pady=5)
            time_label = tk.Label(image_column, text=f"Czas: \n{time_since} ms", font=("Arial", 12))
            time_label.grid(row=idx, column=2, padx=5, pady=5)
            alarm_label = tk.Label(image_column, text=f"Alarm: \n{alarm}", font=("Arial", 12))
            alarm_label.grid(row=idx, column=3, padx=5, pady=5)

        # Dodanie wiersza do tabeli
        table.insert("", tk.END, values=(f"{node_id}", f"{time_since} ms", f"{alarm}"))

# Funkcja do odczytu danych z portu szeregowego
def start_serial_read():
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            try:
                data = json.loads(line)
                print(data)
                if "lastMessageTimes" in data:
                    update_table(data)
            except json.JSONDecodeError:
                print(f"Błąd: Odebrane dane nie są poprawnym JSON-em: {line}")
    except Exception as e:
        print(f"Błąd podczas odczytu z portu szeregowego: {e}")
    
    # Wywołanie ponowne po 100 ms
    root.after(100, start_serial_read)

# Konfiguracja portu szeregowego
port = "/dev/tty.wchusbserial585A0076601"  # Ustaw swój port
baud_rate = 115200                         # Ustawioną szybkość transmisji
ser = serial.Serial(port, baud_rate, timeout=1)

# Tworzenie GUI za pomocą Tkinter
root = tk.Tk()
root.title("Tabela JSON z obrazami")

# Ustawienie rozmiaru okna
root.geometry("1280x720")

# Załadowanie obrazów
images = load_images()

# Główne ramki
image_column = tk.Frame(root)
image_column.grid(row=0, column=0, padx=10, pady=10, sticky="n")

table_frame = tk.Frame(root)
table_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

# Tabela z danymi
table = ttk.Treeview(table_frame, columns=["Node", "Time", "Alarm"], show="headings", height=10)
table.heading("Node", text="Węzeł")
table.heading("Time", text="Czas")
table.heading("Alarm", text="Alarm")

# Rozpocznij odczyt danych z portu szeregowego
root.after(100, start_serial_read)

# Uruchom pętlę Tkinter
root.mainloop()

# Zamknięcie portu po zamknięciu GUI
ser.close()
