// Short Story Pipeline - Frontend JavaScript

/**
 * Base URL for all API endpoints.
 * @constant {string}
 */
const API_BASE = '/api';

/**
 * Currently loaded story ID.
 * Set when a story is generated or loaded from the browser.
 * Used for saving, revising, and exporting operations.
 * @type {string|null}
 */
let currentStoryId = null;

/**
 * Whether the story browser section is currently visible.
 * Used to track browser state for UI updates.
 * @type {boolean}
 */
let storyBrowserVisible = false;

/**
 * Handle API response errors consistently.
 * Extracts error information from response and provides context for debugging.
 * 
 * @param {Response} response - Fetch API response object
 * @param {string} defaultError - Default error message if none provided
 * @param {string} defaultErrorCode - Default error code if none provided
 * @returns {Promise<Error>} Error object with message and error_code
 */
async function handleApiError(response, defaultError = 'Request failed', defaultErrorCode = 'API_ERROR') {
    let errorMessage = defaultError;
    let errorCode = defaultErrorCode;
    
    try {
        const data = await response.json();
        errorMessage = data.error || data.message || `${defaultError} (Status: ${response.status})`;
        errorCode = data.error_code || defaultErrorCode;
    } catch (e) {
        // If response is not JSON, use status text
        errorMessage = response.statusText || `${defaultError} (Status: ${response.status})`;
        errorCode = defaultErrorCode;
    }
    
    const error = new Error(errorMessage);
    error.error_code = errorCode;
    error.status = response.status;
    
    // Log error with context for debugging
    console.error('API Error:', {
        url: response.url,
        status: response.status,
        statusText: response.statusText,
        error: errorMessage,
        errorCode: errorCode
    });
    
    return error;
}

/**
 * Initialize Lucide icons in a specific container.
 * 
 * This function is called only when needed (on page load and when dynamic content
 * is added), not on a timer. This prevents unnecessary DOM manipulation and
 * improves performance, especially on mobile devices.
 * 
 * @param {HTMLElement|Document} container - Container element to initialize icons in (default: document)
 */
function initializeIcons(container = document) {
    if (typeof lucide !== 'undefined') {
        lucide.createIcons(container);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide icons once on page load (not on a timer - only when needed)
    initializeIcons();
    
    // Animate page load with GSAP (GreenSock Animation Platform)
    // These animations provide smooth, professional page transitions:
    // - Container fades in from below (creates depth perception)
    // - Header title fades in from above (draws attention to branding)
    // - Form groups stagger in from left (guides user's eye through form)
    // All animations use easing functions for natural motion (not linear)
    if (typeof gsap !== 'undefined') {
        // Main container: fade in from below with smooth easing
        gsap.from('.container', { 
            duration: 0.8, 
            opacity: 0, 
            y: 30, 
            ease: 'power3.out' 
        });
        // Header title: fade in from above with slight delay for visual hierarchy
        gsap.from('header h1', { 
            duration: 1, 
            opacity: 0, 
            y: -20, 
            delay: 0.2,
            ease: 'power3.out' 
        });
        // Form groups: stagger animation from left creates flow and guides user attention
        gsap.from('.form-group', { 
            duration: 0.6, 
            opacity: 0, 
            x: -20, 
            stagger: 0.1,  // 0.1s delay between each form group
            delay: 0.4,
            ease: 'power2.out' 
        });
    }
    
    loadStoryBrowser();
    setupExportMenu();
    setupStoryBrowser();
    
    // Setup templates - verify button exists first
    const loadBtn = document.getElementById('load-template-btn');
    console.log('Load template button check:', {
        exists: !!loadBtn,
        element: loadBtn,
        id: loadBtn ? loadBtn.id : 'not found'
    });
    
    setupTemplates();
    setupRevisionFeatures();
    setupFormSubmission();
    
    // Debug: Verify template setup after initialization
    setTimeout(() => {
        const btn = document.getElementById('load-template-btn');
        console.log('Template setup verification:', {
            buttonExists: !!btn,
            hasClickListeners: btn ? btn.onclick !== null : false,
            buttonType: btn ? btn.type : 'N/A'
        });
    }, 100);
});

/**
 * Set up form submission handler with progress tracking.
 * Handles story generation form submission, validates inputs, and manages
 * progress indicators during the generation process.
 */
function setupFormSubmission() {
    const storyForm = document.getElementById('story-form');
    if (!storyForm) {
        console.error('Story form not found!');
        return;
    }
    
    storyForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const genre = document.getElementById('genre').value.trim();
    const idea = document.getElementById('idea').value.trim();
    const characterInput = document.getElementById('character').value.trim();
    const theme = document.getElementById('theme').value.trim();
    
    if (!genre) {
        showError('Genre selection is required', 'MISSING_GENRE');
        return;
    }
    
    if (!idea) {
        showError('Story idea is required. Please provide a creative premise for your story.', 'MISSING_IDEA');
        return;
    }
    
    // Parse character (try JSON, fallback to plain text)
    let character = characterInput;
    if (characterInput) {
        try {
            character = JSON.parse(characterInput);
        } catch {
            character = { description: characterInput };
        }
    } else {
        character = {};
    }
    
    showLoading();
    hideError();
    resetProgressSteps();
    
    // Simulate progress updates (since we can't track actual pipeline progress easily)
    setTimeout(() => updateProgressStep('step-premise', true), 500);
    setTimeout(() => updateProgressStep('step-outline', true), 2000);
    setTimeout(() => updateProgressStep('step-scaffold', true), 3500);
    setTimeout(() => updateProgressStep('step-draft', true), 5000);
    
    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                genre,
                idea,
                character,
                theme
            })
        });
        
        if (!response.ok) {
            throw await handleApiError(response, 'Failed to generate story', 'GENERATION_ERROR');
        }
        
        const data = await response.json();
        
        // Mark final step as complete
        updateProgressStep('step-revise', true);
        
        currentStoryId = data.story_id;
        const storyEditor = document.getElementById('story-editor');
        storyEditor.value = data.story;
        
        // Auto-resize textarea to fit content (with max limit for very long stories)
        storyEditor.style.height = 'auto';
        const newHeight = Math.min(Math.max(storyEditor.scrollHeight, 600), 2000);
        storyEditor.style.height = newHeight + 'px';
        
        updateWordCount(data.word_count, data.max_words);
        
        // Show genre info if available
        if (data.genre_config) {
            console.log('Genre config:', data.genre_config);
        }
        
        const outputSection = document.getElementById('output-section');
        outputSection.style.display = 'block';
        // Animate output section appearance: fade in from below to draw attention to generated story
        if (typeof gsap !== 'undefined') {
            gsap.from(outputSection, { 
                opacity: 0, 
                y: 30, 
                duration: 0.6, 
                ease: 'power3.out' 
            });
        }
        outputSection.scrollIntoView({ behavior: 'smooth' });
        
        // Reload story browser to show new story
        loadStoryBrowser();
        
    } catch (error) {
        showError(error.message, error.error_code || 'GENERATION_ERROR');
    } finally {
        setTimeout(() => {
            hideLoading();
            // Reset regenerate button if it exists
            const regenerateBtn = document.getElementById('regenerate-btn');
            if (regenerateBtn) {
                regenerateBtn.disabled = false;
                regenerateBtn.innerHTML = '<i data-lucide="refresh-cw" class="w-4 h-4 inline mr-2"></i>Regenerate';
                initializeIcons(regenerateBtn);
            }
            // Reset loading text
            const loadingText = document.getElementById('loading-text');
            if (loadingText) {
                loadingText.textContent = 'Generating your story...';
            }
        }, 500);
    }
    });
}

