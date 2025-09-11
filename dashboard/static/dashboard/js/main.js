// Dashboard main.js

document.addEventListener('DOMContentLoaded', function() {
    // Toggle sidebar
    const sidebarToggle = document.getElementById('sidebarCollapse');
    const sidebar = document.getElementById('sidebar');
    const content = document.getElementById('content');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('active');
            content.classList.toggle('active');
        });
    }
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    if (alerts.length > 0) {
        alerts.forEach(function(alert) {
            setTimeout(function() {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }, 5000);
        });
    }
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Date range picker initialization for filters (if datepicker is used)
    if (typeof flatpickr !== 'undefined') {
        const dateInputs = document.querySelectorAll('.datepicker');
        dateInputs.forEach(function(input) {
            flatpickr(input, {
                dateFormat: "Y-m-d",
                allowInput: true
            });
        });
    }
    
    // Handle status change forms (AJAX)
    const statusForms = document.querySelectorAll('.status-change-form');
    statusForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const url = this.getAttribute('action');
            const formData = new FormData(this);
            
            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Show success message
                    const alertBox = document.createElement('div');
                    alertBox.className = 'alert alert-success alert-dismissible fade show';
                    alertBox.innerHTML = 'Status updated successfully <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
                    
                    const alertContainer = document.querySelector('.alert-container') || document.querySelector('.container-fluid');
                    alertContainer.prepend(alertBox);
                    
                    // Auto-hide alert
                    setTimeout(function() {
                        bootstrap.Alert.getOrCreateInstance(alertBox).close();
                    }, 5000);
                    
                    // Update status badge if exists
                    const statusBadge = document.querySelector('.order-status-badge');
                    if (statusBadge) {
                        const status = formData.get('status');
                        statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                        
                        // Update badge class
                        statusBadge.className = 'badge order-status-badge';
                        if (status === 'pending') statusBadge.classList.add('bg-warning');
                        else if (status === 'processing') statusBadge.classList.add('bg-info');
                        else if (status === 'shipped') statusBadge.classList.add('bg-primary');
                        else if (status === 'delivered') statusBadge.classList.add('bg-success');
                        else if (status === 'cancelled') statusBadge.classList.add('bg-danger');
                        else statusBadge.classList.add('bg-secondary');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
    
    // Handle delete confirmations
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
    
    // Handle bulk actions
    const bulkActionForm = document.getElementById('bulk-action-form');
    if (bulkActionForm) {
        bulkActionForm.addEventListener('submit', function(e) {
            const action = document.getElementById('bulk-action').value;
            
            if (!action) {
                e.preventDefault();
                alert('Please select an action');
                return;
            }
            
            const checkboxes = document.querySelectorAll('input[name="selected_items"]:checked');
            if (checkboxes.length === 0) {
                e.preventDefault();
                alert('Please select at least one item');
                return;
            }
            
            if (action === 'delete' && !confirm('Are you sure you want to delete the selected items? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    }
    
    // Select all checkbox
    const selectAllCheckbox = document.getElementById('select-all');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('input[name="selected_items"]');
            checkboxes.forEach(function(checkbox) {
                checkbox.checked = selectAllCheckbox.checked;
            });
        });
    }
    
    // Product image preview
    const imageInputs = document.querySelectorAll('.image-input');
    imageInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const preview = document.querySelector(this.dataset.preview);
            if (preview && this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    });
});

// Function to toggle password visibility
function togglePasswordVisibility(fieldId, buttonId) {
    const passwordField = document.getElementById(fieldId);
    const toggleButton = document.getElementById(buttonId);
    
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
        toggleButton.innerHTML = '<i class="fas fa-eye-slash"></i>';
    } else {
        passwordField.type = 'password';
        toggleButton.innerHTML = '<i class="fas fa-eye"></i>';
    }
}

// Function to refresh data (can be used for charts or tables)
function refreshData(url, targetElement) {
    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Update target element with new data
            // Implementation depends on the specific use case
        })
        .catch(error => console.error('Error refreshing data:', error));
}

// Function to handle AJAX form submissions
function submitFormAjax(formId, successCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const url = this.getAttribute('action');
        const method = this.getAttribute('method') || 'POST';
        const formData = new FormData(this);
        
        fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (typeof successCallback === 'function') {
                successCallback(data);
            }
        })
        .catch(error => console.error('Form submission error:', error));
    });
}

// Function to format currency
function formatCurrency(amount, currencyCode = 'USD') {
    return new Intl.NumberFormat('en-US', { 
        style: 'currency', 
        currency: currencyCode 
    }).format(amount);
}

// Function to show loading spinner
function showLoading(container) {
    const spinner = document.createElement('div');
    spinner.className = 'spinner-border text-primary loading-spinner';
    spinner.setAttribute('role', 'status');
    spinner.innerHTML = '<span class="visually-hidden">Loading...</span>';
    
    // Clear container and add spinner
    container.innerHTML = '';
    container.appendChild(spinner);
}
