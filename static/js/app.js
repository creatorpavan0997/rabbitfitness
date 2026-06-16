// Client-Side App Functionality for Rabbit Fitness

// 1. Theme Configuration & Toggling
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        updateThemeBtnIcon(savedTheme);
        themeBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeBtnIcon(newTheme);
            // Re-render charts to adjust text colors
            if (window.renderCharts) window.renderCharts();
        });
    }
});

function updateThemeBtnIcon(theme) {
    const btn = document.getElementById('theme-toggle');
    if (!btn) return;
    if (theme === 'dark') {
        btn.innerHTML = '☀️ <span class="d-none d-md-inline ms-1">Light Mode</span>';
    } else {
        btn.innerHTML = '🌙 <span class="d-none d-md-inline ms-1">Dark Mode</span>';
    }
}

// 2. CSRF Token Helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 3. Simple Markdown Parser for Coach Responses
function parseMarkdown(text) {
    if (!text) return "";
    let html = text
        .replace(/### (.*?)\n/g, '<h5 class="mt-3 text-primary">$1</h5>')
        .replace(/## (.*?)\n/g, '<h4 class="mt-4 text-primary">$1</h4>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/- (.*?)\n/g, '<li class="ms-3">$1</li>')
        .replace(/\n\n/g, '<br>')
        .replace(/\n/g, '<br>');
    return html;
}

// 4. API Request Handler
async function apiRequest(url, method = 'GET', data = null) {
    const config = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };
    if (data) {
        config.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, config);
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.error || `HTTP error! Status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("API Request Failed:", error);
        throw error;
    }
}
