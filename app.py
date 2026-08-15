"""
=============================================================================
AI DOCUMENTATION (assignment requirement)
=============================================================================
AI tools used:
    - Claude (Anthropic) — used for generating the initial app structure,
      the pressure-drop / friction-factor formulas, and the Plotly chart code.

Key prompts given to the AI:
    1. "Build a Streamlit pipe-flow calculator that takes fluid, diameter,
       velocity and pipe length as sidebar inputs and outputs Reynolds
       number, friction factor, and head loss, with a chart and a table."
    2. "Add error handling so that zero/negative diameter, velocity, or
       length shows a Streamlit warning instead of crashing the app."
    3. "Add a Plotly chart that sweeps velocity from 0 to 2x the chosen
       value and plots pressure drop, highlighting the current operating
       point."

Most important thing manually fixed / verified:
    - The AI's first draft used the laminar friction-factor formula
      (f = 64/Re) for ALL flow regimes, which gives wrong results in the
      turbulent range. This was manually fixed by adding a Reynolds-number
      check that switches to the Swamee-Jain explicit approximation for
      turbulent flow (Re > 4000), and a transitional-flow warning in
      between. The resulting friction factors were spot-checked by hand
      against a Moody chart at Re = 10,000 and Re = 100,000.
=============================================================================
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import math

st.set_page_config(page_title="Fluid Flow Calculator", page_icon="🌊", layout="wide")

# -----------------------------------------------------------------------
# Fluid property database (density [kg/m^3], dynamic viscosity [Pa.s])
# -----------------------------------------------------------------------
FLUIDS = {
    "Water (20°C)": {"rho": 998.0, "mu": 1.002e-3},
    "Air (20°C)": {"rho": 1.204, "mu": 1.825e-5},
    "Engine Oil (SAE 30, 20°C)": {"rho": 891.0, "mu": 0.29},
    "Glycerin (20°C)": {"rho": 1261.0, "mu": 1.412},
}

# -----------------------------------------------------------------------
# Core fluid-mechanics functions
# -----------------------------------------------------------------------
def reynolds_number(rho, v, d, mu):
    return (rho * v * d) / mu


def friction_factor(re, relative_roughness):
    """Returns (f, regime_label). Uses laminar formula for Re<2300,
    Swamee-Jain explicit turbulent correlation for Re>4000, and flags
    the transitional range in between."""
    if re <= 0:
        return np.nan, "undefined"
    if re < 2300:
        return 64.0 / re, "Laminar"
    elif re <= 4000:
        # transitional: no reliable closed-form correlation, approximate
        # with Swamee-Jain but flag it clearly to the user
        f = 0.25 / (math.log10((relative_roughness / 3.7) + (5.74 / re ** 0.9))) ** 2
        return f, "Transitional (approximate)"
    else:
        f = 0.25 / (math.log10((relative_roughness / 3.7) + (5.74 / re ** 0.9))) ** 2
        return f, "Turbulent"


def head_loss(f, length, diameter, v, g=9.81):
    return f * (length / diameter) * (v ** 2) / (2 * g)


def pressure_drop(rho, g, hl):
    return rho * g * hl


# -----------------------------------------------------------------------
# Sidebar — interactive inputs
# -----------------------------------------------------------------------
st.sidebar.header("Input Parameters")

fluid_name = st.sidebar.selectbox("Fluid", list(FLUIDS.keys()), index=0)

diameter_mm = st.sidebar.slider(
    "Pipe internal diameter (mm)", min_value=1.0, max_value=500.0, value=50.0, step=1.0
)

velocity = st.sidebar.slider(
    "Mean flow velocity (m/s)", min_value=0.0, max_value=10.0, value=2.0, step=0.1
)

length = st.sidebar.number_input(
    "Pipe length (m)", min_value=0.0, value=100.0, step=1.0
)

roughness_mm = st.sidebar.number_input(
    "Pipe absolute roughness (mm)",
    min_value=0.0,
    value=0.045,
    step=0.005,
    format="%.3f",
    help="Typical: commercial steel ≈ 0.045 mm, PVC ≈ 0.0015 mm, concrete ≈ 0.3–3 mm",
)

st.sidebar.markdown("---")
st.sidebar.caption("Adjust the values above — every chart and table updates live.")

# -----------------------------------------------------------------------
# Main page
# -----------------------------------------------------------------------
st.title("🌊 Fluid Flow Calculator")
st.subheader("Pipe flow: Reynolds number, friction factor & pressure drop")

st.markdown(
    """
