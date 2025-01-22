import tkinter as tk
from tkinter import ttk

root = tk.Tk()
root.title('Konstrukční zakázky')
root.state("zoomed")
root.resizable(False, False)
root.iconbitmap("logo.ico")
root.configure(background="#AEAEAE")

# Configure the grid to take the full width with specific column proportions
root.grid_columnconfigure(0, weight=1, minsize=60)  # 10% of the width
root.grid_columnconfigure(1, weight=7, minsize=420)  # 70% of the width
root.grid_columnconfigure(2, weight=2, minsize=120)  # 20% of the width

# Configure the grid to take the full height
root.grid_rowconfigure(0, weight=1, minsize=400)  # 100% of the height (set a minimum height)


# Create widgets to fill each column
label1 = tk.Label(root, text="Column 1 (10%)", bg="lightblue", width=20, height=4)
label1.grid(row=0, column=0, sticky="nsew")  # sticky to fill cell

separator1 = tk.Frame(root, bg="#FEFEFE", width=2, height=4)
separator1.grid(row=0, column=0, sticky="nse")

# Label for column 2 with thick black borders on left and right
label2 = tk.Label(root, text="Column 2 (70%)", bg="lightgreen", width=20, height=4)
label2.grid(row=0, column=1, sticky="nsew")  # sticky to fill cell

separator1 = tk.Frame(root, bg="#FEFEFE", width=2, height=4)
separator1.grid(row=0, column=1, sticky="nse")

label3 = tk.Label(root, text="Column 3 (20%)", bg="lightcoral", width=20, height=4)
label3.grid(row=0, column=2, sticky="nsew")  # sticky to fill cell


root.mainloop()