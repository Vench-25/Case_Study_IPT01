
document.addEventListener('DOMContentLoaded', function () {
    const root = document.documentElement;
    const themePicker = document.querySelector('[data-theme-picker]');
    const themeStorageKey = 'neust-event-theme';
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');

    function applyTheme(preference) {
        const resolved = preference === 'system'
            ? (systemTheme.matches ? 'dark' : 'light')
            : preference;
        root.dataset.bsTheme = resolved;
        root.dataset.themePreference = preference;
        if (themePicker) {
            themePicker.value = preference;
        }
    }

    if (themePicker) {
        const initialPreference = root.dataset.themePreference || 'system';
        applyTheme(initialPreference);
        themePicker.addEventListener('change', function () {
            const preference = themePicker.value;
            try {
                localStorage.setItem(themeStorageKey, preference);
            } catch (error) {
                const announcement = document.querySelector('[data-ui-announcement]');
                if (announcement) {
                    announcement.textContent = 'The theme could not be saved and will apply only for this page.';
                }
            }
            applyTheme(preference);
        });
        systemTheme.addEventListener('change', function () {
            if (root.dataset.themePreference === 'system') {
                applyTheme('system');
            }
        });
    }

    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    const mobileBreakpoint = window.matchMedia('(max-width: 991.98px)');

    if (sidebarToggle && sidebar && sidebarOverlay) {
        function setSidebarOpen(isOpen, restoreFocus) {
            sidebar.classList.toggle('show', isOpen);
            sidebarOverlay.classList.toggle('show', isOpen);
            sidebarToggle.setAttribute('aria-expanded', String(isOpen));
            sidebarToggle.setAttribute('aria-label', isOpen ? 'Close navigation' : 'Open navigation');
            sidebar.inert = mobileBreakpoint.matches && !isOpen;
            document.body.classList.toggle('navigation-open', mobileBreakpoint.matches && isOpen);
            if (!isOpen && restoreFocus) {
                sidebarToggle.focus();
            }
        }

        function updateNavigationForViewport() {
            if (mobileBreakpoint.matches) {
                document.body.classList.remove('sidebar-collapsed');
                setSidebarOpen(false, false);
            } else {
                sidebar.classList.remove('show');
                sidebarOverlay.classList.remove('show');
                sidebar.inert = false;
                document.body.classList.remove('navigation-open');
                sidebarToggle.setAttribute('aria-expanded', String(!document.body.classList.contains('sidebar-collapsed')));
                sidebarToggle.setAttribute(
                    'aria-label',
                    document.body.classList.contains('sidebar-collapsed') ? 'Expand navigation' : 'Collapse navigation'
                );
            }
        }

        try {
            if (localStorage.getItem('neust-sidebar-collapsed') === 'true' && !mobileBreakpoint.matches) {
                document.body.classList.add('sidebar-collapsed');
            }
        } catch (error) {
            console.warn('The navigation collapse preference could not be loaded.');
        }

        sidebarToggle.addEventListener('click', function () {
            if (mobileBreakpoint.matches) {
                const isOpen = !sidebar.classList.contains('show');
                setSidebarOpen(isOpen, false);
                if (isOpen) {
                    const firstLink = sidebar.querySelector('a, button');
                    if (firstLink) firstLink.focus();
                }
                return;
            }

            const isCollapsed = document.body.classList.toggle('sidebar-collapsed');
            sidebarToggle.setAttribute('aria-expanded', String(!isCollapsed));
            sidebarToggle.setAttribute('aria-label', isCollapsed ? 'Expand navigation' : 'Collapse navigation');
            try {
                localStorage.setItem('neust-sidebar-collapsed', String(isCollapsed));
            } catch (error) {
                console.warn('The navigation collapse preference could not be saved.');
            }
        });

        sidebarOverlay.addEventListener('click', function () {
            setSidebarOpen(false, true);
        });

        sidebar.addEventListener('click', function (event) {
            if (mobileBreakpoint.matches && event.target.closest('a')) {
                setSidebarOpen(false, false);
            }
        });

        document.addEventListener('keydown', function (event) {
            if (!mobileBreakpoint.matches || !sidebar.classList.contains('show')) {
                return;
            }
            if (event.key === 'Escape') {
                setSidebarOpen(false, true);
                return;
            }
            if (event.key === 'Tab') {
                const focusable = Array.from(sidebar.querySelectorAll('a[href], button:not([disabled])'));
                if (!focusable.length) return;
                const first = focusable[0];
                const last = focusable[focusable.length - 1];
                if (event.shiftKey && document.activeElement === first) {
                    event.preventDefault();
                    last.focus();
                } else if (!event.shiftKey && document.activeElement === last) {
                    event.preventDefault();
                    first.focus();
                }
            }
        });

        mobileBreakpoint.addEventListener('change', updateNavigationForViewport);
        updateNavigationForViewport();
    }

    document.querySelectorAll('[data-password-toggle]').forEach(function (button) {
        const input = document.getElementById(button.dataset.passwordToggle);
        if (!input) return;
        button.addEventListener('click', function () {
            const isVisible = input.type === 'text';
            input.type = isVisible ? 'password' : 'text';
            button.setAttribute('aria-pressed', String(!isVisible));
            button.setAttribute('aria-label', isVisible ? 'Show password' : 'Hide password');
            button.querySelector('i').className = isVisible ? 'bi bi-eye' : 'bi bi-eye-slash';
        });
    });

    document.querySelectorAll('[data-table-search]').forEach(function (searchInput) {
        const table = document.getElementById(searchInput.dataset.tableSearch);
        if (!table) return;

        const rows = Array.from(table.querySelectorAll('[data-search-row]'));
        searchInput.addEventListener('input', function () {
            const query = searchInput.value.trim().toLocaleLowerCase();
            rows.forEach(function (row) {
                row.hidden = query !== '' && !row.textContent.toLocaleLowerCase().includes(query);
            });
        });
    });

    document.querySelectorAll('[data-print-trigger]').forEach(function (button) {
        button.addEventListener('click', function () {
            window.print();
        });
    });

    document.querySelectorAll('[data-confirm]').forEach(function (element) {
        element.addEventListener('click', function (event) {
            const message = element.getAttribute('data-confirm') || 'Are you sure you want to proceed?';
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
