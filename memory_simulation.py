import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGridLayout, QGroupBox, QComboBox, QLineEdit,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt

class Partition:
    def __init__(self, size, process_id=None):
        self.size = size
        self.process_id = process_id
        self.is_free = process_id is None


def first_fit(partitions, process_id, process_size):
    holes_examined = 0
    for i, part in enumerate(partitions):
        if part.is_free:
            holes_examined += 1
            if part.size >= process_size:
                if part.size > process_size:
                    remaining = part.size - process_size
                    partitions[i] = Partition(process_size, process_id)
                    partitions.insert(i + 1, Partition(remaining))
                else:
                    part.process_id = process_id
                    part.is_free = False
                return True, holes_examined
    return False, holes_examined


def best_fit(partitions, process_id, process_size):
    holes_examined = 0
    best_idx = -1
    best_size = float("inf")

    for i, part in enumerate(partitions):
        if part.is_free:
            holes_examined += 1
            if part.size >= process_size and part.size < best_size:
                best_size = part.size
                best_idx = i

    if best_idx >= 0:
        part = partitions[best_idx]
        if part.size > process_size:
            remaining = part.size - process_size
            partitions[best_idx] = Partition(process_size, process_id)
            partitions.insert(best_idx + 1, Partition(remaining))
        else:
            part.process_id = process_id
            part.is_free = False
        return True, holes_examined

    return False, holes_examined


def worst_fit(partitions, process_id, process_size):
    holes_examined = 0
    worst_idx = -1
    worst_size = -1

    for i, part in enumerate(partitions):
        if part.is_free:
            holes_examined += 1
            if part.size >= process_size and part.size > worst_size:
                worst_size = part.size
                worst_idx = i

    if worst_idx >= 0:
        part = partitions[worst_idx]
        if part.size > process_size:
            remaining = part.size - process_size
            partitions[worst_idx] = Partition(process_size, process_id)
            partitions.insert(worst_idx + 1, Partition(remaining))
        else:
            part.process_id = process_id
            part.is_free = False
        return True, holes_examined

    return False, holes_examined


def calculate_metrics(partitions, total_memory):
    allocated = sum(p.size for p in partitions if not p.is_free)
    free_holes = [p.size for p in partitions if p.is_free]

    return {
        "utilization": (allocated / total_memory) * 100 if total_memory else 0,
        "free": sum(free_holes),
        "num_holes": len(free_holes),
        "largest_hole": max(free_holes) if free_holes else 0
    }



