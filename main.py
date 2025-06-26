import subprocess
import os
import sys
from tkinter import Tk,Button

def run_simulation(folder_name):
    folder_path = os.path.join(os.path.dirname(__file__), folder_name)
    
    # Find the .py file inside the folder (e.g., Flip_Simulation.py)
    simulation_file = next((f for f in os.listdir(folder_path) if f.endswith("_Simulation.py")), None)
    
    if simulation_file is None:
        print(f"No simulation script found in {folder_name}")
        return
    
    script_path = os.path.join(folder_path, simulation_file)
    subprocess.run([sys.executable, script_path])

def main():
    root = Tk()
    root.title("Simulation Launcher")

    base_dir = os.path.dirname(__file__)
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]

    for folder in folders:
        # Only show buttons for folders that contain *_Simulation.py
        folder_path = os.path.join(base_dir, folder)
        if any(f.endswith("_Simulation.py") for f in os.listdir(folder_path)):
            btn = Button(root, text=folder, command=lambda f=folder: run_simulation(f),
                            font=("Arial", 12), width=25)
            btn.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    main()
