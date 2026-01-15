
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, time, socket
import pandas as pd
import face_recognition, cv2, os
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from pyfirmata import Arduino, SERVO
import pyttsx3
from datetime import datetime


board = Arduino("COM12")
servo_pin = 9
led_pin = 13
buzzer_pin = 8
board.digital[servo_pin].mode = SERVO
board.digital[servo_pin].write(10)


engine = pyttsx3.init()
engine.setProperty('rate', 150)

def speak(text):
    threading.Thread(target=lambda: (engine.say(text), engine.runAndWait())).start()

# ملفات
patients_file = "patients.xlsx"
log_file = "log.xlsx"
if not os.path.exists(patients_file):
    df = pd.DataFrame(columns=["Name", "Disease", "Image"])
    df.to_excel(patients_file, index=False)
if not os.path.exists(log_file):
    df = pd.DataFrame(columns=["Doctor", "Patient", "Medicine", "Quantity", "DateTime"])
    df.to_excel(log_file, index=False)

# بيانات الأطباء
doctors = {"Amjed Dariadi": "C:/Users/computer/Desktop/hackathon_re/MyProject/Doctors/amjed.jpg"}
medicines = [
    "Isoniazid", 
    "Dexamethasone",    
    "Inmazeb",   
    "Ceftriaxone",  
    "Acyclovir"       
]

# وظائف الباب 

def move_servo_smoothly(start, end, step=1, delay=0.03):
    direction = 1 if start < end else -1
    for angle in range(start, end + direction, direction * step):
        board.digital[servo_pin].write(angle)
        time.sleep(delay)
    board.digital[servo_pin].write(end)

def blink_led(times, delay):
    for _ in range(times):
        board.digital[led_pin].write(1)
        time.sleep(delay)
        board.digital[led_pin].write(0)
        time.sleep(delay)

def open_door():

    for _ in range(5):
        board.digital[buzzer_pin].write(1)
        time.sleep(0.3)
        board.digital[buzzer_pin].write(0)
        time.sleep(0.7)

    for _ in range(6):
        board.digital[buzzer_pin].write(1)
        time.sleep(0.1)
        board.digital[buzzer_pin].write(0)
        time.sleep(0.1)


    blink_led(5, 0.1)
    move_servo_smoothly(10, 110)
    time.sleep(10)


    board.digital[buzzer_pin].write(1)
    move_servo_smoothly(110, 10)
    board.digital[buzzer_pin].write(0)



