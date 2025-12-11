function animateCounter(entries, observer) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const counters = document.querySelectorAll('.counter-value');
            counters.forEach(counter => {
                const target = +counter.getAttribute('data-target');
                let current = 0;
                const increment = target / 40;
                const updateCounter = () => {
                    if (current < target) { current += increment; counter.innerText = Math.ceil(current); requestAnimationFrame(updateCounter); } else { counter.innerText = target; }
                };
                updateCounter();
            }); observer.unobserve(entry.target);
        }
    });
}
const counterSection = document.getElementById('strategy-counter');
if (counterSection) {
    const observerOptions = { root: null, threshold: 0.5 };
    const observer = new IntersectionObserver(animateCounter, observerOptions);
    observer.observe(counterSection);
}

// Accordion Functionality (for Objectives)
function toggleAccordion(button) {
    document.querySelectorAll('.accordion-title.active').forEach(activeButton => {
        if (activeButton !== button) { activeButton.classList.remove("active"); const activeContent = activeButton.nextElementSibling; activeContent.classList.remove("show"); activeContent.style.maxHeight = null; }
    });
    button.classList.toggle("active");
    const content = button.nextElementSibling;
    content.classList.toggle("show");
    if (content.style.maxHeight) { content.style.maxHeight = null; } else { content.style.maxHeight = content.scrollHeight + "px"; }
}


// --- JAVASCRIPT FOR THE FLEXBOX CARD LAYOUT ---

// This function is now called directly via onclick="handleDetailsToggle(this)" in the HTML


function handleDetailsToggle(clickedElement) {
    // Determine which action card we are working with
    const cardItem = clickedElement.closest('.action-card-item');

    // Get the two main parts: summary row and details div
    const summaryRow = cardItem.querySelector('.action-summary-row');
    const detailsDiv = cardItem.querySelector('.full-details');
    
    // Get the specific buttons
    const viewButton = summaryRow.querySelector('.view-button');
    const closeButton = summaryRow.querySelector('.close-button');
    
    // Toggle visibility
    if (detailsDiv.style.display === 'none') {
        // Switch to details view
        detailsDiv.style.display = 'block';
        viewButton.style.display = 'none'; // Hide "View"
        closeButton.style.display = 'inline-block'; // Show "Minus Icon"
    } else {
        // Switch back to summary view
        detailsDiv.style.display = 'none';
        viewButton.style.display = 'inline-block'; // Show "View"
        closeButton.style.display = 'none'; // Hide "Minus Icon"
    }
}

// --- END JAVASCRIPT ---


// NOTE: The original toggleUpdate function and toggleActionAccordion function have been removed


// --- All your other existing code below this line is unchanged ---

document.addEventListener('DOMContentLoaded', (event) => {
    function capitalizeEachWord(str) { if (!str) return ''; return str.replace(/\b\w/g, char => char.toUpperCase()); }
    function processExternalLinks(targetElement) { const links = targetElement.querySelectorAll('a'); links.forEach(link => { if (link.hostname !== window.location.hostname) { link.setAttribute('target', '_blank'); link.setAttribute('rel', 'noopener noreferrer'); } }); }
    
    document.querySelectorAll('a[data-theme-id]').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault(); 
            const themeId = this.getAttribute('data-theme-id');
            const urlTemplate = document.getElementById('api-url-template').getAttribute('data-url-template');
            const url = urlTemplate.replace('__ID__', themeId);
            document.getElementById('modalThemeTitle').textContent = "Loading...";
            document.getElementById('dynamicModalContent').innerHTML = '<p>Fetching data, please wait...</p>';
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    const contentArea = document.getElementById('dynamicModalContent');
                    contentArea.innerHTML = data.html_content;
                    processExternalLinks(contentArea); 
                    const capitalizedTitle = capitalizeEachWord(data.title);
                    document.getElementById('modalThemeTitle').textContent = capitalizedTitle;
                    const modalElement = document.getElementById('portfolioModal');
                    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
                    modal.show();
                    // The handleDetailsToggle is called via onclick in the HTML now, no extra JS needed here.
                })
                .catch(error => {
                    console.error('Error fetching theme details:', error);
                    document.getElementById('dynamicModalContent').innerHTML = '<p>Error loading content.</p>';
                    document.getElementById('modalThemeTitle').textContent = 'Error';
                });
        });
    });
    processExternalLinks(document);
});


function closeMCCModal() {
    const modalElement = document.getElementById('portfolioModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.hide();
}