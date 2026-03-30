import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle
import matplotlib.animation as animation

# Global variables
trajectories = []
current_ani = None
target_x = 80
target_y = 0
target_width = 5
target_height = 10

def start_simulation():
    global current_ani

    try:
        v0 = speed_slider.get()
        angle = angle_slider.get()
        color = 'blue' if len(trajectories) == 0 else 'green'

        g = 9.81
        theta = np.radians(angle)
        t_flight = 2 * v0 * np.sin(theta) / g
        t = np.linspace(0, t_flight, num=400)

        x = v0 * np.cos(theta) * t
        y = v0 * np.sin(theta) * t - 0.5 * g * t**2

        # Store trajectory
        trajectories.append((x, y, color))

        # Calculate results
        max_range = max(x)
        max_height = max(y)

        result_label.config(
            text=f"Range: {max_range:.2f} m\nMax Height: {max_height:.2f} m"
        )

        # Stop previous animation if running
        if current_ani is not None:
            current_ani.event_source.stop()

        # Redraw everything cleanly
        ax.clear()
        ax.set_xlim(0, 120)
        ax.set_ylim(0, 60)
        ax.set_xlabel("Distance (m)")
        ax.set_ylabel("Height (m)")
        ax.set_title("Projectile Simulator - Hit the Target!")
        ax.grid(True)

        # Draw target
        target_patch = Rectangle((target_x, target_y), target_width, target_height,
                               color='red', alpha=0.6, label="Target")
        ax.add_patch(target_patch)

        # Plot all previous trajectories (static)
        for traj in trajectories[:-1]:  # all except the current one
            ax.plot(traj[0], traj[1], lw=2, color=traj[2], alpha=0.7)

        # Current trajectory for animation
        current_x, current_y, current_color = trajectories[-1]
        line, = ax.plot([], [], lw=2.5, color=current_color)
        point, = ax.plot([], [], 'o', markersize=8, color=current_color)

        hit_detected = False

        def animate(i):
            nonlocal hit_detected

            if i < len(current_x):
                line.set_data(current_x[:i+1], current_y[:i+1])
                point.set_data(current_x[i], current_y[i])

                # Check for hit
                if not hit_detected:
                    cx = current_x[i]
                    cy = current_y[i]
                    if (target_x <= cx <= target_x + target_width) and \
                       (target_y <= cy <= target_y + target_height):
                        result_label.config(
                            text=f"🎯 HIT THE TARGET! 🎯\nRange: {max(current_x):.2f} m | "
                                 f"Max Height: {max(current_y):.2f} m"
                        )
                        hit_detected = True

                return line, point

            return line, point

        # Create new animation
        current_ani = animation.FuncAnimation(
            fig, animate, frames=len(current_x),
            interval=15, blit=True, repeat=False
        )

        canvas.draw()

    except Exception as e:
        result_label.config(text=f"Error: {str(e)}")


def reset_simulation():
    global trajectories, current_ani
    trajectories = []
    if current_ani is not None:
        current_ani.event_source.stop()
        current_ani = None

    ax.clear()
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 60)
    ax.set_xlabel("Distance (m)")
    ax.set_ylabel("Height (m)")
    ax.set_title("Projectile Simulator - Hit the Target!")
    ax.grid(True)

    # Redraw target
    target_patch = Rectangle((target_x, target_y), target_width, target_height,
                           color='red', alpha=0.6)
    ax.add_patch(target_patch)

    canvas.draw()
    result_label.config(text="")


# ==================== UI ====================
root = tk.Tk()
root.title("🚀 Projectile Game Simulator")
root.geometry("950x620")
root.configure(bg="#f0f0f0")

# Left Control Panel
control_frame = tk.Frame(root, bg="#f0f0f0", width=300)
control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=15, pady=15)

tk.Label(control_frame, text="🚀 Projectile Simulator",
         font=("Arial", 18, "bold"), bg="#f0f0f0").pack(pady=(0, 20))

tk.Label(control_frame, text="Initial Speed (m/s)",
         font=("Arial", 11), bg="#f0f0f0").pack(anchor="w", pady=(10, 5))
speed_slider = tk.Scale(control_frame, from_=10, to=100, orient=tk.HORIZONTAL,
                       length=280, resolution=1)
speed_slider.set(50)
speed_slider.pack(pady=5)

tk.Label(control_frame, text="Launch Angle (degrees)",
         font=("Arial", 11), bg="#f0f0f0").pack(anchor="w", pady=(15, 5))
angle_slider = tk.Scale(control_frame, from_=10, to=80, orient=tk.HORIZONTAL,
                       length=280, resolution=1)
angle_slider.set(45)
angle_slider.pack(pady=5)

tk.Button(control_frame, text="🚀 LAUNCH", command=start_simulation,
          bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2, width=25).pack(pady=20)

tk.Button(control_frame, text="Reset All", command=reset_simulation,
          bg="#f44336", fg="white", font=("Arial", 11), height=2, width=25).pack(pady=5)

result_label = tk.Label(control_frame, text="", font=("Arial", 11, "bold"),
                       bg="#f0f0f0", justify="left", fg="#333")
result_label.pack(pady=20, fill=tk.X)

# Matplotlib Figure
fig, ax = plt.subplots(figsize=(7, 5.5))
fig.patch.set_facecolor('#f0f0f0')

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

# Initial plot setup
ax.set_xlim(0, 120)
ax.set_ylim(0, 60)
ax.set_xlabel("Distance (m)")
ax.set_ylabel("Height (m)")
ax.set_title("Projectile Simulator - Hit the Target!")
ax.grid(True)

# Initial target
target_patch = Rectangle((target_x, target_y), target_width, target_height,
                        color='red', alpha=0.6)
ax.add_patch(target_patch)

root.mainloop()