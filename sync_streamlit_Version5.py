import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, Patch
import time

# --- Session State Initialization ---
if 'is_paused' not in st.session_state:
    st.session_state.is_paused = False
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0.0
if 'prev_phase_deg' not in st.session_state:
    st.session_state.prev_phase_deg = 0.0
if 'rotation_times' not in st.session_state:
    st.session_state.rotation_times = []
if 'cb_closing_time_ms' not in st.session_state:
    st.session_state.cb_closing_time_ms = 100
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = time.time()

# --- Constants ---
grid_freq = 50.0
update_interval = 0.05  # seconds, 50 ms
circle_radius = 1.8
offset = 90  # degrees

# --- UI Controls ---
st.title("Synchroscope Simulation (Streamlit Version)")

gen_freq = st.slider('Gen Freq (Hz)', 49.0, 51.0, 50.1, 0.01)
cb_percent = st.slider('CB Closing Time (%)', 0, 100, 50)

col1, col2, col3, col4 = st.columns(4)
pause_btn = col1.button("Pause" if not st.session_state.is_paused else "Resume")
reset_btn = col2.button("Reset")
clear_btn = col3.button("Clear Rotations")
cb_command_btn = col4.button("CB Close Command")

# --- CB Percent Logic ---
def update_cb_time(percent):
    if percent <= 50:
        step_percent = 50 / 10
        snapped_step = round(percent / step_percent)
        snapped_percent = snapped_step * step_percent
        cb_time_ms = snapped_step * 10
    else:
        step_percent = 50 / 9
        snapped_step = round((percent - 50) / step_percent)
        snapped_percent = 50 + snapped_step * step_percent
        cb_time_ms = 100 + snapped_step * 100
    st.session_state.cb_closing_time_ms = cb_time_ms
    return snapped_percent, cb_time_ms

snapped_percent, cb_time_ms = update_cb_time(cb_percent)
st.write(f"CB Closing Time: {cb_time_ms:.0f} ms")

# --- Button Logic ---
if pause_btn:
    st.session_state.is_paused = not st.session_state.is_paused

if reset_btn:
    st.session_state.elapsed_time = 0.0
    st.session_state.rotation_times.clear()
    st.session_state.prev_phase_deg = 0.0
    st.session_state.is_paused = False

if clear_btn:
    st.session_state.rotation_times.clear()

if cb_command_btn:
    # Pause after CB closing time
    st.session_state.is_paused = False
    # Wait asynchronously using Streamlit's rerun mechanism
    st.session_state.cb_command_triggered = True
    st.session_state.cb_command_start_time = time.time()

# --- CB Command Pause Logic ---
if st.session_state.get("cb_command_triggered", False):
    delay_s = st.session_state.cb_closing_time_ms / 1000.0
    if time.time() - st.session_state.cb_command_start_time >= delay_s:
        st.session_state.is_paused = True
        st.session_state.cb_command_triggered = False
        st.success("Paused after CB Closing Time")

# --- Animation / Frame Update ---
# Only update elapsed_time if not paused
if not st.session_state.is_paused:
    now = time.time()
    st.session_state.elapsed_time += (now - st.session_state.last_update_time)
    st.session_state.last_update_time = now
else:
    st.session_state.last_update_time = time.time()

freq_diff = gen_freq - grid_freq
elapsed_time = st.session_state.elapsed_time
phase_rad = 2 * np.pi * freq_diff * elapsed_time
phase_deg = np.degrees(phase_rad) % 360

# --- Rotation Tracking ---
if (
    st.session_state.prev_phase_deg > 300
    and phase_deg < 60
):
    st.session_state.rotation_times.append(round(elapsed_time, 2))
st.session_state.prev_phase_deg = phase_deg

# --- Plotting ---
fig, ax = plt.subplots(figsize=(6, 8))
plt.subplots_adjust(bottom=0, right=0.85)
ax.set_xlim(-2.4, 2.4)
ax.set_ylim(-3.15, 2.4)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title("Synchroscope Simulation", fontsize=16)

circle = plt.Circle((0, 0), circle_radius, color='black', fill=False, linewidth=2)
ax.add_patch(circle)

# Grid Arrow (static)
ax.arrow(0, 0, 0, circle_radius, head_width=0.09, color='blue', label="Grid")

