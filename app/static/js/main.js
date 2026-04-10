/* JavaScript principal de la aplicación */

// Funciones auxiliares generales

function showNotification(message, type = 'info') {
    const alertClass = {
        'success': 'alert-success',
        'danger': 'alert-danger',
        'warning': 'alert-warning',
        'info': 'alert-info'
    }[type] || 'alert-info';

    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    const container = document.querySelector('main');
    container.insertBefore(alert, container.firstChild);

    // Auto-dismiss después de 5 segundos
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Formatear números como moneda
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Formatear fecha
function formatDate(date) {
    return new Intl.DateTimeFormat('es-CO', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }).format(new Date(date));
}

// Validar formato de placa
function isValidPlate(plate) {
    const patterns = [
        /^[A-Z]{2,3}-\d{3,4}$/,  // ABC-1234
        /^[A-Z]{2,3}\d{3,4}$/,   // ABC1234
        /^\d{3,4}-[A-Z]{2,3}$/   // 1234-ABC
    ];

    return patterns.some(pattern => pattern.test(plate.toUpperCase()));
}

// API Helper
class API {
    static async request(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const response = await fetch(endpoint, { ...defaultOptions, ...options });
        const data = await response.json();

        if (!data.success && response.status !== 200) {
            throw new Error(data.error || 'Error en la solicitud');
        }

        return data;
    }

    static async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    static async post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body)
        });
    }

    static async put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body)
        });
    }

    static async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// Rutas de API
const ROUTES = {
    VEHICLES: {
        LIST: '/api/vehicles',
        SEARCH: (plate) => `/api/vehicles/search/${plate}`,
        CHECKIN: '/api/vehicles/checkin',
        CHECKOUT: (id) => `/api/vehicles/checkout/${id}`
    },
    PAYMENTS: {
        CALCULATE: '/api/payments/calculate',
        CREATE: '/api/payments',
        HISTORY: '/api/payments/history'
    },
    CAMERA: {
        CAPTURE: '/api/camera/capture',
        DETECT: '/api/camera/detect'
    },
    ADMIN: {
        STATS: '/admin/statistics',
        LOGS: '/admin/logs',
        VEHICLES: '/admin/vehicles'
    }
};

// Event listener global para formularios AJAX
document.addEventListener('submit', function (e) {
    const form = e.target;
    if (!form.classList.contains('ajax-form')) return;

    e.preventDefault();

    const formData = new FormData(form);
    const action = form.getAttribute('data-action');
    const method = form.getAttribute('method') || 'POST';

    API.request(action, {
        method: method,
        body: formData
    })
        .then(data => {
            if (data.success) {
                showNotification(data.message || 'Operación exitosa', 'success');
                form.reset();
            } else {
                showNotification(data.error || 'Error en la operación', 'danger');
            }
        })
        .catch(error => {
            showNotification(error.message, 'danger');
        });
});

// Inicialización
document.addEventListener('DOMContentLoaded', function () {
    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Funciones de tiempo real
function updateRealTime() {
    const timeElements = document.querySelectorAll('[data-realtime="true"]');
    timeElements.forEach(el => {
        const startTime = new Date(el.getAttribute('data-start-time'));
        const now = new Date();
        const diff = Math.floor((now - startTime) / 60000); // minutos

        let timeString = '';
        const hours = Math.floor(diff / 60);
        const minutes = diff % 60;

        if (hours > 0) {
            timeString = `${hours}h ${minutes}m`;
        } else {
            timeString = `${minutes}m`;
        }

        el.textContent = timeString;
    });
}

// Actualizar tiempo en tiempo real cada minuto
setInterval(updateRealTime, 60000);
updateRealTime(); // Ejecución inicial
