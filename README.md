# Static QR Web

Tiny Flask web app to generate **static QR codes** for URLs or any text  
(e.g. Google Drive video links).

A *static* QR code encodes the data directly into the image.  
It never expires by itself – it works as long as the underlying URL is valid.

## 🧰 Stack

- Python 3.8+
- Flask
- qrcode + Pillow

## 🚀 Setup

```bash
git clone https://github.com/<your-username>/qr-web.git
cd qr-web

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
