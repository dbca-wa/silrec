import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

def create_scrollable_charts_3_per_row():
    # Create main window
    root = tk.Tk()
    root.title("Scrollable Multi-Chart Canvas - 3 per Row")
    root.geometry("1200x700")

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

    # Create multiple charts - 3 per row
    num_charts = 12  # You can change this number
    charts_per_row = 3
    current_row = 0
    current_col = 0

    # Create a grid system within the scrollable frame
    for i in range(num_charts):
        # Calculate row and column position
        current_row = i // charts_per_row
        current_col = i % charts_per_row

        # Create frame for each chart
        chart_frame = tk.Frame(scrollable_frame, relief=tk.RAISED, bd=1)
        chart_frame.grid(row=current_row, column=current_col, padx=10, pady=10, sticky="nsew")

        # Configure grid weights for responsive layout
        scrollable_frame.grid_rowconfigure(current_row, weight=1)
        scrollable_frame.grid_columnconfigure(current_col, weight=1)

        # Create figure for each chart
        fig, ax = plt.subplots(figsize=(6, 4))

        # Generate sample data
        x = np.linspace(0, 10, 100)
        y = np.sin(x + i * 0.5) + np.random.normal(0, 0.1, 100)

        # Plot data with different styles
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
        color = colors[i % len(colors)]

        ax.plot(x, y, label=f'Dataset {i+1}', color=color, linewidth=2)
        ax.set_title(f'Chart {i+1}\n(Sin Wave + Noise)', fontsize=12, fontweight='bold')
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Embed in tkinter
        chart_canvas = FigureCanvasTkAgg(fig, chart_frame)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

    # Pack canvas and scrollbar
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Add some information label
    info_label = tk.Label(root, text=f"Displaying {num_charts} charts in {current_row + 1} rows (3 charts per row)",
                         relief=tk.SUNKEN, bd=1)
    info_label.pack(side=tk.BOTTOM, fill=tk.X)

    root.mainloop()

# Alternative version with more sophisticated layout and different chart types
def create_scrollable_charts_varied():
    # Create main window
    root = tk.Tk()
    root.title("Scrollable Multi-Chart Canvas - Varied Charts")
    root.geometry("1400x800")

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

    # Create multiple charts with different types
    num_charts = 15
    charts_per_row = 3

    for i in range(num_charts):
        # Calculate row and column position
        current_row = i // charts_per_row
        current_col = i % charts_per_row

        # Create frame for each chart
        chart_frame = tk.Frame(scrollable_frame, relief=tk.RAISED, bd=2, bg='white')
        chart_frame.grid(row=current_row, column=current_col, padx=15, pady=15, sticky="nsew")

        # Configure grid weights for responsive layout
        scrollable_frame.grid_rowconfigure(current_row, weight=1)
        scrollable_frame.grid_columnconfigure(current_col, weight=1)

        # Create figure for each chart
        fig, ax = plt.subplots(figsize=(5, 3.5))

        # Generate different types of charts based on index
        x = np.linspace(0, 10, 100)

        if i % 3 == 0:
            # Line plot
            y1 = np.sin(x + i * 0.5)
            y2 = np.cos(x + i * 0.3)
            ax.plot(x, y1, label='Sine', linewidth=2)
            ax.plot(x, y2, label='Cosine', linewidth=2)
            chart_type = "Line Plot"

        elif i % 3 == 1:
            # Scatter plot
            x_scatter = np.random.normal(5, 1.5, 50)
            y_scatter = np.random.normal(5, 1.5, 50)
            sizes = np.random.uniform(20, 100, 50)
            colors = np.random.rand(50)
            scatter = ax.scatter(x_scatter, y_scatter, c=colors, s=sizes, alpha=0.7, cmap='viridis')
            plt.colorbar(scatter, ax=ax)
            chart_type = "Scatter Plot"

        else:
            # Bar chart
            categories = ['A', 'B', 'C', 'D', 'E']
            values = np.random.randint(1, 20, len(categories))
            bars = ax.bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
            # Add value labels on bars
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                       f'{value}', ha='center', va='bottom')
            chart_type = "Bar Chart"

        ax.set_title(f'Chart {i+1}\n{chart_type}', fontsize=11, fontweight='bold', pad=10)
        ax.set_xlabel('X axis' if i % 3 != 2 else 'Categories')
        ax.set_ylabel('Y axis' if i % 3 != 2 else 'Values')
        ax.legend() if i % 3 != 2 else None
        ax.grid(True, alpha=0.3)

        # Embed in tkinter
        chart_canvas = FigureCanvasTkAgg(fig, chart_frame)
        chart_canvas.draw()
        chart_canvas.get_tk_widget().pack(padx=8, pady=8, fill=tk.BOTH, expand=True)

    # Pack canvas and scrollbar
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Mouse wheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Add resize handling for better responsiveness
    def on_resize(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    scrollable_frame.bind("<Configure>", on_resize)

    # Information panel
    info_text = f"Displaying {num_charts} charts in {(num_charts + charts_per_row - 1) // charts_per_row} rows"
    info_label = tk.Label(root, text=info_text, relief=tk.SUNKEN, bd=1,
                         font=('Arial', 10), bg='lightgray')
    info_label.pack(side=tk.BOTTOM, fill=tk.X)

    root.mainloop()

# Run the simple version

if __name__ == "__main__":
    #create_scrollable_charts_3_per_row()
    create_scrollable_charts_varied()
# Uncomment below to run the varied charts version
# create_scrollable_charts_varied()
