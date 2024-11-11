const { contextBridge, ipcRenderer } = require('electron');

// Expose both selectFolder and runPythonScript in a single object
contextBridge.exposeInMainWorld('electronAPI', {
    selectFolder: () => ipcRenderer.invoke('dialog:openDirectory'),
    
    runPythonScript: (videoName, videoPath, overlayPath, outputDir, segmentDuration, numWorkers) => {
        return ipcRenderer.invoke('electron_short_creation.py', videoName, videoPath, overlayPath, outputDir, segmentDuration, numWorkers);
    }
});
