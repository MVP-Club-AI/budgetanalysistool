#!/usr/bin/env python3
"""
Generate a custom icon for BudgetTracker app
"""

from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

def create_budget_icon(size=256):
    """Create a modern budget tracker icon."""

    # Create image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Colors (matching dashboard theme)
    bg_dark = (15, 15, 15, 255)       # #0f0f0f
    accent_green = (74, 222, 128, 255) # #4ade80
    accent_cyan = (6, 182, 212, 255)   # #06b6d4
    accent_purple = (139, 92, 246, 255) # #8b5cf6
    white = (255, 255, 255, 255)

    # Draw rounded rectangle background
    padding = 16
    corner_radius = 48

    # Main background - dark with subtle gradient effect
    for i in range(size - padding * 2):
        alpha = 255
        r = int(15 + (i / size) * 10)
        g = int(15 + (i / size) * 5)
        b = int(25 + (i / size) * 15)
        draw.line([(padding, padding + i), (size - padding, padding + i)], fill=(r, g, b, alpha))

    # Draw rounded corners (mask out corners)
    # Create a mask for rounded rectangle
    mask = Image.new('L', (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [padding, padding, size - padding, size - padding],
        radius=corner_radius,
        fill=255
    )

    # Apply mask
    img.putalpha(mask)

    # Redraw on masked image
    draw = ImageDraw.Draw(img)

    # Draw bar chart
    bar_width = 28
    bar_spacing = 12
    bar_bottom = size - 70
    bars_start_x = 50

    bar_heights = [80, 120, 60, 140, 100]  # Varied heights
    bar_colors = [accent_purple, accent_cyan, accent_purple, accent_green, accent_cyan]

    for i, (height, color) in enumerate(zip(bar_heights, bar_colors)):
        x = bars_start_x + i * (bar_width + bar_spacing)
        # Draw bar with slight gradient
        for h in range(height):
            # Gradient from darker to lighter
            factor = 0.6 + (h / height) * 0.4
            r = int(color[0] * factor)
            g = int(color[1] * factor)
            b = int(color[2] * factor)
            draw.line([(x, bar_bottom - h), (x + bar_width, bar_bottom - h)], fill=(r, g, b, 255))

        # Rounded top
        draw.ellipse([x, bar_bottom - height - 5, x + bar_width, bar_bottom - height + 10], fill=color)

    # Draw dollar sign
    dollar_x = size - 75
    dollar_y = 55

    # Dollar sign background circle
    circle_radius = 35
    draw.ellipse(
        [dollar_x - circle_radius, dollar_y - circle_radius,
         dollar_x + circle_radius, dollar_y + circle_radius],
        fill=accent_green
    )

    # Draw $ symbol
    # Using basic shapes since we may not have fonts
    s_width = 4

    # Top curve of S
    draw.arc([dollar_x - 15, dollar_y - 20, dollar_x + 15, dollar_y], start=180, end=0, fill=bg_dark, width=s_width)
    # Bottom curve of S
    draw.arc([dollar_x - 15, dollar_y - 5, dollar_x + 15, dollar_y + 15], start=0, end=180, fill=bg_dark, width=s_width)
    # Connecting line
    draw.line([(dollar_x + 12, dollar_y - 10), (dollar_x - 12, dollar_y + 5)], fill=bg_dark, width=s_width)
    # Vertical line through
    draw.line([(dollar_x, dollar_y - 25), (dollar_x, dollar_y + 20)], fill=bg_dark, width=3)

    # Draw trend line (upward)
    trend_points = [
        (45, bar_bottom - 90),
        (85, bar_bottom - 110),
        (125, bar_bottom - 85),
        (165, bar_bottom - 130),
        (205, bar_bottom - 120),
    ]

    # Draw line
    for i in range(len(trend_points) - 1):
        draw.line([trend_points[i], trend_points[i + 1]], fill=white, width=3)

    # Draw dots on trend line
    for point in trend_points:
        draw.ellipse([point[0] - 5, point[1] - 5, point[0] + 5, point[1] + 5], fill=white)

    return img

def save_as_ico(img, filepath):
    """Save image as ICO file with multiple sizes."""
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]

    icons = []
    for size in sizes:
        resized = img.resize(size, Image.LANCZOS)
        icons.append(resized)

    # Save as ICO
    icons[0].save(
        filepath,
        format='ICO',
        sizes=[(s[0], s[1]) for s in sizes],
        append_images=icons[1:]
    )

def main():
    print("Creating BudgetTracker icon...")

    # Create icon
    icon = create_budget_icon(256)

    # Save paths
    project_dir = Path(__file__).parent.parent
    ico_path = project_dir / "BudgetTracker.ico"
    png_path = project_dir / "BudgetTracker.png"

    # Save as ICO
    save_as_ico(icon, ico_path)
    print(f"ICO saved: {ico_path}")

    # Also save as PNG for preview
    icon.save(png_path, 'PNG')
    print(f"PNG saved: {png_path}")

    print("\nIcon created successfully!")

if __name__ == "__main__":
    main()
