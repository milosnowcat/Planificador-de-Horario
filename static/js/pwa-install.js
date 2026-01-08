// PWA Install Prompt Handler
let deferredPrompt;
let installButton;

// Detectar si la app ya está instalada
function isStandalone() {
    return window.matchMedia('(display-mode: standalone)').matches ||
        window.navigator.standalone === true;
}

// Inicializar botón de instalación
document.addEventListener('DOMContentLoaded', () => {
    // No mostrar si ya está instalada
    if (isStandalone()) {
        return;
    }

    // Crear botón de instalación
    createInstallButton();

    // Registrar service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/static/sw.js')
            .then(reg => console.log('Service Worker registrado', reg))
            .catch(err => console.log('Error en Service Worker', err));
    }
});

// Capturar evento beforeinstallprompt (Android)
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;

    if (installButton) {
        installButton.style.display = 'flex';
    }
});

// Crear botón de instalación
function createInstallButton() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    const isAndroid = /Android/.test(navigator.userAgent);

    if (!isIOS && !isAndroid) {
        return; // Solo mostrar en móviles
    }

    installButton = document.createElement('button');
    installButton.id = 'pwa-install-btn';
    installButton.className = 'pwa-install-button';
    installButton.innerHTML = `
    <i class="fas fa-download"></i>
    <span>Instalar App</span>
  `;
    installButton.style.display = 'none';

    // Evento click
    installButton.addEventListener('click', async () => {
        if (isIOS) {
            showIOSInstructions();
        } else if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User response: ${outcome}`);
            deferredPrompt = null;
            installButton.style.display = 'none';
        }
    });

    // Agregar al body
    document.body.appendChild(installButton);

    // Mostrar automáticamente si es iOS o si ya tenemos el prompt
    if (isIOS || deferredPrompt) {
        installButton.style.display = 'flex';
    }
}

// Mostrar instrucciones para iOS
function showIOSInstructions() {
    const modal = document.createElement('div');
    modal.className = 'ios-install-modal';
    modal.innerHTML = `
    <div class="ios-install-content">
      <h3>📱 Instalar Planificador UDG</h3>
      <p>Para instalar esta app en tu iPhone:</p>
      <ol>
        <li>
          Toca el botón de compartir 
          <span class="ios-share-icon">
            <svg width="18" height="24" viewBox="0 0 18 24" fill="none">
              <path d="M9 0L9 14M9 0L5 4M9 0L13 4" stroke="#007AFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <rect x="1" y="10" width="16" height="12" rx="2" stroke="#007AFF" stroke-width="2" fill="none"/>
            </svg>
          </span>
          en la barra inferior de Safari
        </li>
        <li>Desplázate y selecciona <strong>"Agregar a Inicio"</strong></li>
        <li>Toca <strong>"Agregar"</strong> en la esquina superior derecha</li>
      </ol>
      <button onclick="this.parentElement.parentElement.remove()" class="btn btn-primary">Entendido</button>
    </div>
  `;
    document.body.appendChild(modal);

    // Cerrar al hacer click fuera
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Detectar cuando se instala
window.addEventListener('appinstalled', () => {
    console.log('PWA instalada exitosamente');
    if (installButton) {
        installButton.style.display = 'none';
    }
});
