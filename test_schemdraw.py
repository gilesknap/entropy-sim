#!/usr/bin/env python3
"""Test schemdraw component rendering."""

import schemdraw
import schemdraw.elements as elm

# Test rendering a battery
with schemdraw.Drawing(show=False) as d:
    d.config(unit=2)  # Size units
    battery = d.add(elm.Battery())

# Get SVG as string
svg_string = d.get_imagedata("svg")
print("Battery SVG:")
print(svg_string[:500])  # First 500 chars
print("\n---\n")

# Test rendering an LED
with schemdraw.Drawing(show=False) as d:
    d.config(unit=2)
    led = d.add(elm.LED())

svg_string = d.get_imagedata("svg")
print("LED SVG:")
print(svg_string[:500])
print("\n---\n")

# Check what elements are available
print("Available components:")
for name in dir(elm):
    if not name.startswith("_") and name[0].isupper():
        print(f"  - {name}")