// Save button
const saveBtn = document.getElementById('save-btn');
if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
        const text = document.getElementById('story-editor').value;
        if (!text) {
            showError('No story to save. Please generate or load a story first.', 'EMPTY_STORY');
            return;
        }
        
        if (!currentStoryId) {
            showError('No story to save. Please generate a story first.', 'NO_STORY_ID');
            return;
        }
        
        // Disable button during save to prevent double-clicks
        saveBtn.disabled = true;
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 inline mr-2 animate-spin"></i>Saving...';
        initializeIcons(saveBtn);
        
        try {
            const response = await fetch(`${API_BASE}/story/${currentStoryId}/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text })
            });
            
            if (!response.ok) {
                throw await handleApiError(response, 'Failed to save story', 'SAVE_ERROR');
            }
            
            const data = await response.json();
            
            // Update word count if provided
            if (data.word_count !== undefined) {
                updateWordCount(data.word_count, data.max_words || 7500);
            }
            
            // Also download to user's desktop
            try {
                const storyText = text;
                const blob = new Blob([storyText], { type: 'text/plain' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                
                // Create filename with story ID and timestamp
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
                const filename = `story_${currentStoryId}_${timestamp}.txt`;
                a.download = filename;
                
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showSuccess('Story saved to server and downloaded to your computer!');
            } catch (downloadError) {
                console.error('Download error:', downloadError);
                // Still show success for server save even if download fails
                showSuccess('Story saved to server! (Download to desktop failed)');
            }
            
            loadStoryBrowser(); // Refresh story list
        } catch (error) {
            console.error('Save error:', error);
            showError(error.message || 'Failed to save story', error.error_code || 'SAVE_ERROR');
        } finally {
            // Re-enable button
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
            initializeIcons(saveBtn);
        }
    });
} else {
    console.error('Save button not found!');
}

// Regenerate button
const regenerateBtn = document.getElementById('regenerate-btn');
if (regenerateBtn) {
    regenerateBtn.addEventListener('click', async () => {
        // Check if form is valid before regenerating
        const idea = document.getElementById('idea').value.trim();
        if (!idea) {
            showError('Story idea is required to regenerate. Please enter a story idea first.', 'MISSING_IDEA');
            return;
        }
        
        // Show loading state on button
        regenerateBtn.disabled = true;
        const originalText = regenerateBtn.innerHTML;
        regenerateBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 inline mr-2 animate-spin"></i>Regenerating...';
        initializeIcons(regenerateBtn);
        
        // Update loading text to indicate regeneration
        const loadingText = document.getElementById('loading-text');
        if (loadingText) {
            loadingText.textContent = 'Regenerating your story with enhanced dramatic tension...';
        }
        
        // Trigger form submission (which has its own loading indicators)
        document.getElementById('story-form').dispatchEvent(new Event('submit'));
        
        // Re-enable button after a delay (form submission will handle the actual completion)
        // We'll reset it in the form submission handler
    });
}

// Validate button
document.getElementById('validate-btn').addEventListener('click', async () => {
    const text = document.getElementById('story-editor').value;
    
    if (!text) {
        showError('No story to validate. Please generate or load a story first.', 'EMPTY_STORY');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) {
            throw await handleApiError(response, 'Validation failed', 'VALIDATION_ERROR');
        }
        
        const data = await response.json();
        
        displayValidationResults(data);
        
    } catch (error) {
        showError(error.message, error.error_code || 'VALIDATION_ERROR');
    }
});

/**
 * Set up export menu functionality.
 * Handles export button clicks, menu toggling, and export option selection.
 */
function setupExportMenu() {
    const exportBtn = document.getElementById('export-btn');
    const exportMenu = document.getElementById('export-menu');
    
    if (!exportBtn || !exportMenu) return;
    
    exportBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        exportMenu.classList.toggle('hidden');
        exportMenu.classList.toggle('show');
        // Only re-initialize icons in the export menu if it's being shown
        if (!exportMenu.classList.contains('hidden')) {
            initializeIcons(exportMenu);
        }
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!exportBtn.contains(e.target) && !exportMenu.contains(e.target)) {
            exportMenu.classList.add('hidden');
            exportMenu.classList.remove('show');
        }
    });
    
    // Handle export options
    document.querySelectorAll('.export-option').forEach(option => {
        option.addEventListener('click', async (e) => {
            e.stopPropagation();
            const format = option.getAttribute('data-format') || 
                          e.target.closest('.export-option')?.getAttribute('data-format') || 
                          e.target.getAttribute('data-format');
            
            if (!format) {
                showError('Export format not specified. Please try again.', 'EXPORT_FORMAT_ERROR');
                return;
            }
            
            await exportStory(format);
            exportMenu.classList.add('hidden');
            exportMenu.classList.remove('show');
        });
    });
}

/**
 * Export story in the specified format.
 * 
 * @param {string} format - Export format ('txt', 'md', 'pdf', etc.)
 * @returns {Promise<void>}
 */
async function exportStory(format) {
    if (!currentStoryId) {
        showError('No story to export. Please generate or load a story first.', 'NO_STORY_ID');
        return;
    }
    
    if (!format) {
        showError('Export format not specified.', 'EXPORT_FORMAT_ERROR');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/story/${currentStoryId}/export/${format}`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `Export failed: ${response.statusText}`);
        }
        
        // Download the file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `story_${currentStoryId}.${format}`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showSuccess(`Story exported as ${format.toUpperCase()} successfully!`);
    } catch (error) {
        console.error('Export error:', error);
        showError(error.message || 'Export failed. Please try again.', 'EXPORT_ERROR');
    }
}

