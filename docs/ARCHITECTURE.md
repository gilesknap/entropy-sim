# Entropy Simulation - Architecture Document

This document describes the architecture of the Entropy Simulation project, an energy simulation tool for learning about entropy through circuit building.

## Overview

The project follows the **MVVM (Model-View-ViewModel)** architectural pattern:

- **Model**: Data structures representing circuit components (Pydantic models)
- **View**: NiceGUI-based UI components for rendering and interaction
- **ViewModel**: Business logic and state management bridging Model and View

## Module Dependency Graph

```
                           ┌─────────────────────────────────────────────────┐
                           │              External Dependencies              │
                           │     pydantic, nicegui, importlib.resources      │
                           └─────────────────────────────────────────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────────────────────┐
                    │                              │                              │
                    ▼                              ▼                              ▼
         ┌──────────────────┐          ┌──────────────────┐          ┌──────────────────┐
         │   object_type    │          │     _version     │          │      assets/     │
         │                  │          │                  │          │   components/    │
         │   ObjectType     │          │   __version__    │          │   *.svg files    │
         └──────────────────┘          └──────────────────┘          └──────────────────┘
                    │                                                         │
                    │                                                         │
          ┌─────────┴─────────────────────────────────────────────┐          │
          │                                                       │          │
          ▼                                                       │          │
┌──────────────────────────────────────────────────────────────┐  │          │
│                        models/                               │  │          │
│  ┌──────────┐                                                │  │          │
│  │  point   │◄─────────────────────────────────────┐         │  │          │
│  │          │                                      │         │  │          │
│  │  Point   │                                      │         │  │          │
│  │Connection│                                      │         │  │          │
│  │  Point   │                                      │         │  │          │
│  └──────────┘                                      │         │  │          │
│       │                                            │         │  │          │
│       ▼                                            │         │  │          │
│  ┌────────────┐                                    │         │  │          │
│  │circuit_base│◄───────────────────────────────┐   │         │  │          │
│  │            │                                │   │         │  │          │
│  │CircuitBase │                                │   │         │  │          │
│  └────────────┘                                │   │         │  │          │
│       │                                        │   │         │  │          │
│       │    ┌───────────────┬───────────────┬───┴───┴──┐      │  │          │
│       │    │               │               │          │      │  │          │
│       ▼    ▼               ▼               ▼          ▼      │  │          │
│  ┌─────────────┐   ┌─────────────┐   ┌──────────┐  ┌──────┐  │  │          │
│  │   battery   │   │ liion_cell  │   │   led    │  │ wire │  │  │          │
│  │             │   │             │   │          │  │      │  │  │          │
│  │   Battery   │   │  LiIonCell  │   │   LED    │  │ Wire │  │  │          │
│  │             │   │             │   │          │  │Wire- │  │  │          │
│  │             │   │             │   │          │  │Point │  │  │          │
│  └─────────────┘   └─────────────┘   └──────────┘  └──────┘  │  │          │
│       │                   │               │          │       │  │          │
│       └───────────────────┴───────────────┴──────────┘       │  │          │
│                           │                                  │  │          │
│                           ▼                                  │  │          │
│                    ┌─────────────┐                           │  │          │
│                    │   circuit   │                           │  │          │
│                    │             │                           │  │          │
│                    │   Circuit   │                           │  │          │
│                    │  Component  │                           │  │          │
│                    └─────────────┘                           │  │          │
│                           │                                  │  │          │
└───────────────────────────┼──────────────────────────────────┘  │          │
                            │                                     │          │
            ┌───────────────┼─────────────────────────────────────┘          │
            │               │                                                │
            ▼               ▼                                                │
   ┌─────────────────────────────┐                                           │
   │       wire_manager          │                                           │
   │                             │                                           │
   │       WireManager           │                                           │
   │  (wire drawing & editing)   │                                           │
   └─────────────────────────────┘                                           │
                 │                                                           │
                 ▼                                                           │
   ┌─────────────────────────────┐                                           │
   │        viewmodel            │                                           │
   │                             │                                           │
   │    CircuitViewModel         │                                           │
   │  (state & business logic)   │                                           │
   └─────────────────────────────┘                                           │
                 │                                                           │
                 │                                                           │
   ┌─────────────┴─────────────────────────────────────────────────────┐     │
   │                          views/                                   │     │
   │                                                                   │     │
   │  ┌───────────────┐    ┌──────────────┐     ┌─────────────────┐    │     │
   │  │   controls    │    │   palette    │────►│  svg_renderer   │◄───┼─────┘
   │  │               │    │              │     │                 │    │
   │  │ ControlsView  │    │ PaletteView  │     │  SVGRenderer    │    │
   │  └───────────────┘    └──────────────┘     └─────────────────┘    │
   │         │                   │                      │              │
   │         │                   │                      │              │
   │         └───────────────────┼──────────────────────┘              │
   │                             │                                     │
   │                             ▼                                     │
   │                    ┌────────────────┐                             │
   │                    │  canvas_view   │                             │
   │                    │                │                             │
   │                    │CircuitCanvas-  │                             │
   │                    │    View        │                             │
   │                    └────────────────┘                             │
   │                             │                                     │
   │                             ▼                                     │
   │                    ┌────────────────┐                             │
   │                    │     main       │                             │
   │                    │                │                             │
   │                    │  run(), index  │                             │
   │                    └────────────────┘                             │
   │                                                                   │
   └───────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │       __main__         │
                    │                        │
                    │   CLI entry point      │
                    └────────────────────────┘
```

