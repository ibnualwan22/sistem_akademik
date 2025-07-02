// ==============================================
// MODERN COLORFUL THEME 2.0 - INTERAKTIVITAS
// Complete Redesign Version
// ==============================================

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Dynamic Gradient Background Animation
    let gradientAngle = 0;
    setInterval(() => {
        gradientAngle = (gradientAngle + 1) % 360;
        document.documentElement.style.setProperty('--gradient-angle', gradientAngle + 'deg');
    }, 50);

    // 2. Advanced Particle System
    class ParticleSystem {
        constructor() {
            this.particles = [];
            this.colors = ['#667eea', '#f093fb', '#11998e', '#2af598', '#fc4a1a'];
            this.init();
        }

        init() {
            for (let i = 0; i < 5; i++) {
                this.createParticle();
            }
            this.animate();
        }

        createParticle() {
            const particle = document.createElement('div');
            particle.className = 'floating-particle';
            
            const color = this.colors[Math.floor(Math.random() * this.colors.length)];
            const size = Math.random() * 8 + 4;
            const duration = Math.random() * 20 + 20;
            const delay = Math.random() * 10;
            const startX = Math.random() * window.innerWidth;
            const opacity = Math.random() * 0.5 + 0.3;
            
            particle.style.cssText = `
                position: fixed;
                width: ${size}px;
                height: ${size}px;
                background: ${color};
                border-radius: 50%;
                left: ${startX}px;
                bottom: -50px;
                pointer-events: none;
                z-index: 0;
                opacity: ${opacity};
                filter: blur(1px);
                animation: floatUpwards ${duration}s ${delay}s linear infinite;
            `;
            
            document.body.appendChild(particle);
            this.particles.push(particle);
            
            // Remove old particles
            if (this.particles.length > 20) {
                const oldParticle = this.particles.shift();
                oldParticle.remove();
            }
        }

        animate() {
            setInterval(() => {
                this.createParticle();
            }, 3000);
        }
    }

    // Initialize particle system
    new ParticleSystem();

    // 3. Enhanced Card 3D Tilt Effect
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(20px)`;
            
            // Add shine effect
            const shine = card.querySelector('.card-shine') || createShine(card);
            const shineX = (x / rect.width) * 100;
            const shineY = (y / rect.height) * 100;
            shine.style.background = `radial-gradient(circle at ${shineX}% ${shineY}%, rgba(255,255,255,0.3) 0%, transparent 70%)`;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
            const shine = card.querySelector('.card-shine');
            if (shine) shine.style.background = 'transparent';
        });
    });

    function createShine(card) {
        const shine = document.createElement('div');
        shine.className = 'card-shine';
        shine.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            border-radius: inherit;
            transition: background 0.3s ease;
        `;
        card.style.position = 'relative';
        card.appendChild(shine);
        return shine;
    }

    // 4. Animated Number Counters with Easing
    function animateValue(element, start, end, duration) {
        const startTimestamp = Date.now();
        const step = (timestamp) => {
            const progress = Math.min((Date.now() - startTimestamp) / duration, 1);
            const easeOutQuart = 1 - Math.pow(1 - progress, 4);
            element.textContent = Math.floor(easeOutQuart * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    const counters = document.querySelectorAll('.card-text');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.animated) {
                const target = parseInt(entry.target.textContent);
                if (!isNaN(target)) {
                    entry.target.animated = true;
                    animateValue(entry.target, 0, target, 2000);
                }
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => {
        if (counter.textContent.match(/^\d+$/)) {
            observer.observe(counter);
        }
    });

    // 5. Rainbow Progress Bar
    const progressBar = document.createElement('div');
    progressBar.className = 'page-progress';
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        height: 4px;
        background: linear-gradient(90deg, 
            #667eea 0%, 
            #764ba2 20%, 
            #f093fb 40%, 
            #f5576c 60%, 
            #2af598 80%, 
            #009efd 100%
        );
        background-size: 200% 100%;
        animation: rainbowSlide 3s linear infinite;
        z-index: 10000;
        transition: width 0.3s ease;
        box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
    `;
    document.body.appendChild(progressBar);

    window.addEventListener('scroll', () => {
        const scrollPercentage = (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;
        progressBar.style.width = scrollPercentage + '%';
    });

    // 6. Advanced Ripple Effect
    function createRipple(e, element) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.5) 0%, transparent 70%);
            left: ${x}px;
            top: ${y}px;
            transform: scale(0);
            animation: rippleEffect 0.8s ease-out;
            pointer-events: none;
        `;
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 800);
    }

    // Apply ripple to all buttons and clickable elements
    document.querySelectorAll('.btn, .list-group-item-action, .card-link-wrapper').forEach(element => {
        element.addEventListener('click', function(e) {
            createRipple(e, this);
        });
    });

    // 7. Modern Toast Notification System
    class ToastNotification {
        constructor() {
            this.container = this.createContainer();
        }

        createContainer() {
            const container = document.createElement('div');
            container.className = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            `;
            document.body.appendChild(container);
            return container;
        }

        show(message, type = 'info', duration = 3000) {
            const toast = document.createElement('div');
            toast.className = 'modern-toast';
            
            const gradients = {
                'success': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
                'error': 'linear-gradient(135deg, #eb3349 0%, #f45c43 100%)',
                'warning': 'linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%)',
                'info': 'linear-gradient(135deg, #2af598 0%, #009efd 100%)'
            };
            
            const icons = {
                'success': '✓',
                'error': '✕',
                'warning': '!',
                'info': 'i'
            };
            
            toast.style.cssText = `
                display: flex;
                align-items: center;
                gap: 15px;
                background: white;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                min-width: 300px;
                transform: translateX(400px);
                transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                position: relative;
                overflow: hidden;
            `;
            
            const iconElement = document.createElement('div');
            iconElement.style.cssText = `
                width: 30px;
                height: 30px;
                background: ${gradients[type]};
                color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                flex-shrink: 0;
            `;
            iconElement.textContent = icons[type];
            
            const messageElement = document.createElement('div');
            messageElement.textContent = message;
            messageElement.style.cssText = `
                flex: 1;
                color: #2d3436;
                font-weight: 500;
            `;
            
            const progressBar = document.createElement('div');
            progressBar.style.cssText = `
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: ${gradients[type]};
                animation: shrinkWidth ${duration}ms linear;
            `;
            
            toast.appendChild(iconElement);
            toast.appendChild(messageElement);
            toast.appendChild(progressBar);
            this.container.appendChild(toast);
            
            // Animate in
            setTimeout(() => {
                toast.style.transform = 'translateX(0)';
            }, 10);
            
            // Animate out and remove
            setTimeout(() => {
                toast.style.transform = 'translateX(400px)';
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
    }

    // Make toast globally available
    window.toast = new ToastNotification();

    // 8. Table Row Stagger Animation
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach((row, index) => {
        row.style.opacity = '0';
        row.style.transform = 'translateY(20px)';
        setTimeout(() => {
            row.style.transition = 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)';
            row.style.opacity = '1';
            row.style.transform = 'translateY(0)';
        }, index * 50);
    });

    // 9. Search Input Enhancement
    const searchInputs = document.querySelectorAll('input[type="text"], input[type="search"]');
    searchInputs.forEach(input => {
        const wrapper = input.closest('.input-group') || input.parentElement;
        
        input.addEventListener('focus', function() {
            wrapper.style.transform = 'scale(1.02)';
            wrapper.style.boxShadow = '0 10px 30px rgba(102, 126, 234, 0.2)';
        });
        
        input.addEventListener('blur', function() {
            wrapper.style.transform = 'scale(1)';
            wrapper.style.boxShadow = '';
        });
    });

    // 10. Image Loading with Blur Effect
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.style.filter = 'blur(20px)';
        img.style.transition = 'filter 0.5s ease';
        
        if (img.complete) {
            img.style.filter = 'blur(0)';
        } else {
            img.addEventListener('load', function() {
                this.style.filter = 'blur(0)';
            });
        }
    });

    // 11. Smooth Scroll for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // 12. Dynamic Theme Color on Scroll
    let lastScrollY = window.scrollY;
    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        const header = document.querySelector('.main-header');
        
        if (header) {
            if (currentScrollY > 100) {
                header.style.background = 'rgba(255, 255, 255, 0.95)';
                header.style.backdropFilter = 'blur(10px)';
            } else {
                header.style.background = 'white';
                header.style.backdropFilter = 'none';
            }
        }
        
        lastScrollY = currentScrollY;
    });

    // 13. Tab Switch Animation Enhancement
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetPane = document.querySelector(this.getAttribute('data-bs-target'));
            if (targetPane) {
                targetPane.style.opacity = '0';
                targetPane.style.transform = 'translateX(20px)';
                setTimeout(() => {
                    targetPane.style.transition = 'all 0.3s ease';
                    targetPane.style.opacity = '1';
                    targetPane.style.transform = 'translateX(0)';
                }, 100);
            }
        });
    });

    // 14. Card Hover Sound Effect (optional)
    const hoverSound = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBi+H0fPTgjMGHm7A7+OZURE');
    hoverSound.volume = 0.05;

    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            // Uncomment to enable sound
            // hoverSound.currentTime = 0;
            // hoverSound.play();
        });
    });

});

// Additional CSS animations
const additionalStyles = `
@keyframes floatUpwards {
    to {
        transform: translateY(-100vh) translateX(100px) rotate(360deg);
        opacity: 0;
    }
}

@keyframes rainbowSlide {
    0% { background-position: 0% 50%; }
    100% { background-position: 200% 50%; }
}

@keyframes rippleEffect {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

@keyframes shrinkWidth {
    from { width: 100%; }
    to { width: 0%; }
}

.card-shine {
    z-index: 1;
}

.modern-toast {
    animation: slideIn 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes slideIn {
    from { transform: translateX(400px); }
    to { transform: translateX(0); }
}
`;

// Inject additional CSS
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);