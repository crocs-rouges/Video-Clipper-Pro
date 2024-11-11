const { app, BrowserWindow, dialog, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process'); // Import du module child_process

function createWindow() {
    const win = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true,
            enableRemoteModule: false,
            nodeIntegration: false
        },
    });

    win.loadFile('index.html');
}

// Gestionnaire pour ouvrir le dossier
ipcMain.handle('dialog:openDirectory', async () => {
    const result = await dialog.showOpenDialog({
        properties: ['openDirectory']
    });
    return result.filePaths; // Renvoie les chemins sélectionnés
});

app.whenReady().then(createWindow);

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


// Gestionnaire IPC pour exécuter le script Python
ipcMain.handle('electron_short_creation.py', async (event, videoName, videoPath, overlayPath, outputDir, segmentDuration, numWorkers) => {
    return new Promise((resolve, reject) => {
        const pythonProcess = spawn('python', ['electron_short_creation.py', videoName, videoPath, overlayPath, outputDir, segmentDuration, numWorkers]);

        pythonProcess.stdout.on('data', (data) => {
            console.log(`stdout: ${data}`);
            resolve(data.toString());
        });

        pythonProcess.stderr.on('data', (data) => {
            console.error(`stderr: ${data}`);
            reject(data.toString());
        });

        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                reject(`Process exited with code ${code}`);
            }
        });
    });
});