/**
 * Set up template functionality.
 * Loads templates based on selected genre and handles template selection
 * and loading into form fields.
 */
function setupTemplates() {
    console.log('Setting up templates...');
    const genreSelect = document.getElementById('genre');
    const templateSelect = document.getElementById('template-select');
    const loadTemplateBtn = document.getElementById('load-template-btn');
    
    console.log('Template elements check:', {
        genreSelect: !!genreSelect,
        templateSelect: !!templateSelect,
        loadTemplateBtn: !!loadTemplateBtn,
        loadBtnElement: loadTemplateBtn
    });
    
    if (!genreSelect || !templateSelect || !loadTemplateBtn) {
        console.error('Template elements not found:', {
            genreSelect: !!genreSelect,
            templateSelect: !!templateSelect,
            loadTemplateBtn: !!loadTemplateBtn
        });
        // Try again after a short delay in case DOM isn't ready
        if (!loadTemplateBtn) {
            setTimeout(() => {
                const retryBtn = document.getElementById('load-template-btn');
                if (retryBtn) {
                    console.log('Found button on retry, setting up...');
                    setupTemplates();
                } else {
                    console.error('Button still not found after retry');
                }
            }, 500);
        }
        return;
    }
    
    // Load templates when genre changes
    genreSelect.addEventListener('change', async () => {
        const genre = genreSelect.value;
        if (!genre) {
            templateSelect.innerHTML = '<option value="">No template - I have my own idea</option>';
            return;
        }
        
        // Show loading state
        templateSelect.innerHTML = '<option value="">Loading templates...</option>';
        templateSelect.disabled = true;
        
        try {
            const response = await fetch(`${API_BASE}/templates?genre=${encodeURIComponent(genre)}`);
            
            if (!response.ok) {
                throw await handleApiError(response, 'Failed to load templates', 'TEMPLATE_LOAD_ERROR');
            }
            
            const data = await response.json();
            console.log('Templates API response:', data);
            
            templateSelect.innerHTML = '<option value="">No template - I have my own idea</option>';
            templateSelect.disabled = false;
            
            if (data.templates && data.templates.length > 0) {
                console.log(`Loading ${data.templates.length} templates for genre: ${genre}`);
                data.templates.forEach((template, index) => {
                    const option = document.createElement('option');
                    option.value = template.name;
                    option.textContent = `${template.name}${template.description ? ' - ' + template.description : ''}`;
                    const templateJson = JSON.stringify(template);
                    option.dataset.template = templateJson;
                    console.log(`Template ${index + 1}: ${template.name}`, {
                        hasData: !!option.dataset.template,
                        dataLength: templateJson.length
                    });
                    templateSelect.appendChild(option);
                });
                console.log('Templates loaded into dropdown');
            } else {
                // No templates available for this genre
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No examples available for this genre';
                option.disabled = true;
                templateSelect.appendChild(option);
            }
        } catch (error) {
            // Log error with context for debugging
            console.error('Failed to load templates:', {
                genre: genre,
                error: error.message,
                errorCode: error.error_code || 'UNKNOWN_ERROR',
                status: error.status
            });
            
            // Reset dropdown
            templateSelect.innerHTML = '<option value="">No template - I have my own idea</option>';
            templateSelect.disabled = false;
            
            // Show error message to user
            if (error.status && error.status >= 500) {
                showError(`Failed to load templates: ${error.message}. Please try again or start from scratch.`, error.error_code || 'TEMPLATE_LOAD_ERROR');
            } else if (error.status && error.status === 404) {
                // No templates found is not an error, just inform user
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No templates available for this genre';
                option.disabled = true;
                templateSelect.appendChild(option);
            } else {
                showError(`Failed to load templates: ${error.message}`, error.error_code || 'TEMPLATE_LOAD_ERROR');
            }
        }
    });
    
    // Load template button - verify it exists and attach listener
    if (!loadTemplateBtn) {
        console.error('Load template button not found in setupTemplates!');
        return;
    }
    
    console.log('Attaching click listener to load template button', loadTemplateBtn);
    
    // Remove any existing listeners by cloning (prevents duplicate listeners)
    const originalOnClick = loadTemplateBtn.onclick;
    loadTemplateBtn.onclick = null;
    
    loadTemplateBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log('Load template button clicked!', {
            target: e.target,
            currentTarget: e.currentTarget,
            buttonId: e.currentTarget.id,
            buttonType: e.currentTarget.type
        });
        
        // Check if genre is selected first
        const selectedGenre = genreSelect.value;
        if (!selectedGenre) {
            showError('Please select a genre first before loading a template.', 'NO_GENRE_SELECTED');
            return;
        }
        
        // Check if templates are loaded
        if (templateSelect.options.length <= 1) {
            showError('No templates loaded yet. Please wait for templates to load after selecting a genre, or try selecting a different genre that has templates (Literary, Horror, Romance, or General Fiction).', 'TEMPLATES_NOT_LOADED');
            return;
        }
        
        const selectedIndex = templateSelect.selectedIndex;
        console.log('Selected index:', selectedIndex, 'Total options:', templateSelect.options.length);
        
        if (selectedIndex < 0 || selectedIndex >= templateSelect.options.length) {
            showError('Please select a template from the dropdown first. If no templates are available for this genre, you can start from scratch.', 'NO_TEMPLATE_SELECTED');
            return;
        }
        
        const selectedOption = templateSelect.options[selectedIndex];
        console.log('Selected option:', selectedOption);
        console.log('Option value:', selectedOption ? selectedOption.value : 'none');
        console.log('Option disabled:', selectedOption ? selectedOption.disabled : 'N/A');
        console.log('Has dataset.template:', selectedOption ? !!selectedOption.dataset.template : false);
        
        // Check if "No template" or empty option is selected
        if (!selectedOption || !selectedOption.value || selectedOption.value === '' || selectedOption.disabled) {
            showError('Please select an example template from the dropdown (not "No template"). If no examples appear, try selecting a different genre like Literary, Horror, Romance, or General Fiction. Or skip templates entirely and write your own story!', 'NO_TEMPLATE_SELECTED');
            return;
        }
        
        // Check if template data exists
        if (!selectedOption.dataset.template) {
            console.error('Template data missing from option:', selectedOption);
            console.error('All option attributes:', Array.from(selectedOption.attributes).map(attr => `${attr.name}="${attr.value}"`));
            
            // Try to reload templates for this genre
            showError('Template data is missing. Reloading templates...', 'TEMPLATE_DATA_MISSING');
            try {
                const response = await fetch(`${API_BASE}/templates?genre=${encodeURIComponent(selectedGenre)}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.templates && data.templates.length > 0) {
                        // Reload templates
                        templateSelect.innerHTML = '<option value="">Start from scratch</option>';
                        data.templates.forEach(template => {
                            const option = document.createElement('option');
                            option.value = template.name;
                            option.textContent = `${template.name}${template.description ? ' - ' + template.description : ''}`;
                            option.dataset.template = JSON.stringify(template);
                            templateSelect.appendChild(option);
                        });
                        showError('Templates reloaded. Please select a template and try again.', 'TEMPLATE_DATA_MISSING');
                    }
                }
            } catch (reloadError) {
                console.error('Failed to reload templates:', reloadError);
            }
            return;
        }
        
        try {
            console.log('Parsing template data:', selectedOption.dataset.template);
            const template = JSON.parse(selectedOption.dataset.template);
            console.log('Parsed template:', template);
            
            // Validate template structure
            if (!template || typeof template !== 'object') {
                throw new Error('Invalid template structure');
            }
            
            // Populate form fields
            const ideaField = document.getElementById('idea');
            const characterField = document.getElementById('character');
            const themeField = document.getElementById('theme');
            
            if (!ideaField || !characterField || !themeField) {
                throw new Error('Form fields not found');
            }
            
            ideaField.value = template.idea || '';
            
            // Handle character - format it nicely for the textarea
            let characterText = '';
            if (template.character) {
                if (typeof template.character === 'string') {
                    characterText = template.character;
                } else if (typeof template.character === 'object') {
                    // Format character object as readable text
                    const parts = [];
                    if (template.character.name) {
                        parts.push(`Name: ${template.character.name}`);
                    }
                    if (template.character.description) {
                        parts.push(`Description: ${template.character.description}`);
                    }
                    if (template.character.quirks && Array.isArray(template.character.quirks)) {
                        parts.push(`Quirks: ${template.character.quirks.join(', ')}`);
                    }
                    if (template.character.contradictions) {
                        parts.push(`Contradictions: ${template.character.contradictions}`);
                    }
                    characterText = parts.join('\n\n');
                }
            }
            characterField.value = characterText;
            
            themeField.value = template.theme || '';
            
            console.log('Template loaded successfully:', template.name);
            showSuccess(`Template "${template.name || 'Template'}" loaded successfully!`);
        } catch (error) {
            console.error('Failed to load template:', {
                error: error.message,
                stack: error.stack,
                selectedOption: selectedOption ? selectedOption.value : 'none',
                hasDataset: selectedOption ? !!selectedOption.dataset.template : false,
                datasetValue: selectedOption ? selectedOption.dataset.template : 'none'
            });
            showError(`Failed to load template: ${error.message}. Please try selecting a different template or start from scratch.`, 'TEMPLATE_LOAD_ERROR');
        }
    });
}

/**
 * Set up revision features.
 * Handles story revision, version comparison, and revision history loading.
 */
function setupRevisionFeatures() {
    const reviseBtn = document.getElementById('revise-btn');
    const compareBtn = document.getElementById('compare-btn');
    const closeComparisonBtn = document.getElementById('close-comparison-btn');
    const compareVersionsBtn = document.getElementById('compare-versions-btn');
    
    // Revise button - with confirmation to prevent accidental revisions
    reviseBtn.addEventListener('click', async () => {
        if (!currentStoryId) {
            showError('No story to revise. Please generate or load a story first.', 'NO_STORY_ID');
            return;
        }
        
        // Confirm before revising to prevent accidental revisions
        const confirmed = confirm(
            'This will create a new revision of your story. ' +
            'The revision will improve language and distinctiveness, but will create a new version in your revision history. ' +
            'Continue?'
        );
        
        if (!confirmed) {
            return; // User cancelled
        }
        
        // Disable button during revision to prevent double-clicks
        reviseBtn.disabled = true;
        const originalText = reviseBtn.innerHTML;
        reviseBtn.innerHTML = '<i data-lucide="loader-2" class="w-4 h-4 inline mr-2 animate-spin"></i>Revising...';
        initializeIcons(reviseBtn);
        
        showLoading();
        hideError();
        
        try {
            const response = await fetch(`${API_BASE}/story/${currentStoryId}/revise`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                throw await handleApiError(response, 'Failed to revise story', 'REVISION_ERROR');
            }
            
            const data = await response.json();
            
            const storyEditor = document.getElementById('story-editor');
            storyEditor.value = data.story;
            
            // Auto-resize textarea to fit content
            storyEditor.style.height = 'auto';
            const newHeight = Math.min(Math.max(storyEditor.scrollHeight, 600), 2000);
            storyEditor.style.height = newHeight + 'px';
            
            updateWordCount(data.word_count, data.max_words);
            showSuccess(`Story revised! (Revision ${data.revision_number})`);
            
            // Refresh revision history
            await loadRevisionHistory();
        } catch (error) {
            console.error('Revision error:', error);
            showError(error.message, error.error_code || 'REVISION_ERROR');
        } finally {
            hideLoading();
            // Re-enable button
            reviseBtn.disabled = false;
            reviseBtn.innerHTML = originalText;
            initializeIcons(reviseBtn);
        }
    });
    
    // Compare button
    compareBtn.addEventListener('click', async () => {
        if (!currentStoryId) {
            showError('No story to compare. Please generate or load a story first.', 'NO_STORY_ID');
            return;
        }
        
        await loadRevisionHistory();
        document.getElementById('comparison-section').style.display = 'block';
    });
    
    // Close comparison
    closeComparisonBtn.addEventListener('click', () => {
        document.getElementById('comparison-section').style.display = 'none';
    });
    
    // Compare versions button
    compareVersionsBtn.addEventListener('click', async () => {
        const version1 = document.getElementById('compare-version1').value;
        const version2 = document.getElementById('compare-version2').value;
        
        if (!version1 || !version2) {
            showError('Please select both versions to compare', 'MISSING_VERSIONS');
            return;
        }
        
        if (version1 === version2) {
            showError('Please select different versions to compare', 'SAME_VERSIONS');
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/story/${currentStoryId}/compare?version1=${version1}&version2=${version2}`);
            
            if (!response.ok) {
                throw await handleApiError(response, 'Failed to compare versions', 'COMPARISON_ERROR');
            }
            
            const data = await response.json();
            
            displayComparison(data);
        } catch (error) {
            showError(error.message, error.error_code || 'COMPARISON_ERROR');
        }
    });
}

