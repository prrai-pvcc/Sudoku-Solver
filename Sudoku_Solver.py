import tkinter as tk
from tkinter import messagebox

class SudokuCell(tk.Frame):
    def __init__(self, parent, parent_board, row, col, size=60):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.parent_board = parent_board
        self.row = row
        self.col = col
        self.size = size
        self.grid_propagate(False)
        self.value = 0
        self.is_valid = True

        self.value_label = tk.Label(
            self,
            text="",
            font=("Arial", 20, "bold"),
            bg="white"
        )
        self.value_label.place(relx=0.5, rely=0.5, anchor="center")

        self.bind("<Button-1>", self.on_click)
        self.value_label.bind("<Button-1>", self.on_click)

    def on_click(self, _event=None):
        self.parent_board.on_cell_click(self)

    def set_value(self, value):
        self.value = value
        if value == 0:
            self.value_label.config(text="")
        else:
            self.value_label.config(text=str(value))
        self.parent_board.validate_board()

    def highlight(self, color="white"):
        self.configure(bg=color)
        self.value_label.configure(bg=color)

    def mark_invalid(self):
        self.is_valid = False
        self.highlight("lightcoral")

    def mark_valid(self):
        self.is_valid = True
        self.highlight("white")


class SudokuBoard:
    def __init__(self, master):
        self.master = master
        self.master.title("Sudoku Solver")

        main_frame = tk.Frame(master, padx=10, pady=10)
        main_frame.pack(expand=True)

        cell_size = 60

        self.board_frame = tk.Frame(main_frame)
        self.board_frame.pack()

        self.cells = {}
        for block_row in range(3):
            for block_col in range(3):
                block_frame = tk.Frame(
                    self.board_frame,
                    highlightbackground="black",
                    highlightcolor="black",
                    highlightthickness=2
                )
                block_frame.grid(row=block_row, column=block_col, padx=1, pady=1)
                for i in range(3):
                    for j in range(3):
                        row = block_row * 3 + i
                        col = block_col * 3 + j
                        cell = SudokuCell(block_frame, self, row, col, size=cell_size)
                        self.cells[(row, col)] = cell
                        cell.grid(row=i, column=j)

        button_frame = tk.Frame(main_frame, pady=10)
        button_frame.pack()

        buttons = [
            ("Solve", self.solve_puzzle),
            ("Clear", self.clear_board)
        ]

        for text, command in buttons:
            tk.Button(
                button_frame,
                text=text,
                command=command,
                width=15,
                height=2
            ).pack(side=tk.LEFT, padx=5)

        self.selected_cell = None

        self.master.bind("<Key>", self.handle_key)

    def on_cell_click(self, cell):
        if self.selected_cell and self.selected_cell != cell:
            if self.selected_cell.is_valid:
                self.selected_cell.highlight("white")
            else:
                self.selected_cell.highlight("lightcoral")
        self.selected_cell = cell
        cell.highlight("lightblue")
        self.master.focus_set()

    def handle_key(self, event):
        if not self.selected_cell:
            return
        if event.char.isdigit():
            num = int(event.char)
            if 0 <= num <= 9:
                cell = self.selected_cell
                cell.set_value(num)
        self.validate_board()

    def get_board(self):
        board = [[0]*9 for _ in range(9)]
        for (row, col), cell in self.cells.items():
            board[row][col] = cell.value
        return board

    def set_board(self, board):
        for i in range(9):
            for j in range(9):
                self.cells[(i, j)].set_value(board[i][j])
        self.validate_board()

    def validate_board(self):
        for cell in self.cells.values():
            cell.mark_valid()

        board = self.get_board()
        valid = True

        # Check rows
        for i in range(9):
            nums = {}
            for j in range(9):
                val = board[i][j]
                if val != 0:
                    if val in nums:
                        valid = False
                        self.cells[(i, j)].mark_invalid()
                        self.cells[(i, nums[val])].mark_invalid()
                    else:
                        nums[val] = j

        # Check columns
        for j in range(9):
            nums = {}
            for i in range(9):
                val = board[i][j]
                if val != 0:
                    if val in nums:
                        valid = False
                        self.cells[(i, j)].mark_invalid()
                        self.cells[(nums[val], j)].mark_invalid()
                    else:
                        nums[val] = i

        # Check boxes
        for box_row in range(3):
            for box_col in range(3):
                nums = {}
                for i in range(3):
                    for j in range(3):
                        row = box_row * 3 + i
                        col = box_col * 3 + j
                        val = board[row][col]
                        if val != 0:
                            if val in nums:
                                valid = False
                                self.cells[(row, col)].mark_invalid()
                                prev_row, prev_col = nums[val]
                                self.cells[(prev_row, prev_col)].mark_invalid()
                            else:
                                nums[val] = (row, col)

        return valid

    def solve_puzzle(self):
        board = self.get_board()
        solver = DLXSolver(board)
        solution_count = solver.solve(limit=2)

        if solution_count == 0:
            messagebox.showinfo("No Solution", "This puzzle has no valid solution.")
        elif solution_count == 1:
            self.set_board(solver.solutions[0])
            self.validate_board()
        else:
            response = messagebox.askyesno(
                "Multiple Solutions",
                f"This puzzle has multiple solutions ({solution_count}).\nDo you want to see one of them?"
            )
            if response:
                self.set_board(solver.solutions[0])
                self.validate_board()

    def clear_board(self):
        for cell in self.cells.values():
            cell.set_value(0)
            cell.mark_valid()
        self.selected_cell = None


