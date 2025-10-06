import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk

class ZoomableChart:
    ''' Good working version
        python silrec/utils/plot_utils9.py
    '''
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

class RowMaximizer:
    def __init__(self, root, row_charts_data, row_number, row_description):
        self.root = root
        self.row_charts_data = row_charts_data
        self.row_number = row_number
        self.row_description = row_description
        self.maximized_window = None
        self.maximized_canvases = []

    def maximize_row(self):
        # Create new window for maximized row
        self.maximized_window = tk.Toplevel(self.root)
        self.maximized_window.title(f"Maximized View - Row {self.row_number + 1}")
        self.maximized_window.geometry("1400x700")
        self.maximized_window.configure(bg='white')

        # Enable full window controls
        self.maximized_window.resizable(True, True)

        # Set focus to the new window but don't make it modal
        self.maximized_window.focus_set()

        # Create main container with dual scrollbars
        main_container = tk.Frame(self.maximized_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create vertical scrollbar
        v_scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create horizontal scrollbar
        h_scrollbar = ttk.Scrollbar(main_container, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create canvas with both scrollbars
        canvas = tk.Canvas(main_container,
                          yscrollcommand=v_scrollbar.set,
                          xscrollcommand=h_scrollbar.set,
                          bg='white')
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configure scrollbars
        v_scrollbar.config(command=canvas.yview)
        h_scrollbar.config(command=canvas.xview)

        # Create scrollable frame
        scrollable_frame = tk.Frame(canvas, bg='white')

        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=max(canvas.winfo_width(), scrollable_frame.winfo_reqwidth()))

        scrollable_frame.bind("<Configure>", configure_scroll_region)

        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        # Create title with row description
        title_frame = tk.Frame(scrollable_frame, bg='white')
        title_frame.grid(row=0, column=0, columnspan=len(self.row_charts_data) + 1, sticky="ew", pady=(0, 10))

        title_label = tk.Label(title_frame, text=f"Row {self.row_number + 1} - Maximized View",
                              font=('Arial', 14, 'bold'), bg='white')
        title_label.pack()

        # Add row description
        if self.row_description:
            desc_label = tk.Label(title_frame, text=self.row_description,
                                 font=('Arial', 10), bg='white', wraplength=1000, justify=tk.CENTER)
            desc_label.pack(pady=(5, 0))

        # Recreate charts in maximized view with larger size
        for i, (original_fig, original_canvas, original_frame) in enumerate(self.row_charts_data):
            # Create new figure with larger size
            new_fig, new_ax = plt.subplots(figsize=(8, 5))

            # Copy the data and styling from original figure
            original_ax = original_fig.axes[0]

            # Get original plot data - handle different plot types
            for line in original_ax.get_lines():
                x_data = line.get_xdata()
                y_data = line.get_ydata()
                color = line.get_color()
                label = line.get_label()
                linewidth = line.get_linewidth()
                alpha = line.get_alpha()

                # Replot in new figure
                new_ax.plot(x_data, y_data, color=color, label=label,
                           linewidth=linewidth, alpha=alpha)

            # Copy scatter plots if any
            for collection in original_ax.collections:
                if hasattr(collection, 'get_offsets'):
                    offsets = collection.get_offsets()
                    if len(offsets) > 0:
                        x_data = offsets[:, 0]
                        y_data = offsets[:, 1]
                        colors = collection.get_facecolors()
                        if len(colors) > 0:
                            color = colors[0]
                            new_ax.scatter(x_data, y_data, color=color, alpha=collection.get_alpha())

            # Copy title and labels
            new_ax.set_title(original_ax.get_title(), fontsize=12, fontweight='bold')
            new_ax.set_xlabel(original_ax.get_xlabel())
            new_ax.set_ylabel(original_ax.get_ylabel())
            if original_ax.get_legend():
                new_ax.legend()
            new_ax.grid(True, alpha=0.3)

            # Create frame for this chart
            chart_frame = tk.Frame(scrollable_frame, relief=tk.RAISED, bd=2, bg='white')
            chart_frame.grid(row=1, column=i, padx=10, pady=10, sticky="nsew")

            scrollable_frame.grid_columnconfigure(i, weight=1)
            scrollable_frame.grid_rowconfigure(1, weight=1)

            # Create canvas
            new_canvas = FigureCanvasTkAgg(new_fig, chart_frame)
            new_canvas.draw()

            # Make it zoomable
            ZoomableChart(new_fig, new_canvas, chart_frame)

            # Add toolbar
            toolbar_frame = tk.Frame(chart_frame)
            toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)

            toolbar = NavigationToolbar2Tk(new_canvas, toolbar_frame)
            toolbar.update()

            # Pack canvas
            new_canvas.get_tk_widget().pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

            self.maximized_canvases.append((new_fig, new_canvas))

        # Add close button at the bottom
        close_button = tk.Button(self.maximized_window, text="Close Maximized View",
                                command=self.close_maximized,
                                font=('Arial', 10), bg='lightcoral', fg='white')
        close_button.pack(pady=10)

        # Mouse wheel scrolling for popup
        def _on_mousewheel(event):
            if event.state & 0x1:  # Shift key pressed - horizontal scrolling
                canvas.xview_scroll(int(-1*(event.delta/120)), "units")
            else:  # Vertical scrolling
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")

        self.maximized_window.bind_all("<MouseWheel>", _on_mousewheel)

        # Bind escape key to close
        self.maximized_window.bind('<Escape>', lambda e: self.close_maximized())

        # Handle window close event properly
        self.maximized_window.protocol("WM_DELETE_WINDOW", self.close_maximized)

    def close_maximized(self):
        if self.maximized_window:
            # Clean up matplotlib figures
            for fig, canvas in self.maximized_canvases:
                plt.close(fig)
            self.maximized_window.destroy()
            self.maximized_window = None

