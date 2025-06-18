from pathlib import Path

import svgpathtools
from lxml import etree
import re


def remove_svg_margins(input_file, output_file, padding=0):
    """
    Remove margins from an SVG file by adjusting the viewBox and removing whitespace.

    Args:
        input_file (str): Path to input SVG file
        output_file (str): Path to save the modified SVG
        padding (float): Optional padding to retain around content
    """
    # Load paths and attributes using svgpathtools
    paths, _ = svgpathtools.svg2paths(input_file)

    # Parse SVG XML
    doc = etree.parse(input_file)
    root = doc.getroot()

    # Handle width/height/viewBox safely
    width = root.get("width")
    height = root.get("height")

    try:
        width = float(width.replace("px", "").replace("pt", "")) if width else 0
        height = float(height.replace("px", "").replace("pt", "")) if height else 0
    except ValueError:
        width = height = 0

    # Default viewBox if missing
    view_box = root.get("viewBox")
    if view_box:
        view_box_values = list(map(float, view_box.strip().split()))
    else:
        view_box_values = [0, 0, width, height]

    # Bounding box init
    min_x, max_x, min_y, max_y = float("inf"), float("-inf"), float("inf"), float("-inf")

    for path in paths:
        if path:
            bbox = path.bbox()  # returns (xmin, xmax, ymin, ymax)
            min_x = min(min_x, bbox[0])
            max_x = max(max_x, bbox[1])
            min_y = min(min_y, bbox[2])
            max_y = max(max_y, bbox[3])

    if min_x == float("inf"):
        # fallback
        min_x, min_y = 0, 0
        max_x, max_y = width or 100, height or 100

    # Add padding
    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding

    new_width = max_x - min_x
    new_height = max_y - min_y

    # Update SVG size and viewBox
    root.set("width", f"{new_width}")
    root.set("height", f"{new_height}")
    root.set("viewBox", f"{min_x} {min_y} {new_width} {new_height}")

    # Adjust 'translate' in transforms if present
    for elem in doc.iter():
        transform = elem.get("transform")
        if transform and "translate" in transform:
            matches = re.findall(r"translate\(([-\d\.]+)[,\s]+([-\d\.]+)\)", transform)
            for match in matches:
                tx, ty = map(float, match)
                new_tx = tx - min_x
                new_ty = ty - min_y
                new_transform = f"translate({new_tx},{new_ty})"
                transform = re.sub(r"translate\(([-\d\.]+)[,\s]+([-\d\.]+)\)", new_transform, transform)
                elem.set("transform", transform)

    # Write output
    doc.write(output_file, pretty_print=True, encoding="utf-8", xml_declaration=True)
    print(f"✅ Margins removed and saved: {output_file}")


# Example usage
if __name__ == "__main__":
    # input_svg = "input.svg"
    # output_svg = "output_no_margins.svg"

    input_svg = r"D:\Program\SD Front\assets\icons\black\stop-svgrepo-com.svg"
    output_svg = input_svg
    # remove_svg_margins(input_svg, output_svg)
    svg_dir = Path(r"/assets/icons/white")  # Or specify a directory like Path("icons")
    padding = 2  # Adjust padding if needed

    for svg_file in svg_dir.glob("*.svg"):
        remove_svg_margins(svg_file, svg_file, padding=1.35)
        print(f"SVG margins removed. Saved to {output_svg}")