/* Control de cámara y captura de imágenes */

class CameraManager {
    constructor() {
        this.stream = null;
        this.videoElement = null;
        this.canvas = null;
        this.isStreamActive = false;
    }

    async initCamera(videoElementId) {
        this.videoElement = document.getElementById(videoElementId);

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            });

            this.videoElement.srcObject = this.stream;
            this.isStreamActive = true;

            // Esperar a que el video esté cargado
            this.videoElement.onloadedmetadata = () => {
                this.videoElement.play();
            };

            return true;
        } catch (error) {
            console.error('Error al acceder a la cámara:', error);
            return false;
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.isStreamActive = false;
        }
    }

    captureFrame() {
        if (!this.videoElement || !this.isStreamActive) {
            return null;
        }

        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        canvas.width = this.videoElement.videoWidth;
        canvas.height = this.videoElement.videoHeight;

        context.drawImage(this.videoElement, 0, 0);

        return canvas.toDataURL('image/jpeg', 0.9);
    }

    async captureAndSend() {
        const imageData = this.captureFrame();
        if (!imageData) {
            throw new Error('No se pudo capturar la imagen');
        }

        // Convertir data URL a blob
        const response = await fetch(imageData);
        const blob = await response.blob();

        // Enviar al servidor
        const formData = new FormData();
        formData.append('file', blob, 'capture.jpg');

        const result = await fetch('/api/camera/capture', {
            method: 'POST',
            body: formData
        });

        return await result.json();
    }
}

// Instancia global de cámara
const cameraManager = new CameraManager();

// Inicializar cámara si el elemento existe
document.addEventListener('DOMContentLoaded', function () {
    const videoElement = document.getElementById('videoElement');
    if (videoElement) {
        cameraManager.initCamera('videoElement')
            .then(success => {
                if (!success) {
                    document.getElementById('noCameraMessage').style.display = 'block';
                } else {
                    document.getElementById('cameraPreview').style.display = 'block';
                }
            });
    }
});

// Función para procesar imagen con IA
async function processImageWithAI(event) {
    const file = event.target.files[0];
    if (!file) return;

    const aiPreview = document.getElementById('aiImagePreview');
    const aiPreviewImg = document.getElementById('aiPreviewImg');
    const status = document.getElementById('aiProcessingStatus');

    // Mostrar preview
    const reader = new FileReader();
    reader.onload = function (e) {
        aiPreviewImg.src = e.target.result;
        aiPreview.style.display = 'block';
        status.className = 'mt-2 alert alert-info';
        status.innerHTML = '<i class="fas fa-cog fa-spin"></i> Procesando con IA...';
    };
    reader.readAsDataURL(file);

    // Procesar con IA
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/camera/process_ai', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            status.className = 'mt-2 alert alert-success';
            status.innerHTML = `
                <i class="fas fa-check-circle"></i> ¡Vehículo registrado exitosamente!<br>
                <strong>Placa:</strong> ${data.vehicle.placa}<br>
                <strong>Tipo:</strong> ${data.vehicle.tipo}<br>
                <strong>Color:</strong> ${data.vehicle.color}
            `;

            // Resetear formulario después de 3 segundos
            setTimeout(() => {
                event.target.value = '';
                aiPreview.style.display = 'none';
            }, 3000);

        } else {
            status.className = 'mt-2 alert alert-danger';
            status.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${data.error}`;
        }

    } catch (error) {
        console.error('Error:', error);
        status.className = 'mt-2 alert alert-danger';
        status.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error de conexión';
    }
}

// Función para detectar vehículo automáticamente desde la cámara (CORRECCIÓN: Automático y silencioso)
async function detectVehicleAuto() {
    const status = document.getElementById('detectionStatus');
    const resultDiv = document.getElementById('autoDetectionResult');
    const resultContent = document.getElementById('autoResultContent');

    try {
        const response = await fetch('/api/camera/detect_vehicle_auto', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            const placaKey = data.vehicle.placa;

            // CORRECCIÓN: Verificar si el vehículo ya fue registrado (evitar duplicados)
            if (!detectedVehicles.has(placaKey)) {
                detectedVehicles.add(placaKey);
                vehicleCount++;

                // Actualizar contador
                document.getElementById('vehicleCount').textContent = vehicleCount;

                // Mostrar resultado brevemente
                resultContent.innerHTML = `
                    <div class="alert alert-success m-0">
                        <i class="fas fa-check-circle"></i> <strong>¡Vehículo Detectado!</strong><br>
                        <small>Placa: ${data.vehicle.placa} | Tipo: ${data.vehicle.tipo} | Color: ${data.vehicle.color}</small>
                    </div>
                `;
                resultDiv.style.display = 'block';

                // Sonido de notificación (opcional)
                playDetectionSound();

                // Ocultar resultado después de 3 segundos
                setTimeout(() => {
                    resultDiv.style.display = 'none';
                }, 3000);

                console.log('✅ Vehículo detectado:', data.vehicle.placa);
            }

            // Mantener estado "Monitoreando"
            status.className = 'alert alert-success';
            status.innerHTML = '<i class="fas fa-video"></i> <strong>Monitoreando vehículos...</strong> Detectando automáticamente';

        } else {
            // Mantener monitoreando aunque no haya detección
            status.className = 'alert alert-success';
            status.innerHTML = '<i class="fas fa-video"></i> <strong>Monitoreando vehículos...</strong> Detectando automáticamente';
            console.log('ℹ️ Sin vehículos detectados en este frame');
        }

    } catch (error) {
        console.error('Error en detección automática:', error);
        // Mantener estado de monitoreo incluso con errores
        status.className = 'alert alert-warning';
        status.innerHTML = '<i class="fas fa-video"></i> <strong>Monitoreando vehículos...</strong> (Esperando conexión)';
    }
}

// CORRECCIÓN: Función para reproducir sonido de detección
function playDetectionSound() {
    try {
        // Crear un sonido beep simple usando Web Audio API
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.value = 800;
        oscillator.type = 'sine';

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (e) {
        console.log('No se pudo reproducir sonido de notificación');
    }
}
