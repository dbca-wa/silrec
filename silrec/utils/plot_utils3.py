import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, Scrollbar

def create_scrollable_charts():
    ''' create_scrollable_charts()
    '''
    # Create main window
    root = tk.Tk()
    root.title("Scrollable Multi-Chart Canvas")
    root.geometry("800x600")

    # Create a frame with scrollbar
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=1)

    # Create canvas and scrollbar
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # Create multiple charts
    num_charts = 8
    charts_data = []

    for i in range(num_charts):
        # Create figure for each chart
        fig, ax = plt.subplots(figsize=(10, 4))

        # Generate sample data
        x = np.linspace(0, 10, 100)
        y = np.sin(x + i * 0.5) + np.random.normal(0, 0.1, 100)

        # Plot data
        ax.plot(x, y, label=f'Dataset {i+1}')
        ax.set_title(f'Chart {i+1}')
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.legend()
        ax.grid(True)

        # Embed in tkinter
        chart_canvas = FigureCanvasTkAgg(fig, scrollable_frame)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        charts_data.append((fig, chart_canvas))

    # Pack canvas and scrollbar
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    root.mainloop()


if __name__ == "__main__":
    create_scrollable_charts()
