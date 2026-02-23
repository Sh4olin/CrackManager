import os
import shutil
import json
import sys
import stat
import customtkinter as ctk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

if getattr(sys, 'frozen', False):
    base = os.path.dirname(sys.executable)
else:
    base = os.path.dirname(os.path.abspath(__file__))

backup = os.path.join(base, "Original Files")
log = os.path.join(base, "patch_log.json")

display_to_path = {}

def load_log():
    if os.path.exists(log):
        with open(log, 'r') as f:
            return json.load(f)
    return {}

def save_log(data):
    with open(log, 'w') as f:
        json.dump(data, f, indent=4)

def check_structure(*args):
    game = game_var.get()
    crack = crack_var.get()

    if not game or not crack:
        status_label.configure(text="Waiting for folders...", text_color="#666666")
        btn_apply_action.configure(state="disabled", fg_color="#333333")
        return

    if not os.path.isdir(game) or not os.path.isdir(crack):
        status_label.configure(text="Invalid folder path(s).", text_color="#E84A5F")
        btn_apply_action.configure(state="disabled", fg_color="#333333")
        return

    has_files = False
    for _, _, files in os.walk(crack):
        if files:
            has_files = True
            break
    
    if not has_files:
        status_label.configure(text="Crack folder is empty.", text_color="#E84A5F")
        btn_apply_action.configure(state="disabled", fg_color="#333333")
        return

    crack_items = set(os.listdir(crack))
    game_items = set(os.listdir(game))
    
    if crack_items.intersection(game_items):
        status_label.configure(text="✔ Folder structure matches!", text_color="#2FA572")
        btn_apply_action.configure(state="normal", fg_color="#2FA572")
    else:
        status_label.configure(text="✖ No common files/folders. Check selected paths.", text_color="#E84A5F")
        btn_apply_action.configure(state="disabled", fg_color="#333333")

def apply():
    game = game_var.get()
    crack = crack_var.get()

    if not game or not crack:
        messagebox.showwarning("Warning", "Fill both paths.")
        return

    data = load_log()
    name = os.path.basename(game)
    dest = os.path.join(backup, name)

    if not os.path.exists(dest):
        os.makedirs(dest)

    if game in data:
        copied = data[game].get("copied", [])
    else:
        copied = []

    copied_files = 0
    replaced_files = 0

    for root, dirs, files in os.walk(crack):
        for file_name in files:
            crack_path = os.path.join(root, file_name)
            rel = os.path.relpath(crack_path, crack)
            game_path = os.path.join(game, rel)
            backup_path = os.path.join(dest, rel)

            copied_files += 1

            if os.path.exists(game_path):
                replaced_files += 1
                backup_dir = os.path.dirname(backup_path)
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                if not os.path.exists(backup_path):
                    shutil.copy2(game_path, backup_path)

            game_dir = os.path.dirname(game_path)
            if not os.path.exists(game_dir):
                os.makedirs(game_dir)
            shutil.copy2(crack_path, game_path)
            
            if rel not in copied:
                copied.append(rel)

    data[game] = {
        "backup": dest,
        "copied": copied
    }
    
    save_log(data)
    update_list()
    messagebox.showinfo("Success", f"Crack applied successfully!\n\nFiles copied: {copied_files}\nFiles replaced: {replaced_files}")
    game_var.set("")
    crack_var.set("")

def revert():
    display_val = selected_game.get()

    if not display_val or display_val in ["No games patched", "Select..."]:
        messagebox.showwarning("Warning", "Select a valid game.")
        return

    game = display_to_path.get(display_val, display_val)
    data = load_log()

    if not game or game not in data:
        messagebox.showwarning("Error", "No log found for this game.")
        return

    try:
        game_data = data[game]
        copied = game_data.get("copied", [])
        backup_dir = game_data.get("backup", "")

        removed_files = 0
        restored_files = 0

        for rel in copied:
            game_path = os.path.join(game, rel)
            file_name = os.path.basename(rel)
            root_path = os.path.join(game, file_name)

            if os.path.exists(game_path):
                try:
                    os.chmod(game_path, stat.S_IWRITE)
                    os.remove(game_path)
                    removed_files += 1
                except Exception as e:
                    raise Exception(f"Permission denied on {rel}. Close the game and try again.")
            
            elif os.path.exists(root_path) and root_path != game_path:
                try:
                    os.chmod(root_path, stat.S_IWRITE)
                    os.remove(root_path)
                    removed_files += 1
                except Exception:
                    pass

            parent = os.path.dirname(game_path)
            while parent and parent != game:
                try:
                    if not os.listdir(parent):
                        os.rmdir(parent)
                    else:
                        break 
                    parent = os.path.dirname(parent)
                except:
                    break

        if os.path.exists(backup_dir):
            for root, dirs, files in os.walk(backup_dir):
                for file_name in files:
                    backup_path = os.path.join(root, file_name)
                    rel = os.path.relpath(backup_path, backup_dir)
                    game_path = os.path.join(game, rel)
                    
                    game_dir = os.path.dirname(game_path)
                    if not os.path.exists(game_dir):
                        os.makedirs(game_dir)
                    shutil.copy2(backup_path, game_path)
                    restored_files += 1

            shutil.rmtree(backup_dir)

        del data[game]
        save_log(data)
        update_list()
        messagebox.showinfo("Success", f"Reverted to original successfully!\n\nFiles removed: {removed_files}\nFiles restored: {restored_files}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to revert: {str(e)}\n\nMake sure the game is not running.")

