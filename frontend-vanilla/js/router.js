// Router
class Router {
    constructor() {
        this.routes = new Map();
        this.currentRoute = null;
        this.init();
    }

    init() {
        // Handle navigation links
        document.addEventListener('click', (e) => {
            if (e.target.matches('.nav-link')) {
                e.preventDefault();
                const route = e.target.getAttribute('data-route');
                this.navigate(route);
            }
        });

        // Handle browser back/forward
        window.addEventListener('popstate', () => {
            const route = this.getRouteFromHash();
            this.loadRoute(route);
        });

        // Load initial route
        const initialRoute = this.getRouteFromHash() || 'robot-control';
        this.navigate(initialRoute, true);
    }

    register(name, view) {
        this.routes.set(name, view);
    }

    getRouteFromHash() {
        const hash = window.location.hash.slice(1);
        return hash || null;
    }

    navigate(routeName, replace = false) {
        if (!this.routes.has(routeName)) {
            console.error(`Route not found: ${routeName}`);
            return;
        }

        // Update URL
        if (replace) {
            window.history.replaceState({}, '', `#${routeName}`);
        } else {
            window.history.pushState({}, '', `#${routeName}`);
        }

        this.loadRoute(routeName);
    }

    loadRoute(routeName) {
        if (!this.routes.has(routeName)) {
            console.error(`Route not found: ${routeName}`);
            return;
        }

        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('data-route') === routeName) {
                link.classList.add('active');
            }
        });

        // Cleanup current route
        if (this.currentRoute && typeof this.currentRoute.cleanup === 'function') {
            this.currentRoute.cleanup();
        }

        // Load new route
        const ViewClass = this.routes.get(routeName);
        this.currentRoute = new ViewClass();
        
        if (typeof this.currentRoute.render === 'function') {
            const mainContent = document.getElementById('mainContent');
            if (mainContent) {
                mainContent.innerHTML = '';
                mainContent.appendChild(this.currentRoute.render());
            }
        }

        // Initialize the view if it has an init method
        if (typeof this.currentRoute.init === 'function') {
            this.currentRoute.init();
        }
    }
}

export const router = new Router();
