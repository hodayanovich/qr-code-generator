#!/usr/bin/env python3
import base64
import io
import os

from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
import qrcode
from qrcode.image.svg import SvgImage
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Create uploads directory
os.makedirs('uploads', exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def hex_or_default(value: str, default: str) -> str:
    """Very small sanity check for hex colors."""
    if not value:
        return default
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    if len(value) not in (4, 7):
        return default
    return value


def png_to_base64(img) -> str:
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("ascii")
    return f"data:image/png;base64,{img_base64}"


def svg_to_base64(svg_bytes: bytes) -> str:
    img_base64 = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{img_base64}"


def apply_style_preset(style_preset: str, fg_color: str, bg_color: str):
    """
    Style presets for quick classy looks.
    """
    style_preset = style_preset or "custom"
    
    presets = {
        "gold": ("#b38b1b", "#faf5e6"),  # rich gold on warm ivory
        "silver": ("#6f7c89", "#f5f5f7"),  # steel on cool grey
        "wedding_ivory": ("#C6A667", "#FBF7F2"),  # elegant wedding
        "birthday": ("#E63946", "#F8EDFF"),  # festive birthday
        "minimal_tech": ("#000000", "#FFFFFF"),  # clean professional
        "craft_beer": ("#8B4513", "#FFF8DC"),  # warm craft aesthetic
    }
    
    if style_preset in presets:
        return presets[style_preset]
    
    return fg_color, bg_color


def make_circular(img):
    """Convert square image to circular with transparent background."""
    size = img.size
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    
    output = ImageOps.fit(img, size, centering=(0.5, 0.5))
    output = output.convert('RGBA')
    output.putalpha(mask)
    return output


def add_minimal_personalization(img, content_type, content, fg_color, bg_color):
    """MINIMAL MODE: Clean placement below QR."""
    width, height = img.size
    new_height = height + 100
    canvas = Image.new('RGB', (width, new_height), bg_color)
    canvas.paste(img, (0, 0))
    draw = ImageDraw.Draw(canvas)
    
    if content_type == "text" and content:
        # Clean typography centered below QR
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
            except:
                font = ImageFont.load_default()
        
        text = content.upper()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = height + (100 - text_height) // 2
        
        # Subtle shadow
        draw.text((x + 2, y + 2), text, fill=fg_color + "40", font=font)
        draw.text((x, y), text, fill=fg_color, font=font)
    
    elif content_type in ["logo", "image"] and content:
        # Small centered badge
        logo = content if isinstance(content, Image.Image) else Image.open(content)
        badge_size = int(width * 0.25)
        logo = logo.resize((badge_size, badge_size), Image.Resampling.LANCZOS)
        
        if content_type == "image":
            logo = make_circular(logo)
        
        logo_x = (width - badge_size) // 2
        logo_y = height + (100 - badge_size) // 2
        
        # Background circle
        draw.ellipse(
            [logo_x - 5, logo_y - 5, logo_x + badge_size + 5, logo_y + badge_size + 5],
            fill=bg_color
        )
        
        canvas.paste(logo, (logo_x, logo_y), logo if logo.mode == 'RGBA' else None)
    
    return canvas


def add_focal_personalization(img, content_type, content, fg_color, bg_color):
    """FOCAL POINT MODE: Large, prominent in center safe zone."""
    width, height = img.size
    draw = ImageDraw.Draw(img)
    center_x, center_y = width // 2, height // 2
    safe_radius = int(min(width, height) * 0.15)
    
    if content_type == "text" and content:
        # Large stylized initials in center
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 120)
            except:
                font = ImageFont.load_default()
        
        text = content.upper()[:3]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        circle_radius = max(text_width, text_height) // 2 + 20
        
        # Circular background
        draw.ellipse(
            [center_x - circle_radius, center_y - circle_radius,
             center_x + circle_radius, center_y + circle_radius],
            fill=bg_color,
            outline=fg_color,
            width=4
        )
        
        text_x = center_x - text_width // 2
        text_y = center_y - text_height // 2
        draw.text((text_x, text_y), text, fill=fg_color, font=font)
    
    elif content_type in ["logo", "image"] and content:
        # Circular logo/portrait in center
        logo = content if isinstance(content, Image.Image) else Image.open(content)
        logo_size = safe_radius * 2
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        logo = make_circular(logo)
        
        # Frame
        draw.ellipse(
            [center_x - logo_size // 2 - 10, center_y - logo_size // 2 - 10,
             center_x + logo_size // 2 + 10, center_y + logo_size // 2 + 10],
            fill=bg_color,
            outline=fg_color,
            width=6
        )
        
        logo_x = center_x - logo_size // 2
        logo_y = center_y - logo_size // 2
        img.paste(logo, (logo_x, logo_y), logo)
    
    return img


def add_easter_egg_personalization(img, content_type, content, fg_color):
    """EASTER EGG MODE: Subtle, hidden, discoverable."""
    width, height = img.size
    
    if content_type == "text" and content:
        draw = ImageDraw.Draw(img, 'RGBA')
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
        except:
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 8)
            except:
                font = ImageFont.load_default()
        
        text = content.upper()
        
        # Convert hex to RGBA with low alpha
        if fg_color.startswith('#'):
            r = int(fg_color[1:3], 16)
            g = int(fg_color[3:5], 16)
            b = int(fg_color[5:7], 16)
            subtle_color = (r, g, b, 80)
        else:
            subtle_color = (0, 0, 0, 80)
        
        # Multiple subtle placements
        positions = [
            (width - 80, height - 20),
            (20, height // 2),
            (width // 2 - 30, 20)
        ]
        
        for pos in positions:
            draw.text(pos, text, fill=subtle_color, font=font)
    
    elif content_type in ["logo", "image"] and content:
        # Watermark overlay
        logo = content if isinstance(content, Image.Image) else Image.open(content)
        watermark_size = int(min(width, height) * 0.4)
        logo = logo.resize((watermark_size, watermark_size), Image.Resampling.LANCZOS)
        
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        # Very low opacity
        alpha = logo.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(0.15)
        logo.putalpha(alpha)
        
        logo_x = (width - watermark_size) // 2
        logo_y = (height - watermark_size) // 2
        
        img = img.convert('RGBA')
        img.paste(logo, (logo_x, logo_y), logo)
        img = img.convert('RGB')
    
    return img


def decorate_png_qr(img, fg_color: str, add_frame: bool, personalization_mode: str,
                    content_type: str, content, bg_color: str):
    """Add decorations to PNG QR based on personalization mode."""
    img = img.copy()
    
    # Legacy frame (can be used with any mode)
    if add_frame:
        draw = ImageDraw.Draw(img)
        w, h = img.size
        size = min(w, h)
        margin = int(size * 0.035)
        rect = (margin, margin, w - margin, h - margin)
        width = max(2, int(size * 0.015))
        radius = int(size * 0.06)
        try:
            draw.rounded_rectangle(rect, radius=radius, outline=fg_color, width=width)
        except AttributeError:
            draw.rectangle(rect, outline=fg_color, width=width)
    
    # Apply personalization mode
    if personalization_mode == "minimal":
        img = add_minimal_personalization(img, content_type, content, fg_color, bg_color)
    elif personalization_mode == "focal":
        img = add_focal_personalization(img, content_type, content, fg_color, bg_color)
    elif personalization_mode == "easter_egg":
        img = add_easter_egg_personalization(img, content_type, content, fg_color)
    
    return img


def make_qr(
    data: str,
    box_size: int = 10,
    border: int = 4,
    fg_color: str = "#000000",
    bg_color: str = "#ffffff",
    transparent_bg: bool = False,
    image_format: str = "png",
    style_preset: str = "custom",
    add_frame: bool = False,
    personalization_mode: str = "none",
    content_type: str = "text",
    content = None,
) -> tuple[str, str]:
    """
    Generate a QR code and return (data_url, suggested_filename).
    """
    if not data:
        raise ValueError("No data provided")

    fg_color = hex_or_default(fg_color, "#000000")
    bg_color = hex_or_default(bg_color, "#ffffff")
    fg_color, bg_color = apply_style_preset(style_preset, fg_color, bg_color)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # SVG (no decorations)
    if image_format == "svg":
        img = qr.make_image(
            image_factory=SvgImage,
            fill_color=fg_color,
            back_color="transparent" if transparent_bg else bg_color,
        )
        buffer = io.BytesIO()
        img.save(buffer)
        svg_bytes = buffer.getvalue()
        data_url = svg_to_base64(svg_bytes)
        return data_url, "qr-code.svg"

    # PNG
    img = qr.make_image(fill_color=fg_color, back_color=bg_color).convert("RGBA")

    # Transparent background
    if transparent_bg:
        datas = img.getdata()
        new_data = []
        bg_pixel = datas[0]
        for pixel in datas:
            if pixel[:3] == bg_pixel[:3]:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(pixel)
        img.putdata(new_data)

    # Add decorations
    if add_frame or personalization_mode != "none":
        img = decorate_png_qr(img, fg_color, add_frame, personalization_mode,
                             content_type, content, bg_color)

    data_url = png_to_base64(img)
    return data_url, "qr-code.png"


@app.route("/", methods=["GET", "POST"])
def index():
    qr_data_url = None
    filename = None
    error = None

    # Default form values
    input_data = ""
    box_size = 10
    border = 4
    fg_color = "#000000"
    bg_color = "#ffffff"
    transparent_bg = False
    image_format = "png"
    style_preset = "classic"
    add_frame = True
    personalization_mode = "none"
    content_type = "text"
    initials = ""

    if request.method == "POST":
        input_data = request.form.get("data", "").strip()
        box_size = int(request.form.get("box_size", 10) or 10)
        border = int(request.form.get("border", 4) or 4)
        fg_color = request.form.get("fg_color", "#000000")
        bg_color = request.form.get("bg_color", "#ffffff")
        transparent_bg = bool(request.form.get("transparent_bg"))
        image_format = request.form.get("image_format", "png")
        style_preset = request.form.get("style_preset", "classic")
        add_frame = bool(request.form.get("add_frame"))
        personalization_mode = request.form.get("personalization_mode", "none")
        content_type = request.form.get("content_type", "text")
        initials = request.form.get("initials", "").strip()

        # Handle content based on type
        content = None
        
        if content_type == "text":
            content = initials
        elif content_type == "logo" and 'logo_upload' in request.files:
            file = request.files['logo_upload']
            if file and file.filename and allowed_file(file.filename):
                filename_safe = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_safe)
                file.save(filepath)
                content = filepath
        elif content_type == "image" and 'photo_upload' in request.files:
            file = request.files['photo_upload']
            if file and file.filename and allowed_file(file.filename):
                filename_safe = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename_safe)
                file.save(filepath)
                content = filepath

        try:
            qr_data_url, filename = make_qr(
                data=input_data,
                box_size=box_size,
                border=border,
                fg_color=fg_color,
                bg_color=bg_color,
                transparent_bg=transparent_bg,
                image_format=image_format,
                style_preset=style_preset,
                add_frame=add_frame,
                personalization_mode=personalization_mode,
                content_type=content_type,
                content=content,
            )
            
            # Clean up uploaded files
            if content and isinstance(content, str) and os.path.exists(content):
                os.remove(content)
                
        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        qr_data_url=qr_data_url,
        filename=filename,
        error=error,
        input_data=input_data,
        box_size=box_size,
        border=border,
        fg_color=fg_color,
        bg_color=bg_color,
        transparent_bg=transparent_bg,
        image_format=image_format,
        style_preset=style_preset,
        add_frame=add_frame,
        personalization_mode=personalization_mode,
        content_type=content_type,
        initials=initials,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
