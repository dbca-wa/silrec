
m matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def create_plot(parent_frame, title):
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot([1, 2, 3, 4, 5], [2, 4, 1, 5, 2])
    ax.set_title(title)
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
    return canvas

def main():
    root = tk.Tk()
    root.title("Scrollable Matplotlib Charts")

    # Create a main frame to hold the canvas and scrollbar
    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Create the canvas and scrollbar
    canvas = tk.Canvas(main_frame)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Create a frame inside the canvas to hold the plots
    plot_frame = tk.Frame(canvas)
    canvas.create_window((0, 0), window=plot_frame, anchor="nw")

    # Add multiple plots
    create_plot(plot_frame, "Chart 1")
    create_plot(plot_frame, "Chart 2")
    create_plot(plot_frame, "Chart 3")
    create_plot(plot_frame, "Chart 4")
    create_plot(plot_frame, "Chart 5")

    # Update scroll region when the plot_frame size changes
    plot_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    root.mainloop()

if __name__ == "__main__":
    main()
