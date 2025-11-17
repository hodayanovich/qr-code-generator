# Static QR Code Generator

Simple CLI tool to generate **static QR codes** for URLs or any text.

A *static* QR code means the data (e.g. a Google Drive link) is encoded directly
into the QR. The QR itself never expires — it will keep working as long as the
underlying link stays valid.

## 🧰 Tech

- Python 3.8+
- [qrcode](https://pypi.org/project/qrcode/) + Pillow

## 🚀 Setup

```bash
git clone https://github.com/<your-username>/static-qr-generator.git
cd static-qr-generator

python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

pip install -r requirements.txt