def handle_drop(event, var, entry):
    path = event.data
    if path.startswith('{') and path.endswith('}'):
        path = path[1:-1]
    
    if os.path.isdir(path):
        var.set(path)
        entry.after(10, lambda: scroll_to_end(entry))
    else:
        messagebox.showwarning("Invalid Input", "Please drop a folder, not a file.")

def scroll_to_end(widget):
    try:
        if hasattr(widget, "icursor"):
            widget.icursor("end")
        elif hasattr(widget, "_entry"):
            widget._entry.icursor("end")
        widget._entry.xview_moveto(1)
    except Exception:
        pass

def find_dir(var, entry=None):
    path = filedialog.askdirectory()
    if path:
        var.set(path)
        if entry:
            entry.after(10, lambda: scroll_to_end(entry))

def update_list():
    data = load_log()
    games = list(data.keys())
    
    display_to_path.clear()
    
    if games:
        for g in games:
            display_to_path[g] = g
            
        game_dropdown.configure(values=games)
        
        if len(games) > 1:
            selected_game.set("Select...")
        else:
            selected_game.set(games[0])
            game_dropdown.after(50, lambda: scroll_to_end(game_dropdown))
    else:
        game_dropdown.configure(values=["No games patched"])
        selected_game.set("No games patched")

def show_apply():
    btn_tab_apply.configure(fg_color="#242424", hover_color="#242424")
    btn_tab_revert.configure(fg_color="#141414", hover_color="#1E1E1E")
    frame_revert.pack_forget()
    frame_apply.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    bridge.place(in_=btn_tab_apply, relx=0, rely=1.0, y=-5, relwidth=1.0)
    bridge.lift()

def show_revert():
    btn_tab_revert.configure(fg_color="#242424", hover_color="#242424")
    btn_tab_apply.configure(fg_color="#141414", hover_color="#1E1E1E")
    frame_apply.pack_forget()
    frame_revert.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    bridge.place(in_=btn_tab_revert, relx=0, rely=1.0, y=-5, relwidth=1.0)
    bridge.lift()

ctk.set_appearance_mode("dark")

class App(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)

window = App()
window.title("Crack Manager")
window.geometry("642x420")
window.configure(fg_color="#101010")

base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
icon_path = os.path.join(base_path, "icon.ico")

try:
    window.iconbitmap(icon_path)
except Exception:
    pass

main_font = ctk.CTkFont(family="Segoe UI", size=13)
title_font = ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
btn_font = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")

tab_menu = ctk.CTkFrame(window, height=45, corner_radius=0, fg_color="transparent")
tab_menu.pack(fill="x", padx=15, pady=(15, 0))

btn_tab_apply = ctk.CTkButton(tab_menu, text="Apply Crack", font=title_font, corner_radius=5, height=45, command=show_apply)
btn_tab_apply.pack(side="left", fill="x", expand=True, padx=(0, 1))

btn_tab_revert = ctk.CTkButton(tab_menu, text="Revert to original", font=title_font, corner_radius=5, height=45, command=show_revert)
btn_tab_revert.pack(side="left", fill="x", expand=True, padx=(1, 0))

frame_apply = ctk.CTkFrame(window, corner_radius=5, fg_color="#242424")
frame_revert = ctk.CTkFrame(window, corner_radius=5, fg_color="#242424")

bridge = ctk.CTkFrame(window, corner_radius=0, fg_color="#242424", height=10)

