document.addEventListener("DOMContentLoaded", function() {
    const fileButton = document.getElementById('video-file-button');
    const videoFileView = document.getElementById('video-file-view');
    const fileInput = document.getElementById('file-input');
    let selectedVideoPath = null;

    const OverlayVidButton = document.getElementById('overlay-file-button');
    const OverlayFileInput = document.getElementById('overlay-file-input');
    const OverlayfileView = document.getElementById('overlay-file-view');
    let selectedOverlayPath = null;

    const shortFolderButton = document.getElementById('output-short-folder-button');
    const shortFolderView = document.getElementById('short-folder-view');
    let selectedOutputFolder = null;

    const createShortButton = document.getElementById('create-short-button');
    
    const currentShortCreation = document.getElementById('current-short-creation');
    const videoNameInput = document.getElementById('video-name');

    const segment30secButton = document.getElementById('30-secondes-button');
    const segment1minButton = document.getElementById('1-minutes-button');
    const segment3minButton = document.getElementById('3-minutes-button');

    const segmentslider = document.getElementById('duration-slider');
    const segmentsliderValueDisplay = document.getElementById('slider-value');

    const processslider = document.getElementById('processus-slider');
    const processsliderValueDisplay = document.getElementById('video-slider-value');


    // File selection for the main video
    fileButton.addEventListener('click', function() {
        fileInput.click();
    });

    fileInput.addEventListener('change', function() {
        const file = fileInput.files[0];
        if (file) {
            selectedVideoPath = file.path;  // Store the file path
            videoFileView.innerText = `Fichier vidéo sélectionné: ${file.name}`;
        } else {
            videoFileView.innerText = "Aucun fichier sélectionné.";
        }
    });

    // File selection for the overlay video
    OverlayVidButton.addEventListener('click', function() {
        OverlayFileInput.click();
    });

    OverlayFileInput.addEventListener('change', function() {
        const file = OverlayFileInput.files[0];
        if (file) {
            selectedOverlayPath = file.path;  // Store the file path
            OverlayfileView.innerText = `Vidéo d'overlay: ${file.name}`;
        } else {
            OverlayfileView.innerText = "Aucun fichier sélectionné.";
        }
    });

    // Folder selection for the output
    shortFolderButton.addEventListener('click', async function() {
        // Ouvrir la fenêtre de sélection de dossier
        const folderPath = await window.electronAPI.selectFolder();  
        if (folderPath && folderPath.length > 0) {
            selectedOutputFolder = folderPath[0];  // Stocker le chemin du dossier
            shortFolderView.innerText = `Dossier sélectionné: ${selectedOutputFolder}`; // Mettre à jour le texte affiché
        } else {
            shortFolderView.innerText = "Aucun dossier sélectionné."; // Affichage par défaut
        }
    });


    // Functions to handle segment duration buttons
    segment30secButton.addEventListener('click', function() {
        segmentupdateSliderValue(30); // 30 seconds
        segmentslider.value = 30;
    });
    
    segment1minButton.addEventListener('click', function() {
        segmentupdateSliderValue(60); // 60 seconds
        segmentslider.value = 60;
    });

    segment3minButton.addEventListener('click', function() {
        segmentupdateSliderValue(180); // 180 seconds
        segmentslider.value = 180;
    });

    // Function to display the selected segment duration
    const segmentupdateSliderValue = (value) => {
        let minutes = Math.floor(value / 60);
        let seconds = value % 60;

        if (minutes > 0) {
            segmentsliderValueDisplay.innerText = `${minutes} minutes et ${seconds} secondes`;
        } else {
            segmentsliderValueDisplay.innerText = `${seconds} secondes`;
        }
    };

    // Update segment slider value display when adjusted
    segmentslider.addEventListener('input', function() {
        segmentupdateSliderValue(this.value);
    });

    // Update the number of simultaneous video creation processes
    const updateprocessSliderValue = (value) => {
        processsliderValueDisplay.innerText = `${value} vidéo(s) créées en simultané`;
    };

    processslider.addEventListener('input', function() {
        updateprocessSliderValue(this.value);
    });

    // Initialize the slider values
    segmentupdateSliderValue(segmentslider.value);
    updateprocessSliderValue(processslider.value);

    // Launch the Python script for short video creation
    createShortButton.addEventListener('click', async function() {
        const videoName = videoNameInput.value;
        const segmentDuration = segmentslider.value;
        const numWorkers = processslider.value;

        if (!videoName) {
            currentShortCreation.innerText = "Veuillez saisir le nom de la vidéo.";
            return;
        }
        if (!selectedVideoPath) {
            currentShortCreation.innerText = "Aucune vidéo sélectionnée.";
            return;
        }
        if (!selectedOverlayPath) {
            currentShortCreation.innerText = "Aucune vidéo d'overlay sélectionnée.";
            return;
        }
        if (!selectedOutputFolder) {
            currentShortCreation.innerText = "Aucun dossier de sortie sélectionné.";
            return;
        }

        currentShortCreation.innerText = "Exécution du script Python...";

        try {
            // Pass all required arguments to the Python script via the Electron API
            const result = await window.electronAPI.runPythonScript(
                videoName, 
                selectedVideoPath, 
                selectedOverlayPath, 
                selectedOutputFolder, 
                segmentDuration, 
                numWorkers
            );
            currentShortCreation.innerText = `Résultat du script Python: ${result}`;
        } catch (error) {
            currentShortCreation.innerText = `Erreur lors de l'exécution : ${error}`;
        }
        
    });
});