def create_scrollable_charts_with_horizontal_scroll():
    # Create main window
    root = tk.Tk()
    root.title("Scrollable Multi-Chart Canvas - Horizontal & Vertical Scrolling")
    root.geometry("1400x800")

    # Create main container
    main_container = tk.Frame(root)
    main_container.pack(fill=tk.BOTH, expand=True)

    # Create vertical scrollbar
    v_scrollbar = ttk.Scrollbar(main_container, orient=tk.VERTICAL)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Create horizontal scrollbar
    h_scrollbar = ttk.Scrollbar(main_container, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # Create canvas with both scrollbars
    canvas = tk.Canvas(main_container,
                      yscrollcommand=v_scrollbar.set,
                      xscrollcommand=h_scrollbar.set)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Configure scrollbars
    v_scrollbar.config(command=canvas.yview)
    h_scrollbar.config(command=canvas.xview)

    # Create scrollable frame
    scrollable_frame = tk.Frame(canvas)

    # Create window in canvas
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    # Function to update scroll region and canvas size
    def configure_scroll_region(event):
        # Update the scrollbars to match the size of the frame
        canvas.configure(scrollregion=canvas.bbox("all"))

        # Set the canvas window width to be at least the canvas width
        canvas.itemconfig(canvas_window, width=max(canvas.winfo_width(), scrollable_frame.winfo_reqwidth()))

    scrollable_frame.bind("<Configure>", configure_scroll_region)

    # Function to set canvas width when canvas is resized
    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", on_canvas_configure)

    # Create multiple charts - increased number for horizontal scrolling
    num_charts = 20  # More charts to demonstrate horizontal scrolling
    charts_per_row = 5  # Increased from 3 to 5 for horizontal scrolling
    zoomable_charts = []
    row_data = {}  # Store chart data by row
    row_descriptions = {}  # Store descriptions for each row

    # Sample row descriptions
    sample_descriptions = [
        "Analysis of quarterly sales data showing seasonal trends and growth patterns across different regions.",
        "Performance metrics for Q2 2024 demonstrating significant improvement in efficiency and throughput.",
        "Experimental results from phase 3 testing with control groups and variable parameters.",
        "Customer satisfaction survey results across different demographic segments and product categories.",
        "Financial indicators and market analysis for the current fiscal year showing positive growth trends."
    ]

    for i in range(num_charts):
        # Calculate row and column position
        current_row = i // charts_per_row
        current_col = i % charts_per_row

        # Add row description for the first chart in each row
        if current_col == 0 and current_row not in row_descriptions:
            # Use sample description or create generic one
            if current_row < len(sample_descriptions):
                row_descriptions[current_row] = sample_descriptions[current_row]
            else:
                row_descriptions[current_row] = f"Data analysis for period {current_row + 1} showing various metrics and performance indicators."

        # Create row description frame for the first column of each row
        if current_col == 0:
            # Calculate the actual display row (each logical row takes 2 grid rows: header+desc and charts)
            display_row = current_row * 2

            # Create row header frame
            row_header_frame = tk.Frame(scrollable_frame)
            row_header_frame.grid(row=display_row, column=0, padx=(5, 0), pady=(10, 5), sticky="ns")

            # Add maximize button for the row
            maximize_btn = tk.Button(row_header_frame, text="⤢",
                                   font=('Arial', 12, 'bold'),
                                   command=lambda r=current_row: maximize_row_popup(r),
                                   bg='lightblue', width=3)
            maximize_btn.pack(padx=5, pady=5)

            # Add row label
            row_label = tk.Label(row_header_frame, text=f"Row {current_row + 1}",
                               font=('Arial', 10, 'bold'))
            row_label.pack(padx=5, pady=2)

            # Create row description frame (above the charts)
            desc_frame = tk.Frame(scrollable_frame, relief=tk.GROOVE, bd=1, bg='lightyellow')
            desc_frame.grid(row=display_row, column=1, columnspan=charts_per_row,
                           padx=5, pady=(10, 5), sticky="ew")

            # Add description text
            desc_label = tk.Label(desc_frame, text=row_descriptions[current_row],
                                 font=('Arial', 9), bg='lightyellow', wraplength=1200, justify=tk.LEFT)
            desc_label.pack(padx=8, pady=6)

            # Adjust column for charts to start from column 1
            chart_col = current_col + 1
            chart_row = display_row + 1  # Charts go below description
        else:
            chart_col = current_col + 1
            chart_row = (current_row * 2) + 1  # Charts go below description

        # Create frame for the chart
        chart_frame = tk.Frame(scrollable_frame, relief=tk.RAISED, bd=1)
        chart_frame.grid(row=chart_row, column=chart_col, padx=5, pady=5, sticky="nsew")

        # Configure grid weights for responsive layout
        scrollable_frame.grid_rowconfigure(chart_row, weight=1)
        scrollable_frame.grid_columnconfigure(chart_col, weight=1)

        # Create figure for each chart (smaller to fit more per row)
        fig, ax = plt.subplots(figsize=(4, 3))

        # Generate sample data
        x = np.linspace(0, 10, 200)
        y = np.sin(x + i * 0.5) + 0.3 * np.cos(x * 2 + i) + np.random.normal(0, 0.1, 200)

        # Plot data with different styles
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray',
                 'olive', 'cyan', 'magenta', 'yellow', 'navy', 'maroon', 'teal', 'coral',
                 'indigo', 'salmon', 'gold', 'lime']
        color = colors[i % len(colors)]

        ax.plot(x, y, label=f'Dataset {i+1}', color=color, linewidth=1.5, alpha=0.8)
        ax.set_title(f'Chart {i+1}', fontsize=9, fontweight='bold', pad=8)
        ax.set_xlabel('X axis', fontsize=8)
        ax.set_ylabel('Y axis', fontsize=8)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.tick_params(labelsize=7)

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
        chart_canvas.get_tk_widget().pack(padx=3, pady=3, fill=tk.BOTH, expand=True)

        # Store chart data for row maximization
        if current_row not in row_data:
            row_data[current_row] = []
        row_data[current_row].append((fig, chart_canvas, chart_frame))

    # Configure the first column for row headers
    scrollable_frame.grid_columnconfigure(0, weight=0, minsize=80)

    def maximize_row_popup(row_index):
        if row_index in row_data:
            description = row_descriptions.get(row_index, f"Row {row_index + 1} analysis")
            maximizer = RowMaximizer(root, row_data[row_index], row_index, description)
            maximizer.maximize_row()

    # Mouse wheel scrolling for both directions
    def _on_mousewheel(event):
        if event.state & 0x1:  # Shift key pressed - horizontal scrolling
            canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        else:  # Vertical scrolling
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Bind keyboard shortcuts for scrolling
    def _on_key_press(event):
        if event.keysym == 'Left':
            canvas.xview_scroll(-1, "units")
        elif event.keysym == 'Right':
            canvas.xview_scroll(1, "units")
        elif event.keysym == 'Up':
            canvas.yview_scroll(-1, "units")
        elif event.keysym == 'Down':
            canvas.yview_scroll(1, "units")

    root.bind('<KeyPress>', _on_key_press)
    root.focus_set()

    # Add scroll instructions
    instructions = tk.Label(root,
                          text="Scroll: Mouse Wheel (vertical) | Shift+Mouse Wheel (horizontal) | Arrow Keys",
                          font=('Arial', 8), bg='lightyellow', relief=tk.SUNKEN)
    instructions.pack(side=tk.BOTTOM, fill=tk.X)

    root.mainloop()

# Run the function
create_scrollable_charts_with_horizontal_scroll()