def get_constraints(row, col, digit):
    cell_constraint = 9 * row + col
    row_constraint = 81 + 9 * row + (digit - 1)
    col_constraint = 162 + 9 * col + (digit - 1)
    box_constraint = 243 + 9 * (3 * (row // 3) + (col // 3)) + (digit - 1)
    return [cell_constraint, row_constraint, col_constraint, box_constraint]


class DLXSolver:
    def __init__(self, board):
        self.board = board
        self.solutions = []
        self.solution_nodes = []
        self.solution_count = 0
        self.header = None

    def solve(self, limit=2):
        self.build_exact_cover_matrix()
        self.algorithm_x(0, limit)
        return self.solution_count

    def build_exact_cover_matrix(self):
        self.header = ColumnNode("header")
        columns = []

        for i in range(324):
            column = ColumnNode(str(i))
            columns.append(column)
            self.header = self.header.link_right(column)

        for row in range(9):
            for col in range(9):
                if self.board[row][col] == 0:
                    digits = range(1, 10)
                else:
                    digits = [self.board[row][col]]
                for digit in digits:
                    row_nodes = []
                    constraints = get_constraints(row, col, digit)
                    for constraint in constraints:
                        column = columns[constraint]
                        node = DataNode(column)
                        row_nodes.append(node)
                    if row_nodes:
                        first_node = row_nodes[0]
                        for node in row_nodes[1:]:
                            first_node.link_right(node)
                    for node in row_nodes:
                        node.column.link_down(node)

    def algorithm_x(self, k, limit):
        if self.header.right == self.header:
            self.solution_count += 1
            solution = self.convert_to_board()
            self.solutions.append(solution)
            return self.solution_count >= limit

        column = self.select_column()
        column.cover()
        row_node = column.down
        while row_node != column:
            self.solution_nodes.append(row_node)
            j = row_node.right
            while j != row_node:
                j.column.cover()
                j = j.right
            if self.algorithm_x(k + 1, limit):
                return True
            self.solution_nodes.pop()
            j = row_node.left
            while j != row_node:
                j.column.uncover()
                j = j.left
            row_node = row_node.down
        column.uncover()
        return False

    def select_column(self):
        min_size = float('inf')
        min_column = None
        c = self.header.right
        while c != self.header:
            if c.size < min_size:
                min_size = c.size
                min_column = c
            c = c.right
        return min_column

    def convert_to_board(self):
        result = [[0 for _ in range(9)] for _ in range(9)]
        for node in self.solution_nodes:
            row = col = digit = None
            n = node
            while True:
                constraint_index = int(n.column.name)
                if constraint_index < 81:
                    row = constraint_index // 9
                    col = constraint_index % 9
                elif 81 <= constraint_index < 162:
                    digit = (constraint_index - 81) % 9 + 1
                n = n.right
                if n == node:
                    break
            if row is not None and col is not None and digit is not None:
                result[row][col] = digit
        return result
class ColumnNode:
    def __init__(self, name):
        self.name = name
        self.size = 0
        self.up = self.down = self
        self.left = self.right = self
        self.column = self

    def link_down(self, node):
        node.down = self
        node.up = self.up
        self.up.down = node
        self.up = node
        node.column = self
        self.size += 1

    def link_right(self, node):
        node.right = self.right
        node.left = self
        self.right.left = node
        self.right = node
        return self

    def cover(self):
        self.right.left = self.left
        self.left.right = self.right
        i = self.down
        while i != self:
            j = i.right
            while j != i:
                j.down.up = j.up
                j.up.down = j.down
                j.column.size -= 1
                j = j.right
            i = i.down

    def uncover(self):
        i = self.up
        while i != self:
            j = i.left
            while j != i:
                j.column.size += 1
                j.down.up = j
                j.up.down = j
                j = j.left
            i = i.up
        self.right.left = self
        self.left.right = self


class DataNode:
    def __init__(self, column):
        self.column = column
        self.up = self.down = self
        self.left = self.right = self

    def link_right(self, node):
        node.right = self.right
        node.right.left = node
        node.left = self
        self.right = node

    def link_down(self, node):
        node.down = self.down
        node.down.up = node
        node.up = self
        self.down = node
        node.column = self.column


def main():
    root = tk.Tk()
    root.configure(bg='white')
    SudokuBoard(root)
    root.mainloop()


if __name__ == "__main__":
    main()