class MemoryTable(QWidget):
    def __init__(self, title):
        super().__init__()
        layout = QVBoxLayout(self)

        title_label = QLabel(f"<b>{title}</b>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Partition", "Size", "Process"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #CCCCCC; }
            QHeaderView::section { background-color: #F5F5F5; padding: 4px; }
        """)
        layout.addWidget(self.table)

        self.waiting = QLabel("Waiting: -")
        layout.addWidget(self.waiting)

    def update_table(self, partitions, waiting):
        self.table.setRowCount(len(partitions))
        for i, part in enumerate(partitions):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))

            size_item = QTableWidgetItem(str(part.size))
            size_item.setBackground(QColor(255, 200, 200) if part.is_free else QColor(200, 255, 200))
            self.table.setItem(i, 1, size_item)

            process_item = QTableWidgetItem("" if part.is_free else part.process_id)
            self.table.setItem(i, 2, process_item)

        self.waiting.setText("Waiting: " + (", ".join(waiting) if waiting else "-"))


class MemorySimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Memory Allocation Simulator (Clean UI)")
        self.setMinimumSize(1200, 820)
        self.build_ui()

    def build_ui(self):
        main = QWidget()
        root = QVBoxLayout(main)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        box = QGroupBox("Input Configuration")
        box.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 1px solid #CCCCCC; 
                border-radius: 6px; 
                padding: 10px; 
            }
        """)
        grid = QGridLayout()
        grid.setHorizontalSpacing(25)
        grid.setVerticalSpacing(15)

        # Partition Input
        left = QVBoxLayout()
        left.addWidget(QLabel("<b>Partitions (sizes, comma-separated):</b>"))
        small = QLabel("Example: 100,500,200,300,600,400")
        small.setStyleSheet("color: gray; font-size: 11px;")
        left.addWidget(small)

        self.part_field = QLineEdit()
        self.part_field.setPlaceholderText("100,500,200,300,600,400")
        self.part_field.setMinimumHeight(28)
        left.addWidget(self.part_field)

        grid.addLayout(left, 0, 0)

        # Process Table
        right = QVBoxLayout()
        right.addWidget(QLabel("<b>Processes:</b>"))
        right.addWidget(QLabel("Enter process name and size"))

        self.proc_table = QTableWidget()
        self.proc_table.setColumnCount(2)
        self.proc_table.setHorizontalHeaderLabels(["Name", "Size"])
        self.proc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.proc_table.setRowCount(4)
        self.proc_table.setMinimumHeight(160)

        defaults = [("p1", "312"), ("p2", "196"), ("p3", "80"), ("p4", "486")]
        for i, (n, s) in enumerate(defaults):
            self.proc_table.setItem(i, 0, QTableWidgetItem(n))
            self.proc_table.setItem(i, 1, QTableWidgetItem(s))

        right.addWidget(self.proc_table)

        # Add/Remove Row Buttons
        rowBtns = QHBoxLayout()
        addBtn = QPushButton("Add Row")
        remBtn = QPushButton("Remove Row")
        addBtn.clicked.connect(self.add_row)
        remBtn.clicked.connect(self.remove_row)
        rowBtns.addWidget(addBtn)
        rowBtns.addWidget(remBtn)
        right.addLayout(rowBtns)

        grid.addLayout(right, 0, 1)

        # Algorithm Option
        grid.addWidget(QLabel("<b>Algorithm:</b>"), 1, 0)
        self.algo = QComboBox()
        self.algo.addItems(["First-Fit", "Best-Fit", "Worst-Fit", "Compare All"])
        grid.addWidget(self.algo, 1, 1)

        # Run / Reset Buttons
        buttons = QHBoxLayout()
        buttons.setSpacing(25)

        run = QPushButton("Run Allocation")
        run.setStyleSheet("""
                          QPushButton {
                              background: #4CFA50;
                              color: white;
                              padding: 8px;
                              font-weight: bold;
                              border-radius: 4px;
                          }
                          QPushButton:hover { 
                              background: #45A049; 
                          }
                          """)
        run.setMinimumWidth(150)
        run.clicked.connect(self.run_simulation)

        reset = QPushButton("Reset")
        reset.setStyleSheet("""
            QPushButton {
                background: #E0E0E0;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: #CCCCCC;
            }
        """)

        reset.setMinimumWidth(150)
        reset.clicked.connect(self.reset_ui)

        buttons.addStretch()
        buttons.addWidget(run)
        buttons.addWidget(reset)
        buttons.addStretch()

        grid.addLayout(buttons, 2, 0, 1, 2)
        box.setLayout(grid)
        root.addWidget(box)

        row = QHBoxLayout()
        self.first = MemoryTable("First-Fit")
        self.best = MemoryTable("Best-Fit")
        self.worst = MemoryTable("Worst-Fit")

        row.addWidget(self.first)
        row.addWidget(self.best)
        row.addWidget(self.worst)

        root.addLayout(row)

        self.setCentralWidget(main)
    def add_row(self):
        self.proc_table.insertRow(self.proc_table.rowCount())

    def remove_row(self):
        if self.proc_table.rowCount() > 1:
            self.proc_table.removeRow(self.proc_table.rowCount() - 1)

    def parse_processes(self):
        processes = []
        for r in range(self.proc_table.rowCount()):
            name = self.proc_table.item(r, 0)
            size = self.proc_table.item(r, 1)
            if name and size and name.text().strip() and size.text().strip().isdigit():
                processes.append((name.text(), int(size.text())))
        return processes

    def run_simulation(self):
        try:
            parts = [int(x.strip()) for x in self.part_field.text().split(",") if x.strip()]
        except:
            QMessageBox.warning(self, "Error", "Invalid partition input!")
            return

        processes = self.parse_processes()
        if not processes:
            QMessageBox.warning(self, "Error", "No valid processes!")
            return

        algo = self.algo.currentText()

        # Run each algorithm as requested
        if algo == "First-Fit" or algo == "Compare All":
            self.run_algo(parts, processes, "ff")

        if algo == "Best-Fit" or algo == "Compare All":
            self.run_algo(parts, processes, "bf")

        if algo == "Worst-Fit" or algo == "Compare All":
            self.run_algo(parts, processes, "wf")

    def run_algo(self, partition_sizes, processes, mode):
        # Copy partitions
        parts = [Partition(p) for p in partition_sizes]
        waiting = []

        for name, size in processes:
            if mode == "ff":
                ok, _ = first_fit(parts, name, size)
            elif mode == "bf":
                ok, _ = best_fit(parts, name, size)
            else:
                ok, _ = worst_fit(parts, name, size)

            if not ok:
                waiting.append(name)

        if mode == "ff":
            self.first.update_table(parts, waiting)
        elif mode == "bf":
            self.best.update_table(parts, waiting)
        else:
            self.worst.update_table(parts, waiting)

    def reset_ui(self):
        self.part_field.clear()
        self.proc_table.setRowCount(4)
        defaults = [("p1", "312"), ("p2", "196"), ("p3", "80"), ("p4", "486")]
        for i, (n, s) in enumerate(defaults):
            self.proc_table.setItem(i, 0, QTableWidgetItem(n))
            self.proc_table.setItem(i, 1, QTableWidgetItem(s))

        self.first.update_table([], [])
        self.best.update_table([], [])
        self.worst.update_table([], [])

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MemorySimulator()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
