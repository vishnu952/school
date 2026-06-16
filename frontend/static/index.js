    document.addEventListener('DOMContentLoaded', () => {
        // Global Logo Integration: Use the web-accessible path and ensure the element exists



        const menuToggle = document.getElementById('menu-toggle');
        const navLinks = document.querySelector('.nav-links');

        // Toggle menu and animation
        if (menuToggle && navLinks) {
            menuToggle.addEventListener('click', () => {
                menuToggle.classList.toggle('active');
                navLinks.classList.toggle('active');
            });
        }

        // Close button inside menu: Added safety check to prevent crash
        const closeMenuBtn = document.getElementById('close-menu');
        if (closeMenuBtn && menuToggle && navLinks) {
            closeMenuBtn.addEventListener('click', () => {
                menuToggle.classList.remove('active');
                navLinks.classList.remove('active');
            });
        }

        // Close menu when a link is clicked
        document.querySelectorAll('.nav-links a').forEach(link => {
            link.addEventListener('click', () => {
                if (menuToggle) menuToggle.classList.remove('active');
                if (navLinks) navLinks.classList.remove('active');
            });
        });
    });


    


//  <!-- ==================== LOGICAL INTERACTIVE SCRIPT SYSTEM ==================== -->
   
        // Hero Carousel Data Store
        const carouselImages = [
            "https://images.unsplash.com/photo-1541339907198-e08756dedf3f?auto=format&fit=crop&w=1600&q=80",
            "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?auto=format&fit=crop&w=1600&q=80",
            "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=1600&q=80"
        ];
        let currentCarouselIndex = 0;

        function setCarousel(index) {
            currentCarouselIndex = index;
            const imgElement = document.getElementById('carousel-img');
            if (imgElement) {
                imgElement.src = carouselImages[currentCarouselIndex];
            }
            
            // Highlight current active pagination indicator
            const dots = document.querySelectorAll('.carousel-dot');
            dots.forEach((dot, idx) => {
                if (idx === currentCarouselIndex) {
                    dot.className = "carousel-dot w-6 h-1.5 rounded-full bg-brand-600 cursor-pointer transition-all";
                } else {
                    dot.className = "carousel-dot w-2 h-2 rounded-full bg-slate-300 cursor-pointer transition-all";
                }
            });
        }

        // Rotate slide manually via arrow indicators matching whiteboard sketch
        function rotateCarousel(direction) {
            let nextIndex = (currentCarouselIndex + direction + carouselImages.length) % carouselImages.length;
            setCarousel(nextIndex);
        }

        // Automatic Carousel rotation loop
        setInterval(() => {
            rotateCarousel(1);
        }, 8000);

        // SPA Navigation Views switching logic
        function switchView(viewName) {
            const views = {
                'home': document.getElementById('view-home'),
                'about': document.getElementById('view-about'),
                'contact': document.getElementById('view-contact')
            };

            const options = {
                'home': document.getElementById('opt-home'),
                'about': document.getElementById('opt-about'),
                'contact': document.getElementById('opt-contact')
            };

            // Toggle view panels
            Object.keys(views).forEach(key => {
                if (views[key]) {
                    if (key === viewName) {
                        views[key].classList.remove('hidden');
                        views[key].classList.add('block');
                    } else {
                        views[key].classList.remove('block');
                        views[key].classList.add('hidden');
                    }
                }
            });

            // Toggle active styles inside nested menu options
            Object.keys(options).forEach(key => {
                if (options[key]) {
                    if (key === viewName) {
                        options[key].className = "w-full flex items-center gap-2.5 p-2 rounded-lg text-brand-600 bg-brand-50/50 font-bold text-left transition-colors";
                    } else {
                        options[key].className = "w-full flex items-center gap-2.5 p-2 rounded-lg text-slate-600 hover:bg-slate-50 font-semibold text-left transition-colors";
                    }
                }
            });

            // Scroll smoothly to top of active card space
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        // Dropdown Toggle for "Menu" button
        function toggleNavigationMenu() {
            const dropdown = document.getElementById('navigation-dropdown');
            const chevron = document.getElementById('menu-chevron');
            if (dropdown) {
                const isHidden = dropdown.classList.contains('hidden');
                if (isHidden) {
                    dropdown.classList.remove('hidden');
                    if (chevron) chevron.style.transform = 'rotate(180deg)';
                } else {
                    dropdown.classList.add('hidden');
                    if (chevron) chevron.style.transform = 'rotate(0deg)';
                }
            }
        }

        // Dropdown Toggle for User Profile Popover
        function toggleProfileDropdown() {
            const panel = document.getElementById('profile-dropdown');
            if (panel) {
                panel.classList.toggle('hidden');
            }
        }

        // Close dropdowns if clicked outside
        window.addEventListener('click', function(e) {
            const menuToggle = document.getElementById('menu-toggle-btn');
            const menuDropdown = document.getElementById('navigation-dropdown');
            if (menuToggle && menuDropdown && !menuToggle.contains(e.target) && !menuDropdown.contains(e.target)) {
                menuDropdown.classList.add('hidden');
                const chevron = document.getElementById('menu-chevron');
                if (chevron) chevron.style.transform = 'rotate(0deg)';
            }
        });

        // Notification Modal popup triggers
        function showNotice(text) {
            const toast = document.getElementById('toast-notice');
            const message = document.getElementById('toast-message');
            if (toast && message) {
                message.textContent = text;
                toast.classList.remove('hidden');
                toast.classList.add('flex');
                
                // Automatically auto-close alert after 4 seconds
                setTimeout(() => {
                    dismissNotice();
                }, 4000);
            }
        }

        function dismissNotice() {
            const toast = document.getElementById('toast-notice');
            if (toast) {
                toast.classList.remove('flex');
                toast.classList.add('hidden');
            }
        }

        // Document initialize trigger on load
        window.onload = function () {
            switchView('home');
        };
  