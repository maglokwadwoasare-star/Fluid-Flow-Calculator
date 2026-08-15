[README.md](https://github.com/user-attachments/files/31109320/README.md)
# Fluid Flow Calculator

A Streamlit engineering app that calculates Reynolds number, flow regime, Darcy friction factor,
head loss, and pressure drop for pipe flow, given a chosen fluid and pipe geometry. Users adjust
the fluid type, pipe diameter, flow velocity, pipe length, and roughness from the sidebar, and the
app live-updates an interactive Plotly chart of pressure drop vs. velocity along with a Pandas
results table sweeping a range of velocities.

**Live app:** [ADD YOUR STREAMLIT COMMUNITY CLOUD URL HERE]

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Features

- Sidebar with fluid selection, diameter, velocity, pipe length, and roughness inputs
- Reynolds number and flow-regime classification (laminar / transitional / turbulent)
- Darcy friction factor via the laminar formula and the Swamee-Jain correlation
- Interactive Plotly chart of pressure drop vs. velocity
- Pandas results table across a range of velocities
- Input validation with Streamlit warnings for invalid values
