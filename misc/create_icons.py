import os

from PIL import Image, ImageDraw


def create_icon(filename, draw_func):
    # Canvas: 44x44 (Retina @2x for 22pt logical height)
    size = (44, 44)
    # Background: Transparent
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw the icon content
    draw_func(draw, size)
    
    # Save
    path = os.path.join("src/icons", filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)
    print(f"Generated: {path}")

def draw_mic(draw, size):
    # Color: Pure Black
    fill = (0, 0, 0, 255)
    w, h = size
    
    # Mic body (capsule)
    # Center x: 22
    # Body width: 10px, Body height: 20px
    body_w = 10
    body_h = 20
    x1 = (w - body_w) // 2
    y1 = 8 # Top padding
    x2 = x1 + body_w
    y2 = y1 + body_h
    draw.rounded_rectangle([x1, y1, x2, y2], radius=5, fill=fill)
    
    # Mic stand (U-shape)
    # Line width: 2px
    stand_y_start = y1 + 12
    stand_y_end = y2 + 2
    stand_w = 18
    sx1 = (w - stand_w) // 2
    sx2 = sx1 + stand_w
    
    # Draw U shape using an arc? Or thick lines.
    # Let's use lines for pixel perfection
    # Left vertical
    draw.line([sx1, stand_y_start, sx1, stand_y_end], fill=fill, width=2)
    # Right vertical
    draw.line([sx2, stand_y_start, sx2, stand_y_end], fill=fill, width=2)
    # Bottom curve (simplified as a line for now or we can do an arc)
    draw.line([sx1, stand_y_end, sx2, stand_y_end], fill=fill, width=2)
    
    # Base vertical line
    base_h = 4
    bx = w // 2
    by1 = stand_y_end
    by2 = by1 + base_h
    draw.line([bx, by1, bx, by2], fill=fill, width=2)
    
    # Base horizontal line
    base_w = 12
    bHx1 = (w - base_w) // 2
    bHx2 = bHx1 + base_w
    draw.line([bHx1, by2, bHx2, by2], fill=fill, width=2)

def draw_rec(draw, size):
    # Stop square (or circle)
    fill = (0, 0, 0, 255)
    w, h = size
    
    # A rounded square (Stop button style)
    rw = 18
    rh = 18
    x1 = (w - rw) // 2
    y1 = (h - rh) // 2
    x2 = x1 + rw
    y2 = y1 + rh
    draw.rounded_rectangle([x1, y1, x2, y2], radius=3, fill=fill)

def draw_process(draw, size):
    # Three dots ...
    fill = (0, 0, 0, 255)
    w, h = size
    
    dot_size = 6
    spacing = 4
    
    total_w = (dot_size * 3) + (spacing * 2)
    start_x = (w - total_w) // 2
    y1 = (h - dot_size) // 2
    y2 = y1 + dot_size
    
    for i in range(3):
        x1 = start_x + (i * (dot_size + spacing))
        x2 = x1 + dot_size
        draw.ellipse([x1, y1, x2, y2], fill=fill)

def draw_success(draw, size):
    # Checkmark
    fill = (0, 0, 0, 255)
    w, h = size
    
    # Simplified checkmark points
    # Start (left) -> Middle (bottom) -> End (right-top)
    points = [
        (10, 22),
        (18, 30),
        (34, 14)
    ]
    draw.line(points, fill=fill, width=3, joint="curve")

if __name__ == "__main__":
    create_icon("icon_idle_Template.png", draw_mic)
    create_icon("icon_rec_Template.png", draw_rec)
    create_icon("icon_process_Template.png", draw_process)
    create_icon("icon_success_Template.png", draw_success)
