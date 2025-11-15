/**
 * Backup Management Dashboard JavaScript
 */

class BackupDashboard {
    constructor() {
        this.apiBase = '/backup/api/';
        this.currentPage = 1;
        this.pageSize = 10;
        this.activeOperations = new Set(); // Track active backup/restore operations
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadStatistics();
        this.loadBackups();
        this.loadRestores();
        this.loadSchedules();
        this.loadSettings();
        this.loadAvailableBackups();
        this.setupFileUploads();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Tab switching
        document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const targetTab = e.target.getAttribute('data-bs-target');
                if (targetTab === '#backups') {
                    this.loadBackups();
                } else if (targetTab === '#restores') {
                    this.loadRestores();
                } else if (targetTab === '#schedules') {
                    this.loadSchedules();
                }
            });
        });

        // Form submissions
        document.getElementById('createBackupForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createBackup();
        });

        document.getElementById('restoreFromBackupForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.restoreFromBackup();
        });

        document.getElementById('uploadRestoreForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadAndRestore();
        });

        document.getElementById('createScheduleForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createSchedule();
        });

        document.getElementById('settingsForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSettings();
        });

        // Filters
        document.getElementById('backupTypeFilter').addEventListener('change', () => this.loadBackups());
        document.getElementById('backupStatusFilter').addEventListener('change', () => this.loadBackups());
        document.getElementById('backupSearch').addEventListener('input', this.debounce(() => this.loadBackups(), 500));

        // Buttons
        document.getElementById('testSettingsBtn').addEventListener('click', () => this.testSettings());
        document.getElementById('cleanupBtn').addEventListener('click', () => this.cleanupOldBackups());

        // Schedule type change
        document.getElementById('scheduleType').addEventListener('change', (e) => {
            this.toggleScheduleOptions(e.target.value);
        });

        // Backup selection change
        document.getElementById('selectBackup').addEventListener('change', (e) => {
            this.showBackupDetails(e.target.value);
        });

        // Modal event listeners - reload available backups when restore modal opens
        const restoreModal = document.getElementById('restoreFromBackupModal');
        if (restoreModal) {
            restoreModal.addEventListener('show.bs.modal', () => {
                console.log('Restore modal opening, reloading backups...');
                this.loadAvailableBackups();
            });
        }
    }

    setupFileUploads() {
        // Database file upload
        const databaseZone = document.getElementById('databaseUploadZone');
        const databaseInput = document.getElementById('databaseFile');
        
        databaseZone.addEventListener('click', () => databaseInput.click());
        databaseZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            databaseZone.classList.add('dragover');
        });
        databaseZone.addEventListener('dragleave', () => {
            databaseZone.classList.remove('dragover');
        });
        databaseZone.addEventListener('drop', (e) => {
            e.preventDefault();
            databaseZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                databaseInput.files = files;
                this.showFileInfo('database', files[0]);
            }
        });
        
        databaseInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.showFileInfo('database', e.target.files[0]);
            }
        });

        // Media file upload
        const mediaZone = document.getElementById('mediaUploadZone');
        const mediaInput = document.getElementById('mediaFile');
        
        mediaZone.addEventListener('click', () => mediaInput.click());
        mediaZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            mediaZone.classList.add('dragover');
        });
        mediaZone.addEventListener('dragleave', () => {
            mediaZone.classList.remove('dragover');
        });
        mediaZone.addEventListener('drop', (e) => {
            e.preventDefault();
            mediaZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                mediaInput.files = files;
                this.showFileInfo('media', files[0]);
            }
        });
        
        mediaInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.showFileInfo('media', e.target.files[0]);
            }
        });

        // Remove file buttons
        document.getElementById('removeDatabaseFile').addEventListener('click', () => {
            document.getElementById('databaseFile').value = '';
            document.getElementById('databaseFileInfo').style.display = 'none';
        });
        
        document.getElementById('removeMediaFile').addEventListener('click', () => {
            document.getElementById('mediaFile').value = '';
            document.getElementById('mediaFileInfo').style.display = 'none';
        });

        // Restore type change for upload modal
        document.getElementById('uploadRestoreType').addEventListener('change', (e) => {
            this.toggleUploadSections(e.target.value);
        });
    }

    showFileInfo(type, file) {
        const fileName = document.getElementById(`${type}FileName`);
        const fileSize = document.getElementById(`${type}FileSize`);
        const fileInfo = document.getElementById(`${type}FileInfo`);
        
        fileName.textContent = file.name;
        fileSize.textContent = this.formatBytes(file.size);
        fileInfo.style.display = 'block';
    }

    toggleUploadSections(restoreType) {
        const databaseSection = document.getElementById('databaseUploadSection');
        const mediaSection = document.getElementById('mediaUploadSection');
        
        if (restoreType === 'database') {
            databaseSection.style.display = 'block';
            mediaSection.style.display = 'none';
        } else if (restoreType === 'media') {
            databaseSection.style.display = 'none';
            mediaSection.style.display = 'block';
        } else {
            databaseSection.style.display = 'block';
            mediaSection.style.display = 'block';
        }
    }

    async loadStatistics() {
        try {
            const response = await fetch(`${this.apiBase}statistics/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const stats = await response.json();
            
            document.getElementById('totalBackups').textContent = stats.total_backups;
            document.getElementById('completedBackups').textContent = stats.completed_backups;
            document.getElementById('failedBackups').textContent = stats.failed_backups;
            document.getElementById('totalRestores').textContent = stats.total_restores || 0;
        } catch (error) {
            console.error('Error loading statistics:', error);
        }
    }

    async loadBackups() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                page_size: this.pageSize,
            });

            // Add filters
            const typeFilter = document.getElementById('backupTypeFilter').value;
            const statusFilter = document.getElementById('backupStatusFilter').value;
            const search = document.getElementById('backupSearch').value;
            
            if (typeFilter) params.append('type', typeFilter);
            if (statusFilter) params.append('status', statusFilter);
            if (search) params.append('search', search);

            const response = await fetch(`${this.apiBase}backups/?${params}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Check for completed operations and hide progress if needed
            this.checkCompletedOperations(data.results || data, 'backup');
            
            this.renderBackupsTable(data.results || data);
            if (data.count) {
                this.renderPagination('backups', data.count);
            }
        } catch (error) {
            console.error('Error loading backups:', error);
        }
    }

    renderBackupsTable(backups) {
        const tbody = document.getElementById('backupsTableBody');
        
        if (!backups.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No backups found</td></tr>';
            return;
        }

        tbody.innerHTML = backups.map(backup => `
            <tr>
                <td>
                    <strong>${backup.name}</strong>
                    ${backup.description ? `<br><small class="text-muted">${backup.description}</small>` : ''}
                </td>
                <td>
                    <span class="badge backup-type-badge bg-info">${backup.backup_type_display}</span>
                </td>
                <td>
                    <span class="badge status-badge ${this.getStatusBadgeClass(backup.status)}">${backup.status_display}</span>
                    ${backup.status === 'in_progress' ? '<div class="backup-progress mt-1"><div class="progress-bar bg-primary" style="width: 100%"></div></div>' : ''}
                </td>
                <td>
                    <span class="file-size">${backup.formatted_size}</span>
                    ${backup.database_size > 0 ? `<br><small>DB: ${backup.formatted_database_size}</small>` : ''}
                    ${backup.media_size > 0 ? `<br><small>Media: ${backup.formatted_media_size}</small>` : ''}
                </td>
                <td>
                    <small>${this.formatDate(backup.created_at)}</small>
                    ${backup.created_by_username ? `<br><small class="text-muted">by ${backup.created_by_username}</small>` : ''}
                </td>
                <td>
                    <small>${backup.duration ? this.formatDuration(backup.duration) : '-'}</small>
                </td>
                <td class="table-actions">
                    ${this.renderBackupActions(backup)}
                </td>
            </tr>
        `).join('');
    }

    renderBackupActions(backup) {
        let actions = '';
        
        if (backup.status === 'completed') {
            if (backup.database_file) {
                actions += `<a href="/backup/download/${backup.id}/database/" class="btn btn-sm btn-outline-primary me-1" title="Download Database"><i class="fas fa-download"></i></a>`;
            }
            if (backup.media_file) {
                actions += `<a href="/backup/download/${backup.id}/media/" class="btn btn-sm btn-outline-primary me-1" title="Download Media"><i class="fas fa-images"></i></a>`;
            }
        }
        
        actions += `<button class="btn btn-sm btn-outline-danger" onclick="backupDashboard.deleteBackup(${backup.id})" title="Delete"><i class="fas fa-trash"></i></button>`;
        
        return actions;
    }

    getStatusBadgeClass(status) {
        switch (status) {
            case 'completed': return 'bg-success';
            case 'failed': return 'bg-danger';
            case 'in_progress': return 'bg-warning';
            case 'pending': return 'bg-secondary';
            default: return 'bg-light text-dark';
        }
    }

    async loadRestores() {
        try {
            const response = await fetch(`${this.apiBase}restores/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Check for completed restore operations
            this.checkCompletedOperations(data.results || data, 'restore');
            
            this.renderRestoresTable(data.results || data);
        } catch (error) {
            console.error('Error loading restores:', error);
        }
    }

    renderRestoresTable(restores) {
        const tbody = document.getElementById('restoresTableBody');
        
        if (!restores.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No restores found</td></tr>';
            return;
        }

        tbody.innerHTML = restores.map(restore => `
            <tr>
                <td>
                    <strong>${restore.name}</strong>
                    ${restore.description ? `<br><small class="text-muted">${restore.description}</small>` : ''}
                </td>
                <td>
                    <span class="badge backup-type-badge bg-info">${restore.restore_type_display || restore.restore_type}</span>
                </td>
                <td>
                    <span class="badge status-badge ${this.getStatusBadgeClass(restore.status)}">${restore.status_display || restore.status}</span>
                </td>
                <td>
                    ${restore.backup_record ? `<small>Backup: ${restore.backup_record_name}</small>` : '<small>Uploaded files</small>'}
                </td>
                <td>
                    <small>${this.formatDate(restore.created_at)}</small>
                </td>
                <td>
                    <small>${restore.duration ? this.formatDuration(restore.duration) : '-'}</small>
                </td>
                <td class="table-actions">
                    <button class="btn btn-sm btn-outline-danger" onclick="backupDashboard.deleteRestore(${restore.id})" title="Delete"><i class="fas fa-trash"></i></button>
                </td>
            </tr>
        `).join('');
    }

    async loadSchedules() {
        try {
            const response = await fetch(`${this.apiBase}schedules/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.renderSchedulesTable(data.results || data);
        } catch (error) {
            console.error('Error loading schedules:', error);
        }
    }

    renderSchedulesTable(schedules) {
        const tbody = document.getElementById('schedulesTableBody');
        
        if (!schedules.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No schedules found</td></tr>';
            return;
        }

        tbody.innerHTML = schedules.map(schedule => `
            <tr>
                <td>
                    <strong>${schedule.name}</strong>
                </td>
                <td>
                    <span class="badge backup-type-badge bg-info">${schedule.backup_type_display || schedule.backup_type}</span>
                </td>
                <td>
                    <small>${schedule.schedule_display || schedule.schedule_type}</small>
                </td>
                <td>
                    <span class="badge ${schedule.is_active ? 'bg-success' : 'bg-secondary'}">${schedule.is_active ? 'Active' : 'Inactive'}</span>
                </td>
                <td>
                    <small>${schedule.last_run ? this.formatDate(schedule.last_run) : 'Never'}</small>
                </td>
                <td>
                    <small>${schedule.next_run ? this.formatDate(schedule.next_run) : 'Not scheduled'}</small>
                </td>
                <td class="table-actions">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="backupDashboard.toggleSchedule(${schedule.id})" title="Toggle">
                        <i class="fas fa-power-off"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="backupDashboard.deleteSchedule(${schedule.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    async loadSettings() {
        try {
            const response = await fetch(`${this.apiBase}settings/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            if (data.length > 0) {
                this.populateSettingsForm(data[0]);
            }
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    populateSettingsForm(settings) {
        // Populate form fields with current settings
        const form = document.getElementById('settingsForm');
        Object.keys(settings).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = settings[key];
                } else {
                    input.value = settings[key] || '';
                }
            }
        });
    }

    async createBackup() {
        const form = document.getElementById('createBackupForm');
        const formData = new FormData(form);
        
        try {
            this.showProgress('Creating backup...');
            
            const response = await fetch(`${this.apiBase}backups/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Backup creation started:', result);
                
                // Track this backup operation
                this.activeOperations.add(`backup-${result.id}`);
                
                this.closeModal('createBackupModal');
                form.reset();
                this.showAlert('Backup started successfully! Please wait for completion...', 'success');
                
                // Don't hide progress yet - let auto-refresh handle it
                this.updateProgressMessage('Backup in progress... Please wait for completion.');
                
                this.loadBackups();
                this.loadStatistics();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create backup');
            }
        } catch (error) {
            this.hideProgress();
            this.showAlert('Error creating backup: ' + error.message, 'danger');
        }
    }

    async deleteBackup(backupId) {
        if (!confirm('Are you sure you want to delete this backup? This will also delete the backup files.')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}backups/${backupId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });

            if (response.ok) {
                this.showAlert('Backup deleted successfully!', 'success');
                this.loadBackups();
                this.loadStatistics();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete backup');
            }
        } catch (error) {
            this.showAlert('Error deleting backup: ' + error.message, 'danger');
        }
    }

    async restoreFromBackup() {
        const form = document.getElementById('restoreFromBackupForm');
        const formData = new FormData(form);
        
        try {
            console.log('Starting restore from backup...');
            this.showProgress('Starting restore process...');
            
            const response = await fetch(`${this.apiBase}restores/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: formData,
                credentials: 'same-origin'
            });

            console.log('Restore API response status:', response.status);

            if (response.ok) {
                const result = await response.json();
                console.log('Restore started successfully:', result);
                
                // Track this restore operation
                this.activeOperations.add(`restore-${result.id}`);
                
                this.closeModal('restoreFromBackupModal');
                form.reset();
                
                // Reset dropdown and details
                document.getElementById('selectBackup').innerHTML = '<option value="">Select a backup...</option>';
                document.getElementById('backupDetails').style.display = 'none';
                
                // Don't hide progress yet - let auto-refresh handle it
                this.updateProgressMessage('Restore in progress... Please wait for completion.');
                
                this.showAlert('Restore started successfully! Please wait for completion...', 'success');
                this.loadRestores();
                this.loadStatistics();
            } else {
                const error = await response.json();
                console.error('Restore API error:', error);
                throw new Error(error.detail || error.message || 'Failed to start restore');
            }
        } catch (error) {
            console.error('Restore error:', error);
            this.hideProgress();
            this.showAlert('Error starting restore: ' + error.message, 'danger');
        }
    }

    async uploadAndRestore() {
        const form = document.getElementById('uploadRestoreForm');
        const formData = new FormData(form);
        
        try {
            console.log('Starting upload and restore...');
            this.showProgress('Uploading files and starting restore...');
            
            const response = await fetch(`${this.apiBase}restores/upload_and_restore/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: formData,
                credentials: 'same-origin'
            });

            console.log('Upload restore API response status:', response.status);

            if (response.ok) {
                const result = await response.json();
                console.log('Upload restore started successfully:', result);
                
                this.hideProgress();
                this.closeModal('uploadRestoreModal');
                form.reset();
                
                // Reset file info displays
                document.getElementById('databaseFileInfo').style.display = 'none';
                document.getElementById('mediaFileInfo').style.display = 'none';
                
                this.showAlert('Upload and restore started successfully! Check the Restores tab for progress.', 'success');
                this.loadRestores();
                this.loadStatistics();
            } else {
                const error = await response.json();
                console.error('Upload restore API error:', error);
                throw new Error(error.detail || error.message || 'Failed to start upload and restore');
            }
        } catch (error) {
            console.error('Upload restore error:', error);
            this.hideProgress();
            this.showAlert('Error starting upload and restore: ' + error.message, 'danger');
        }
    }

    async loadAvailableBackups() {
        console.log('Loading available backups...');
        try {
            const csrfToken = this.getCSRFToken();
            console.log('CSRF Token:', csrfToken ? 'Found' : 'Missing');
            
            const response = await fetch(`${this.apiBase}available-backups/`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });
            
            console.log('API Response Status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('API Error:', errorText);
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const backups = await response.json();
            console.log('Loaded backups:', backups.length);
            
            const select = document.getElementById('selectBackup');
            if (!select) {
                console.error('selectBackup element not found!');
                return;
            }
            
            select.innerHTML = '<option value="">Select a backup...</option>';
            
            backups.forEach(backup => {
                const option = document.createElement('option');
                option.value = backup.id;
                option.textContent = `${backup.name} (${backup.backup_type_display}, ${backup.file_size_formatted})`;
                option.dataset.backup = JSON.stringify(backup);
                select.appendChild(option);
            });
            
            console.log('Dropdown populated with', backups.length, 'backups');
        } catch (error) {
            console.error('Error loading available backups:', error);
            // Show user-friendly error message
            const select = document.getElementById('selectBackup');
            if (select) {
                select.innerHTML = '<option value="">Error loading backups</option>';
            }
        }
    }

    showBackupDetails(backupId) {
        const select = document.getElementById('selectBackup');
        const detailsDiv = document.getElementById('backupDetails');
        
        if (!backupId) {
            detailsDiv.style.display = 'none';
            return;
        }
        
        const option = select.querySelector(`option[value="${backupId}"]`);
        if (option && option.dataset.backup) {
            const backup = JSON.parse(option.dataset.backup);
            
            document.getElementById('backupTypeDetail').textContent = backup.backup_type_display;
            document.getElementById('backupSizeDetail').textContent = backup.file_size_formatted;
            document.getElementById('backupDateDetail').textContent = this.formatDate(backup.created_at);
            
            const filesList = document.getElementById('backupFilesList');
            filesList.innerHTML = '';
            
            if (backup.has_database) {
                const li = document.createElement('li');
                li.textContent = 'Database backup';
                filesList.appendChild(li);
            }
            if (backup.has_media) {
                const li = document.createElement('li');
                li.textContent = 'Media backup';
                filesList.appendChild(li);
            }
            
            detailsDiv.style.display = 'block';
        }
    }

    async createSchedule() {
        const form = document.getElementById('createScheduleForm');
        const formData = new FormData(form);
        
        try {
            console.log('Creating backup schedule...');
            this.showProgress('Creating backup schedule...');
            
            const response = await fetch(`${this.apiBase}schedules/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: formData,
                credentials: 'same-origin'
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Schedule created successfully:', result);
                
                this.hideProgress();
                this.closeModal('createScheduleModal');
                form.reset();
                
                this.showAlert('Backup schedule created successfully!', 'success');
                this.loadSchedules();
            } else {
                const error = await response.json();
                console.error('Schedule creation error:', error);
                throw new Error(error.detail || error.message || 'Failed to create schedule');
            }
        } catch (error) {
            console.error('Create schedule error:', error);
            this.hideProgress();
            this.showAlert('Error creating schedule: ' + error.message, 'danger');
        }
    }

    async saveSettings() {
        const form = document.getElementById('settingsForm');
        const formData = new FormData(form);
        
        try {
            console.log('Saving backup settings...');
            this.showProgress('Saving settings...');
            
            const response = await fetch(`${this.apiBase}settings/1/`, {
                method: 'PUT',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: formData,
                credentials: 'same-origin'
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Settings saved successfully:', result);
                
                this.hideProgress();
                this.showAlert('Settings saved successfully!', 'success');
            } else {
                const error = await response.json();
                console.error('Settings save error:', error);
                throw new Error(error.detail || error.message || 'Failed to save settings');
            }
        } catch (error) {
            console.error('Save settings error:', error);
            this.hideProgress();
            this.showAlert('Error saving settings: ' + error.message, 'danger');
        }
    }

    async testSettings() {
        try {
            console.log('Testing backup settings...');
            this.showProgress('Testing backup configuration...');
            
            const response = await fetch('/backup/test-settings/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            const result = await response.json();
            this.hideProgress();
            
            if (result.success) {
                this.showAlert('Backup configuration test successful!', 'success');
            } else {
                this.showAlert('Configuration test failed: ' + result.message, 'danger');
            }
        } catch (error) {
            console.error('Test settings error:', error);
            this.hideProgress();
            this.showAlert('Error testing configuration: ' + error.message, 'danger');
        }
    }

    async cleanupOldBackups() {
        if (!confirm('Are you sure you want to cleanup old backups? This action cannot be undone.')) {
            return;
        }

        try {
            console.log('Starting backup cleanup...');
            this.showProgress('Cleaning up old backups...');
            
            const response = await fetch(`${this.apiBase}cleanup-old-backups/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                const result = await response.json();
                console.log('Cleanup completed:', result);
                
                this.hideProgress();
                this.showAlert(result.message, 'success');
                this.loadBackups();
                this.loadStatistics();
            } else {
                const error = await response.json();
                console.error('Cleanup error:', error);
                throw new Error(error.detail || error.message || 'Failed to cleanup old backups');
            }
        } catch (error) {
            console.error('Cleanup error:', error);
            this.hideProgress();
            this.showAlert('Error during cleanup: ' + error.message, 'danger');
        }
    }

    async toggleSchedule(scheduleId) {
        try {
            const response = await fetch(`${this.apiBase}schedules/${scheduleId}/toggle_active/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin'
            });

            if (response.ok) {
                this.showAlert('Schedule status updated!', 'success');
                this.loadSchedules();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to toggle schedule');
            }
        } catch (error) {
            console.error('Toggle schedule error:', error);
            this.showAlert('Error toggling schedule: ' + error.message, 'danger');
        }
    }

    async deleteSchedule(scheduleId) {
        if (!confirm('Are you sure you want to delete this schedule?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}schedules/${scheduleId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });

            if (response.ok) {
                this.showAlert('Schedule deleted successfully!', 'success');
                this.loadSchedules();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete schedule');
            }
        } catch (error) {
            this.showAlert('Error deleting schedule: ' + error.message, 'danger');
        }
    }

    async deleteRestore(restoreId) {
        if (!confirm('Are you sure you want to delete this restore record?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}restores/${restoreId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                }
            });

            if (response.ok) {
                this.showAlert('Restore record deleted successfully!', 'success');
                this.loadRestores();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete restore record');
            }
        } catch (error) {
            this.showAlert('Error deleting restore record: ' + error.message, 'danger');
        }
    }

    toggleScheduleOptions(scheduleType) {
        const dayOfWeekSection = document.getElementById('dayOfWeekSection');
        const dayOfMonthSection = document.getElementById('dayOfMonthSection');
        
        if (scheduleType === 'weekly') {
            dayOfWeekSection.style.display = 'block';
            dayOfMonthSection.style.display = 'none';
        } else if (scheduleType === 'monthly') {
            dayOfWeekSection.style.display = 'none';
            dayOfMonthSection.style.display = 'block';
        } else {
            dayOfWeekSection.style.display = 'none';
            dayOfMonthSection.style.display = 'none';
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    }

    formatDuration(duration) {
        // Parse duration string (e.g., "0:02:30.123456")
        const parts = duration.split(':');
        const hours = parseInt(parts[0]);
        const minutes = parseInt(parts[1]);
        const seconds = parseInt(parts[2].split('.')[0]);
        
        if (hours > 0) {
            return `${hours}h ${minutes}m ${seconds}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${seconds}s`;
        } else {
            return `${seconds}s`;
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';
    }

    showProgress(message) {
        document.getElementById('progressMessage').textContent = message;
        new bootstrap.Modal(document.getElementById('progressModal')).show();
    }

    updateProgressMessage(message) {
        const progressMessageEl = document.getElementById('progressMessage');
        if (progressMessageEl) {
            progressMessageEl.textContent = message;
        }
    }

    checkCompletedOperations(records, type) {
        let completedAny = false;
        
        // Check if any tracked operations have completed
        for (const operationId of this.activeOperations) {
            if (operationId.startsWith(`${type}-`)) {
                const recordId = operationId.split('-')[1];
                const record = records.find(r => r.id.toString() === recordId);
                
                if (record && (record.status === 'completed' || record.status === 'failed')) {
                    console.log(`${type} operation ${recordId} completed with status: ${record.status}`);
                    this.activeOperations.delete(operationId);
                    completedAny = true;
                    
                    if (record.status === 'completed') {
                        this.showAlert(`${type.charAt(0).toUpperCase() + type.slice(1)} "${record.name}" completed successfully!`, 'success');
                    } else if (record.status === 'failed') {
                        this.showAlert(`${type.charAt(0).toUpperCase() + type.slice(1)} "${record.name}" failed. Check the logs for details.`, 'danger');
                    }
                }
            }
        }
        
        // Hide progress modal if no more active operations
        if (completedAny && this.activeOperations.size === 0) {
            console.log('All operations completed, hiding progress modal');
            this.hideProgress();
        }
    }

    hideProgress() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
        if (modal) modal.hide();
    }

    closeModal(modalId) {
        const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
        if (modal) modal.hide();
    }

    showAlert(message, type = 'info') {
        // Create and show Bootstrap alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    startAutoRefresh() {
        setInterval(() => {
            // Refresh statistics and current tab data
            this.loadStatistics();
            
            const activeTab = document.querySelector('.nav-link.active');
            if (activeTab) {
                const targetTab = activeTab.getAttribute('data-bs-target');
                if (targetTab === '#backups') {
                    this.loadBackups();
                } else if (targetTab === '#restores') {
                    this.loadRestores();
                }
            }
        }, 10000); // Refresh every 10 seconds
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.backupDashboard = new BackupDashboard();
});