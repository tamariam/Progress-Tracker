

// static/js/custom.js

// Function to handle the actual counting animation
function animateCounter(entries, observer) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            // Found the section, now find all specific counter elements inside it
            const counters = document.querySelectorAll('.counter-value');
            
            counters.forEach(counter => {
                const target = +counter.getAttribute('data-target'); // Get the final number (4, 29, 122)
                let current = 0;
                const increment = target / 40; // Determines the speed (150 frames total)

                const updateCounter = () => {
                    if (current < target) {
                        current += increment;
                        // Use innerText to update the visible number
                        counter.innerText = Math.ceil(current); 
                        requestAnimationFrame(updateCounter); // Loop the animation
                    } else {
                        counter.innerText = target; // Ensure the final value is exactly the target
                    }
                };
                updateCounter();
            });
            
            // Stop observing after the animation runs once
            observer.unobserve(entry.target); 
        }
    });
}
// finish counter animation

// Set up the Intersection Observer to watch for the section scrolling into view
const counterSection = document.getElementById('strategy-counter');
if (counterSection) {
    const observerOptions = {
        root: null, // observe against the viewport
        threshold: 0.5 // trigger when 50% of the section is visible
    };
    const observer = new IntersectionObserver(animateCounter, observerOptions);
    observer.observe(counterSection);
}

// Accordion Functionality (for Objectives)
function toggleAccordion(button) {
    // We target the class 'accordion-title' used in your HTML
    document.querySelectorAll('.accordion-title.active').forEach(activeButton => {
        if (activeButton !== button) {
            activeButton.classList.remove("active");
            const activeContent = activeButton.nextElementSibling;
            activeContent.classList.remove("show");
            activeContent.style.maxHeight = null;
        }
    });

    // Toggle the current accordion
    button.classList.toggle("active");
    const content = button.nextElementSibling;
    content.classList.toggle("show");
    if (content.style.maxHeight) { 
        content.style.maxHeight = null; 
    } else { 
        content.style.maxHeight = content.scrollHeight + "px"; 
    }
}

// NOTE: The toggleUpdate function is NOT used in the HTML provided in your last message.
// It seems you removed the "View Update" button functionality. I will keep it in case you add it back later.
function toggleUpdate(button) {
    const actionCard = button.closest('.action-card');
    if (actionCard) {
        document.querySelectorAll('.update-content.show-update').forEach(activeUpdate => {
            const associatedButton = activeUpdate.closest('.action-card').querySelector('.update-toggle-button'); 
            if (activeUpdate !== actionCard.querySelector('.update-content')) {
                activeUpdate.classList.remove("show-update");
                if (associatedButton) associatedButton.textContent = "View Update";
            }
        });

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

// Nested Action Accordion Functionality (for "Action Plan" buttons)
function toggleActionAccordion(button) {
    // We target the class 'action-sub-title' used in your HTML
    document.querySelectorAll('.action-sub-title.active-action').forEach(activeButton => {
        if (activeButton !== button) {
            activeButton.classList.remove("active-action");
            // The next element sibling is the .action-sub-content
            const activeContent = activeButton.nextElementSibling;
            activeContent.classList.remove("show-action");
            activeContent.style.maxHeight = null;
        }
    });

    // Toggle the current action accordion
    button.classList.toggle("active-action");
    const content = button.nextElementSibling; // This is the .action-sub-content div
    content.classList.toggle("show-action");
    if (content.style.maxHeight) { 
        content.style.maxHeight = null; 
    } else { 
        content.style.maxHeight = content.scrollHeight + "px"; 
    }
    
    // Ensure the parent objective accordion expands if needed
    const parentAccordionContent = button.closest('.accordion-content');
    if (parentAccordionContent && parentAccordionContent.style.maxHeight) {
         // Recalculate parent height
         // Note: The smooth maxHeight transition needs careful recalculation for nested items
         parentAccordionContent.style.maxHeight = (parentAccordionContent.scrollHeight + content.scrollHeight) + "px";
    }
}




// --- All your other existing code below this line is unchanged ---

document.addEventListener('DOMContentLoaded', (event) => {
    // ... (rest of the code for the modal functionality is here) ...
    function capitalizeEachWord(str) {
        if (!str) return '';
        return str.replace(/\b\w/g, char => char.toUpperCase());
    }
    function processExternalLinks(targetElement) {
        const links = targetElement.querySelectorAll('a');
        links.forEach(link => {
            if (link.hostname !== window.location.hostname) {
                link.setAttribute('target', '_blank');
                link.setAttribute('rel', 'noopener noreferrer');
            }
        });
    }
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
// counting animation


