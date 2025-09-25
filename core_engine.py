import subprocess
from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
import json
import time
import sys
import os
import ctypes
import uuid
import io
import base64
import socket

# Imports for cryptography
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

# Imports for reportlab PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# --- Configuration ---
PROJECT_DIR = Path(__file__).parent
SDELETE_PATH = PROJECT_DIR / "sdelete64.exe"
PRIVATE_KEY_PATH = PROJECT_DIR / "private_key.pem"
PUBLIC_KEY_PATH = PROJECT_DIR / "public_key.pem"


# --- Certificate and Signature Functions ---
def generate_key_pair():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo))

def sign_certificate_data(data: dict) -> bytes:
    if not PRIVATE_KEY_PATH.exists():
        generate_key_pair()
    with open(PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    payload = json.dumps(data, sort_keys=True).encode('utf-8')
    return private_key.sign(payload)

def generate_pdf_certificate(certificate_data: dict, signature_hex: str) -> bytes:
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # --- Define Colors & Styles ---
    sih_blue = HexColor("#0033a0")
    dark_grey = HexColor("#2c3e50")
    light_grey = HexColor("#bdc3c7")
    text_color = HexColor("#34495e")

    # --- Draw Watermark ---
    p.saveState()
    p.setFont('Helvetica-Bold', 72)
    p.setFillColor(HexColor("#eeeeee"))
    p.translate(width / 2, height / 2)
    p.rotate(45)
    p.drawCentredString(0, 0, "CertiWipe")
    p.restoreState()

    # --- Header ---
    gradient_path = PROJECT_DIR / "header_gradient.jpg"
    if gradient_path.exists():
        p.drawImage(str(gradient_path), 0, height - 1 * inch, width=width, height=1 * inch)
    else:
        # Fallback to a solid color if no gradient image is found
        p.setFillColor(sih_blue)
        p.rect(0, height - 1 * inch, width, 1 * inch, stroke=0, fill=1)

    # Always draw the Centered Title
    p.setFont("Helvetica-Bold", 36)
    p.setFillColorRGB(1, 1, 1) # White
    p.drawCentredString(width / 2.0, height - 0.65 * inch, "CertiWipe")

    # --- Title ---
    p.setFont("Helvetica-Bold", 22)
    p.setFillColor(dark_grey)
    p.drawCentredString(width / 2.0, height - 1.75 * inch, "Certificate of Data Erasure")

    # --- Body Text ---
    p.setFont("Helvetica", 11)
    p.setFillColor(text_color)
    p.drawCentredString(width / 2.0, height - 2.2 * inch, "This document certifies the secure and irreversible erasure of the following data:")

    # --- Details Box ---
    box_y = height - 4.7 * inch
    p.setStrokeColor(light_grey)
    p.setLineWidth(1)
    p.roundRect(1 * inch, box_y, width - 2 * inch, 2.2 * inch, 10, stroke=1, fill=0)

    # --- Add New Information ---
    try:
        user_info = f"{os.getlogin()}@{socket.gethostname()}"
    except:
        user_info = "N/A"
    
    timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S Z', time.gmtime(certificate_data["timestamp"]))

    details = {
        "Wipe Target": certificate_data["target_details"],
        "Wipe Method": certificate_data["wipe_method"],
        "Timestamp (UTC)": timestamp_str,
        "Performed By": user_info,
        "Software Version": "1.0.0",
        "Certificate ID": certificate_data["certificate_id"]
    }

    text = p.beginText(1.25 * inch, box_y + 1.8 * inch)
    text.setFont("Helvetica-Bold", 11)
    text.setLeading(24)
    
    for key, value in details.items():
        text.setFont("Helvetica-Bold", 11)
        text.textOut(f"{key}: ")
        text.setFont("Courier", 11)
        text.textOut(value)
        text.textLine('') 

    p.drawText(text)
    
    # --- Signature Section ---
    sig_y = height - 6.8 * inch
    p.setFont("Helvetica-Bold", 12)
    p.setFillColor(dark_grey)
    p.drawCentredString(width/2.0, sig_y, "Digital Signature (Ed25519)")

    p.setFont("Courier", 10)
    p.setFillColor(text_color)
    sig1 = signature_hex[:64]
    sig2 = signature_hex[64:]
    p.drawCentredString(width/2.0, sig_y - 0.35 * inch, sig1)
    p.drawCentredString(width/2.0, sig_y - 0.55 * inch, sig2)

    # --- Footer ---
    p.setFillColor(dark_grey)
    p.rect(0, 0, width, 0.75 * inch, stroke=0, fill=1)
    p.setFont("Helvetica", 10)
    p.setFillColor(light_grey)
    p.drawCentredString(width / 2.0, 0.4 * inch, "Authenticity of this certificate can be verified using the CertiWipe public key.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()

# --- System Functions ---
def check_admin_privileges():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except AttributeError:
        is_admin = os.getuid() == 0
    return is_admin

def get_drive_list():
    try:
        status_output = subprocess.run(["manage-bde", "-status"], capture_output=True, text=True, check=True, shell=True, encoding='utf-8').stdout
        drives = []
        for line in status_output.splitlines():
            if "Volume" in line and ":" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    drive_letter = parts[0].strip().replace("Volume ", "")
                    drive_name = parts[1].strip()
                    if drive_letter and len(drive_letter) == 1:
                        drives.append({"letter": drive_letter, "name": drive_name})
        return drives
    except Exception as e:
        return {"error": str(e)}

# --- WIPE EXECUTION FUNCTIONS ---

def start_file_wipe(file_paths: list):
    try:
        total_files = len(file_paths)
        for i, file_path_str in enumerate(file_paths):
            file_path = Path(file_path_str)
            if not file_path.exists():
                print(json.dumps({"type": "progress", "message": f"Skipping non-existent file: {file_path.name}"}))
                continue
            print(json.dumps({"type": "progress", "message": f"Wiping file ({i+1}/{total_files}): {file_path.name}..."}))
            # UPDATED: Added -accepteula flag
            command = [str(SDELETE_PATH), "-accepteula", "-p", "3", "-q", str(file_path)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                raise Exception(f"SDelete failed for {file_path.name}: {stderr}")
        
        certificate_data = {"certificate_id": str(uuid.uuid4()), "timestamp": int(time.time()),"target_details": f"{total_files} file(s)","wipe_method": "sdelete (3 passes)"}
        signature = sign_certificate_data(certificate_data)
        pdf_bytes = generate_pdf_certificate(certificate_data, signature.hex())
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        print(json.dumps({"type": "success", "message": f"{total_files} file(s) wiped successfully.", "pdf_base64": pdf_base64}))
    except Exception as e:
        print(json.dumps({"type": "error", "message": str(e)}))

def start_folder_wipe(folder_path_str: str):
    try:
        folder_path = Path(folder_path_str)
        if not folder_path.exists() or not folder_path.is_dir():
            print(json.dumps({"type": "error", "message": f"Folder not found: {folder_path_str}"}))
            return

        print(json.dumps({"type": "progress", "message": f"Wiping all contents of folder: {folder_path.name}..."}))
        # UPDATED: Create a target with a wildcard to wipe contents INSIDE the folder
        wipe_target = os.path.join(folder_path_str, '*')
        # UPDATED: The command now uses the correct wipe_target
        command = [str(SDELETE_PATH), "-accepteula", "-p", "3", "-s", "-q", wipe_target]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            if "Access is denied" in stderr:
                raise Exception(f"SDelete failed for folder {folder_path.name}: Access is denied. Please ensure no applications (like OneDrive) are using the folder and try again.")
            else:
                raise Exception(f"SDelete failed for folder {folder_path.name}: {stderr}")
        
        # New code added to try to remove the folder and handle potential errors.
        try:
            print(json.dumps({"type": "progress", "message": "All folder contents wiped. Attempting to remove the now-empty folder..."}))
            os.rmdir(folder_path_str)
            print(json.dumps({"type": "progress", "message": "Folder removed successfully."}))
        except OSError as e:
            # Handle the case where the folder cannot be removed.
            # This can happen even if empty, due to lingering file handles, etc.
            print(json.dumps({"type": "progress", "message": f"WARNING: Could not remove folder '{folder_path.name}' after wiping its contents. Error: {e}"}))
            print(json.dumps({"type": "progress", "message": "The folder may be in use by another program. You may need to delete it manually."}))
            
        print(json.dumps({"type": "progress", "message": "Folder wipe complete. Generating certificate..."}))
        certificate_data = {"certificate_id": str(uuid.uuid4()), "timestamp": int(time.time()),"target_details": f"Folder: {folder_path.name}","wipe_method": "sdelete (3 passes, recursive)"}
        signature = sign_certificate_data(certificate_data)
        pdf_bytes = generate_pdf_certificate(certificate_data, signature.hex())
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        print(json.dumps({"type": "success", "message": "Folder wiped successfully.", "pdf_base64": pdf_base64}))
    except Exception as e:
        print(json.dumps({"type": "error", "message": str(e)}))

# UPDATED: Replaced with the real free space wipe function
def start_free_space_wipe(drive_letter: str):
    try:
        target_path = f"{drive_letter}:\\"
        if not Path(target_path).exists():
            print(json.dumps({"type": "error", "message": f"Drive {drive_letter}: not found."}))
            return

        print(json.dumps({"type": "progress", "message": f"Starting free space wipe on drive {drive_letter}:\\."}))
        print(json.dumps({"type": "progress", "message": "This will take a very long time depending on drive size."}))
        
        # This is the command for a real free-space wipe with 3 passes.
        command = [str(SDELETE_PATH), "-accepteula", "-c", "-p", "3", "-q", target_path]
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', bufsize=1)

        # Read stdout line by line to get live progress from sdelete
        for line in iter(process.stdout.readline, ''):
            if line:
                # SDelete prints progress, so we can pass it along
                print(json.dumps({"type": "progress", "message": line.strip()}))
        
        process.stdout.close()
        process.wait()

        if process.returncode != 0:
            stderr_output = process.stderr.read()
            raise Exception(f"SDelete process failed. Error: {stderr_output}")

        print(json.dumps({"type": "progress", "message": "Free space wipe complete. Generating certificate..."}))
        
        certificate_data = {
            "certificate_id": str(uuid.uuid4()), 
            "timestamp": int(time.time()),
            "target_details": f"Drive Free Space on {drive_letter}:",
            "wipe_method": "sdelete (3 passes - clean free space)"
        }
        signature = sign_certificate_data(certificate_data)
        pdf_bytes = generate_pdf_certificate(certificate_data, signature.hex())
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        print(json.dumps({
            "type": "success", 
            "message": f"Free space on drive {drive_letter}: wiped successfully.",
            "pdf_base64": pdf_base64
        }))

    except Exception as e:
        print(json.dumps({"type": "error", "message": str(e)}))


# --- Main execution block ---
if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command == "get_drives": print(json.dumps(get_drive_list()))
    elif command == "check_admin": print(json.dumps({"is_admin": check_admin_privileges()}))
    elif command == "wipe_files":
        files_to_wipe = sys.argv[2:]
        if files_to_wipe: start_file_wipe(files_to_wipe)
        else: print(json.dumps({"error": "No files provided to wipe."}))
    elif command == "wipe_folder":
        folder_to_wipe = sys.argv[2] if len(sys.argv) > 2 else None
        if folder_to_wipe: start_folder_wipe(folder_to_wipe)
        else: print(json.dumps({"error": "No folder provided to wipe."}))
    elif command == "start_free_space_wipe":
        drive_letter = sys.argv[2] if len(sys.argv) > 2 else None
        if drive_letter: start_free_space_wipe(drive_letter)
        else: print(json.dumps({"error": "No drive letter provided."}))
    else: print(json.dumps({"error": f"No or unknown command provided: {command}"}))