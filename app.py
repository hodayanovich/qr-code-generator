#!/usr/bin/env python3
import base64
import io

from flask import Flask, render_template, request

import qrcode

app = Flask(__name__)


def generate_qr_image(data: str, box_size: int = 10, border: int = 4) -> str:
    """
    Generate a QR code image and return it as a base64-encoded PNG string.
    """
    if not data:
        raise ValueError("No data provided")

    qr = qrcode.QRCode(
        version=None,  # auto size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image()

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode to base64 for embedding in HTML
    img_base64 = base64.b64encode(buffer.read()).decode("ascii")
    return img_base64


@app.route("/", methods=["GET", "POST"])
def index():
    qr_data_url = None
    error = None
    input_data = ""
    box_size = 10
    border = 4

    if request.method == "POST":
        input_data = request.form.get("data", "").strip()
        box_size = int(request.form.get("box_size", 10) or 10)
        border = int(request.form.get("border", 4) or 4)

        try:
            img_base64 = generate_qr_image(
                data=input_data,
                box_size=box_size,
                border=border,
            )
            qr_data_url = f"data:image/png;base64,{img_base64}"
        except Exception as e:
            error = str(e)

    return render_template(
        "index.html",
        qr_data_url=qr_data_url,
        error=error,
        input_data=input_data,
        box_size=box_size,
        border=border,
    )


if __name__ == "__main__":
    # For local dev
    app.run(host="0.0.0.0", port=5000, debug=True)