# Tick marks
for angle in np.linspace(0, 2 * np.pi, 12, endpoint=False):
    x_outer = circle_radius * np.cos(angle)
    y_outer = circle_radius * np.sin(angle)
    x_inner = 1.575 * np.cos(angle)
    y_inner = 1.575 * np.sin(angle)
    ax.plot([x_outer, x_inner], [y_outer, y_inner], color='black', linewidth=1)

# --- Sync lights ---
def angular_diff(a1, a2):
    diff = abs(a1 - a2) % 360
    return diff if diff <= 180 else 360 - diff

phase_error = angular_diff(phase_deg, 0)

sync_lights_pos = {
    '5': (-1.8, -2.1),
    '10': (0, -2.1),
    '20': (1.8, -2.1)
}
sync_colors = {
    '5': 'green' if phase_error <= 5 else 'gray',
    '10': 'blue' if phase_error <= 10 else 'gray',
    '20': 'orange' if phase_error <= 20 else 'gray',
}
for key, pos in sync_lights_pos.items():
    ax.add_patch(plt.Circle(pos, 0.09, color=sync_colors[key]))

# Labels
ax.text(-1.8, -2.45, "±5°", fontsize=10, ha='center')
ax.text(0, -2.45, "±10°", fontsize=10, ha='center')
ax.text(1.8, -2.45, "±20°", fontsize=10, ha='center')

# Shaded sync zones
shaded_areas = [
    Wedge(center=(0, 0), r=circle_radius, theta1=-5 + offset, theta2=5 + offset, facecolor='green', alpha=0.25, label='±5° Window'),
    Wedge(center=(0, 0), r=circle_radius, theta1=-10 + offset, theta2=-5 + offset, facecolor='pink', alpha=0.25, label='± 5° to 10° Window'),
    Wedge(center=(0, 0), r=circle_radius, theta1=5 + offset, theta2=10 + offset, facecolor='pink', alpha=0.25),
    Wedge(center=(0, 0), r=circle_radius, theta1=-20 + offset, theta2=-10 + offset, facecolor='brown', alpha=0.25, label='±10° to 20° Window'),
    Wedge(center=(0, 0), r=circle_radius, theta1=10 + offset, theta2=20 + offset, facecolor='brown', alpha=0.25),
]
for wedge in shaded_areas:
    ax.add_patch(wedge)

legend_patches = [
    Patch(color='green', alpha=0.25, label='±5° Window'),
    Patch(color='pink', alpha=0.25, label='±5° to 10° Window'),
    Patch(color='brown', alpha=0.25, label='±10° to 20° Window'),
]
ax.legend(
    handles=legend_patches,
    loc='center left',
    bbox_to_anchor=(1.05, 0.5),
    fontsize=9,
    borderaxespad=0.5,
    title="Sync Windows"
)

# Generator arrow (dynamic)
x = circle_radius * np.sin(phase_rad)
y = circle_radius * np.cos(phase_rad)
ax.arrow(0, 0, x, y, head_width=0.09, color='red', label="Generator")

direction = (
    "Fast (Clockwise)" if freq_diff > 0
    else "Slow (Counter-Clockwise)" if freq_diff < 0
    else "In Sync"
)

# --- Text Info ---
st.markdown(
    f"**Grid:** {grid_freq:.2f} Hz &nbsp; | &nbsp; **Gen:** {gen_freq:.2f} Hz &nbsp; | &nbsp; **Δf:** {freq_diff:.2f} Hz &nbsp; | &nbsp; "
    f"**Phase:** {phase_deg:.1f}° &nbsp; | &nbsp; **{direction}**"
)
st.markdown(
    f"**Elapsed Time:** {elapsed_time:.2f} s &nbsp; | &nbsp; **CB Closing Time:** {cb_time_ms:.1f} ms"
)

if st.session_state.rotation_times:
    times_str = ', '.join(f"{t:.2f}" for t in st.session_state.rotation_times[-5:])
    st.markdown(f"**Full Rotation Occurs at t(s):** {times_str}")
else:
    st.markdown("**Full Rotation Occurs at t(s):**")

st.pyplot(fig)

# --- Auto-refresh for animation effect ---
st.experimental_rerun()