/**
 * Load revision history for the current story.
 * Fetches revision history from the API and populates the revision list
 * and comparison dropdowns.
 * 
 * @returns {Promise<void>}
 */
async function loadRevisionHistory() {
    if (!currentStoryId) return;
    
    try {
        const response = await fetch(`${API_BASE}/story/${currentStoryId}/revisions`);
        
        if (!response.ok) {
            throw await handleApiError(response, 'Failed to load revision history', 'REVISION_HISTORY_ERROR');
        }
        
        const data = await response.json();
        
        // Display revision history
        const revisionList = document.getElementById('revision-list');
        const historySection = document.getElementById('revision-history-section');
        
        if (data.revision_history && data.revision_history.length > 0) {
            // Use DocumentFragment for efficient DOM manipulation (single reflow)
            const fragment = document.createDocumentFragment();
            const listContainer = document.createElement('div');
            listContainer.className = 'revision-list';
            
            // Build revision items efficiently
            data.revision_history.forEach(rev => {
                const date = new Date(rev.timestamp).toLocaleString();
                const item = document.createElement('div');
                item.className = 'revision-item';
                
                // Use textContent for safety (prevents XSS) instead of innerHTML
                item.innerHTML = `
                    <div class="revision-header">
                        <span class="revision-version">Version ${escapeHtml(String(rev.version || ''))}</span>
                        <span class="revision-type">${escapeHtml(String(rev.type || ''))}</span>
                        <span class="revision-date">${escapeHtml(date)}</span>
                    </div>
                    <div class="revision-meta">
                        <span>${escapeHtml(String(rev.word_count || 0))} words</span>
                    </div>
                `;
                listContainer.appendChild(item);
            });
            
            fragment.appendChild(listContainer);
            
            // Clear and update in single operation (minimizes reflows)
            revisionList.innerHTML = '';
            revisionList.appendChild(fragment);
            historySection.style.display = 'block';
        }
        
        // Populate comparison dropdowns efficiently
        const version1Select = document.getElementById('compare-version1');
        const version2Select = document.getElementById('compare-version2');
        
        // Use DocumentFragment for dropdowns too (single reflow)
        const fragment1 = document.createDocumentFragment();
        const fragment2 = document.createDocumentFragment();
        
        if (data.revision_history && data.revision_history.length > 0) {
            data.revision_history.forEach(rev => {
                const option1 = document.createElement('option');
                const option2 = document.createElement('option');
                const versionText = `Version ${rev.version} (${rev.type})`;
                option1.value = String(rev.version);
                option1.textContent = versionText;
                option2.value = String(rev.version);
                option2.textContent = versionText;
                fragment1.appendChild(option1);
                fragment2.appendChild(option2);
            });
            
            // Clear and update in single operations
            version1Select.innerHTML = '';
            version2Select.innerHTML = '';
            version1Select.appendChild(fragment1);
            version2Select.appendChild(fragment2);
            
            // Set defaults to first and last
            if (data.revision_history.length > 1) {
                version1Select.value = String(data.revision_history[0].version);
                version2Select.value = String(data.revision_history[data.revision_history.length - 1].version);
            }
        } else {
            // Clear dropdowns if no history
            version1Select.innerHTML = '';
            version2Select.innerHTML = '';
        }
    } catch (error) {
        // Log error with context for debugging
        console.error('Failed to load revision history:', {
            storyId: currentStoryId,
            error: error.message,
            errorCode: error.error_code || 'UNKNOWN_ERROR',
            status: error.status
        });
        // Show non-intrusive error (revision history is optional feature)
        // Only show if it's a critical error
        if (error.status && error.status >= 500) {
            showError(`Failed to load revision history: ${error.message}`, error.error_code || 'REVISION_HISTORY_ERROR');
        }
    }
}

