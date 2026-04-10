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

// Función para detectar vehículo automáticamente desde la cámara
async function detectVehicleAuto() {
    const status = document.getElementById('detectionStatus');
    const resultDiv = document.getElementById('autoDetectionResult');
    const resultContent = document.getElementById('autoResultContent');
    const btn = document.getElementById('autoDetectBtn');

    // Cambiar estado del botón
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detectando...';

    // Cambiar mensaje de estado
    status.className = 'alert alert-info';
    status.innerHTML = '<i class="fas fa-eye"></i> Detectando vehículo...';

    try {
        const response = await fetch('/api/camera/detect_vehicle_auto', {
            method: 'POST'
        });

        const data = await response.json();

        if (data.success) {
            status.className = 'alert alert-success';
            status.innerHTML = '<i class="fas fa-check-circle"></i> ¡Vehículo detectado y registrado!';

            // Mostrar resultado
            resultContent.innerHTML = `
                <h6><i class="fas fa-car"></i> Vehículo Registrado</h6>
                <p><strong>Placa:</strong> ${data.vehicle.placa}</p>
                <p><strong>Tipo:</strong> ${data.vehicle.tipo}</p>
                <p><strong>Color:</strong> ${data.vehicle.color}</p>
                <p><strong>Imagen guardada:</strong> ${data.vehicle.imagen.split('/').pop()}</p>
                ${data.vehicle.confianza_placa ? `<p><strong>Confianza placa:</strong> ${(data.vehicle.confianza_placa * 100).toFixed(1)}%</p>` : ''}
            `;
            resultDiv.style.display = 'block';

            // Ocultar resultado después de 10 segundos
            setTimeout(() => {
                resultDiv.style.display = 'none';
            }, 10000);

        } else {
            status.className = 'alert alert-danger';
            status.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${data.error}`;
            resultDiv.style.display = 'none';
        }

    } catch (error) {
        console.error('Error:', error);
        status.className = 'alert alert-danger';
        status.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error de conexión';
        resultDiv.style.display = 'none';
    } finally {
        // Restaurar botón
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-magic"></i> Detectar y Registrar Vehículo';
    }
}
