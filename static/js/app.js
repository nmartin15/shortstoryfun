// Short Story Pipeline - Frontend JavaScript

const API_BASE = '/api';

let currentStoryId = null;

// Form submission
document.getElementById('story-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const genre = document.getElementById('genre').value.trim();
    const idea = document.getElementById('idea').value.trim();
    const characterInput = document.getElementById('character').value.trim();
    const theme = document.getElementById('theme').value.trim();
    
    if (!genre) {
        showError('Genre selection is required');
        return;
    }
    
    if (!idea) {
        showError('Story idea is required');
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
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to generate story');
        }
        
        currentStoryId = data.story_id;
        document.getElementById('story-editor').value = data.story;
        updateWordCount(data.word_count, data.max_words);
        
        // Show genre info if available
        if (data.genre_config) {
            console.log('Genre config:', data.genre_config);
        }
        
        document.getElementById('output-section').style.display = 'block';
        document.getElementById('output-section').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
});

// Save button
document.getElementById('save-btn').addEventListener('click', () => {
    const text = document.getElementById('story-editor').value;
    if (!text) {
        showError('No story to save');
        return;
    }
    
    // For now, just show success (can implement file saving later)
    showSuccess('Story saved! (File saving will be implemented)');
});

// Regenerate button
document.getElementById('regenerate-btn').addEventListener('click', () => {
    document.getElementById('story-form').dispatchEvent(new Event('submit'));
});

// Validate button
document.getElementById('validate-btn').addEventListener('click', async () => {
    const text = document.getElementById('story-editor').value;
    
    if (!text) {
        showError('No story to validate');
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
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Validation failed');
        }
        
        displayValidationResults(data);
        
    } catch (error) {
        showError(error.message);
    }
});

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
    
    try {
        const response = await fetch(`${API_BASE}/story/${currentStoryId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to update story');
        }
        
        updateWordCount(data.word_count, data.max_words);
        
    } catch (error) {
        console.error('Failed to auto-save:', error);
    }
});

// Helper functions
function countWords(text) {
    if (!text) return 0;
    return text.trim().split(/\s+/).filter(word => word.length > 0).length;
}

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

function updateWordCountStatus(status) {
    const statusEl = document.getElementById('word-count-status');
    statusEl.className = `status-${status}`;
}

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

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
    document.getElementById('error').style.display = 'none';
}

function showSuccess(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.className = 'success';
    errorDiv.style.display = 'block';
    errorDiv.scrollIntoView({ behavior: 'smooth' });
    
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 3000);
}

