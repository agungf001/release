import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- IEC Curve Parameters ---
curve_params = {
    "Normal Inv": (0.14, 0.02),
    "Very Inv": (13.5, 1.0),
    "Extremely Inv": (80.0, 2.0)
}

I = np.logspace(1, 5, 500)
t_inrush = np.linspace(0, 10, 10000)
dt = t_inrush[1] - t_inrush[0]

def calc_curve(TMS, pickup, mode):
    alpha, beta = curve_params[mode]
    M = I / pickup
    t = np.where(M > 1, TMS * (alpha / (M**beta - 1)), np.inf)
    I_flat = 20 * pickup
    t_flat = np.min(t[I <= I_flat])
    t = np.where(I >= I_flat, t_flat, t)
    return t, I_flat, t_flat

st.title("Overcurrent Relay Operating Time Calculator due to Transformer Inrush Current")

col1, col2 = st.columns(2)

with col1:
    TMS = st.slider("TMS", 0.05, 10.0, 0.28, 0.01)
    pickup = st.slider("Pickup (A)", 100, 5000, 1050, 10)
with col2:
    I_init = st.slider("Peak Inrush Current (A)", 100, 10000, 10000, 10)
    Tau = st.slider("Inrush Time Constant (s)", 0.1, 3.0, 0.8, 0.1)

mode = st.radio("IEC Relay Curves:", list(curve_params.keys()), horizontal=True)

t_curve, I_flat, t_flat = calc_curve(TMS, pickup, mode)
I_inrush = I_init * np.exp(-t_inrush / Tau)

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(I, t_curve, 'b-', lw=2, label=f"IEC {mode}")
ax.plot(I_inrush, t_inrush, 'm--', lw=2, label="Inrush")

# Calculate trip point
energy, trip_time, trip_current = 0, None, None
for ti, Ii in zip(t_inrush, I_inrush):
    if Ii >= pickup:
        T_oper = np.interp(Ii, I, t_curve)
        if T_oper > 0 and np.isfinite(T_oper):
            energy += (dt / T_oper)
        if energy >= 1.0:
            trip_time, trip_current = ti, Ii
            break

if trip_time is not None:
    ax.plot([trip_current], [trip_time], 'ro', markersize=10, label="Trip Point")
    st.success(f"Relay Tripping Time: {trip_time:.3f} s")
else:
    st.warning("Relay Tripping Time: N/A")

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(10, 100000); ax.set_ylim(0.01, 100)
ax.set_xlabel("Current (A)"); ax.set_ylabel("Time (s)")
ax.set_title("Relay Operating Time Calculator due to Transformer Inrush Current")
ax.grid(True, which="both", ls="-", color="green", alpha=0.3)
ax.legend()
st.pyplot(fig)