## Module Descriptions

### Core Modules

| Module | File | Description |
|--------|------|-------------|
| `object_type` | `object_type.py` | `ObjectType` enum defining component types (BATTERY, LED, WIRE, etc.) |
| `_version` | `_version.py` | Version number managed by setuptools_scm |

### Models Package (`models/`)

The models package contains Pydantic data models for circuit components.

| Module | Classes | Description |
|--------|---------|-------------|
| `point` | `Point`, `ConnectionPoint` | 2D coordinates and component connection terminals |
| `circuit_base` | `CircuitBase` | Abstract base class for all circuit objects with common properties |
| `battery` | `Battery` | 9V battery with positive/negative terminals |
| `liion_cell` | `LiIonCell` | Cylindrical Li-Ion battery cell (3.7V) |
| `led` | `LED` | Light-emitting diode with anode/cathode |
| `wire` | `Wire`, `WirePoint` | Wire connections with path routing |
| `circuit` | `Circuit`, `Component` | Container for all circuit components with factory methods |

#### Model Inheritance Hierarchy

```
BaseModel (pydantic)
    │
    ├── Point
    ├── ConnectionPoint
    ├── WirePoint
    │
    └── CircuitBase
            │
            ├── Battery
            ├── LiIonCell
            ├── LED
            └── Wire
```

### Business Logic Modules

| Module | Classes | Description |
|--------|---------|-------------|
| `wire_manager` | `WireManager` | Wire drawing, corner dragging, and orthogonal constraints |
| `viewmodel` | `CircuitViewModel` | Central state management, undo/redo, component operations |

### Views Package (`views/`)

NiceGUI-based UI components following the View layer of MVVM.

| Module | Classes | Description |
|--------|---------|-------------|
| `svg_renderer` | `SVGRenderer` | Generates SVG from circuit state, loads component templates |
| `palette` | `PaletteView` | Component selection toolbar with undo/redo buttons |
| `controls` | `ControlsView` | Clear, Save, Load buttons |
| `canvas_view` | `CircuitCanvasView` | Main canvas composing all views, handles mouse events |
| `main` | `run()`, `index()` | NiceGUI application entry point |

### Assets (`assets/components/`)

SVG template files for component rendering:
- `battery.svg`, `battery_mini.svg` - 9V battery graphics
- `liion_cell.svg`, `liion_cell_mini.svg` - Li-Ion cell graphics
- `led.svg`, `led_mini.svg` - LED graphics

## Data Flow

