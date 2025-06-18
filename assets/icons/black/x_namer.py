from pathlib import Path

# Get current directory
current_dir = Path.cwd()

# List all .svg files
svg_files: list[Path]= list(current_dir.glob("*.svg"))

# Print paths
with open("xtemp.txt", "w") as file:
    for svg in svg_files:
        name = svg.stem
        name = name.removesuffix("-svgrepo-com")
        keyword = name.replace("-", "_")
        keyword = keyword.upper()
        file.write(f"{keyword} = \"{name}\"\n")
