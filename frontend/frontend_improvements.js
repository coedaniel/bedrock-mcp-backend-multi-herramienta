// MEJORAS DE FRONTEND PARA BEDROCK PLAYGROUND

// 1. GESTIÓN DE ESTADO AVANZADA
class StateManager {
    constructor() {
        this.state = {
            messages: [],
            systemPrompt: '',
            settings: {
                model: 'anthropic.claude-3-5-sonnet-20240620-v1:0',
                temperature: 0.7,
                maxTokens: 1500,
                useMCP: true,
                generateDeliverables: false
            },
            ui: {
                isLoading: false,
                currentStep: null,
                processingSteps: []
            },
            stats: {
                messageCount: 0,
                totalTokens: 0,
                totalCost: 0,
                totalTime: 0
            }
        };
        this.listeners = [];
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    setState(updates) {
        this.state = { ...this.state, ...updates };
        this.listeners.forEach(listener => listener(this.state));
    }

    getState() {
        return this.state;
    }
}

// 2. CACHE LOCAL INTELIGENTE
class LocalCache {
    constructor() {
        this.cache = new Map();
        this.maxSize = 100;
        this.ttl = 30 * 60 * 1000; // 30 minutos
    }

    set(key, value) {
        if (this.cache.size >= this.maxSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }

        this.cache.set(key, {
            value,
            timestamp: Date.now()
        });
    }

    get(key) {
        const item = this.cache.get(key);
        if (!item) return null;

        if (Date.now() - item.timestamp > this.ttl) {
            this.cache.delete(key);
            return null;
        }

        return item.value;
    }

    clear() {
        this.cache.clear();
    }
}

// 3. MANEJO DE ERRORES ROBUSTO
class ErrorHandler {
    constructor() {
        this.errorQueue = [];
        this.maxErrors = 10;
    }

    handleError(error, context = {}) {
        const errorInfo = {
            message: error.message,
            stack: error.stack,
            context,
            timestamp: new Date().toISOString(),
            id: Math.random().toString(36).substr(2, 9)
        };

        this.errorQueue.push(errorInfo);
        if (this.errorQueue.length > this.maxErrors) {
            this.errorQueue.shift();
        }

        this.displayError(errorInfo);
        this.logError(errorInfo);
    }

    displayError(errorInfo) {
        const notification = document.createElement('div');
        notification.className = 'error-notification fixed top-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <div>
                    <h4 class="font-bold">Error</h4>
                    <p class="text-sm">${errorInfo.message}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    logError(errorInfo) {
        console.error('Application Error:', errorInfo);
        
        // En producción, enviar a servicio de logging
        // this.sendToLoggingService(errorInfo);
    }

    getErrorHistory() {
        return this.errorQueue;
    }
}

// 4. OPTIMIZACIÓN DE RENDIMIENTO
class PerformanceOptimizer {
    constructor() {
        this.debounceTimers = new Map();
        this.throttleTimers = new Map();
    }

    debounce(func, delay, key) {
        if (this.debounceTimers.has(key)) {
            clearTimeout(this.debounceTimers.get(key));
        }

        const timer = setTimeout(() => {
            func();
            this.debounceTimers.delete(key);
        }, delay);

        this.debounceTimers.set(key, timer);
    }

    throttle(func, delay, key) {
        if (this.throttleTimers.has(key)) {
            return;
        }

        func();
        const timer = setTimeout(() => {
            this.throttleTimers.delete(key);
        }, delay);

        this.throttleTimers.set(key, timer);
    }

    // Lazy loading de componentes
    lazyLoad(selector, callback) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    callback(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        });

        document.querySelectorAll(selector).forEach(el => {
            observer.observe(el);
        });
    }
}

// 5. ACCESIBILIDAD MEJORADA
class AccessibilityManager {
    constructor() {
        this.announcer = this.createAnnouncer();
    }

    createAnnouncer() {
        const announcer = document.createElement('div');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.className = 'sr-only';
        document.body.appendChild(announcer);
        return announcer;
    }

    announce(message) {
        this.announcer.textContent = message;
        setTimeout(() => {
            this.announcer.textContent = '';
        }, 1000);
    }

    addKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Navegación con teclado
            if (e.key === 'Tab') {
                this.handleTabNavigation(e);
            }
            
            // Atajos de teclado
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'Enter':
                        e.preventDefault();
                        this.sendMessage();
                        break;
                    case 'k':
                        e.preventDefault();
                        this.clearChat();
                        break;
                }
            }
        });
    }

    handleTabNavigation(e) {
        const focusableElements = document.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
        }
    }
}

// 6. ANALYTICS Y MÉTRICAS
class AnalyticsManager {
    constructor() {
        this.events = [];
        this.sessionStart = Date.now();
    }

    trackEvent(eventName, properties = {}) {
        const event = {
            name: eventName,
            properties,
            timestamp: Date.now(),
            sessionTime: Date.now() - this.sessionStart
        };

        this.events.push(event);
        this.sendEvent(event);
    }

    trackPageView(page) {
        this.trackEvent('page_view', { page });
    }

    trackUserInteraction(action, element) {
        this.trackEvent('user_interaction', { action, element });
    }

    trackPerformance(metric, value) {
        this.trackEvent('performance', { metric, value });
    }

    sendEvent(event) {
        // En producción, enviar a servicio de analytics
        console.log('Analytics Event:', event);
    }

    getSessionStats() {
        return {
            sessionDuration: Date.now() - this.sessionStart,
            eventCount: this.events.length,
            events: this.events
        };
    }
}

// 7. PROGRESSIVE WEB APP (PWA)
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.setupServiceWorker();
        this.setupInstallPrompt();
    }

    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js')
                .then(registration => {
                    console.log('SW registered:', registration);
                })
                .catch(error => {
                    console.log('SW registration failed:', error);
                });
        }
    }

    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallButton();
        });
    }

    showInstallButton() {
        const installButton = document.createElement('button');
        installButton.textContent = 'Instalar App';
        installButton.className = 'install-button';
        installButton.onclick = () => this.promptInstall();
        
        document.body.appendChild(installButton);
    }

    async promptInstall() {
        if (this.deferredPrompt) {
            this.deferredPrompt.prompt();
            const result = await this.deferredPrompt.userChoice;
            console.log('Install prompt result:', result);
            this.deferredPrompt = null;
        }
    }
}

// 8. TEMA DINÁMICO
class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.applyTheme(this.currentTheme);
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.currentTheme = theme;
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    getTheme() {
        return this.currentTheme;
    }
}

// 9. INICIALIZACIÓN DE MEJORAS
class FrontendEnhancer {
    constructor() {
        this.stateManager = new StateManager();
        this.cache = new LocalCache();
        this.errorHandler = new ErrorHandler();
        this.performance = new PerformanceOptimizer();
        this.accessibility = new AccessibilityManager();
        this.analytics = new AnalyticsManager();
        this.pwa = new PWAManager();
        this.theme = new ThemeManager();
        
        this.init();
    }

    init() {
        // Configurar manejo global de errores
        window.addEventListener('error', (e) => {
            this.errorHandler.handleError(e.error, { type: 'global' });
        });

        window.addEventListener('unhandledrejection', (e) => {
            this.errorHandler.handleError(e.reason, { type: 'promise' });
        });

        // Configurar accesibilidad
        this.accessibility.addKeyboardNavigation();

        // Track página inicial
        this.analytics.trackPageView('bedrock-playground');

        console.log('Frontend enhancements initialized');
    }

    // Método para integrar con el código existente
    enhanceExistingFunctions() {
        // Envolver funciones existentes con mejoras
        const originalSendMessage = window.sendMessage;
        window.sendMessage = async () => {
            try {
                this.analytics.trackUserInteraction('send_message', 'chat_input');
                const startTime = performance.now();
                
                await originalSendMessage();
                
                const endTime = performance.now();
                this.analytics.trackPerformance('message_send_time', endTime - startTime);
            } catch (error) {
                this.errorHandler.handleError(error, { function: 'sendMessage' });
            }
        };
    }
}

// Inicializar mejoras cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    window.frontendEnhancer = new FrontendEnhancer();
    window.frontendEnhancer.enhanceExistingFunctions();
});