game_var = ctk.StringVar()
crack_var = ctk.StringVar()
selected_game = ctk.StringVar()

inputs_apply = ctk.CTkFrame(frame_apply, fg_color="transparent")
inputs_apply.pack(pady=(25, 0), fill="x")

g1 = ctk.CTkFrame(inputs_apply, fg_color="transparent")
g1.pack(pady=(5, 5))
ctk.CTkLabel(g1, text="Game Folder:", font=title_font).pack(anchor="w", padx=10, pady=(0, 5))
row1 = ctk.CTkFrame(g1, fg_color="transparent")
row1.pack()
entry_game = ctk.CTkEntry(row1, textvariable=game_var, width=400, font=main_font, height=35)
entry_game.pack(side="left", padx=(10, 5))

entry_game.drop_target_register(DND_FILES) # type: ignore
entry_game.dnd_bind('<<Drop>>', lambda e: handle_drop(e, game_var, entry_game)) # type: ignore

ctk.CTkButton(row1, text="Browse", width=90, height=35, font=main_font, command=lambda: find_dir(game_var, entry_game)).pack(side="left", padx=(5, 10))

g2 = ctk.CTkFrame(inputs_apply, fg_color="transparent")
g2.pack(pady=(10, 5))
ctk.CTkLabel(g2, text="Crack Folder:", font=title_font).pack(anchor="w", padx=10, pady=(0, 5))
row2 = ctk.CTkFrame(g2, fg_color="transparent")
row2.pack()
entry_crack = ctk.CTkEntry(row2, textvariable=crack_var, width=400, font=main_font, height=35)
entry_crack.pack(side="left", padx=(10, 5))

entry_crack.drop_target_register(DND_FILES) # type: ignore
entry_crack.dnd_bind('<<Drop>>', lambda e: handle_drop(e, crack_var, entry_crack)) # type: ignore

ctk.CTkButton(row2, text="Browse", width=90, height=35, font=main_font, command=lambda: find_dir(crack_var, entry_crack)).pack(side="left", padx=(5, 10))

status_label = ctk.CTkLabel(g2, text="Waiting for folders...", font=main_font, text_color="#666666")
status_label.pack(anchor="w", padx=10, pady=(5, 0))

btn_frame_apply = ctk.CTkFrame(frame_apply, fg_color="transparent")
btn_frame_apply.pack(expand=True, fill="both")
btn_apply_action = ctk.CTkButton(btn_frame_apply, text="Apply Crack", command=apply, font=btn_font, height=40, width=180, fg_color="#333333", text_color_disabled="#888888", hover_color="#106A43", state="disabled")
btn_apply_action.pack(expand=True)

game_var.trace_add("write", check_structure)
crack_var.trace_add("write", check_structure)

inputs_revert = ctk.CTkFrame(frame_revert, fg_color="transparent")
inputs_revert.pack(pady=(55, 0), fill="x")

ctk.CTkLabel(inputs_revert, text="Select Game to Revert:", font=title_font).pack(pady=(15, 10))
game_dropdown = ctk.CTkComboBox(inputs_revert, variable=selected_game, width=450, height=35, font=main_font, dropdown_font=main_font, state="readonly", command=lambda v: game_dropdown.after(10, lambda: scroll_to_end(game_dropdown)))
game_dropdown.pack(pady=5)

if hasattr(game_dropdown, "_canvas"):
    game_dropdown._canvas.configure(cursor="hand2")
    game_dropdown._canvas.bind("<Enter>", lambda e: game_dropdown._canvas.configure(cursor="hand2"), add="+")
    game_dropdown._canvas.bind("<Motion>", lambda e: game_dropdown._canvas.configure(cursor="hand2"), add="+")

if hasattr(game_dropdown, "_entry"):
    game_dropdown._entry.configure(cursor="hand2")
    game_dropdown._entry.bind("<Enter>", lambda e: game_dropdown._entry.configure(cursor="hand2"), add="+")
    game_dropdown._entry.bind("<Button-1>", lambda e: game_dropdown._clicked(), add="+")

btn_frame_revert = ctk.CTkFrame(frame_revert, fg_color="transparent")
btn_frame_revert.pack(expand=True, fill="both")
ctk.CTkButton(btn_frame_revert, text="Revert to original", command=revert, font=btn_font, height=40, width=180, fg_color="#E84A5F", hover_color="#C03546").pack(expand=True)

show_apply()
update_list()

window.mainloop()
