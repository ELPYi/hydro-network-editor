# Hydro Network Editor

A desktop application for visually creating and editing hydrological network models. Built with Python and PyQt6.

## Features

- **Visual Network Canvas** - Drag-and-drop interface for building hydrological networks
- **Element Types** - Subbasins, reaches, nodes, diversions, and connection lines
- **Properties Editing** - Configure element parameters via dialogs and a properties panel
- **Subbasin Parameters** - Dedicated dialogs for subbasin configuration and tabular data entry
- **Save / Load** - Serialize and deserialize network models to file
- **Element Palette** - Sidebar palette for quick access to network elements

## Requirements

- Python 3.12+
- PyQt6

## Installation

```bash
pip install PyQt6
```

## Usage

```bash
python main.py
```

## Project Structure

```
hydro_network_editor/
├── main.py                  # Application entry point
└── app/
    ├── main_window.py       # Main window and menu/toolbar setup
    ├── canvas/
    │   ├── network_scene.py # QGraphicsScene for the network
    │   ├── network_view.py  # QGraphicsView with pan/zoom
    │   └── items/           # Graphical items (subbasin, reach, node, etc.)
    ├── dialogs/             # Property and parameter dialogs
    ├── model/
    │   ├── network_model.py # Core data model
    │   └── serializer.py    # Save/load logic
    └── palette/
        ├── element_palette.py   # Drag-and-drop element palette
        └── properties_panel.py  # Properties inspector panel
```
