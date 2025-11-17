#!/usr/bin/env python3
import base64
import io
import os

from flask import Flask, render_template, request
import qrcode
from qrcode.image.svg import SvgImage


app = Flask(__name__)


def hex_or_default(value: str, default: str) -> str:
    """Very small sanity check for hex colors."""
    if not value:
        return default
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    # naive length check, but enough for our simple UI
    if len(value) not in (4, 7):
        return default
    return value


def png_to_base64(img) -> str:
    """Return a base64 PNG data URI for a PIL image."""
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode("ascii")
    return f"data:image/png;base64,{img_base64}"


def svg_to_base64(svg_bytes: bytes) -> str:
    """Return a base64 SVG data URI."""
    img_base64 = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{img_base64}"


def make_qr(
    data: str,
    box_size: int = 10,
    border: int = 4,
    fg_color: str = "#000000",
    bg_color: str = "#ffffff",
    transparent_bg: bool = False,
    image_format: str = "png",
) -> tuple[str, str]:
    """
    Generate a QR code and return (data_url, suggested_filename).

    image_format: "png" or "svg"
    """
    if not data:
        raise ValueError("No data provided")

    fg_color = hex_or_default(fg_color, "#000000")
    bg_color = hex_or_default(bg_color, "#ffffff")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # safer for printing / logos
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # SVG output
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

    # PNG output
    img = qr.make_image(
        fill_color=fg_color,
        back_color=bg_color,
    ).convert("RGBA")

    if transparent_bg:
        # Turn the background pixels into fully transparent
        datas = img.getdata()
        new_data = []
        # assume background is the first pixel
        bg_pixel = datas[0]
        for pixel in datas:
            if pixel[:3] == bg_pixel[:3]:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(pixel)
        img.putdata(new_data)

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

    if request.method == "POST":
        input_data = request.form.get("data", "").strip()
        box_size = int(request.form.get("box_size", 10) or 10)
        border = int(request.form.get("border", 4) or 4)
        fg_color = request.form.get("fg_color", "#000000")
        bg_color = request.form.get("bg_color", "#ffffff")
        transparent_bg = bool(request.form.get("transparent_bg"))
        image_format = request.form.get("image_format", "png")

        try:
            qr_data_url, filename = make_qr(
                data=input_data,
                box_size=box_size,
                border=border,
                fg_color=fg_color,
                bg_color=bg_color,
                transparent_bg=transparent_bg,
                image_format=image_format,
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
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
