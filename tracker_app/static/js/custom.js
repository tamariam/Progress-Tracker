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
    // Add the capitalization function here
    function capitalizeEachWord(str) {
        if (!str) return '';
        // Regular expression to find the start of each word (\b) and the first character (\w)
        return str.replace(/\b\w/g, char => char.toUpperCase());
    }

    // Selector looks for any <a> tag with the 'data-theme-id' attribute
    document.querySelectorAll('a[data-theme-id]').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault(); // Stop the link's default behavior

            const themeId = this.getAttribute('data-theme-id');
            const urlTemplate = document.getElementById('api-url-template').getAttribute('data-url-template');
            const url = urlTemplate.replace('__ID__', themeId);
             

            document.getElementById('modalThemeTitle').textContent = "Loading...";
            document.getElementById('dynamicModalContent').innerHTML = '<p>Fetching data, please wait...</p>';

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('dynamicModalContent').innerHTML = data.html_content;
                    
                    // Use the function to capitalize the title before setting it
                    const capitalizedTitle = capitalizeEachWord(data.title);
                    document.getElementById('modalThemeTitle').textContent = capitalizedTitle;
                    
                    // Manually show the modal using Bootstrap JS
                    const modalElement = document.getElementById('portfolioModal');
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
function toggleActionAccordion(button) {
    button.classList.toggle("active-action");
    const content = button.nextElementSibling;
    content.classList.toggle("show-action");
    if (content.style.maxHeight) { content.style.maxHeight = null; } else { content.style.maxHeight = content.scrollHeight + "px"; }
    
    // Ensure the parent objective accordion expands if needed
    const parentAccordionContent = button.closest('.accordion-content');
    if (parentAccordionContent && parentAccordionContent.style.maxHeight) {
        parentAccordionContent.style.maxHeight = parentAccordionContent.scrollHeight + content.scrollHeight + "px";
    }
}