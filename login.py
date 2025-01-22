import tkinter as tk
import sqlite3

conn = sqlite3.connect("test.db")

cursor = conn.cursor()

add_user_query = """CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT NOT NULL,
                    age INTEGER,
                    gender TEXT,
                    address TEXT
                );"""
cursor.execute(add_user_query)
conn.commit()
conn.close()


def center_window(width, height):
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

class Welcomewindow(tk.Frame):
    pass

class LoginWindow(tk.Frame):
    pass

class RegisterWindow(tk.Frame):
    def __init__(self, master):
        super().__init__()
        self.master = master
        self.master.title("Register")
        self.master.resizale(False, False)
        center_window(320, 350)

        tk.Label(self, text="Name").grid(row=0, column=0, sticky="w")
        self.first_name_entry = tk.Entry(self, width=26)
        self.first_name_entry.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        tk.Label(self, text="Password").grid(row=2, column=0, sticky="w")
        self.password_entry = tk.Entry(self, show="*", width=26)
        self.password_entry.grid(row=2, column=1, padx=10, pady=10, sticky="e")

        tk.Label(self, text="Email").grid(row=3, column=0, sticky="w")
        self.email_entry = tk.Entry(self, width=26)
        self.email_entry.grid(row=3, column=1, padx=10, pady=10, sticky="e")

        tk.Label(self, text="Gender").grid(row=4, column=0, sticky="w")
        self.gender_entry = tk.Entry(self, width=26)
        self.gender_entry.grid(row=4, column=1, padx=10, pady=10, sticky="e")

        tk.Label(self, text="Age").grid(row=5, column=0, sticky="w")
        self.age_entry = tk.Entry(self, width=26)
        self.age_entry.grid(row=5, column=1, padx=10, pady=10, sticky="e")

        tk.Label(self, text="Address").grid(row=6, column=0, sticky="w")
        self.address_entry = tk.Text(self, width=20, height=3)
        self.address_entry.grid(row=6, column=1, padx=10, pady=10, sticky="e")

        submit_button = tk.Button(self, text="Submit", width=8, command=self.submit)
        submit_button.grid(row=7, column=1, padx=10, pady=10, sticky="e")

        submit_button = tk.Button(self, text="Back", width=8, command=self.back)
        submit_button.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        self.pack()

    def submit(self):
        inser_user_data = """INSTER INTO users(name, password, email, age, gender, address)
                            VALUES (?, ?, ?, ?, ?, ?)"""
        
        user_data = (self.first_name_entry.get(),
                    self.password_entry.get(),
                    self.email_entry.get(),
                    self.age_entry.get(),
                    self.gender_entry.get(),
                    self.address_entry.get(1.0, tk.END))
        
        cursor.execute(inser_user_data, user_data)
        conn.commit()

        self.destroy()
        MainWindow(self.master)
        

    def back(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.destroy()
        Welcomewindow(self.master)

class MainWindow(tk.Frame):
    pass

root = tk.Tk()
root.eval('tk::PlaceWindow . center')
Welcomewindow(root)
root.mainloop()