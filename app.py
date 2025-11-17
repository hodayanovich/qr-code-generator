#!/usr/bin/env python3
import base64
import io
import os

from flask import Flask, render_template, request
import qrcode
from qrcode.image.svg import SvgImage
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)


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

    - gold: warm gold on soft ivory
    - silver: cool silver on light grey
    """
    style_preset = style_preset or "custom"
    if style_preset == "gold":
        fg_color = "#b38b1b"  # rich gold
        bg_color = "#faf5e6"  # warm ivory
    elif style_preset == "silver":
        fg_color = "#6f7c89"  # steel / slate
        bg_color = "#f5f5f7"  # cool light grey
    # "classic" just uses whatever user chose (defaults are black/white)
    return fg_color, bg_color


def decorate_png_qr(img, accent_color: str, initials: str, add_frame: bool):
    """
    Add an optional frame and center initials to a PNG QR.
    """
    img = img.copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    size = min(w, h)

    # Decorative frame
    if add_frame:
        margin = int(size * 0.035)
        rect = (margin, margin, w - margin, h - margin)
        width = max(2, int(size * 0.015))
        radius = int(size * 0.06)
        try:
            draw.rounded_rectangle(rect, radius=radius, outline=accent_color, width=width)
        except AttributeError:
            # Older Pillow: fall back to plain rectangle
            draw.rectangle(rect, outline=accent_color, width=width)

    # Center initials
    initials = (initials or "").strip()
    if initials:
        badge_w = int(size * 0.32)
        badge_h = int(size * 0.22)
        cx, cy = w // 2, h // 2
        left = cx - badge_w // 2
        top = cy - badge_h // 2
        right = cx + badge_w // 2
        bottom = cy + badge_h // 2

        # Semi-opaque light badge so the QR is still scannable
        badge_color = (255, 255, 255, 230)
        radius = int(badge_h * 0.45)
        try:
            draw.rounded_rectangle(
                (left, top, right, bottom),
                radius=radius,
                fill=badge_color,
                outline=None,
            )
        except AttributeError:
            draw.rectangle((left, top, right, bottom), fill=badge_color)

        # Font
        try:
            font_size = int(badge_h * 0.55)
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

        text = initials[:6].upper()
        tw, th = draw.textsize(text, font=font)
        tx = cx - tw / 2
        ty = cy - th / 2 - 2  # tiny vertical tweak
        draw.text((tx, ty), text, font=font, fill=accent_color)

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
    initials: str | None = None,
) -> tuple[str, str]:
    """
    Generate a QR code and return (data_url, suggested_filename).

    image_format: "png" or "svg"
    Decorations (frame/initials) are applied for PNG only.
    """
    if not data:
        raise ValueError("No data provided")

    fg_color = hex_or_default(fg_color, "#000000")
    bg_color = hex_or_default(bg_color, "#ffffff")

    # Apply preset (gold/silver/etc.)
    fg_color, bg_color = apply_style_preset(style_preset, fg_color, bg_color)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # safer for printing / logos
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # SVG (no decorations, but keeps colors)
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
    img = qr.make_image(
        fill_color=fg_color,
        back_color=bg_color,
    ).convert("RGBA")

    # Make background transparent if requested
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

    # Add frame / initials for PNG
    if add_frame or (initials or "").strip():
        img = decorate_png_qr(img, accent_color=fg_color, initials=initials, add_frame=add_frame)

    data_url = png_to_base64(img)
    return data_url, "qr-code.png"


@app.route("/", methods=["GET", "POST"])
def index():
    qr_data_url = None
    filename = None
    error = None

    # default form values
    input_data = ""
    box_size = 10
    border = 4
    fg_color = "#000000"
    bg_color = "#ffffff"
    transparent_bg = False
    image_format = "png"
    style_preset = "classic"
    add_frame = True
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
        initials = request.form.get("initials", "").strip()

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
                initials=initials,
            )
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
        initials=initials,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