```
┌─────────────┐     Mouse/Keyboard      ┌──────────────┐
│    User     │ ──────Events──────────► │  canvas_view │
└─────────────┘                         └──────────────┘
                                               │
                                               │ Calls methods
                                               ▼
                                       ┌───────────────┐
                                       │  viewmodel    │
                                       │               │
                                       │ - place_      │
                                       │   component() │
                                       │ - delete_     │
                                       │   object()    │
                                       │ - undo/redo() │
                                       └───────────────┘
                                         │           │
                              Wire ops   │           │  Updates
                                         ▼           ▼
                               ┌──────────────┐  ┌─────────┐
                               │ wire_manager │  │ Circuit │
                               └──────────────┘  │ (model) │
                                                 └─────────┘
                                                      │
                                           Notifies   │
                                           change     │
                                               ┌──────┘
                                               ▼
                                       ┌───────────────┐
                                       │ svg_renderer  │
                                       │               │
                                       │ render()      │
                                       └───────────────┘
                                               │
                                               │ SVG string
                                               ▼
                                       ┌───────────────┐
                                       │  canvas_view  │
                                       │               │
                                       │ Updates       │
                                       │ interactive_  │
                                       │ image         │
                                       └───────────────┘
```

## Key Design Patterns

### 1. Discriminated Unions (Pydantic)

Components use Pydantic's discriminated unions for type-safe serialization:

```python
Component = Annotated[
    Battery | LiIonCell | LED | Wire,
    Discriminator("object_type"),
]
```

This enables correct deserialization during undo/redo operations.

### 2. Property-Based Polymorphism

Instead of `isinstance` checks, components expose properties:
- `has_connections` - Whether component has connection points
- `connection_points` - List of connection points
- `display_name` - Human-readable name from ObjectType enum

### 3. Observer Pattern

The ViewModel notifies Views of changes via callbacks:

```python
self._on_change_callbacks: list[Callable[[], None]] = []
```

### 4. Factory Pattern

`Circuit.add_object()` creates components by ObjectType:

```python
circuit.add_object(ObjectType.BATTERY, position=Point(100, 100))
```

## File Structure

```
src/entropy_sim/
├── __init__.py          # Public API exports
├── __main__.py          # CLI entry point
├── _version.py          # Version (setuptools_scm)
├── object_type.py       # ObjectType enum
├── viewmodel.py         # State management
├── wire_manager.py      # Wire operations
├── assets/
│   └── components/      # SVG templates
│       ├── battery.svg
│       ├── battery_mini.svg
│       ├── led.svg
│       ├── led_mini.svg
│       ├── liion_cell.svg
│       └── liion_cell_mini.svg
├── models/
│   ├── __init__.py      # Model exports
│   ├── battery.py       # Battery class
│   ├── circuit.py       # Circuit container
│   ├── circuit_base.py  # CircuitBase abstract class
│   ├── led.py           # LED class
│   ├── liion_cell.py    # LiIonCell class
│   ├── point.py         # Point, ConnectionPoint
│   └── wire.py          # Wire, WirePoint
└── views/
    ├── __init__.py      # View exports
    ├── canvas_view.py   # Main canvas
    ├── controls.py      # Button controls
    ├── main.py          # App entry
    ├── palette.py       # Component palette
    └── svg_renderer.py  # SVG generation
```

## Dependencies

### External

| Package | Purpose |
|---------|---------|
| `pydantic>=2.0` | Data validation)and JSON serialization |
| `nicegui>=1.4` | Web UI framework |

### Development

| Package | Purpose |
|---------|---------|
| `pytest` | Testing |
| `ruff` | Linting |
| `pyright` | Type checking |
| `tox` | Test automation |

## Extension Points

To add a new component type:

1. Add entry to `ObjectType` enum in `object_type.py`
2. Create new model class in `models/` extending `CircuitBase`
3. Add to `Component` union type in `models/circuit.py`
4. Add SVG template to `assets/components/`
5. Add rendering method to `SVGRenderer`
6. Add palette item in `PaletteView`
