import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import tkinter as tk
from tkinter import ttk
import geopandas as gpd

class ZoomableChart:
    ''' Good working version - plots user provided gdf's
        python silrec/utils/plot_utils10.py
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
        for i, (original_fig, original_canvas, original_frame, gdf, title) in enumerate(self.row_charts_data):
            # Create new figure with larger size
            new_fig, new_ax = plt.subplots(figsize=(8, 5))

            # Plot the GeoDataFrame geometry
            if gdf is not None and not gdf.empty:
                gdf.plot(ax=new_ax, color='blue', alpha=0.7, edgecolor='black')
                new_ax.set_title(title, fontsize=12, fontweight='bold')
                new_ax.set_xlabel('Longitude')
                new_ax.set_ylabel('Latitude')
                new_ax.grid(True, alpha=0.3)
            else:
                # Fallback if no valid GeoDataFrame
                new_ax.text(0.5, 0.5, 'No geometry data', ha='center', va='center', transform=new_ax.transAxes)
                new_ax.set_title(title, fontsize=12, fontweight='bold')

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

def create_scrollable_charts_with_horizontal_scroll(*row_lists, row_descriptions=None, chart_titles=None):
    """
    Create a scrollable multi-chart canvas with horizontal and vertical scrolling.

    Parameters:
    *row_lists: Variable number of lists, each containing GeoDataFrames for a row
    row_descriptions: Optional list of descriptions for each row
    chart_titles: Optional nested list of titles for each chart
    """
    # Create main window
    root = tk.Tk()
    root.title("GeoDataFrame Charts - Horizontal & Vertical Scrolling")
    root.geometry("1400x800")

    # Validate input
    if not row_lists:
        raise ValueError("At least one row of GeoDataFrames must be provided")

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
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(canvas_window, width=max(canvas.winfo_width(), scrollable_frame.winfo_reqwidth()))

    scrollable_frame.bind("<Configure>", configure_scroll_region)

    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    canvas.bind("<Configure>", on_canvas_configure)

    zoomable_charts = []
    row_data = {}  # Store chart data by row

    # Default row descriptions
    default_descriptions = [
        "Spatial analysis of geographic features and distributions across the study area.",
        "Regional mapping showing territorial boundaries and spatial relationships.",
        "Geographic data visualization with coordinate reference system projections.",
        "Spatial patterns and clustering analysis of geographic phenomena.",
        "Cartographic representation of spatial data with thematic mapping."
    ]

    # Use provided descriptions or defaults
    if row_descriptions is None:
        row_descriptions = {}
        for i in range(len(row_lists)):
            if i < len(default_descriptions):
                row_descriptions[i] = default_descriptions[i]
            else:
                row_descriptions[i] = f"Spatial data visualization for geographic dataset {i+1}"
    elif isinstance(row_descriptions, list):
        row_descriptions = {i: desc for i, desc in enumerate(row_descriptions)}

    # Process each row
    for row_idx, row_gdfs in enumerate(row_lists):
        if not row_gdfs:
            continue

        charts_per_row = len(row_gdfs)

        # Calculate the actual display row (each logical row takes 2 grid rows: header+desc and charts)
        display_row = row_idx * 2

        # Create row header frame
        row_header_frame = tk.Frame(scrollable_frame)
        row_header_frame.grid(row=display_row, column=0, padx=(5, 0), pady=(10, 5), sticky="ns")

        # Add maximize button for the row
        maximize_btn = tk.Button(row_header_frame, text="⤢",
                               font=('Arial', 12, 'bold'),
                               command=lambda r=row_idx: maximize_row_popup(r),
                               bg='lightblue', width=3)
        maximize_btn.pack(padx=5, pady=5)

        # Add row label
        row_label = tk.Label(row_header_frame, text=f"Row {row_idx + 1}",
                           font=('Arial', 10, 'bold'))
        row_label.pack(padx=5, pady=2)

        # Create row description frame
        desc_frame = tk.Frame(scrollable_frame, relief=tk.GROOVE, bd=1, bg='lightyellow')
        desc_frame.grid(row=display_row, column=1, columnspan=charts_per_row,
                       padx=5, pady=(10, 5), sticky="ew")

        # Add description text
        desc_label = tk.Label(desc_frame, text=row_descriptions.get(row_idx, f"Spatial data row {row_idx + 1}"),
                             font=('Arial', 9), bg='lightyellow', wraplength=1200, justify=tk.LEFT)
        desc_label.pack(padx=8, pady=6)

        # Process each GeoDataFrame in the row
        for col_idx, gdf in enumerate(row_gdfs):
            chart_col = col_idx + 1
            chart_row = display_row + 1  # Charts go below description

            # Create frame for the chart
            chart_frame = tk.Frame(scrollable_frame, relief=tk.RAISED, bd=1)
            chart_frame.grid(row=chart_row, column=chart_col, padx=5, pady=5, sticky="nsew")

            # Configure grid weights for responsive layout
            scrollable_frame.grid_rowconfigure(chart_row, weight=1)
            scrollable_frame.grid_columnconfigure(chart_col, weight=1)

            # Create figure for each chart
            fig, ax = plt.subplots(figsize=(4, 3))

            # Generate chart title
            if chart_titles and row_idx < len(chart_titles) and col_idx < len(chart_titles[row_idx]):
                title = chart_titles[row_idx][col_idx]
            else:
                title = f"GeoChart {row_idx + 1}-{col_idx + 1}"

            # Plot the GeoDataFrame geometry
            if gdf is not None and not gdf.empty and hasattr(gdf, 'geometry'):
                try:
                    gdf.plot(ax=ax, color='blue', alpha=0.7, edgecolor='black')
                    ax.set_title(title, fontsize=9, fontweight='bold', pad=8)
                    ax.set_xlabel('Longitude', fontsize=8)
                    ax.set_ylabel('Latitude', fontsize=8)
                    ax.grid(True, alpha=0.3)
                    ax.tick_params(labelsize=7)
                except Exception as e:
                    # Fallback if plotting fails
                    ax.text(0.5, 0.5, f'Plot error: {str(e)}', ha='center', va='center',
                           transform=ax.transAxes, fontsize=8)
                    ax.set_title(title, fontsize=9, fontweight='bold')
            else:
                # Fallback if no valid GeoDataFrame
                ax.text(0.5, 0.5, 'No valid geometry data', ha='center', va='center',
                       transform=ax.transAxes, fontsize=8)
                ax.set_title(title, fontsize=9, fontweight='bold')

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
            if row_idx not in row_data:
                row_data[row_idx] = []
            row_data[row_idx].append((fig, chart_canvas, chart_frame, gdf, title))

    # Configure the first column for row headers
    scrollable_frame.grid_columnconfigure(0, weight=0, minsize=80)

    def maximize_row_popup(row_index):
        if row_index in row_data:
            description = row_descriptions.get(row_index, f"Row {row_index + 1} spatial analysis")
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

# Example usage function
def example_usage():
    """
    Example of how to use the function with sample data.
    This requires geopandas and some sample geographic data.
    """
    try:
        import geopandas as gpd
        from shapely.geometry import Point, Polygon

        # Create sample GeoDataFrames
        # Row 1: Points
        points1 = gpd.GeoDataFrame({
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 0), Point(1, -1)]
        })
        points2 = gpd.GeoDataFrame({
            'geometry': [Point(0.5, 0.5), Point(1.5, 1.5), Point(2.5, 0.5)]
        })

        # Row 2: Polygons
        poly1 = gpd.GeoDataFrame({
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        })
        poly2 = gpd.GeoDataFrame({
            'geometry': [Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])]
        })

        # Create row lists
        row1 = [points1, points2]
        row2 = [poly1, poly2]

        # Custom descriptions and titles
        descriptions = [
            "Point data analysis showing spatial distribution of sample locations",
            "Polygon features representing geographic boundaries and areas of interest"
        ]

        titles = [
            ["Sample Points Set 1", "Sample Points Set 2"],
            ["Study Area Boundary", "Region of Interest"]
        ]

        # Call the function
        create_scrollable_charts_with_horizontal_scroll(
            row1, row2,
            row_descriptions=descriptions,
            chart_titles=titles
        )

    except ImportError:
        print("geopandas or shapely not available. Using empty example.")
        # Fallback example without actual GeoDataFrames
        empty_row1 = [None, None]  # Placeholder for GeoDataFrames
        empty_row2 = [None, None]

        create_scrollable_charts_with_horizontal_scroll(empty_row1, empty_row2)

# Uncomment to run the example
# example_usage()

# Main function call for user data
# create_scrollable_charts_with_horizontal_scroll(list1, list2, list3, list4)

if __name__ == "__main__":
    gdf1 = gpd.read_file('silrec/utils/Shapefiles/demarcation_1_polygons/Demarcation_Boundary_1_polygons.shp')
    gdf2 = gpd.read_file('silrec/utils/Shapefiles/demarcation_2_polygons/Demarcation_Boundary_2_polygons.shp')
    gdf5 = gpd.read_file('silrec/utils/Shapefiles/demarcation_5_polygons/Demarcation_Boundary_5_polygons.shp')
    gdf16= gpd.read_file('silrec/utils/Shapefiles/demarcation_16_polygons/Demarcation_Boundary_16_polygons.shp')
    list1 = [gdf1, gdf2, gdf5, gdf16]
    list2 = [gdf1, gdf2, gdf5, gdf16]
    list3 = [gdf1, gdf2, gdf5, gdf16]
    list4 = [gdf1, gdf2, gdf5, gdf16]
    create_scrollable_charts_with_horizontal_scroll(list1, list2, list3, list4)

