// static/js/custom.js

// Accordion Functionality
function toggleAccordion(button) {
    button.classList.toggle("active");
    const content = button.nextElementSibling;
    content.classList.toggle("show");
    if (content.style.maxHeight) { content.style.maxHeight = null; } else { content.style.maxHeight = content.scrollHeight + "px"; }
}

// Expandable Update Functionality
// static/js/custom.js

// ... (Keep toggleAccordion and other code the same) ...

// Expandable Update Functionality - Simplified
function toggleUpdate(button) {
    const actionCard = button.closest('.action-card');
    if (actionCard) {
        const updateContent = actionCard.querySelector('.update-content');
        if (updateContent) {
            updateContent.classList.toggle("show-update");
            if (updateContent.classList.contains("show-update")) {
                button.textContent = "Hide Update";
            } else {
                button.textContent = "View Update";
            }
        }
    }
}


// ... (Keep the rest of the AJAX code the same) ...


// AJAX functionality to fetch content when a theme link is clicked
document.addEventListener('DOMContentLoaded', (event) => {
    // Selector looks for any <a> tag with the 'data-theme-id' attribute
    document.querySelectorAll('a[data-theme-id]').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault(); // Stop the link's default behavior

            const themeId = this.getAttribute('data-theme-id');
            const urlTemplate = document.getElementById('api-url-template').getAttribute('data-url-template');
            const url = urlTemplate.replace('0', themeId); 

            document.getElementById('modalThemeTitle').textContent = "Loading...";
            document.getElementById('dynamicModalContent').innerHTML = '<p>Fetching data, please wait...</p>';

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('dynamicModalContent').innerHTML = data.html_content;
                    document.getElementById('modalThemeTitle').textContent = data.title;
                    
                    // Manually show the modal using Bootstrap JS
                    const modalElement = document.getElementById('portfolioModal');
                    // Ensure you have Bootstrap JS loaded *before* custom.js
                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                    modal.show();
                })
                .catch(error => {
                    console.error('Error fetching theme details:', error);
                    document.getElementById('dynamicModalContent').innerHTML = '<p>Error loading content.</p>';
                    document.getElementById('modalThemeTitle').textContent = 'Error';
                });
        });
    });
});

function closeMCCModal() {
    const modalElement = document.getElementById('portfolioModal');
    // Get the Bootstrap instance and call the hide() method gracefully
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.hide();
}