/**
 * Display version comparison results.
 * Renders a side-by-side comparison of two story versions with statistics.
 * 
 * @param {Object} data - Comparison data containing version1, version2, and comparison stats
 */
function displayComparison(data) {
    const resultsDiv = document.getElementById('comparison-results');
    
    const v1 = data.version1;
    const v2 = data.version2;
    const comp = data.comparison;
    
    // Sanitize all user-controlled data to prevent XSS
    // Ensure all values are properly escaped, especially type fields which could contain user input
    const v1Version = escapeHtml(String(v1.version || ''));
    const v1Type = escapeHtml(String(v1.type || ''));
    const v1Text = escapeHtml(String(v1.text || '').substring(0, 1000));
    const v1WordCount = escapeHtml(String(v1.word_count || 0));
    const v1Timestamp = escapeHtml(new Date(v1.timestamp || Date.now()).toLocaleString());
    
    const v2Version = escapeHtml(String(v2.version || ''));
    const v2Type = escapeHtml(String(v2.type || ''));
    const v2Text = escapeHtml(String(v2.text || '').substring(0, 1000));
    const v2WordCount = escapeHtml(String(v2.word_count || 0));
    const v2Timestamp = escapeHtml(new Date(v2.timestamp || Date.now()).toLocaleString());
    
    // Sanitize comparison stats (numeric values should be safe, but escape for defense in depth)
    const wordCountDiff = escapeHtml(String(comp.word_count_diff || 0));
    const wordsAdded = escapeHtml(String(comp.words_added || 0));
    const wordsRemoved = escapeHtml(String(comp.words_removed || 0));
    
    // Use safe class name (only 'positive' or 'negative', never user-controlled)
    const diffClass = (comp.word_count_diff >= 0) ? 'positive' : 'negative';
    const diffSign = (comp.word_count_diff >= 0) ? '+' : '';
    
    let html = `
        <div class="comparison-summary">
            <h4>Comparison Summary</h4>
            <div class="comparison-stats">
                <div class="stat-item">
                    <strong>Word Count Change:</strong> 
                    <span class="${diffClass}">
                        ${diffSign}${wordCountDiff}
                    </span>
                </div>
                <div class="stat-item">
                    <strong>Words Added:</strong> ${wordsAdded}
                </div>
                <div class="stat-item">
                    <strong>Words Removed:</strong> ${wordsRemoved}
                </div>
            </div>
        </div>
        <div class="comparison-texts">
            <div class="comparison-version">
                <h4>Version ${v1Version} (${v1Type})</h4>
                <div class="version-text">${v1Text}${(v1.text || '').length > 1000 ? '...' : ''}</div>
                <div class="version-meta">${v1WordCount} words | ${v1Timestamp}</div>
            </div>
            <div class="comparison-version">
                <h4>Version ${v2Version} (${v2Type})</h4>
                <div class="version-text">${v2Text}${(v2.text || '').length > 1000 ? '...' : ''}</div>
                <div class="version-meta">${v2WordCount} words | ${v2Timestamp}</div>
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = html;
}

/**
 * Escape HTML special characters to prevent XSS attacks.
 * 
 * @param {string} text - Text to escape
 * @returns {string} Escaped HTML string
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Set up story browser functionality.
 * Handles showing/hiding the story browser and toggling browser visibility.
 */
function setupStoryBrowser() {
    const showBrowserBtn = document.getElementById('show-browser-btn');
    const toggleBrowserBtn = document.getElementById('toggle-browser-btn');
    const browserSection = document.getElementById('story-browser-section');
    
    // Initially hide browser
    browserSection.style.display = 'none';
    
    showBrowserBtn.addEventListener('click', () => {
        browserSection.style.display = browserSection.style.display === 'none' ? 'block' : 'none';
        storyBrowserVisible = browserSection.style.display === 'block';
        if (storyBrowserVisible) {
            loadStoryBrowser();
        }
    });
    
    toggleBrowserBtn.addEventListener('click', () => {
        browserSection.style.display = 'none';
        storyBrowserVisible = false;
    });
}

/**
 * Load and display the story browser.
 * Fetches all stories from the API and renders them in a grid layout
 * with load buttons for each story.
 * 
 * @returns {Promise<void>}
 */
async function loadStoryBrowser() {
    const storyList = document.getElementById('story-list');
    storyList.innerHTML = '<p class="loading-text">Loading stories...</p>';
    
    try {
        const response = await fetch(`${API_BASE}/stories`);
        
        if (!response.ok) {
            throw await handleApiError(response, 'Failed to load stories', 'STORIES_LOAD_ERROR');
        }
        
        const data = await response.json();
        
        if (data.stories.length === 0) {
            storyList.innerHTML = '<p class="empty-message">No stories found. Create your first story!</p>';
            return;
        }
        
        let html = '<div class="story-grid">';
        data.stories.forEach(story => {
            const date = story.updated_at ? new Date(story.updated_at).toLocaleDateString() : 'Unknown date';
            const preview = story.premise ? (story.premise.length > 100 ? story.premise.substring(0, 100) + '...' : story.premise) : 'No premise';
            
            html += `
                <div class="story-card" data-story-id="${story.id}">
                    <div class="story-card-header">
                        <h3 class="story-title">${story.genre || 'Unknown Genre'}</h3>
                        <span class="story-date">${date}</span>
                    </div>
                    <p class="story-preview">${preview}</p>
                    <div class="story-meta">
                        <span class="story-word-count">${story.word_count ? story.word_count.toLocaleString() : 0} words</span>
                    </div>
                    <div class="story-card-actions">
                        <button class="btn btn-small load-story-btn" data-story-id="${story.id}">Load</button>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        storyList.innerHTML = html;
        
        // Initialize icons only in the newly added story list content
        initializeIcons(storyList);
        
        // Add event listeners to load buttons
        document.querySelectorAll('.load-story-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const storyId = e.target.getAttribute('data-story-id');
                await loadStory(storyId);
            });
        });
        
    } catch (error) {
        storyList.innerHTML = `<p class="error-message">Error loading stories: ${error.message}</p>`;
    }
}