**How to use this app:** choose a fluid and pipe geometry from the sidebar on the left.
The app calculates the Reynolds number, identifies the flow regime (laminar / transitional /
turbulent), estimates the Darcy friction factor, and reports the resulting head loss and
pressure drop along the pipe. The chart shows how pressure drop varies with velocity, and the
table lists results across a range of velocities for comparison.
"""
)

# -----------------------------------------------------------------------
# Error handling — validate inputs before computing
# -----------------------------------------------------------------------
errors = []
if diameter_mm <= 0:
    errors.append("Pipe diameter must be greater than 0 mm.")
if velocity < 0:
    errors.append("Velocity cannot be negative.")
if length <= 0:
    errors.append("Pipe length must be greater than 0 m.")
if roughness_mm < 0:
    errors.append("Roughness cannot be negative.")

if errors:
    for e in errors:
        st.warning(f"⚠️ {e}")
    st.stop()

try:
    rho = FLUIDS[fluid_name]["rho"]
    mu = FLUIDS[fluid_name]["mu"]
    diameter = diameter_mm / 1000.0
    roughness = roughness_mm / 1000.0
    relative_roughness = roughness / diameter

    if velocity == 0:
        st.info("Velocity is 0 m/s — flow is static, no pressure drop.")
        re, regime, f, hl, dp = 0.0, "Static", 0.0, 0.0, 0.0
    else:
        re = reynolds_number(rho, velocity, diameter, mu)
        f, regime = friction_factor(re, relative_roughness)
        hl = head_loss(f, length, diameter, velocity)
        dp = pressure_drop(rho, 9.81, hl)

except ZeroDivisionError:
    st.warning("⚠️ Diameter cannot be zero — division by zero in relative roughness.")
    st.stop()
except Exception as ex:
    st.warning(f"⚠️ Could not compute results with the given inputs: {ex}")
    st.stop()

# -----------------------------------------------------------------------
# Results — key metrics
# -----------------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Reynolds number", f"{re:,.0f}")
col2.metric("Flow regime", regime)
col3.metric("Head loss", f"{hl:.3f} m")
col4.metric("Pressure drop", f"{dp:,.0f} Pa")

if regime == "Transitional (approximate)":
    st.info(
        "ℹ️ Flow is in the transitional range (2300 < Re < 4000). "
        "No universally accepted correlation exists here — the value shown "
        "is an approximation and should be treated with caution."
    )

# -----------------------------------------------------------------------
# Chart — pressure drop vs velocity (Plotly), updates with inputs
# -----------------------------------------------------------------------
st.markdown("### Pressure Drop vs. Velocity")

v_range = np.linspace(0.01, max(velocity * 2, 1.0), 60)
dp_values = []
regime_values = []
for v in v_range:
    re_i = reynolds_number(rho, v, diameter, mu)
    f_i, regime_i = friction_factor(re_i, relative_roughness)
    hl_i = head_loss(f_i, length, diameter, v)
    dp_i = pressure_drop(rho, 9.81, hl_i)
    dp_values.append(dp_i)
    regime_values.append(regime_i)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=v_range,
        y=dp_values,
        mode="lines",
        name="Pressure drop",
        line=dict(color="#1f77b4", width=3),
    )
)
fig.add_trace(
    go.Scatter(
        x=[velocity],
        y=[dp],
        mode="markers",
        name="Current operating point",
        marker=dict(color="red", size=12, symbol="star"),
    )
)
fig.update_layout(
    xaxis_title="Velocity (m/s)",
    yaxis_title="Pressure drop (Pa)",
    hovermode="x unified",
    template="plotly_white",
    height=450,
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------------------
# Table — results across a range of velocities (Pandas)
# -----------------------------------------------------------------------
st.markdown("### Results Table")

table_velocities = np.linspace(0.5, max(velocity * 2, 1.0), 8)
rows = []
for v in table_velocities:
    re_i = reynolds_number(rho, v, diameter, mu)
    f_i, regime_i = friction_factor(re_i, relative_roughness)
    hl_i = head_loss(f_i, length, diameter, v)
    dp_i = pressure_drop(rho, 9.81, hl_i)
    rows.append(
        {
            "Velocity (m/s)": round(v, 2),
            "Reynolds Number": round(re_i, 0),
            "Regime": regime_i,
            "Friction Factor": round(f_i, 5),
            "Head Loss (m)": round(hl_i, 4),
            "Pressure Drop (Pa)": round(dp_i, 1),
        }
    )

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(
    "Fluid Flow Calculator · Darcy-Weisbach equation with laminar (f = 64/Re) and "
    "Swamee-Jain turbulent friction factor correlation."
)
