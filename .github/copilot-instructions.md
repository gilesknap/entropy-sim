# Copilot Instructions for Entropy Simulation Project

**IMPORTANT: Keep this file updated as new features are added to the project.**

## Project Overview

This is an energy simulation tool for learning about entropy. It provides a circuit builder interface where users can create and visualize electrical circuits. But this will be expanded to include many kinds of energy and many devices that transform energy from one form to another. The initial focus is on simple electrical circuits with batteries, LEDs, and wires.

## Architecture

The project follows the **MVVM (Model-View-ViewModel)** pattern:

### Model Layer (`src/entropy_sim/models.py`)
- `Point`: 2D coordinate on canvas
- `ConnectionPoint`: Terminal on a component (with position and connection state)
- `CircuitObject`: Base class for circuit components
- `Battery`: Power source with positive/negative terminals
- `LED`: Light-emitting diode with anode/cathode terminals
- `Wire`: Connection between components with path routing
- `Circuit`: Collection of all components (batteries, LEDs, wires)

All models use **Pydantic** for validation and JSON serialization.

### ViewModel Layer (`src/entropy_sim/viewmodel.py`)
- `CircuitViewModel`: Manages all circuit state and business logic
  - Component placement and selection
  - Wire drawing with snap-to-connection-point
  - Component dragging
  - Undo/redo with JSON state snapshots
  - Change notification via callbacks

### View Layer (`src/entropy_sim/views/`)
- `main.py`: NiceGUI application entry point with `@ui.page` decorator
- `canvas_view.py`: Main view composing all UI components
- `palette.py`: Component palette with Battery, LED, Wire selection
- `controls.py`: Clear, Save, Load buttons
- `svg_renderer.py`: SVG generation for all circuit components

### Supporting Modules
- `pathfinding.py`: Orthogonal wire routing algorithm (L-shaped and Z-shaped paths)

## UI Framework

Uses **NiceGUI** with:
- `ui.interactive_image` for the canvas (provides `image_x`/`image_y` mouse coordinates)
- SVG rendered as base64 data URI for the circuit visualization
- Mouse events: mousedown, mousemove, mouseup
- Keyboard shortcuts: Ctrl+Z (undo), Ctrl+Shift+Z (redo)

## Current Features

1. **Component Placement**
   - Click palette item to select
   - Click canvas to place Battery or LED
   - Components render with SVG graphics

2. **Wire Drawing**
   - Click and drag to draw wires
   - Wires snap to connection points when within 20px
   - Orthogonal routing for aesthetic paths

3. **Component Dragging**
   - Click and drag existing components to move them
   - Connected wires update automatically

4. **Undo/Redo**
   - Full state history (up to 50 states)
   - Buttons in palette + keyboard shortcuts

5. **Circuit Persistence**
   - Save exports to JSON (currently prints to console)
   - Load placeholder (not yet implemented)

## Development Setup

- Python 3.11+
- Dependencies: `pydantic>=2.0`, `nicegui>=1.4`
- Dev tools: `pytest`, `ruff`, `pyright`, `tox`
- Run with: `uv run entropy-sim`
- Tests: `uv run tox -p`

## Code Style

- Type hints required (pyright strict mode)
- Ruff for linting (88 char line limit)
- SVG strings should be split across lines to avoid E501
- Public methods for cross-class usage (no `_` prefix if called externally)

## File Structure

```
src/entropy_sim/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point
├── _version.py          # Version (setuptools_scm)
├── models.py            # Pydantic data models
├── viewmodel.py         # State management
├── pathfinding.py       # Wire routing
└── views/
    ├── __init__.py
    ├── main.py          # App entry
    ├── canvas_view.py   # Main canvas
    ├── palette.py       # Component palette
    ├── controls.py      # Buttons
    └── svg_renderer.py  # SVG generation
```

## Future Development Areas

- Circuit simulation (current flow, LED activation)
- Energy/entropy calculations
- More component types
- File save/load dialogs
- Component deletion
- Multi-select and group operations
- Zoom and pan on canvas
