from flask import Flask, request, jsonify
from flask_cors import CORS
import platform
import tempfile
import os
import win32print
import win32api
import logging
import requests

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)

def print_using_win32(content):
    if platform.system() != "Windows":
        raise Exception("Only supported on Windows")

    # Check if the printer is available
    printers = [printer[2] for printer in win32print.EnumPrinters(
        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    )]

    PRINTER_NAME = printers[0]
    app.logger.info(f"Detected default printer: {PRINTER_NAME}")

    # Create a temporary text file for printing
    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp:
        tmp.write(content)
        tmp_file_path = tmp.name

    try:
        # Use ShellExecute to print the file with the hardcoded printer
        print(f"Printing using printer '{PRINTER_NAME}': {tmp_file_path}")
        win32api.ShellExecute(
            0,
            "print",
            tmp_file_path,
            f'"/d:{PRINTER_NAME}"',
            ".",
            0
        )
    finally:
        # Delay before deleting to avoid race condition
        import time
        time.sleep(5)
        os.remove(tmp_file_path)

def print_receipt(content, printer):
    if platform.system() != "Windows":
        raise Exception("Only supported on Windows")

    # Get the default or target Epson printer
    printers = [printer[2] for printer in win32print.EnumPrinters(
        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    )]
    app.logger.info(f"Detected default printer: {printers}")

    printer_name = None
    for p in printers:
        if printer in p:
            printer_name = p
            break 

    if not printer_name:
        raise Exception(f"{printer} printer not found")
    # printer_name = printers[0] 

    handle = win32print.OpenPrinter(printer_name)
    try:
        info = win32print.GetPrinter(handle, 2)  # PRINTER_INFO_2
        port_name = info['pPortName']  # This might include the IP address
        app.logger.info(f"Detected default printer port: {port_name}")
    finally:
        win32print.ClosePrinter(handle)

   #  # Send raw data directly to printer
    handle = win32print.OpenPrinter(printer_name)
    try:
        job = win32print.StartDocPrinter(handle, 1, ("Receipt", None, "RAW"))
        win32print.StartPagePrinter(handle)
        win32print.WritePrinter(handle, content.encode("utf-8"))
        win32print.EndPagePrinter(handle)
        win32print.EndDocPrinter(handle)
    finally:
        win32print.ClosePrinter(handle)

@app.route('/print', methods=['POST'])
def print_text():
    data = request.get_json()
    content = data.get("content", "").strip()
    printer = data.get("printer","").strip()

    if not content:
        return jsonify({"error": "Content to print is required"}), 400

    try:
        print_receipt(content, printer)
        return jsonify({"message": f"Printed successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)