/**
 * Load a specific story by ID.
 * Fetches story data from the API and populates the story editor.
 * 
 * @param {string} storyId - The ID of the story to load
 * @returns {Promise<void>}
 */
async function loadStory(storyId) {
    try {
        const response = await fetch(`${API_BASE}/story/${storyId}`);
        
        if (!response.ok) {
            throw await handleApiError(response, 'Failed to load story', 'LOAD_ERROR');
        }
        
        const data = await response.json();
        
        currentStoryId = storyId;
        const storyEditor = document.getElementById('story-editor');
        storyEditor.value = data.story;
        
        // Auto-resize textarea to fit content
        storyEditor.style.height = 'auto';
        const newHeight = Math.min(Math.max(storyEditor.scrollHeight, 600), 2000);
        storyEditor.style.height = newHeight + 'px';
        
        updateWordCount(data.word_count, data.max_words);
        
        const outputSection = document.getElementById('output-section');
        outputSection.style.display = 'block';
        if (typeof gsap !== 'undefined') {
            gsap.from(outputSection, { 
                opacity: 0, 
                y: 30, 
                duration: 0.6, 
                ease: 'power3.out' 
            });
        }
        outputSection.scrollIntoView({ behavior: 'smooth' });
        
        // Hide browser after loading
        const browserSection = document.getElementById('story-browser-section');
        if (typeof gsap !== 'undefined') {
            gsap.to(browserSection, { 
                opacity: 0, 
                height: 0, 
                duration: 0.4, 
                ease: 'power2.in',
                onComplete: () => {
                    browserSection.style.display = 'none';
                }
            });
        } else {
            browserSection.style.display = 'none';
        }
        storyBrowserVisible = false;
        
        // Load revision history if available
        await loadRevisionHistory();
        
        showSuccess('Story loaded successfully!');
    } catch (error) {
        showError(error.message, error.error_code || 'LOAD_ERROR');
    }
}

