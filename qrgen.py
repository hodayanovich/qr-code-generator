#!/usr/bin/env python3
"""
Simple static QR code generator.

Usage:
    python qrgen.py --data "https://example.com" --output qr.png

This generates a static PNG QR code that never expires as long as the URL stays valid.
"""

import argparse
import os
import sys

import qrcode


def generate_qr(data: str, output_path: str, box_size: int = 10, border: int = 4) -> None:
    """
    Generate a static QR code PNG file.

    :param data: The string / URL to encode in the QR.
    :param output_path: Output file path for the PNG image.
    :param box_size: Size of each QR box in pixels.
    :param border: Border size (in boxes) around the QR code.
    """
    if not data:
        raise ValueError("No data provided to encode in QR code.")

    qr = qrcode.QRCode(
        version=None,         # automatically size the QR
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image()

    # Make sure target directory exists
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    img.save(output_path)
    print(f"✅ QR code saved to: {output_path}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Generate a static PNG QR code for a URL or any text."
    )
    parser.add_argument(
        "--data", "-d",
        required=True,
        help="The URL or text to encode in the QR code (e.g. a Google Drive link).",
    )
    parser.add_argument(
        "--output", "-o",
        default="qr.png",
        help="Output PNG file path (default: qr.png).",
    )
    parser.add_argument(
        "--box-size",
        type=int,
        default=10,
        help="Size of each QR box in pixels (default: 10).",
    )
    parser.add_argument(
        "--border",
        type=int,
        default=4,
        help="Border size in boxes around the QR (default: 4).",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        generate_qr(
            data=args.data,
            output_path=args.output,
            box_size=args.box_size,
            border=args.border,
        )
    except Exception as e:
        print(f"❌ Failed to generate QR code: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