def recognize_doctor():
    known_faces = []
    known_names = []
    for name, path in doctors.items():
        if os.path.exists(path):
            img = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(img)[0]
            known_faces.append(encoding)
            known_names.append(name)

    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)
        for enc in encodings:
            matches = face_recognition.compare_faces(known_faces, enc)
            if True in matches:
                idx = matches.index(True)
                cap.release()
                cv2.destroyAllWindows()
                return known_names[idx]
        cv2.imshow("Recognizing...", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return None


class App:
    def __init__(self, root):
        self.root = root
        self.root.geometry("900x600")
        self.root.title("Medical Robot System")
        self.root.configure(bg="#1E1E2F")
        self.canvas = tk.Canvas(root, bg="#0F0F1A", highlightthickness=0)
        self.canvas.place(relwidth=1, relheight=1)
        self.circles = []
        self.create_animation()
        self.notifications = []
        self.create_notification_label()
        self.create_buttons()
        tk.Label(self.root, text="Developer: Amjed Dariadi", bg="#1E1E2F", fg="#888", font=("Arial", 10)).place(x=10, y=570)

        threading.Thread(target=self.listen_notifications, daemon=True).start()

    def create_buttons(self):
        tk.Button(self.root, text="👥 View Patients", command=self.view_patients, bg="#2196F3", fg="white", font=("Arial", 14), width=25, height=2).pack(pady=20)
        tk.Button(self.root, text="📸 Recognize Doctor", command=self.start_recognition, bg="#4CAF50", fg="white", font=("Arial", 14), width=25, height=2).pack(pady=20)
        tk.Button(self.root, text="📊 View Statistics", command=self.view_statistics, bg="#FF9800", fg="white", font=("Arial", 14), width=25, height=2).pack(pady=20)
        tk.Button(self.root, text="🤖 Medical Chatbot", command=self.open_chatbot, bg="#9C27B0", fg="white", font=("Arial", 14), width=25, height=2).pack(pady=20)

    def create_animation(self):
        import random
        for _ in range(15):
            x, y = random.randint(0, 900), random.randint(0, 600)
            r, speed = random.randint(10, 30), random.uniform(0.3, 1.5)
            circle = self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#00FFFF", outline="")
            self.circles.append((circle, x, y, r, speed))
        self.animate()

    def animate(self):
        for i, (c, x, y, r, s) in enumerate(self.circles):
            y += s
            if y - r > 600:
                y = -r
            self.canvas.move(c, 0, s)
            self.circles[i] = (c, x, y, r, s)
        self.root.after(50, self.animate)

    def create_notification_label(self):
        self.notification_label = tk.Label(self.root, text="", bg="#222", fg="white", font=("Arial", 12), anchor="w")
        self.notification_label.place(x=10, y=10, width=880, height=30)

    def push_notification(self, msg):
        self.notification_label.config(text=msg)
        self.root.after(5000, lambda: self.notification_label.config(text=""))

    def listen_notifications(self):
        server = socket.socket()
        try:
            server.bind(("", 12345))
            server.listen(1)
            while True:
                conn, _ = server.accept()
                msg = conn.recv(1024).decode()

             
                board.digital[buzzer_pin].write(1)
                time.sleep(0.2)
                board.digital[buzzer_pin].write(0)

                
                self.push_notification(f"📲 Tablet: {msg}")
                conn.close()
        except Exception as e:
            print("Socket error:", e)


    def view_patients(self):
        top = tk.Toplevel(self.root)
        top.title("Patients")
        top.geometry("500x400")
        frame = tk.Frame(top, bg="#1E1E2F")
        frame.pack(fill="both", expand=True)
        df = pd.read_excel(patients_file)
        for i, row in df.iterrows():
            tk.Label(frame, text=f"{row['Name']} - {row['Disease']}", bg="#2C2C3E", fg="white", font=("Arial", 12)).pack(fill="x", pady=2, padx=10)
        tk.Button(top, text="➕ Add Patient", command=lambda: self.add_patient(top), bg="#4CAF50", fg="white").pack(pady=10)

    def add_patient(self, win):
        top = tk.Toplevel(win)
        top.geometry("300x300")
        top.configure(bg="#2B2B3D")
        name, disease, img_path = tk.StringVar(), tk.StringVar(), tk.StringVar()
        tk.Entry(top, textvariable=name).pack(pady=5)
        tk.Entry(top, textvariable=disease).pack(pady=5)
        tk.Button(top, text="Choose Image", command=lambda: img_path.set(filedialog.askopenfilename())).pack()
        def save():
            df = pd.read_excel(patients_file)
            df.loc[len(df)] = [name.get(), disease.get(), img_path.get()]
            df.to_excel(patients_file, index=False)
            top.destroy()
        tk.Button(top, text="Save", command=save).pack(pady=10)

    def start_recognition(self):
        self.push_notification("🔍 Detecting doctor...")
        def recognize_and_continue():
            name = recognize_doctor()
            if name:
                speak(f"Welcome Doctor {name}")
                messagebox.showinfo("Welcome", f"Doctor {name} recognized")
                self.show_medicine_assignment(name)
            else:
                messagebox.showwarning("Failed", "Doctor not recognized")
        threading.Thread(target=recognize_and_continue).start()

    def show_medicine_assignment(self, doctor_name):
        top = tk.Toplevel(self.root)
        top.title("Assign Medicines")
        top.geometry("600x500")
        df = pd.read_excel(patients_file)
        self.assignments = []
        for i, row in df.iterrows():
            frame = tk.Frame(top)
            frame.pack(pady=5)
            tk.Label(frame, text=row["Name"]).pack(side="left")
            med = tk.StringVar()
            qty = tk.StringVar()
            ttk.Combobox(frame, textvariable=med, values=medicines, width=20).pack(side="left", padx=5)
            tk.Entry(frame, textvariable=qty, width=5).pack(side="left")
            self.assignments.append((row["Name"], med, qty))

        def confirm():
            df_log = pd.read_excel(log_file)
            for patient, med_var, qty_var in self.assignments:
                med, qty = med_var.get(), qty_var.get()
                if med and qty:
                    df_log.loc[len(df_log)] = [doctor_name, patient, med, qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            df_log.to_excel(log_file, index=False)
            messagebox.showinfo("Saved", "Medicines assigned successfully.")
            top.destroy()
            threading.Thread(target=open_door).start()
        tk.Button(top, text="✅ Confirm", command=confirm, bg="#4CAF50", fg="white").pack(pady=20)

    def view_statistics(self):
        df = pd.read_excel(patients_file)
        if df.empty:
            messagebox.showinfo("Info", "No data")
            return
        counts = df["Disease"].value_counts()
        plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%")
        plt.title("Common Diseases")
        plt.show()

    def open_chatbot(self):
        top = tk.Toplevel(self.root)
        top.title("Medical ChatBot")
        top.geometry("400x400")
        chat = tk.Text(top, state="disabled", wrap="word", bg="black", fg="lime")
        chat.pack(expand=True, fill="both")
        entry = tk.Entry(top)
        entry.pack(fill="x")

        def respond(event=None):
            msg = entry.get()
            entry.delete(0, "end")
            chat.configure(state="normal")
            chat.insert("end", f"\n👤 You: {msg}\n")
            response = "🤖 Bot: " + self.get_diagnosis(msg) + "\n"
            chat.insert("end", response)
            chat.configure(state="disabled")
        entry.bind("<Return>", respond)

    def get_diagnosis(self, msg):
        msg = msg.lower()
        if "fever" in msg:
            return "You might have flu. Take Paracetamol."
        elif "cough" in msg:
            return "You may have cold. Stay hydrated."
        elif "headache" in msg:
            return "Possibly dehydration. Rest well."
        else:
            return "Consult a real doctor."

# تشغيل
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()