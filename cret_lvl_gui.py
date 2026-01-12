import json
import os
import time
import tkinter as tk
from tkinter import messagebox
from solver import NonogramSolver

class CreateLevelGUI:
    def __init__(self, root:tk.Tk):
        # Variables
        self.root = root
        
        self.name_var = tk.StringVar(value='custom-1')
        self.rows_var = tk.IntVar(value=5)
        self.cols_var = tk.IntVar(value=5)
        
        self.row_entries = []
        self.col_entries = []
        
        # Create Frame
        top = tk.Frame(root)
        top.pack(padx=8, pady=8)
        root.title('Create Custom Nonogram Level')

        tk.Label(top, text='Level name:').grid(row=0, column=0, sticky='w')
        tk.Entry(top, textvariable=self.name_var, width=10).grid(row=0, column=1, sticky='w')

        tk.Label(top, text='Rows:').grid(row=0, column=2, sticky='w')
        tk.Spinbox(top, from_=1, to=30, width=4, textvariable=self.rows_var).grid(row=0, column=3, sticky='w')
        
        tk.Label(top, text='Cols:').grid(row=0, column=4, sticky='w', padx=(8,0))
        tk.Spinbox(top, from_=1, to=30, width=4, textvariable=self.cols_var).grid(row=0, column=5, sticky='w')
        
        tk.Button(top, text='Solve Level', command=self.on_solve).grid(row=0, column=6, columnspan=2, pady=(0,5))

        # update fields automatically when row/col count changes
        try:
            # modern tkinter: trace_add
            self.rows_var.trace_add('write', lambda *a: self.generate_fields())
            self.cols_var.trace_add('write', lambda *a: self.generate_fields())
        except AttributeError:
            # older tkinter: trace
            self.rows_var.trace('w', lambda *a: self.generate_fields())
            self.cols_var.trace('w', lambda *a: self.generate_fields())


        # container for clue entries
        self.container = tk.Frame(root)
        self.container.pack(padx=8, pady=8, fill='both', expand=True)

        # area to display solution (initially empty)
        self.solution_frame = tk.Frame(root)
        self.solution_frame.pack(padx=8, pady=(0,8), fill='both', expand=False)
        self.solution_canvas = None
        self.solution_info_label = None

        # initial generation
        self.generate_fields()

    def clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def parse_clue_text(self, text:str):
        text = text.strip()
        if not text:
            return []
        parts = [p.strip() for p in text.split(',') if p.strip()]
        try:
            return [int(p) for p in parts]
        except ValueError:
            return None

    def generate_fields(self):
        self.clear_container()
        # robustly parse values from the IntVars (user may type invalid text)
        try:
            R = max(1, int(self.rows_var.get()))
        except Exception:
            R = 1
        try:
            C = max(1, int(self.cols_var.get()))
        except Exception:
            C = 1
        # top-left empty label
        # layout: row 0 = column clues (entries), column 0 = row clues (entries)
        # and the solution cells occupy rows 1..R, cols 1..C so the whole looks like one matrix
        self.col_entries = []
        self.row_entries = []
        self.solution_cells = [[None] * C for _ in range(R)]

        tk.Label(self.container, text='').grid(row=0, column=0)

        for c in range(C):
            e = tk.Entry(self.container, width=8)
            e.grid(row=0, column=c+1, padx=2, pady=2)
            e.insert(0, '')
            self.col_entries.append(e)

        for r in range(R):
            e = tk.Entry(self.container, width=20)
            e.grid(row=r+1, column=0, padx=2, pady=2, sticky='w')
            e.insert(0, '')
            self.row_entries.append(e)

        # Create solution cell widgets in the same grid so everything appears as one matrix
        CELL = 20
        for r in range(R):
            for c in range(C):
                cell = tk.Canvas(self.container, width=CELL, height=CELL, bg='white', highlightthickness=1, highlightbackground='gray')
                cell.grid(row=r+1, column=c+1, padx=0, pady=0)
                self.solution_cells[r][c] = cell

        # clear any previous solution display when fields are regenerated
        if self.solution_canvas:
            try:
                self.solution_canvas.destroy()
            except Exception:
                pass
            self.solution_canvas = None
        if self.solution_info_label:
            try:
                self.solution_info_label.destroy()
            except Exception:
                pass
            self.solution_info_label = None

    def collect_clues(self):
        rows = []
        cols = []
        # parse rows
        for e in self.row_entries:
            parsed = self.parse_clue_text(e.get())
            if parsed is None:
                return None, None, 'Invalid row clues: must be comma-separated integers'
            rows.append(parsed)
        # parse cols
        for e in self.col_entries:
            parsed = self.parse_clue_text(e.get())
            if parsed is None:
                return None, None, 'Invalid column clues: must be comma-separated integers'
            cols.append(parsed)
        return rows, cols, None

    def save_level(self):
        LEVELS_FILE = 'custom-levels.json'
        name = self.name_var.get().strip()
        if not name:
            #messagebox.showerror('Error', 'Please enter a level name')
            return
        rows, cols, err = self.collect_clues()
        if err:
            #messagebox.showerror('Error', err)
            return
        if len(rows) == 0 or len(cols) == 0:
            #messagebox.showerror('Error', 'Rows and columns must be at least 1')
            return

        # merge into JSON file
        data = {}
        if os.path.exists(LEVELS_FILE):
            try:
                with open(LEVELS_FILE, 'r') as f:
                    data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                data = {}

        data[name] = {'rows': rows, 'cols': cols}
        try:
            with open(LEVELS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as ex:
            #messagebox.showerror('Error', f'Failed to write file: {ex}')
            return

        # messagebox.showinfo('Saved', f"Level '{name}' saved to {LEVELS_FILE}")

    def on_solve(self):
        # save the Game
        self.save_level()
        
        # Collect clues from current fields
        rows, cols, err = self.collect_clues()
        if err:
            #messagebox.showerror('Error', err)
            return

        # run solver
        solver = NonogramSolver(rows, cols)
        self.root.config(cursor='watch')
        self.root.update()
        solved = solver.solve(time_limit=10, allow_partial=True, debug=False)
        self.root.config(cursor='')

        if not solved:
            messagebox.showinfo('Result', 'No solution found or timed out.')
            return

        # draw solution into the solution_cells created in the same grid
        R = len(rows)
        C = len(cols)
        for r in range(R):
            for c in range(C):
                try:
                    cell = self.solution_cells[r][c]
                    val = solver.board[r][c]
                    if val == 1:
                        cell.config(bg='black')
                    else:
                        cell.config(bg='white')
                except Exception:
                    pass

        # show info below the grid inside the solution_frame area (reuse label)
        info = f"Solved in {time.time()-solver.start_time:.2f}s, nodes={solver.nodes}"
        if self.solution_info_label:
            try:
                self.solution_info_label.config(text=info)
            except Exception:
                pass
        else:
            self.solution_info_label = tk.Label(self.solution_frame, text=info)
            self.solution_info_label.pack(pady=(0,8))

if __name__ == '__main__':
    root = tk.Tk()
    app = CreateLevelGUI(root)
    root.mainloop()
