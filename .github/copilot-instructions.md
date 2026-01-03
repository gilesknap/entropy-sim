# Copilot Instructions for Entropy Simulation Project

**IMPORTANT: Keep this file updated as new features are added to the project.**

**When making changes:**
- Add new modules to the Architecture or File Structure sections
- Update Current Features list when implementing new functionality
- Update Future Development Areas when completing planned features
- Document any major code restructuring or pattern changes

## Project Overview

This is an energy simulation tool for learning about entropy. It provides a circuit builder interface where users can create and visualize electrical circuits. But this will be expanded to include many kinds of energy and many devices that transform energy from one form to another. The initial focus is on simple electrical circuits with batteries, LEDs, and wires.

## Architecture

The project follows the **MVVM (Model-View-ViewModel)** pattern:

### Model Layer (`src/entropy_sim/models.py`)
- `Point`: 2D coordinate on canvas
- `ConnectionPoint`: Terminal on a component (with position and connection state)
- `CircuitObject`: Base class for circuit components
- `Battery`: 9V battery power source with positive/negative terminals at top
- `LiIonCell`: Cylindrical lithium-ion battery (3.7V) with button positive terminal at top, flat negative at bottom
- `LED`: Light-emitting diode with anode/cathode terminals
- `Wire`: Connection between components with path routing
- `Circuit`: Collection of all components (batteries, liion_cells, LEDs, wires)

All models use **Pydantic** for validation and JSON serialization.

### ViewModel Layer (`src/entropy_sim/viewmodel.py`)
- `CircuitViewModel`: Manages all circuit state and business logic
  - Component placement and selection
  - Wire drawing with snap-to-connection-point (delegated to WireManager)
  - Component dragging and rotation
  - Component deletion via context menu
  - Undo/redo with JSON state snapshots
  - Change notification via callbacks

### View Layer (`src/entropy_sim/views/`)
- `main.py`: NiceGUI application entry point with `@ui.page` decorator
  - Configured with `reload=True` and `storage_secret` for development
  - Custom CSS for full-height responsive layout
- `canvas_view.py`: Main view composing all UI components
  - Right-click context menu for component actions (rotate, delete)
- `palette.py`: Component palette with Battery, Li-Ion Cell, LED, Wire selection
- `controls.py`: Clear, Save, Load buttons
- `svg_renderer.py`: SVG generation loading templates from asset files

### Supporting Modules
- `pathfinding.py`: Orthogonal wire routing algorithm (L-shaped and Z-shaped paths)
- `wire_manager.py`: Wire drawing, corner dragging, and connected wire updates
  - Separated from viewmodel for cleaner architecture
  - Handles all wire-related state and operations

### Assets (`src/entropy_sim/assets/`)
- `components/`: SVG files for electronic components
  - **Source**: Custom-created Fritzing-style realistic component graphics
  - **Can be replaced with**: Actual Fritzing parts from [fritzing/fritzing-parts](https://github.com/fritzing/fritzing-parts) repo
  - Current components: `battery.svg`, `battery_mini.svg`, `liion_cell.svg`, `liion_cell_mini.svg`, `led.svg`, `led_mini.svg`
  - Loaded using `importlib.resources` for proper package bundling
  - LED SVG uses template strings (`{led_color}`, `{body_color}`, `{glow}`) for dynamic coloring

## UI Framework

Uses **NiceGUI** with:
- `ui.interactive_image` for the canvas (provides `image_x`/`image_y` mouse coordinates)
- `ui.context_menu` for right-click component actions
- SVG rendered as base64 data URI for the circuit visualization
- Mouse events: mousedown, mousemove, mouseup, contextmenu
- Keyboard shortcuts: Ctrl+Z (undo), Ctrl+Shift+Z (redo)
- Auto-reload enabled for development (requires main guard change for multiprocessing)

## Current Features

1. **Component Placement**
   - Click palette item to select
   - Click canvas to place Battery or LED
   - Components render with Fritzing-style realistic SVG graphics (semi-transparent)

2. **Wire Drawing**
   - Click to start wire, click to add corners, click on connection point to finish
   - Wires snap to connection points when within 20px
   - Orthogonal routing with 90-degree angles maintained
   - Draggable corner points for wire reshaping

3. **Component Manipulation**
   - Click and drag components to move them
   - Connected wires update automatically during drag
   - Right-click for context menu:
     - Rotate 90° CW/CCW (batteries and LEDs)
     - Delete component (removes connected wires)

4. **Wire Corner Editing**
   - Drag wire corner points to reshape paths
   - Maintains orthogonal (90°) constraints with propagation
   - Snaps to horizontal/vertical based on alternating pattern

5. **Undo/Redo**
   - Full state history (up to 50 states)
   - Buttons in palette + keyboard shortcuts

6. **Circuit Persistence**
   - Save exports to JSON (currently prints to console)
   - Load placeholder (not yet implemented)

## Development Setup

- Python 3.11+
- Dependencies: `pydantic>=2.0`, `nicegui>=1.4`
- Dev tools: `pytest`, `ruff`, `pyright`, `tox`
- Run with: `uv run entropy-sim`
- Tests: `uv run tox -p`
- **Install packages with: `uv pip install <package>` (not plain `pip`)**

## Code Style

- Type hints required (pyright strict mode)
- Ruff for linting (88 char line limit)
- Public methods for cross-class usage (no `_` prefix if called externally)
- Component SVGs loaded from external files, not embedded in Python code

## File Structure

```
src/entropy_sim/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point
├── _version.py          # Version (setuptools_scm)
├── models.py            # Pydantic data models
├── viewmodel.py         # State management
├── pathfinding.py       # Wire routing
├── wire_manager.py      # Wire drawing and manipulation
├── assets/              # Component assets
│   └── components/      # SVG files for components
│       ├── battery.svg
│       ├── battery_mini.svg
│       ├── led.svg
│       └── led_mini.svg
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
- Multi-select and group operations
- Zoom and pan on canvas
- Replace custom SVGs with actual Fritzing parts
