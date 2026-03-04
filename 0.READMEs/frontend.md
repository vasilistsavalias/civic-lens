# Frontend

## Purpose
Describe the Streamlit UI composition, chart rendering, and resident/analyst interaction flow.

## Who Should Read This
Both

## Key Concepts
- Card-to-detail flow:
  Practical example: user clicks "Open card" and sees map, comments, and metrics for one proposal.
- Dashboard modes:
  Practical example: asic and dvanced modes call the same payload function with different view depth.
- Chart contract coupling:
  Practical example: chart functions in ui/charts.py assume exact field names from dashboard series dataclasses.

## Analogy
The frontend is the control panel of a machine: buttons and gauges expose what the backend is already doing.

## Key Files and Directories
- pp.py
- src/alpha_app/ui/charts.py
- src/alpha_app/ui/theme.py
- src/alpha_app/ui/state.py

## Interfaces and Contracts
- UI state contract: selected proposal ID + service filters in st.session_state.
- Visualization contract: plotly-ready rows returned by uild_dashboard_data(...).

## How to Run or Verify
`powershell
streamlit run app.py
`
Manual checks:
- login form renders
- cards open correctly
- charts populate without exceptions

## Failure Modes and Diagnosis
- Blank chart: inspect dataframe creation in chart function and upstream payload keys.
- Session resets unexpectedly: check st.session_state keys in ui/state.py and pp.py.

## Known Tradeoffs and Future Improvements
- Tradeoff: Streamlit speed is good for mockups, limited for complex client-side interactivity.
- Future: preserve contracts and migrate UI layer to production web stack if needed.
