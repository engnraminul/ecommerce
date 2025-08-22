// Profile Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Set up CSRF token for AJAX requests
    const csrfToken = window.csrfToken || '';
    
    // No need for $.ajaxSetup since we're using fetch API
    // We'll add the CSRF token to each fetch request individually
    
    // Tab navigation
    const navItems = document.querySelectorAll('.profile-nav li');
    const profileSections = document.querySelectorAll('.profile-section');

    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-target');
            
            // Update active nav item
            navItems.forEach(navItem => navItem.classList.remove('active'));
            this.classList.add('active');
            
            // Show target section
            profileSections.forEach(section => {
                section.classList.remove('active');
                if (section.id === targetId) {
                    section.classList.add('active');
                }
            });
            
            // Update URL hash without scrolling
            history.pushState(null, null, `#${targetId}`);
        });
    });
    
    // Handle direct URL with hash
    const handleUrlHash = () => {
        if (location.hash) {
            const targetId = location.hash.substring(1);
            const targetTab = document.querySelector(`.profile-nav li[data-target="${targetId}"]`);
            if (targetTab) {
                targetTab.click();
            }
        }
    };
    
    // Initial check for hash in URL
    handleUrlHash();
    
    // Listen for hash changes
    window.addEventListener('hashchange', handleUrlHash);
    
    // Profile picture upload
    const profilePictureInput = document.getElementById('profile-picture-input');
    const profilePictureForm = document.getElementById('profile-picture-form');
    const profileImage = document.getElementById('profile-image');
    
    if (profilePictureInput) {
        profilePictureInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const formData = new FormData(profilePictureForm);
                formData.append('form_type', 'profile_picture');
                
                // Show loading indicator
                const profilePicture = document.querySelector('.profile-picture');
                profilePicture.classList.add('uploading');
                
                // Make AJAX request
                fetch('/api/v1/profile-picture/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    },
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    // Remove loading indicator
                    profilePicture.classList.remove('uploading');
                    
                    if (data.success) {
                        // Update profile image
                        if (profileImage) {
                            profileImage.src = data.image_url;
                        } else {
                            // If no image yet, replace initials div with image
                            const initialsDiv = document.querySelector('.profile-initials');
                            if (initialsDiv) {
                                const parentDiv = initialsDiv.parentNode;
                                initialsDiv.remove();
                                
                                const newImage = document.createElement('img');
                                newImage.src = data.image_url;
                                newImage.alt = 'Profile Picture';
                                newImage.id = 'profile-image';
                                parentDiv.prepend(newImage);
                            }
                        }
                        
                        // Show success message
                        showToast('Profile picture updated successfully!', 'success');
                    } else {
                        showToast(data.error || 'Failed to update profile picture', 'error');
                    }
                })
                .catch(error => {
                    // Remove loading indicator
                    profilePicture.classList.remove('uploading');
                    
                    console.error('Error:', error);
                    showToast('An error occurred while updating profile picture', 'error');
                });
            }
        });
    }
    
    // Address management
    const addAddressBtn = document.getElementById('add-address-btn');
    const emptyAddAddressBtn = document.getElementById('empty-add-address-btn');
    const addressModal = document.getElementById('address-modal');
    const addressForm = document.getElementById('address-form');
    const modalTitle = document.getElementById('address-modal-title');
    
    // Open modal for new address
    const openAddressModal = (isEdit = false, addressData = null) => {
        modalTitle.textContent = isEdit ? 'Edit Address' : 'Add New Address';
        
        // Reset form
        addressForm.reset();
        document.getElementById('address_id').value = '';
        
        // Fill form if editing
        if (isEdit && addressData) {
            document.getElementById('address_id').value = addressData.id;
            document.getElementById('address_type').value = addressData.type;
            document.getElementById('address_line_1').value = addressData.line1;
            document.getElementById('address_line_2').value = addressData.line2 || '';
            document.getElementById('city').value = addressData.city;
            document.getElementById('state').value = addressData.state;
            document.getElementById('postal_code').value = addressData.postal_code;
            document.getElementById('country').value = addressData.country;
            document.getElementById('is_default').checked = addressData.is_default;
        }
        
        // Show modal
        addressModal.classList.add('show');
    };
    
    // Button click handlers
    if (addAddressBtn) {
        addAddressBtn.addEventListener('click', () => openAddressModal());
    }
    
    if (emptyAddAddressBtn) {
        emptyAddAddressBtn.addEventListener('click', () => openAddressModal());
    }
    
    // Close modal
    document.querySelectorAll('[data-dismiss="modal"]').forEach(btn => {
        btn.addEventListener('click', () => {
            addressModal.classList.remove('show');
        });
    });
    
    // Close modal when clicking outside
    if (addressModal) {
        addressModal.addEventListener('click', (e) => {
            if (e.target === addressModal) {
                addressModal.classList.remove('show');
            }
        });
    }
    
    // Edit address button click
    document.querySelectorAll('.edit-address-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const addressId = this.getAttribute('data-id');
            
            // Fetch address data from server
            fetch(`/api/v1/addresses/${addressId}/`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                openAddressModal(true, data);
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Failed to load address data', 'error');
            });
        });
    });
    
    // Delete address button click
    document.querySelectorAll('.delete-address-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const addressId = this.getAttribute('data-id');
            if (confirm('Are you sure you want to delete this address?')) {
                // Send delete request
                fetch(`/api/v1/addresses/${addressId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrfToken
                    },
                    credentials: 'same-origin'
                })
                .then(response => {
                    if (response.ok) {
                        // Remove address card from UI
                        const addressCard = document.querySelector(`.address-card[data-id="${addressId}"]`);
                        if (addressCard) {
                            addressCard.remove();
                        }
                        showToast('Address deleted successfully', 'success');
                        
                        // Show empty state if no addresses left
                        const addressesContainer = document.querySelector('.addresses-container');
                        if (addressesContainer && !addressesContainer.querySelector('.address-card')) {
                            addressesContainer.innerHTML = `
                                <div class="empty-state">
                                    <i class="fas fa-map-marker-alt"></i>
                                    <h3>No Addresses Added</h3>
                                    <p>You haven't added any addresses yet. Add your shipping and billing addresses for faster checkout.</p>
                                    <button class="btn btn-primary" id="empty-add-address-btn">
                                        <i class="fas fa-plus"></i> Add New Address
                                    </button>
                                </div>
                            `;
                            // Re-attach event listener
                            document.getElementById('empty-add-address-btn').addEventListener('click', () => openAddressModal());
                        }
                    } else {
                        throw new Error('Failed to delete address');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Failed to delete address', 'error');
                });
            }
        });
    });
    
    // Set default address button click
    document.querySelectorAll('.set-default-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const addressId = this.getAttribute('data-id');
            const addressType = this.getAttribute('data-type');
            
            // Send update request
            fetch(`/api/v1/addresses/${addressId}/set_default/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin',
                body: JSON.stringify({ address_type: addressType })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update UI
                    document.querySelectorAll(`.address-card[data-type="${addressType}"]`).forEach(card => {
                        card.classList.remove('default');
                        const defaultBadge = card.querySelector('.default-badge');
                        if (defaultBadge) defaultBadge.remove();
                        
                        // Show Set as Default button
                        const setDefaultBtn = card.querySelector('.set-default-btn');
                        if (!setDefaultBtn) {
                            const actionsDiv = card.querySelector('.address-actions');
                            const editBtn = actionsDiv.querySelector('.edit-address-btn');
                            const newSetDefaultBtn = document.createElement('button');
                            newSetDefaultBtn.className = 'btn btn-sm set-default-btn';
                            newSetDefaultBtn.setAttribute('data-id', card.getAttribute('data-id'));
                            newSetDefaultBtn.setAttribute('data-type', addressType);
                            newSetDefaultBtn.innerHTML = '<i class="fas fa-check-circle"></i> Set as Default';
                            actionsDiv.insertBefore(newSetDefaultBtn, editBtn.nextSibling);
                        }
                    });
                    
                    // Update current address card
                    const currentCard = document.querySelector(`.address-card[data-id="${addressId}"]`);
                    currentCard.classList.add('default');
                    
                    // Add default badge
                    const header = currentCard.querySelector('.address-header');
                    const badge = document.createElement('span');
                    badge.className = 'default-badge';
                    badge.textContent = 'Default';
                    header.appendChild(badge);
                    
                    // Remove set as default button
                    const setDefaultBtn = currentCard.querySelector('.set-default-btn');
                    if (setDefaultBtn) setDefaultBtn.remove();
                    
                    showToast('Default address updated successfully', 'success');
                } else {
                    showToast(data.error || 'Failed to update default address', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('An error occurred while updating default address', 'error');
            });
        });
    });
    
    // Address form submission
    if (addressForm) {
        addressForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const addressId = document.getElementById('address_id').value;
            const isEdit = !!addressId;
            
            // Send to server
            const url = isEdit ? `/api/v1/addresses/${addressId}/` : '/api/v1/addresses/';
            const method = isEdit ? 'PUT' : 'POST';
            
            fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Close modal
                    addressModal.classList.remove('show');
                    
                    // Reload page to show updated addresses
                    window.location.reload();
                } else {
                    showToast(data.error || 'Failed to save address', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('An error occurred while saving the address', 'error');
            });
        });
    }
    
    // Password strength meter
    const passwordInput = document.getElementById('new_password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const strengthBar = document.querySelector('.strength-bar');
    const strengthText = document.querySelector('.password-strength-text span');
    const matchText = document.querySelector('.password-match-text');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            
            // Update strength indicator
            strengthBar.className = 'strength-bar';
            strengthText.textContent = '';
            
            if (password) {
                switch(strength) {
                    case 0:
                        strengthBar.classList.add('strength-weak');
                        strengthText.textContent = 'Weak';
                        break;
                    case 1:
                        strengthBar.classList.add('strength-fair');
                        strengthText.textContent = 'Fair';
                        break;
                    case 2:
                        strengthBar.classList.add('strength-good');
                        strengthText.textContent = 'Good';
                        break;
                    case 3:
                        strengthBar.classList.add('strength-strong');
                        strengthText.textContent = 'Strong';
                        break;
                }
            }
            
            // Check match if confirm password has value
            if (confirmPasswordInput && confirmPasswordInput.value) {
                checkPasswordMatch();
            }
        });
    }
    
    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', checkPasswordMatch);
    }
    
    function checkPasswordMatch() {
        if (!passwordInput || !confirmPasswordInput || !matchText) return;
        
        const password = passwordInput.value;
        const confirmPassword = confirmPasswordInput.value;
        
        if (!confirmPassword) {
            matchText.textContent = '';
            matchText.className = 'password-match-text form-text';
            return;
        }
        
        if (password === confirmPassword) {
            matchText.textContent = 'Passwords match';
            matchText.className = 'password-match-text form-text password-match-success';
        } else {
            matchText.textContent = 'Passwords do not match';
            matchText.className = 'password-match-text form-text password-match-error';
        }
    }
    
    function checkPasswordStrength(password) {
        let strength = 0;
        
        // Length check
        if (password.length >= 8) strength += 1;
        
        // Character variety check
        if (/[A-Z]/.test(password) && /[a-z]/.test(password)) strength += 1;
        if (/[0-9]/.test(password)) strength += 0.5;
        if (/[^A-Za-z0-9]/.test(password)) strength += 0.5;
        
        return Math.min(Math.floor(strength), 3);
    }
    
    // Disable submit button if passwords don't match
    const passwordForm = document.getElementById('password-form');
    const changePasswordBtn = document.getElementById('change-password-btn');
    
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            
            if (password !== confirmPassword) {
                e.preventDefault();
                showToast('Passwords do not match', 'error');
                return false;
            }
            
            // Additional validation could be added here
            return true;
        });
    }
    
    // Toast notification function
    function showToast(message, type = 'info') {
        // Check if toast container exists, create if not
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container';
            document.body.appendChild(toastContainer);
        }
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <i class="${getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="toast-close">&times;</button>
        `;
        
        // Add toast to container
        toastContainer.appendChild(toast);
        
        // Show toast with animation
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);
        
        // Close button functionality
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
            }, 300);
        });
        
        // Auto close after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.remove('show');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.remove();
                    }
                }, 300);
            }
        }, 5000);
    }
    
    function getToastIcon(type) {
        switch (type) {
            case 'success': return 'fas fa-check-circle';
            case 'error': return 'fas fa-exclamation-circle';
            case 'warning': return 'fas fa-exclamation-triangle';
            default: return 'fas fa-info-circle';
        }
    }
});
