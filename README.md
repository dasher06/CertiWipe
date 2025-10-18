<div align="center">
  <h1>CertiWipe 🛡️</h1>
  <p><strong>Secure Data Erasure with a Verifiable, Tamper-Proof Audit Trail.</strong></p>
</div>

---

**CertiWipe** is a professional-grade data sanitization utility for Windows that **permanently and irreversibly erases** sensitive information. By combining a sleek, modern user interface built with Electron with a powerful and robust Python backend, it makes secure data destruction both accessible and reliable.

Its standout feature is the generation of a unique, **digitally signed PDF certificate of erasure** for every operation. This provides an undeniable, tamper-proof audit trail, offering verifiable proof that your data has been forensically wiped and is completely unrecoverable.

---

## 🤔 Why CertiWipe?

In an age where data is currency, simply "deleting" a file is not enough. Standard deletion only removes the pointer to the data, leaving the actual information intact and easily recoverable. CertiWipe addresses this critical security gap.

* **Beyond Deletion, Towards Destruction:** We don't just delete; we sanitize. Using a multi-pass overwrite technique that adheres to recognized standards, CertiWipe ensures that once your data is gone, it's gone for good.

* **Absolute Proof, Not Just a Promise:** Other tools might erase your data, but CertiWipe provides proof. Our unique, cryptographically signed certificates offer an unprecedented level of assurance, creating a verifiable audit trail perfect for business compliance or personal peace of mind.

* **Elegant & Simple:** Powerful security tools are often complex. We've leveraged the power of Electron to build an intuitive and visually appealing interface, making enterprise-grade data sanitization accessible to everyone, regardless of technical skill.

---

## ✨ Key Features

* ### 🗑️ **Secure Sanitization Engine**
    CertiWipe uses the industry-respected **Microsoft Sysinternals `SDelete`** tool as its core engine. Every wipe operation performs a **3-pass overwrite**, a method compliant with the DoD 5220.22-M standard, ensuring your data is forensically unrecoverable.

* ### 🗂️ **Multiple Wipe Modes**
    Flexibility is key. CertiWipe provides three distinct modes to suit your needs:
    * **File Mode:** Select one or more specific files from anywhere on your system.
    * **Folder Mode:** Target an entire folder and all its contents for complete removal.
    * **Drive Free Space Mode:** Sanitize the free space on a selected drive to destroy remnants of previously deleted files.

* ### 📄 **Tamper-Proof Certificates**
    This is the core of CertiWipe's commitment to trust and verification.
    * **Cryptographic Signature:** Every PDF certificate is digitally signed using the modern and highly secure **Ed25519** algorithm.
    * **Guaranteed Authenticity:** The signature is generated using a private key. On first run, the application automatically generates a unique key pair (`private_key.pem` and `public_key.pem`) if one doesn't exist, ensuring your installation has a unique signature identity.
    * **Undeniable Audit Trail:** The certificate serves as a permanent, verifiable record of the sanitization event, perfect for corporate data disposal policies, IT asset decommissioning, or simply proving a sensitive file was destroyed.

* ### 🖥️ **Modern & User-Friendly Interface**
    Built with Electron, the UI is clean, responsive, and easy to navigate. A live status log provides real-time feedback during the wiping process, so you're never left wondering what's happening.

---

## 💻 Technology Deep Dive

CertiWipe's architecture was strategically chosen to combine a rich user interface with a powerful backend for processing and cryptography.

| Category | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Frontend** | **Electron**, HTML5, CSS3, Bootstrap 5 | Creates the native desktop experience and responsive UI. |
| **Backend** | **Python** | Handles core logic, file system operations, and generation. |
| **Communication Bridge** | `python-shell` (Node.js) | Manages the seamless, real-time communication between Electron and Python. |
| **Core Wiping Utility** | Microsoft Sysinternals `sdelete64.exe` | The engine for performing the secure data overwrite. |
| **PDF & Cryptography** | `reportlab` (Python)<br>`cryptography` (Python) | For dynamically creating PDF certificates and applying Ed25519 digital signatures. |

This **Electron + Python** stack allows us to leverage the best of both worlds: JavaScript's ecosystem for beautiful user interfaces and Python's robust libraries for complex tasks like PDF generation and high-security cryptography.

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:
* ✅ **Node.js and npm**
* ✅ **Python 3.x and pip**
* ✅ **Windows Operating System** (as the project relies on `sdelete64.exe`)

### Installation & Setup

1.  **Clone the Repository**
    ```sh
    git clone [https://github.com/dasher06/CertiWipe.git](https://github.com/dasher06/CertiWipe.git)
    cd CertiWipe
    ```

2.  **Download Core Utility**
    Download `sdelete64.exe` from the official Microsoft Sysinternals website and place it in the root directory of the project. Due to licensing, it is not included in the repository.

3.  **Install Node.js Dependencies**
    This will install Electron and other necessary packages.
    ```sh
    npm install
    ```

4.  **Install Python Dependencies**
    The required Python packages are listed in `requirements.txt`.
    ```sh
    pip install -r requirements.txt
    ```
    > **Note:** It's highly recommended to do this within a Python virtual environment.

### ⚠️ Important Security Notice

The application automatically generates a `private_key.pem` and `public_key.pem` in the root directory if they don't exist.

* **DO NOT commit `private_key.pem` to a public repository.** This key is the secret that guarantees your certificates are authentic. If it is exposed, anyone can forge certificates.
* Ensure your `.gitignore` file includes `private_key.pem` to prevent accidental commits.

### Running in Development

To run the application in development mode, execute the following command in your terminal.
**Important:** For wiping drive free space and some protected files, you may need to run your terminal as an **Administrator**.

```sh
npm start
```

### Building for Production

You can build a distributable .exe installer for Windows using Electron Builder.

1.  Ensure `sdelete64.exe` is present in the root of your project directory. The builder is configured to package it for you.
2.  Run the build command:
    ```sh
    npm run build
    ```
3.  The completed installer will be located in the `dist` folder.

---

## 🔮 Future Roadmap

CertiWipe is currently a fully functional proof-of-concept. Future enhancements could include:

* **Built-in Certificate Verifier:** An in-app tool to drag-and-drop a certificate and verify its signature against the public key.
* **Customizable Wipe Passes:** Allow users to select the number of overwrite passes (e.g., 1, 3, 7).
* **Cross-Platform Support:** Adapt the application for macOS and Linux using native secure-delete utilities like `srm` or `shred`.
* **Centralized Settings:** A settings panel to manage preferences and view the public key.
