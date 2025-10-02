import tkinter as tk
from tkinter import ttk
import psutil
import time
import threading
from collections import deque
import platform
import math

class ComputerMoodDetector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Perfomance Police Detector")
        self.root.geometry("500x650")
        self.root.resizable(False, False)
        self.root.configure(bg='#0f0f1f')
        
        # Remove default title bar
        self.root.overrideredirect(True)
        
        # System status data with funny messages
        self.mood_data = {
            'cpu': [
                {'threshold': 30, 'emoji': "😴", 'message': "CPU chilling: Everything's smooth, no stress."},
                {'threshold': 50, 'emoji': "😊", 'message': "CPU okay: Running fine, nothing crazy."},
                {'threshold': 70, 'emoji': "😅", 'message': "CPU sweating: Doing some heavy lifting, but coping."},
                {'threshold': 85, 'emoji': "😰", 'message': "CPU stressed: Close some apps or it will explode!"},
                {'threshold': 95, 'emoji': "🔥", 'message': "CPU on fire: Run! Save your work NOW!"}
            ],
            'ram': [
                {'threshold': 40, 'emoji': "💾", 'message': "RAM happy: Plenty of memory, smooth sailing."},
                {'threshold': 65, 'emoji': "🤔", 'message': "RAM thinking: Could slow down if you open more stuff."},
                {'threshold': 85, 'emoji': "😵", 'message': "RAM stressed: Might lag soon, be careful."},
                {'threshold': 95, 'emoji': "💀", 'message': "RAM dead tired: Close some programs or face doom!"}
            ],
            'disk': [
                {'threshold': 50, 'emoji': "📁", 'message': "Disk healthy: Plenty of space, all good."},
                {'threshold': 80, 'emoji': "🍔", 'message': "Disk full-ish: Maybe clean some junk."},
                {'threshold': 95, 'emoji': "🎈", 'message': "Disk about to pop: Free some space ASAP!"}
            ],
            'network': [
                {'threshold': 30, 'emoji': "🚀", 'message': "Network flying: Fast and smooth."},
                {'threshold': 60, 'emoji': "🚗", 'message': "Network normal: Works fine, nothing to worry about."},
                {'threshold': 80, 'emoji': "🐢", 'message': "Network crawling: Things loading slow, patience."},
                {'threshold': 95, 'emoji': "☠️", 'message': "Network dead: Might need a restart or check cables."}
            ],
            'battery': [
                {'threshold': 15, 'emoji': "🪫", 'message': "Battery empty: Plug in NOW or bye-bye PC."},
                {'threshold': 30, 'emoji': "🔴", 'message': "Battery low: Better save your work."},
                {'threshold': 80, 'emoji': "🟡", 'message': "Battery okay: Still got juice, keep going."},
                {'threshold': 101, 'emoji': "🟢", 'message': "Battery full: Party time, fully charged!"}
            ]
        }
        
        # Store previous values for network calculation
        self.prev_net_io = psutil.net_io_counters()
        self.prev_time = time.time()
        self.network_speeds = deque(maxlen=10)
        
        # Animation states
        self.emoji_animation = None
        self.animation_running = False
        
        self.setup_ui()
        self.setup_bindings()
        self.start_monitoring()
        
    def setup_ui(self):
        # Main container with gradient background
        self.main_canvas = tk.Canvas(self.root, bg='#0f0f1f', highlightthickness=0)
        self.main_canvas.pack(fill='both', expand=True)
        
        # Draw gradient background
        self.draw_gradient_background()
        
        # Main window frame
        self.window_frame = tk.Frame(self.main_canvas, bg='#191923', bd=0, relief='flat')
        self.window_frame.place(relx=0.5, rely=0.5, anchor='center', width=460, height=600)
        
        # Create window border effect
        self.create_window_border()
        
        # Title bar
        self.title_bar = tk.Frame(self.window_frame, bg='#191923')
        self.title_bar.pack(fill='x', padx=25, pady=(25, 20))
        
        self.title_label = tk.Label(
            self.title_bar,
            text="Performance Police",
            font=('Segoe UI', 16, 'bold'),
            fg='#a090ff',
            bg='#191923'
        )
        self.title_label.pack(side='left')
        
        # Window controls
        self.controls = tk.Frame(self.title_bar, bg='#191923')
        self.controls.pack(side='right')
        
        self.close_btn = self.create_control_button('close', '#ff4646')
        self.minimize_btn = self.create_control_button('minimize', '#ffb446')
        
        # Status container
        self.status_container = tk.Frame(self.window_frame, bg='#191923')
        self.status_container.pack(fill='both', expand=True, padx=25, pady=10)
        
        # Mood display
        self.mood_display = tk.Frame(self.status_container, bg='#0a0a12', relief='flat', bd=1)
        self.mood_display.pack(fill='x', pady=(0, 20))
        self.mood_display.configure(highlightbackground='#333344', highlightthickness=1)
        
        self.emoji_label = tk.Label(
            self.mood_display,
            text="😴",
            font=('Segoe UI', 48),
            fg='white',
            bg='#0a0a12'
        )
        self.emoji_label.pack(pady=(20, 10))
        
        self.message_label = tk.Label(
            self.mood_display,
            text="Initializing mood detection...",
            font=('Segoe UI', 12, 'bold'),
            fg='white',
            bg='#0a0a12',
            wraplength=400,
            justify='center'
        )
        self.message_label.pack(pady=(0, 20), padx=20)
        
        # Stats grid - now 3x2 for battery
        self.stats_frame = tk.Frame(self.status_container, bg='#191923')
        self.stats_frame.pack(fill='both', expand=True)
        
        # Configure grid for 3 rows and 2 columns
        self.stats_frame.columnconfigure(0, weight=1)
        self.stats_frame.columnconfigure(1, weight=1)
        self.stats_frame.rowconfigure(0, weight=1)
        self.stats_frame.rowconfigure(1, weight=1)
        self.stats_frame.rowconfigure(2, weight=1)
        
        # Create stat widgets including battery
        self.cpu_stat = self.create_stat_widget("CPU Usage", 0, 0, 'cpu')
        self.ram_stat = self.create_stat_widget("RAM Usage", 0, 1, 'ram')
        self.disk_stat = self.create_stat_widget("Disk Usage", 1, 0, 'disk')
        self.network_stat = self.create_stat_widget("Network", 1, 1, 'network')
        self.battery_stat = self.create_stat_widget("Battery", 2, 0, 'battery')
        
        # Footer
        self.footer = tk.Frame(self.window_frame, bg='#191923')
        self.footer.pack(fill='x', padx=25, pady=(10, 25))
        
        self.loader_canvas = tk.Canvas(
            self.footer,
            width=20,
            height=20,
            bg='#191923',
            highlightthickness=0
        )
        self.loader_canvas.pack(side='left', padx=(0, 10))
        
        self.footer_label = tk.Label(
            self.footer,
            text="Monitoring system resources...",
            font=('Segoe UI', 10),
            fg='#b0b0b0',
            bg='#191923'
        )
        self.footer_label.pack(side='left')
        
        # Start loader animation
        self.loader_angle = 0
        self.animate_loader()
        
    def draw_gradient_background(self):
        # Create a simple gradient effect using rectangles
        colors = ['#0f0f1f', '#1a1a2f', '#2d1a4a']
        height = self.root.winfo_screenheight()
        
        for i, color in enumerate(colors):
            y1 = i * height // len(colors)
            y2 = (i + 1) * height // len(colors)
            self.main_canvas.create_rectangle(0, y1, 500, y2, fill=color, outline='')
        
    def create_window_border(self):
        # Create border effect using canvas
        border_canvas = tk.Canvas(self.window_frame, bg='#191923', highlightthickness=0)
        border_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Draw top accent line
        border_canvas.create_line(0, 1, 460, 1, fill='#6464ff', width=2)
        
    def create_control_button(self, type, color):
        btn = tk.Canvas(
            self.controls,
            width=12,
            height=12,
            bg='#191923',
            highlightthickness=0
        )
        btn.pack(side='left', padx=5)
        btn.create_oval(2, 2, 10, 10, fill=color, outline='')
        
        # Bind click events - FIXED: Use withdraw() instead of iconify() for override-redirect windows
        if type == 'close':
            btn.bind('<Button-1>', lambda e: self.root.quit())
        elif type == 'minimize':
            btn.bind('<Button-1>', lambda e: self.root.withdraw())
            
        btn.bind('<Enter>', lambda e: btn.configure(cursor='hand2'))
        return btn
        
    def create_stat_widget(self, title, row, col, stat_type):
        frame = tk.Frame(
            self.stats_frame,
            bg='#0a0a12',
            relief='flat',
            bd=1
        )
        frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        frame.configure(highlightbackground='#333344', highlightthickness=1)
        
        # Title
        title_label = tk.Label(
            frame,
            text=title,
            font=('Segoe UI', 10),
            fg='#b0b0b0',
            bg='#0a0a12'
        )
        title_label.pack(anchor='w', padx=15, pady=(15, 5))
        
        # Value
        value_var = tk.StringVar(value="0%")
        value_label = tk.Label(
            frame,
            textvariable=value_var,
            font=('Segoe UI', 16, 'bold'),
            fg='white',
            bg='#0a0a12'
        )
        value_label.pack(anchor='w', padx=15, pady=5)
        
        # Progress bar container
        progress_container = tk.Frame(frame, bg='#1a1a1a', height=6)
        progress_container.pack(fill='x', padx=15, pady=(5, 15))
        progress_container.pack_propagate(False)
        
        # Progress bar canvas
        progress_canvas = tk.Canvas(
            progress_container,
            height=6,
            bg='#1a1a1a',
            highlightthickness=0
        )
        progress_canvas.pack(fill='x')
        
        # Store references
        setattr(self, f"{stat_type}_value", value_var)
        setattr(self, f"{stat_type}_progress", progress_canvas)
        
        return frame
        
    def animate_loader(self):
        self.loader_canvas.delete("all")
        # Draw loader arc
        self.loader_canvas.create_arc(
            2, 2, 18, 18,
            start=self.loader_angle, extent=300,
            outline='#6464ff', width=2,
            style='arc'
        )
        self.loader_angle = (self.loader_angle + 20) % 360
        self.root.after(50, self.animate_loader)
        
    def setup_bindings(self):
        # Make window draggable
        self.title_bar.bind('<Button-1>', self.start_move)
        self.title_bar.bind('<B1-Motion>', self.on_move)
        self.title_label.bind('<Button-1>', self.start_move)
        self.title_label.bind('<B1-Motion>', self.on_move)
        
        # Add double-click to close on title bar
        self.title_bar.bind('<Double-Button-1>', lambda e: self.root.quit())
        self.title_label.bind('<Double-Button-1>', lambda e: self.root.quit())
        
    def start_move(self, event):
        self.x = event.x
        self.y = event.y
        
    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
        
    def get_system_stats(self):
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # RAM usage
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        
        # Disk usage
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
        except:
            try:
                disk = psutil.disk_usage('C:/')
                disk_percent = disk.percent
            except:
                disk_percent = 0
        
        # Network usage
        current_net_io = psutil.net_io_counters()
        current_time = time.time()
        time_diff = current_time - self.prev_time
        
        if time_diff > 0:
            bytes_sent = current_net_io.bytes_sent - self.prev_net_io.bytes_sent
            bytes_recv = current_net_io.bytes_recv - self.prev_net_io.bytes_recv
            
            # Convert to MB/s and create a 0-100 scale
            total_speed = (bytes_sent + bytes_recv) / time_diff / 1024 / 1024
            network_percent = min(total_speed * 10, 100)
            
            self.network_speeds.append(network_percent)
            network_avg = sum(self.network_speeds) / len(self.network_speeds) if self.network_speeds else 0
            
            self.prev_net_io = current_net_io
            self.prev_time = current_time
        else:
            network_avg = 0
        
        # Battery status
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_percent = battery.percent
                # If plugged in, show as "full" for mood purposes
                if battery.power_plugged:
                    battery_percent = 100
            else:
                battery_percent = 100  # Assume desktop PC
        except:
            battery_percent = 100  # Default for systems without battery
            
        return cpu_percent, ram_percent, disk_percent, network_avg, battery_percent
    
    def update_display(self, cpu, ram, disk, network, battery):
        # Update progress bars and values
        self.update_progress_bar('cpu', cpu)
        self.update_progress_bar('ram', ram)
        self.update_progress_bar('disk', disk)
        self.update_progress_bar('network', network)
        self.update_progress_bar('battery', battery)
        
        # Determine overall mood based on highest usage (excluding battery for overall mood)
        max_usage = max(cpu, ram, disk, network)
        mood_category = 'cpu'
        
        if max_usage == ram:
            mood_category = 'ram'
        elif max_usage == disk:
            mood_category = 'disk'
        elif max_usage == network:
            mood_category = 'network'
            
        self.update_mood_display(mood_category, max_usage, battery)
        
    def update_progress_bar(self, stat_type, value):
        value_var = getattr(self, f"{stat_type}_value")
        canvas = getattr(self, f"{stat_type}_progress")
        
        # Format value display based on type
        if stat_type == 'battery':
            value_var.set(f"{value:.0f}%")
        else:
            value_var.set(f"{value:.1f}%")
        
        # Clear previous progress
        canvas.delete("progress")
        
        # Calculate width based on value
        width = canvas.winfo_width()
        if width <= 1:  # Canvas not yet rendered
            width = 150  # Default width
            
        progress_width = (value / 100) * width
        
        # Define colors based on stat type
        colors = {
            'cpu': ('#46dc78', '#6464ff'),  # Green to Purple
            'ram': ('#46dc78', '#ffb446'),  # Green to Yellow
            'disk': ('#46dc78', '#ff4646'), # Green to Red
            'network': ('#46dc78', '#70c0ff'), # Green to Blue
            'battery': ('#46dc78', '#ffb446') # Green to Yellow for battery
        }
        
        color1, color2 = colors.get(stat_type, ('#46dc78', '#6464ff'))
        
        # Special handling for battery - different color based on level
        if stat_type == 'battery':
            if value <= 15:
                color2 = '#ff4646'  # Red for low battery
            elif value <= 30:
                color2 = '#ffb446'  # Orange for warning
            else:
                color2 = '#46dc78'  # Green for good battery
        
        # Draw progress bar
        canvas.create_rectangle(
            0, 0, progress_width, 6,
            fill=color2, outline='',
            tags="progress"
        )
        
        # Add animation for high usage (except battery)
        if value > 90 and stat_type != 'battery' and not hasattr(self, f'{stat_type}_pulse'):
            setattr(self, f'{stat_type}_pulse', True)
            self.pulse_animation(canvas, stat_type, 0)
        elif (value <= 90 or stat_type == 'battery') and hasattr(self, f'{stat_type}_pulse'):
            setattr(self, f'{stat_type}_pulse', False)
            
    def pulse_animation(self, canvas, stat_type, phase):
        if not hasattr(self, f'{stat_type}_pulse') or not getattr(self, f'{stat_type}_pulse'):
            return
            
        # Simple pulse effect by adjusting opacity (simulated with color brightness)
        intensity = 0.7 + 0.3 * math.sin(phase)
        canvas.itemconfig("progress", fill=self.adjust_color_brightness('#ff4646', intensity))
        self.root.after(100, lambda: self.pulse_animation(canvas, stat_type, phase + 0.5))
        
    def adjust_color_brightness(self, color, factor):
        # Convert hex to RGB
        hex_color = color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Adjust brightness
        new_rgb = tuple(min(255, int(c * factor)) for c in rgb)
        
        # Convert back to hex
        return '#{:02x}{:02x}{:02x}'.format(*new_rgb)
        
    def update_mood_display(self, category, value, battery):
        # Check battery first for critical low battery
        if battery <= 15:
            moods = self.mood_data.get('battery', self.mood_data['cpu'])
            selected_mood = moods[0]  # Default to first battery mood
        else:
            moods = self.mood_data.get(category, self.mood_data['cpu'])
            selected_mood = moods[0]  # Default to first mood in category
        
        # Find the appropriate mood based on thresholds
        for mood in moods:
            if value >= mood['threshold']:
                selected_mood = mood
                
        # Override with battery mood if battery is critical
        if battery <= 15:
            battery_moods = self.mood_data['battery']
            for mood in battery_moods:
                if battery <= mood['threshold']:
                    selected_mood = mood
                    break
                
        self.emoji_label.configure(text=selected_mood['emoji'])
        self.message_label.configure(text=selected_mood['message'])
        
        # Update emoji animation based on stress level
        if value > 90 or battery <= 15:
            self.add_emoji_animation('shake')
        elif value > 70:
            self.add_emoji_animation('bounce')
        else:
            self.remove_emoji_animation()
            
    def add_emoji_animation(self, animation_type):
        if self.emoji_animation == animation_type:
            return
            
        self.emoji_animation = animation_type
        self.animation_running = True
        
        if animation_type == 'shake':
            self.shake_emoji(0)
        elif animation_type == 'bounce':
            self.bounce_emoji(0, True)
            
    def remove_emoji_animation(self):
        self.emoji_animation = None
        self.animation_running = False
        
    def shake_emoji(self, offset):
        if not self.animation_running or self.emoji_animation != 'shake':
            return
            
        x_offset = math.sin(offset * 8) * 3
        self.emoji_label.place(x=x_offset)  # Simple shake effect
        self.root.after(50, lambda: self.shake_emoji(offset + 1))
        
    def bounce_emoji(self, step, going_up):
        if not self.animation_running or self.emoji_animation != 'bounce':
            return
            
        if going_up:
            y_offset = -5
            if step >= 5:
                going_up = False
                step = 0
            else:
                step += 1
        else:
            y_offset = 0
            if step >= 5:
                going_up = True
                step = 0
            else:
                step += 1
                
        self.emoji_label.pack(pady=(20 + y_offset, 10))
        self.root.after(100, lambda: self.bounce_emoji(step, going_up))
        
    def start_monitoring(self):
        def monitor():
            while True:
                try:
                    cpu, ram, disk, network, battery = self.get_system_stats()
                    self.root.after(0, self.update_display, cpu, ram, disk, network, battery)
                    time.sleep(3)  # Update every 3 seconds
                except Exception as e:
                    print(f"Monitoring error: {e}")
                    time.sleep(5)
                    
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        
    def run(self):
        # Center the window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.mainloop()

if __name__ == "__main__":
    app = ComputerMoodDetector()
    app.run()