// Auto-update word count as user edits
document.getElementById('story-editor').addEventListener('input', async (e) => {
    const text = e.target.value;
    const wordCount = countWords(text);
    updateWordCount(wordCount, 7500);
    
    // Auto-validate if over limit
    if (wordCount > 7500) {
        updateWordCountStatus('error');
    } else if (wordCount > 7000) {
        updateWordCountStatus('warning');
    } else {
        updateWordCountStatus('ok');
    }
});

// Update story if we have a story ID
document.getElementById('story-editor').addEventListener('blur', async () => {
    if (!currentStoryId) return;
    
    const text = document.getElementById('story-editor').value;
    
    // Don't attempt to save empty stories
    if (!text || text.trim().length === 0) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/story/${currentStoryId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text })
        });
        
        if (!response.ok) {
            throw await handleApiError(response, 'Failed to auto-save story', 'AUTO_SAVE_ERROR');
        }
        
        const data = await response.json();
        updateWordCount(data.word_count, data.max_words);
        
        // Show subtle success indicator (non-intrusive)
        const wordCountEl = document.getElementById('word-count-text');
        if (wordCountEl) {
            const originalText = wordCountEl.textContent;
            wordCountEl.textContent = originalText + ' ✓';
            setTimeout(() => {
                wordCountEl.textContent = originalText;
            }, 2000);
        }
        
    } catch (error) {
        // Log error with context for debugging
        console.error('Failed to auto-save story:', {
            storyId: currentStoryId,
            error: error.message,
            errorCode: error.error_code || 'UNKNOWN_ERROR',
            status: error.status
        });
        
        // Show non-intrusive warning to user about auto-save failure
        // Use a subtle notification that doesn't interrupt workflow
        const wordCountEl = document.getElementById('word-count-text');
        if (wordCountEl) {
            const originalText = wordCountEl.textContent;
            wordCountEl.textContent = originalText + ' ⚠ (save failed)';
            wordCountEl.style.color = '#ef4444';
            setTimeout(() => {
                wordCountEl.textContent = originalText;
                wordCountEl.style.color = '';
            }, 5000);
        }
        
        // Show error notification only for critical errors (server errors, not client errors like validation)
        // This prevents interrupting the user for temporary network issues
        if (error.status && error.status >= 500) {
            showError('Auto-save failed. Your changes may not be saved. Please save manually.', error.error_code || 'AUTO_SAVE_ERROR');
        } else if (error.status && error.status === 0) {
            // Network error (status 0 usually means network failure)
            showError('Auto-save failed. Check your internet connection and save manually.', error.error_code || 'AUTO_SAVE_ERROR');
        }
        // For 4xx errors (client errors), we just show the word count indicator
        // as these are usually validation errors that the user can fix
    }
});

/**
 * Reset all progress steps to their initial state.
 * Clears active and completed classes from all pipeline progress steps.
 */
function resetProgressSteps() {
    const steps = ['step-premise', 'step-outline', 'step-scaffold', 'step-draft', 'step-revise'];
    steps.forEach(stepId => {
        const step = document.getElementById(stepId);
        if (step) {
            step.classList.remove('active', 'completed');
            const icon = step.querySelector('.step-icon');
            if (icon) icon.textContent = '○';
        }
    });
}

/**
 * Update a progress step's visual state.
 * 
 * @param {string} stepId - ID of the progress step element
 * @param {boolean} completed - Whether the step is completed (default: false)
 */
function updateProgressStep(stepId, completed = false) {
    const step = document.getElementById(stepId);
    if (!step) return;
    
    if (completed) {
        step.classList.add('active', 'completed');
        const icon = step.querySelector('.step-icon');
        if (icon) {
            icon.textContent = '✓';
            icon.style.fontSize = '1.5rem';
            if (typeof gsap !== 'undefined') {
                gsap.from(icon, { 
                    scale: 0, 
                    duration: 0.4, 
                    ease: 'back.out(2)' 
                });
            }
        }
        // Scroll the step into view when it completes
        step.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (typeof gsap !== 'undefined') {
            gsap.to(step, { 
                scale: 1.05, 
                duration: 0.3, 
                yoyo: true, 
                repeat: 1,
                ease: 'power2.inOut' 
            });
        }
    } else {
        step.classList.add('active');
        step.classList.remove('completed');
        const icon = step.querySelector('.step-icon');
        if (icon) {
            icon.textContent = '⟳';
            icon.style.fontSize = '1.5rem';
            // Animate the spinning icon
            if (typeof gsap !== 'undefined') {
                gsap.to(icon, {
                    rotation: 360,
                    duration: 2,
                    repeat: -1,
                    ease: 'linear'
                });
            }
        }
        // Scroll the active step into view
        step.scrollIntoView({ behavior: 'smooth', block: 'center' });
        if (typeof gsap !== 'undefined') {
            gsap.from(step, { 
                x: -20, 
                opacity: 0, 
                duration: 0.5, 
                ease: 'power2.out' 
            });
        }
    }
}

/**
 * Count words in a text string.
 * Splits text on whitespace and filters out empty strings.
 * 
 * @param {string} text - Text to count words in
 * @returns {number} Number of words in the text
 */
