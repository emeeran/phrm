// Main JavaScript for Personal Health Record Manager
import { FileUploadManager } from './file-manager.js';
import { ChatManager } from './chat-manager.js';
import { validateFiles, showUploadProgress } from './utils.js';

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap components
    initializeBootstrap();
    
    // Initialize file upload management
    if (document.getElementById('documents-input')) {
        new FileUploadManager('documents-input');
    }
    
    // Initialize legacy file inputs
    initializeLegacyFileInputs();
    
    // Initialize chat system
    new ChatManager();
    
    // Initialize other UI components
    initializeFiltering();
    initializeConfirmations();
    initializeDynamicForms();
    initializeDateRangePicker();
    initializeFormSubmissions();
});

function initializeBootstrap() {
    // Bootstrap tooltips
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
        new bootstrap.Tooltip(el);
    });

    // Bootstrap popovers
    document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => {
        new bootstrap.Popover(el);
    });
}

function initializeLegacyFileInputs() {
    document.querySelectorAll('.file-upload').forEach(input => {
        if (input.id === 'documents-input') return; // Skip enhanced input
        
        input.addEventListener('change', function () {
            const fileLabel = this.nextElementSibling;
            if (this.files?.length > 0) {
                const fileNames = Array.from(this.files).map(file => file.name).join(', ');
                fileLabel.textContent = fileNames;

                // Show preview for image files
                if (this.files[0].type.match('image.*')) {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        const previewContainer = document.querySelector('.file-preview');
                        if (previewContainer) {
                            previewContainer.innerHTML = `<img src="${e.target.result}" class="img-fluid img-thumbnail mb-3" alt="Preview">`;
                        }
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            } else {
                fileLabel.textContent = 'Choose file...';
            }
        });
    });
}

function initializeFiltering() {
    // Health Record filtering
    const filterButtons = document.querySelectorAll('.filter-btn');
    if (filterButtons.length === 0) return;

    filterButtons.forEach(button => {
        button.addEventListener('click', function () {
            const filter = this.dataset.filter;
            const records = document.querySelectorAll('.record-item');

            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            records.forEach(record => {
                record.style.display = (filter === 'all' || record.dataset.type === filter) ? 'block' : 'none';
            });
        });
    });
}

function initializeConfirmations() {
    document.querySelectorAll('[data-confirm]').forEach(button => {
        button.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
}

function initializeDynamicForms() {
    // Dynamic form fields for medications
    const addMedBtn = document.getElementById('add-medication');
    if (!addMedBtn) return;

    let medicationCount = document.querySelectorAll('.medication-item').length;

    addMedBtn.addEventListener('click', function () {
        const container = document.getElementById('medications-container');
        const newMedication = document.createElement('div');
        newMedication.className = 'medication-item row mb-3';
        newMedication.innerHTML = `
            <div class="col-md-4">
                <input type="text" class="form-control" name="medication_name_${medicationCount}" placeholder="Medication Name" required>
            </div>
            <div class="col-md-3">
                <input type="text" class="form-control" name="medication_dosage_${medicationCount}" placeholder="Dosage">
            </div>
            <div class="col-md-3">
                <input type="text" class="form-control" name="medication_frequency_${medicationCount}" placeholder="Frequency">
            </div>
            <div class="col-md-2">
                <button type="button" class="btn btn-danger remove-medication">Remove</button>
            </div>
        `;
        container.appendChild(newMedication);
        medicationCount++;

        // Add event listener to the new remove button
        newMedication.querySelector('.remove-medication').addEventListener('click', function () {
            this.closest('.medication-item').remove();
        });
    });

    // Event delegation for removing medication fields
    document.addEventListener('click', function (e) {
        if (e.target?.classList.contains('remove-medication')) {
            e.target.closest('.medication-item').remove();
        }
    });
}

function initializeDateRangePicker() {
    const dateRangePicker = document.getElementById('date-range-picker');
    if (!dateRangePicker || typeof $ === 'undefined') return;

    const today = new Date();
    const lastMonth = new Date();
    lastMonth.setMonth(lastMonth.getMonth() - 1);

    $(dateRangePicker).daterangepicker({
        startDate: lastMonth,
        endDate: today,
        ranges: {
            'Today': [today, today],
            'Yesterday': [new Date(today - 86400000), new Date(today - 86400000)],
            'Last 7 Days': [new Date(today - 6 * 86400000), today],
            'Last 30 Days': [new Date(today - 29 * 86400000), today],
            'This Month': [new Date(today.getFullYear(), today.getMonth(), 1), new Date(today.getFullYear(), today.getMonth() + 1, 0)],
            'Last Month': [new Date(today.getFullYear(), today.getMonth() - 1, 1), new Date(today.getFullYear(), today.getMonth(), 0)]
        }
    }, function (start, end) {
        filterRecordsByDate(start, end);
    });

    function filterRecordsByDate(start, end) {
        document.querySelectorAll('.record-item').forEach(record => {
            const recordDate = new Date(record.dataset.date);
            record.style.display = (recordDate >= start && recordDate <= end) ? 'block' : 'none';
        });
    }
}

function initializeFormSubmissions() {
    document.querySelectorAll('form[enctype="multipart/form-data"]').forEach(form => {
        form.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('#documents-input');
            if (fileInput?.files.length > 0) {
                if (!validateFiles(fileInput.files)) {
                    e.preventDefault();
                    return false;
                }
                // Show progress indicator for multiple files
                if (fileInput.files.length > 1) {
                    showUploadProgress();
                }
            }
        });
    });
}