// A global variable to keep track of the current wipe task
let wipeTask = {
    mode: 'files', // 'files', 'folder', or 'drive'
    targets: []
};

// --- UI Helper Functions ---
function logMessage(message) {
    const logOutput = document.getElementById('log-output');
    logOutput.innerHTML += `${message}\n`;
    logOutput.scrollTop = logOutput.scrollHeight; // Auto-scroll to bottom
}

function updateEraseButtonState() {
    const eraseBtn = document.getElementById('erase-btn');
    // Enable the button only if there are targets to wipe
    if (wipeTask.targets.length > 0) {
        eraseBtn.disabled = false;
        eraseBtn.innerHTML = '<i class="bi bi-trash3-fill me-2"></i>Securely Erase';
    } else {
        eraseBtn.disabled = true;
        eraseBtn.innerHTML = '<i class="bi bi-x-circle me-2"></i>Select a Target First';
    }
}

function resetWipeTask() {
    wipeTask.targets = [];
    document.getElementById('file-list').innerHTML = '';
    document.getElementById('folder-path').textContent = 'No folder selected.';
    document.getElementById('download-container').innerHTML = ''; // Clear old download buttons
    updateEraseButtonState();
}

// --- Drive Population and Admin Check ---
function populateDrives(drives) {
  const driveSelect = document.getElementById('drive-select');
  driveSelect.innerHTML = '';
  if (drives && drives.length > 0) {
    drives.forEach(drive => {
      const option = document.createElement('option');
      option.value = drive.letter;
      option.textContent = `${drive.letter}: ${drive.name}`;
      driveSelect.appendChild(option);
    });
    driveSelect.disabled = false;
    // If the drive tab is active, set its default target
    if (wipeTask.mode === 'drive') {
        wipeTask.targets = [drives[0].letter];
        updateEraseButtonState();
    }
  } else {
    driveSelect.innerHTML = '<option>No drives found or an error occurred.</option>';
  }
}

function showAdminError() {
    logMessage("ERROR: This application requires Administrator privileges. Please close and run as Administrator.");
}

// === MAIN EVENT LISTENERS ===

// On window load, check admin rights and get drives
window.addEventListener('DOMContentLoaded', async () => {
    const adminStatus = await window.api.invoke('check-admin');
    if (adminStatus.is_admin) {
        logMessage("Administrator privileges detected. Detecting drives...");
        const drives = await window.api.invoke('get-drives');
        if (drives.error) {
            logMessage(`PYTHON ERROR: ${drives.error}`);
            populateDrives(null);
        } else {
            populateDrives(drives);
        }
    } else {
        showAdminError();
    }
    updateEraseButtonState(); // Set initial button state
});

// --- Tab Switching Logic ---
const tabs = document.querySelectorAll('#wipe-tabs .nav-link');
tabs.forEach(tab => {
    tab.addEventListener('shown.bs.tab', (event) => {
        resetWipeTask();
        const activeTabId = event.target.id;
        if (activeTabId === 'files-tab') {
            wipeTask.mode = 'files';
        } else if (activeTabId === 'folder-tab') {
            wipeTask.mode = 'folder';
        } else if (activeTabId === 'drive-tab') {
            wipeTask.mode = 'drive';
            // If drives are loaded, set the first one as the default target
            const driveSelect = document.getElementById('drive-select');
            if (driveSelect.options.length > 0 && driveSelect.options[0].value) {
                wipeTask.targets = [driveSelect.value];
            }
        }
        updateEraseButtonState();
    });
});

// --- Button Click Handlers ---
document.getElementById('select-files-btn').addEventListener('click', async () => {
    const files = await window.api.invoke('select-files');
    if (files.length > 0) {
        wipeTask.targets = files;
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = ''; // Clear previous list
        files.forEach(file => {
            const li = document.createElement('li');
            li.className = 'list-group-item bg-dark text-white-50 border-secondary small';
            li.textContent = path.basename(file);
            fileList.appendChild(li);
        });
        updateEraseButtonState();
    }
});

document.getElementById('select-folder-btn').addEventListener('click', async () => {
    const folder = await window.api.invoke('select-folder');
    if (folder) {
        wipeTask.targets = [folder];
        document.getElementById('folder-path').textContent = folder;
        updateEraseButtonState();
    }
});

document.getElementById('drive-select').addEventListener('change', (event) => {
    if (wipeTask.mode === 'drive') {
        wipeTask.targets = [event.target.value];
        updateEraseButtonState();
    }
});

document.getElementById('erase-btn').addEventListener('click', () => {
    let confirmationMessage = "ARE YOU SURE you want to proceed?\n\nThis action is irreversible.";

    // Updated logic to show a specific warning for drive wipes
    if (wipeTask.mode === 'files') {
        confirmationMessage = `ARE YOU SURE you want to securely erase ${wipeTask.targets.length} file(s)?\n\nThis action is irreversible.`;
    } else if (wipeTask.mode === 'folder') {
        confirmationMessage = `ARE YOU SURE you want to securely erase the entire folder:\n\n${wipeTask.targets[0]}\n\nThis action is irreversible.`;
    } else if (wipeTask.mode === 'drive') {
        confirmationMessage = `⚠️ WARNING: You are about to wipe the free space on drive ${wipeTask.targets[0]}:\\.` +
            `\n\nThis is a very slow process that can take several hours and will heavily use your disk.` +
            `\n\nAre you sure you want to continue?`;
    }

    const confirmation = confirm(confirmationMessage);
    if (confirmation) {
        const eraseBtn = document.getElementById('erase-btn');
        eraseBtn.disabled = true;
        eraseBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            Wiping...
        `;
        document.getElementById('download-container').innerHTML = '';
        logMessage(`\nStarting secure wipe process (Mode: ${wipeTask.mode})...`);
        window.api.send('start-wipe', wipeTask);
    }
});

// --- Wipe Progress and Completion Listeners ---
window.api.on('wipe-progress', (rawMessage) => {
    try {
        const messageObj = JSON.parse(rawMessage);
        logMessage(messageObj.message);
    } catch {
        logMessage(rawMessage);
    }
});

window.api.on('wipe-complete', (result) => {
  logMessage(`\n--- WIPE COMPLETE ---`);
  // This function will reset the button to its normal state
  updateEraseButtonState();

  if (result.success) {
      logMessage(`✅ Success! ${result.message}`);
      const downloadContainer = document.getElementById('download-container');
      const downloadBtn = document.createElement('button');
      downloadBtn.className = 'btn btn-success btn-lg';
      downloadBtn.innerHTML = '<i class="bi bi-download me-2"></i>Download Certificate';
      
      downloadBtn.addEventListener('click', async () => {
          const saveResult = await window.api.invoke('save-certificate', result.pdf_base64);
          if (saveResult.success) {
              logMessage(`Certificate saved to: ${saveResult.filePath}`);
          } else {
              logMessage('Certificate download was cancelled.');
          }
          downloadContainer.innerHTML = '';
      });
      downloadContainer.innerHTML = '';
      downloadContainer.appendChild(downloadBtn);
  } else {
      logMessage(`❌ ERROR: ${result.message}`);
  }
});

// A simple helper to get the filename from a full path
const path = {
    basename: (p) => p.split(/[\\/]/).pop()
};