const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const fs = require('fs');
const { PythonShell } = require('python-shell');

let win;

function createWindow() {
  win = new BrowserWindow({
    width: 900,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  });
  win.loadFile('index.html');
}

app.whenReady().then(() => {
  // --- Handler to open the file selection dialog ---
  ipcMain.handle('select-files', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog(win, {
      title: 'Select Files to Wipe',
      properties: ['openFile', 'multiSelections']
    });
    return canceled ? [] : filePaths;
  });

  // --- Handler to open the folder selection dialog ---
  ipcMain.handle('select-folder', async () => {
    const { canceled, filePaths } = await dialog.showOpenDialog(win, {
      title: 'Select Folder to Wipe',
      properties: ['openDirectory']
    });
    return canceled ? null : filePaths[0];
  });
  
  ipcMain.handle('check-admin', async () => {
    try {
      const results = await PythonShell.run('core_engine.py', { 
        mode: 'json',
        pythonPath: 'python',
        // Use __dirname for development mode. This will be adjusted by electron-builder for production.
        scriptPath: __dirname, 
        args: ['check_admin'] 
      });
      return results[0];
    } catch (err) { return { error: err.message }; }
  });

  ipcMain.handle('get-drives', async () => {
    try {
      const results = await PythonShell.run('core_engine.py', {
        mode: 'json',
        pythonPath: 'python',
        scriptPath: __dirname,
        args: ['get_drives']
      });
      return results[0];
    } catch (err) { return { error: err.message }; }
  });

  ipcMain.handle('save-certificate', async (event, pdfBase64) => {
    const { canceled, filePath } = await dialog.showSaveDialog(win, {
      title: 'Save Certificate',
      defaultPath: `CertiWipe-Certificate-${Date.now()}.pdf`,
      filters: [{ name: 'PDF Documents', extensions: ['pdf'] }]
    });
    if (canceled || !filePath) { return { success: false }; }
    try {
      const pdfBuffer = Buffer.from(pdfBase64, 'base64');
      fs.writeFileSync(filePath, pdfBuffer);
      return { success: true, filePath: filePath };
    } catch (err) { return { success: false, error: err.message }; }
  });

  // --- WIPE HANDLER (REAL WIPE) ---
  ipcMain.on('start-wipe', (event, payload) => {
    let args;
    switch(payload.mode) {
      case 'files':
        args = ['wipe_files', ...payload.targets];
        break;
      case 'folder':
        args = ['wipe_folder', payload.targets[0]];
        break;
      case 'drive':
        args = ['start_free_space_wipe', payload.targets[0]];
        break;
      default:
        win.webContents.send('wipe-complete', { success: false, message: "Unknown wipe mode specified." });
        return;
    }

    const messages = [];
    const pyshell = new PythonShell('core_engine.py', {
      pythonPath: 'python',
      pythonOptions: ['-u'],
      scriptPath: __dirname,
      args: args
    });

    pyshell.on('message', (message) => { messages.push(message); win.webContents.send('wipe-progress', message); });
    pyshell.on('stderr', function (stderr) { console.error('Python STDERR:', stderr); const errMessage = JSON.stringify({ type: 'error', message: `PYTHON SCRIPT ERROR: ${stderr}` }); win.webContents.send('wipe-progress', errMessage); });
    pyshell.end((err) => {
        if (err) { win.webContents.send('wipe-complete', { success: false, message: err.message }); }
        else {
            try {
                const nonEmptyMessages = messages.filter(msg => msg.trim() !== '');
                const lastMessage = nonEmptyMessages[nonEmptyMessages.length - 1];
                const finalResult = JSON.parse(lastMessage);
                win.webContents.send('wipe-complete', { ...finalResult, success: finalResult.type === 'success' });
            } catch (parseErr) {
                win.webContents.send('wipe-complete', { success: false, message: "Could not parse the final script result." });
            }
        }
    });
  });

  // --- DEMO WIPE HANDLER ---
  ipcMain.on('start-wipe-demo', (event, payload) => {
    const messages = [];
    const pyshell = new PythonShell('core_engine.py', {
      pythonPath: 'python',
      pythonOptions: ['-u'],
      scriptPath: __dirname,
      args: ['start_free_space_wipe_demo', payload.targets[0]]
    });

    pyshell.on('message', (message) => { messages.push(message); win.webContents.send('wipe-progress', message); });
    pyshell.on('stderr', function (stderr) { console.error('Python STDERR:', stderr); const errMessage = JSON.stringify({ type: 'error', message: `PYTHON SCRIPT ERROR: ${stderr}` }); win.webContents.send('wipe-progress', errMessage); });
    pyshell.end((err) => {
        if (err) { win.webContents.send('wipe-complete', { success: false, message: err.message }); }
        else {
            try {
                const nonEmptyMessages = messages.filter(msg => msg.trim() !== '');
                const lastMessage = nonEmptyMessages[nonEmptyMessages.length - 1];
                const finalResult = JSON.parse(lastMessage);
                win.webContents.send('wipe-complete', { ...finalResult, success: finalResult.type === 'success' });
            } catch (parseErr) {
                win.webContents.send('wipe-complete', { success: false, message: "Could not parse the final script result." });
            }
        }
    });
  });

  createWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});