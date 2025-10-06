import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk

class ZoomableChart:
    def __init__(self, fig, canvas, chart_frame):
        self.fig = fig
        self.canvas = canvas
        self.chart_frame = chart_frame
        self.zoom_level = 1.0
        self.original_figsize = fig.get_size_inches()
        self.setup_zoom_handlers()

    def setup_zoom_handlers(self):
        # Bind mouse events for zooming
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.canvas.mpl_connect('button_release_event', self.on_button_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.dragging = False
        self.start_x = 0
        self.start_y = 0

    def on_scroll(self, event):
        if event.inaxes:
            # Zoom factor
            zoom_factor = 1.1 if event.button == 'up' else 0.9

            # Get current limits
            xlim = event.inaxes.get_xlim()
            ylim = event.inaxes.get_ylim()

            # Calculate new limits
            xdata = event.xdata
            ydata = event.ydata

            new_xlim = [
                xdata - (xdata - xlim[0]) * zoom_factor,
                xdata + (xlim[1] - xdata) * zoom_factor
            ]
            new_ylim = [
                ydata - (ydata - ylim[0]) * zoom_factor,
                ydata + (ylim[1] - ydata) * zoom_factor
            ]

            # Apply new limits
            event.inaxes.set_xlim(new_xlim)
            event.inaxes.set_ylim(new_ylim)
            self.canvas.draw_idle()

    def on_button_press(self, event):
        if event.button == 2:  # Middle mouse button for panning
            self.dragging = True
            self.start_x = event.x
            self.start_y = event.y
            self.canvas.widgetlock(self)

    def on_button_release(self, event):
        if event.button == 2:
            self.dragging = False
            self.canvas.widgetlock.release(self)

    def on_motion(self, event):
        if self.dragging and event.inaxes:
            dx = event.x - self.start_x
            dy = event.y - self.start_y

            # Convert pixel distance to data distance
            xlim = event.inaxes.get_xlim()
            ylim = event.inaxes.get_ylim()

            xrange = xlim[1] - xlim[0]
            yrange = ylim[1] - ylim[0]

            # Adjust limits based on drag
            scale_x = xrange / self.fig.bbox.width
            scale_y = yrange / self.fig.bbox.height

            new_xlim = [xlim[0] - dx * scale_x, xlim[1] - dx * scale_x]
            new_ylim = [ylim[0] + dy * scale_y, ylim[1] + dy * scale_y]

            event.inaxes.set_xlim(new_xlim)
            event.inaxes.set_ylim(new_ylim)

            self.start_x = event.x
            self.start_y = event.y
            self.canvas.draw_idle()

def create_scrollable_charts_3_per_row():
    # Create main window
    root = tk.Tk()
    root.title("Scrollable Multi-Chart Canvas - 3 per Row with Zoom")
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

    # Create multiple charts - 3 per row
    num_charts = 12
    charts_per_row = 3
    zoomable_charts = []  # Store zoomable chart objects

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
        x = np.linspace(0, 10, 200)
        y = np.sin(x + i * 0.5) + 0.3 * np.cos(x * 2 + i) + np.random.normal(0, 0.1, 200)

        # Plot data with different styles
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta', 'yellow']
        color = colors[i % len(colors)]

        ax.plot(x, y, label=f'Dataset {i+1}', color=color, linewidth=1.5, alpha=0.8)
        ax.set_title(f'Chart {i+1}\n(Zoomable - Scroll wheel to zoom, Middle drag to pan)',
                    fontsize=10, fontweight='bold', pad=10)
        ax.set_xlabel('X axis')
        ax.set_ylabel('Y axis')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Embed in tkinter
        chart_canvas = FigureCanvasTkAgg(fig, chart_frame)
        chart_canvas.draw()

        # Create zoomable chart instance
        zoom_chart = ZoomableChart(fig, chart_canvas, chart_frame)
        zoomable_charts.append(zoom_chart)

        # Add matplotlib navigation toolbar for each chart
        toolbar_frame = tk.Frame(chart_frame)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)

        toolbar = NavigationToolbar2Tk(chart_canvas, toolbar_frame)
        toolbar.update()

        # Pack the chart canvas
        chart_canvas.get_tk_widget().pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

    # Pack canvas and scrollbar
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Mouse wheel scrolling for the main window
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Add global zoom controls
    control_frame = tk.Frame(root)
    control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

    tk.Label(control_frame, text="Global Controls:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)

    def reset_all_zooms():
        for zoom_chart in zoomable_charts:
            zoom_chart.fig.tight_layout()
            zoom_chart.canvas.draw_idle()

    def zoom_all_in():
        for zoom_chart in zoomable_charts:
            for ax in zoom_chart.fig.get_axes():
                xlim = ax.get_xlim()
                ylim = ax.get_ylim()
                x_center = np.mean(xlim)
                y_center = np.mean(ylim)
                x_range = xlim[1] - xlim[0]
                y_range = ylim[1] - ylim[0]

                ax.set_xlim([x_center - x_range * 0.5, x_center + x_range * 0.5])
                ax.set_ylim([y_center - y_range * 0.5, y_center + y_range * 0.5])
            zoom_chart.canvas.draw_idle()

    def zoom_all_out():
        for zoom_chart in zoomable_charts:
            for ax in zoom_chart.fig.get_axes():
                ax.relim()
                ax.autoscale_view()
            zoom_chart.canvas.draw_idle()

    # Add control buttons
    tk.Button(control_frame, text="Reset All Zooms", command=reset_all_zooms).pack(side=tk.LEFT, padx=5)
    tk.Button(control_frame, text="Zoom All In", command=zoom_all_in).pack(side=tk.LEFT, padx=5)
    tk.Button(control_frame, text="Zoom All Out", command=zoom_all_out).pack(side=tk.LEFT, padx=5)

    # Add instructions
    instructions = """
    Chart Controls:
    • Mouse Wheel: Zoom in/out on individual charts
    • Middle Mouse Button + Drag: Pan around charts
    • Toolbar: Use matplotlib navigation tools below each chart
    • Global Buttons: Apply zoom to all charts simultaneously
    """

    instruction_label = tk.Label(root, text=instructions, justify=tk.LEFT,
                                font=('Arial', 9), bg='lightyellow', relief=tk.SUNKEN)
    instruction_label.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)

    # Add some information label
    info_label = tk.Label(root,
                         text=f"Displaying {num_charts} charts in {current_row + 1} rows (3 charts per row) with zoom functionality",
                         relief=tk.SUNKEN, bd=1, font=('Arial', 10))
    info_label.pack(side=tk.BOTTOM, fill=tk.X)

    # Add keyboard shortcuts
    def on_key_press(event):
        if event.keysym == 'r':  # Reset zoom on 'r' key
            reset_all_zooms()
        elif event.keysym == 'equal':  # Zoom in on '=' key
            zoom_all_in()
        elif event.keysym == 'minus':  # Zoom out on '-' key
            zoom_all_out()

    root.bind('<KeyPress>', on_key_press)

    # Add focus to root window to capture key events
    root.focus_set()

    root.mainloop()

# Run the function
create_scrollable_charts_3_per_row()
