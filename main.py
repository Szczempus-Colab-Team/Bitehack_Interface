import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial
import json

# Folder z obrazami
IMAGES_FOLDER = "./images"
CSV_FOLDER = "./csv"
CSV_FILE = os.path.join(CSV_FOLDER, "trajectory.csv")  # Ścieżka do pliku CSV z danymi

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

    for idx, entry in enumerate(data.get("lastMessageTimes", []), start=1):
        node_id = entry.get("node", "Brak danych")
        time_since = entry.get("timeSinceLastMessage", "Brak danych")
        alarm = entry.get("alarm", False)
        distance = entry.get("distance", None)
        status = entry.get("status", None)

        img = images.get(idx, None)

        if img:
            img_label = tk.Label(image_column, image=img)
            img_label.grid(row=idx, column=0, padx=5, pady=5)
            text_label = tk.Label(image_column, text=f"Węzeł \n{node_id}", font=("Arial", 12))
            text_label.grid(row=idx, column=1, padx=5, pady=5)
            time_label = tk.Label(image_column, text=f"Czas: \n{time_since} ms", font=("Arial", 12))
            time_label.grid(row=idx, column=2, padx=5, pady=5)
            alarm_label = tk.Label(image_column, text=f"Alarm: \n{alarm}", font=("Arial", 12))
            alarm_label.grid(row=idx, column=3, padx=5, pady=5)
            distance_label = tk.Label(image_column, text=f"Distance: \n{distance}" if distance is not None else "", font=("Arial", 12))
            distance_label.grid(row=idx, column=4, padx=5, pady=5)
            status_label = tk.Label(image_column, text=f"Status: \n{status}" if status is not None else "", font=("Arial", 12))
            status_label.grid(row=idx, column=5, padx=5, pady=5)

        table.insert("", tk.END, values=(
            f"{node_id}",
            f"{time_since} ms",
            f"{alarm}",
            f"{distance if distance is not None else ''}",
            f"{status if status is not None else ''}"
        ))

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
    
    root.after(100, start_serial_read)

# Funkcja do tworzenia wykresu 3D na podstawie danych z pliku CSV
def create_3d_plot_from_csv(csv_file):
    try:
        # Odczyt danych z CSV
        df = pd.read_csv(csv_file)

        fig = Figure(figsize=(7, 6), dpi=100)
        ax = fig.add_subplot(111, projection='3d')

        # Wykres trajektorii
        sc = ax.scatter(df['x'], df['y'], df['z'], c=df['time'], cmap='viridis', label='Trajektoria 3D')
        ax.set_title("Trajektoria ruchu strażaka w czasie")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        fig.colorbar(sc, ax=ax, label='Czas')

        return fig
    except Exception as e:
        print(f"Błąd podczas tworzenia wykresu 3D: {e}")
        return None

# Konfiguracja portu szeregowego
port = "/dev/tty.wchusbserial585A0076601"
baud_rate = 115200
ser = serial.Serial(port, baud_rate, timeout=1)

# Tworzenie GUI za pomocą Tkinter
root = tk.Tk()
root.title("Lista strażaków i wykresem 3D")

# Ustawienie rozmiaru okna
root.geometry("1280x720")

images = load_images()

# Ramka na obrazy
image_column = tk.Frame(root)
image_column.grid(row=0, column=0, padx=10, pady=10, sticky="n")

# Ramka na tabelę
table_frame = tk.Frame(root)
table_frame.grid(row=0, column=1, padx=10, pady=10, sticky="n")

table = ttk.Treeview(table_frame, columns=["Node", "Time", "Alarm", "Distance", "Status"], show="headings", height=10)

# Tworzenie ramki na wykres 3D
plot_frame = tk.Frame(root)
plot_frame.grid(row=0, column=2, columnspan=2, padx=10, pady=10)

# Dodanie wykresu 3D do ramki
figure = create_3d_plot_from_csv(CSV_FILE)
if figure:
    canvas = FigureCanvasTkAgg(figure, master=plot_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack()

# Rozpocznij odczyt danych z portu szeregowego
root.after(100, start_serial_read)

# Uruchomienie głównej pętli Tkinter
root.mainloop()

# Zamknięcie portu po zamknięciu GUI
ser.close()
