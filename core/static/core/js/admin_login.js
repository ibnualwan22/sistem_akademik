document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.querySelector('.login-btn');
    const inputs = document.querySelectorAll('.form-input');
    const form = document.querySelector('form');
    
    // Form submission handling
    if (form) {
        form.addEventListener('submit', function(e) {
            let hasError = false;
            
            // Validate inputs
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    input.classList.add('error');
                    hasError = true;
                    
                    setTimeout(() => {
                        input.classList.remove('error');
                    }, 1000);
                }
            });
            
            if (!hasError && loginBtn) {
                loginBtn.innerHTML = '⏳ Memproses...';
                loginBtn.disabled = true;
                loginBtn.style.opacity = '0.7';
            }
        });
    }
    
    // Remove error class on input
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('error');
        });
        
        // Add focus effect
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'translateY(-2px)';
            this.parentElement.style.transition = 'transform 0.3s ease';
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'translateY(0)';
        });
    });
    
    // Auto-hide messages
    const messages = document.querySelectorAll('.alert');
    messages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateX(100px)';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 5000);
    });
    
    // Add click to close messages
    messages.forEach(message => {
        message.style.cursor = 'pointer';
        message.addEventListener('click', function() {
            this.style.opacity = '0';
            this.style.transform = 'translateX(100px)';
            setTimeout(() => {
                this.remove();
            }, 300);
        });
    });
    
    // Add interactive header buttons
    const menuBtn = document.querySelector('.menu-btn');
    const navIcons = document.querySelectorAll('.nav-icon');
    
    if (menuBtn) {
        menuBtn.addEventListener('click', function() {
            this.style.transform = 'rotate(90deg)';
            setTimeout(() => {
                this.style.transform = 'rotate(0deg)';
            }, 300);
        });
    }
    
    navIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            this.style.transform = 'scale(0.9)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
    
    // Add particle effect on login button hover
    if (loginBtn) {
        loginBtn.addEventListener('mouseenter', function() {
            createParticles(this);
        });
    }
    
    function createParticles(element) {
        for (let i = 0; i < 3; i++) {
            const particle = document.createElement('div');
            particle.style.position = 'absolute';
            particle.style.width = '4px';
            particle.style.height = '4px';
            particle.style.background = 'rgba(255, 255, 255, 0.8)';
            particle.style.borderRadius = '50%';
            particle.style.pointerEvents = 'none';
            particle.style.zIndex = '1000';
            
            const rect = element.getBoundingClientRect();
            particle.style.left = (rect.left + Math.random() * rect.width) + 'px';
            particle.style.top = (rect.top + Math.random() * rect.height) + 'px';
            
            document.body.appendChild(particle);
            
            // Animate particle
            particle.animate([
                { transform: 'translateY(0px)', opacity: 1 },
                { transform: 'translateY(-20px)', opacity: 0 }
            ], {
                duration: 800,
                easing: 'ease-out'
            }).onfinish = () => {
                particle.remove();
            };
        }
    }
    
    // Add typing effect for placeholder
    const usernameInput = document.getElementById('id_username');
    const passwordInput = document.getElementById('id_password');
    
    if (usernameInput && passwordInput) {
        const placeholders = [
            'Masukkan nama pengguna',
            'Username Anda',
            'Nama pengguna'
        ];
        
        let currentPlaceholder = 0;
        
        setInterval(() => {
            if (usernameInput !== document.activeElement && !usernameInput.value) {
                usernameInput.placeholder = placeholders[currentPlaceholder];
                currentPlaceholder = (currentPlaceholder + 1) % placeholders.length;
            }
        }, 3000);
    }
    
    // Add subtle animation to dots
    const dots = document.querySelectorAll('.dot');
    dots.forEach((dot, index) => {
        dot.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.5)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        dot.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1)';
        });
    });
    
    // Add keyboard navigation
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.tagName !== 'BUTTON') {
            const nextInput = getNextInput(e.target);
            if (nextInput) {
                nextInput.focus();
            } else if (loginBtn) {
                loginBtn.click();
            }
        }
    });
    
    function getNextInput(currentInput) {
        const inputList = Array.from(inputs);
        const currentIndex = inputList.indexOf(currentInput);
        return inputList[currentIndex + 1];
    }
});