function countWords(text) {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

/**
 * Update the word count display in the UI.
 * Formats and displays current word count, max words, and remaining words.
 * 
 * @param {number} count - Current word count
 * @param {number} max - Maximum allowed word count
 */
function updateWordCount(count, max) {
    const wordCountText = document.getElementById('word-count-text');
    wordCountText.textContent = `${count.toLocaleString()} / ${max.toLocaleString()} words`;
    
    const remaining = max - count;
    if (remaining < 0) {
        wordCountText.textContent += ` (${Math.abs(remaining)} over limit)`;
    } else {
        wordCountText.textContent += ` (${remaining} remaining)`;
    }
}

/**
 * Update the word count status indicator.
 * Sets the visual status (ok, warning, error) based on word count.
 * 
 * @param {string} status - Status type: 'ok', 'warning', or 'error'
 */
function updateWordCountStatus(status) {
    const statusEl = document.getElementById('word-count-status');
    statusEl.className = `status-indicator status-${status}`;
}

/**
 * Display validation results in the UI.
 * Renders word count validation and distinctiveness score with suggestions.
 * 
 * @param {Object} data - Validation data containing word_count, max_words, 
 *                        is_valid, and distinctiveness information
 */
function displayValidationResults(data) {
    const resultsDiv = document.getElementById('validation-results');
    resultsDiv.style.display = 'block';
    
    const distinctiveness = data.distinctiveness;
    const score = distinctiveness.distinctiveness_score;
    const scorePercent = (score * 100).toFixed(1);
    
    let html = `
        <h3>Validation Results</h3>
        <div class="result-item">
            <strong>Word Count:</strong> ${data.word_count.toLocaleString()} / ${data.max_words.toLocaleString()}
            ${data.is_valid ? '✓' : '✗'}
        </div>
        <div class="result-item">
            <strong>Distinctiveness Score:</strong> 
            <span class="score">${scorePercent}%</span>
            ${score >= 0.7 ? '✓' : '⚠ Needs improvement'}
        </div>
    `;
    
    if (distinctiveness.has_cliches) {
        html += `
            <div class="result-item">
                <strong>Clichés Found:</strong> ${distinctiveness.cliche_count}
                <ul>
                    ${distinctiveness.found_cliches.map(c => `<li>${c}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    if (distinctiveness.suggestions && distinctiveness.suggestions.length > 0) {
        html += `
            <div class="result-item">
                <strong>Suggestions:</strong>
                <ul>
                    ${distinctiveness.suggestions.map(s => `<li>${s}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    resultsDiv.innerHTML = html;
}

/**
 * Show the loading indicator.
 * Displays a loading overlay with animation.
 */
function showLoading() {
    const loadingEl = document.getElementById('loading');
    if (!loadingEl) return;
    
    // Make sure it's visible
    loadingEl.style.display = 'block';
    loadingEl.classList.remove('hidden');
    
    // Scroll to loading indicator so user sees it
    loadingEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    document.getElementById('loading-text').textContent = 'Generating your story...';
    
    if (typeof gsap !== 'undefined') {
        gsap.from(loadingEl, { 
            opacity: 0, 
            scale: 0.9, 
            duration: 0.4, 
            ease: 'power2.out' 
        });
    }
    // Only initialize icons in the loading element (if any icons are added dynamically)
    initializeIcons(loadingEl);
}

/**
 * Hide the loading indicator.
 * Hides the loading overlay with fade-out animation.
 */
function hideLoading() {
    const loadingEl = document.getElementById('loading');
    if (!loadingEl) return;
    
    if (typeof gsap !== 'undefined') {
        gsap.to(loadingEl, { 
            opacity: 0, 
            scale: 0.9, 
            duration: 0.3, 
            ease: 'power2.in',
            onComplete: () => {
                loadingEl.classList.add('hidden');
                loadingEl.style.display = 'none';
            }
        });
    } else {
        loadingEl.classList.add('hidden');
        loadingEl.style.display = 'none';
    }
}

/**
 * Display an error message to the user.
 * Shows an error notification with optional error code and auto-hides after 10 seconds.
 * 
 * @param {string} message - Error message to display
 * @param {string|null} errorCode - Optional error code to include in the message
 */
function showError(message, errorCode = null) {
    const errorDiv = document.getElementById('error');
    const errorMessage = errorDiv.querySelector('.error-message');
    
    errorDiv.className = 'error';
    errorMessage.textContent = message;
    
    // Add error code if provided
    if (errorCode) {
        errorMessage.textContent += ` (Error: ${errorCode})`;
    }
    
    errorDiv.classList.remove('hidden');
    if (typeof gsap !== 'undefined') {
        gsap.from(errorDiv, { 
            opacity: 0, 
            x: -30, 
            duration: 0.4, 
            ease: 'power2.out' 
        });
    }
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    // Only initialize icons in the error element (if any icons are added dynamically)
    initializeIcons(errorDiv);
    
    // Auto-hide after 10 seconds
    setTimeout(() => {
        if (!errorDiv.classList.contains('hidden')) {
            if (typeof gsap !== 'undefined') {
                gsap.to(errorDiv, { 
                    opacity: 0, 
                    x: -30, 
                    duration: 0.3, 
                    ease: 'power2.in',
                    onComplete: () => {
                        errorDiv.classList.add('hidden');
                    }
                });
            } else {
                errorDiv.classList.add('hidden');
            }
        }
    }, 10000);
}

/**
 * Hide the error message.
 * Removes the error notification from view.
 */
function hideError() {
    const errorDiv = document.getElementById('error');
    errorDiv.classList.add('hidden');
}

/**
 * Display a success message to the user.
 * Shows a success notification with animation and auto-hides after 3 seconds.
 * 
 * @param {string} message - Success message to display
 */
function showSuccess(message) {
    const errorDiv = document.getElementById('error');
    const errorMessage = errorDiv.querySelector('.error-message');
    
    errorDiv.className = 'success';
    errorMessage.textContent = message;
    errorDiv.classList.remove('hidden');
    if (typeof gsap !== 'undefined') {
        gsap.from(errorDiv, { 
            opacity: 0, 
            y: -20, 
            scale: 0.95,
            duration: 0.4, 
            ease: 'back.out(1.5)' 
        });
    }
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    // Only initialize icons in the success/error element (if any icons are added dynamically)
    initializeIcons(errorDiv);
    
    setTimeout(() => {
        if (typeof gsap !== 'undefined') {
            gsap.to(errorDiv, { 
                opacity: 0, 
                y: -20, 
                scale: 0.95,
                duration: 0.3, 
                ease: 'power2.in',
                onComplete: () => {
                    errorDiv.classList.add('hidden');
                }
            });
        } else {
            errorDiv.classList.add('hidden');
        }
    }, 3000);
}
