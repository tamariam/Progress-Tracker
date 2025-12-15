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
    // Determine which action row (TR) we are working with
    const summaryRow = clickedElement.closest('tr.action-summary-row'); 
    
    // The details row is the very next TR sibling (this is the one we hide/show)
    const detailsDiv = summaryRow.nextElementSibling; 

    // Get the specific buttons within the summary row
    const viewButton = summaryRow.querySelector('.view-button');
    const closeButton = summaryRow.querySelector('.close-button');
    
    // Toggle visibility ('' shows the TR, 'none' hides it)
    if (detailsDiv.style.display === 'none') {
        // Switch to details view
        detailsDiv.style.display = ''; // Show the table row
        viewButton.style.display = 'none'; // Hide "Show More"
        closeButton.style.display = 'inline-block'; // Show "Minus Icon"
    } else {
        // Switch back to summary view
        detailsDiv.style.display = 'none'; // Hide the table row
        viewButton.style.display = 'inline-block'; // Show "Show More"
        closeButton.style.display = 'none'; // Hide "Minus Icon"
    }
}

// --- END JAVASCRIPT ---


// NOTE: The original toggleUpdate function and toggleActionAccordion function have been removed
function hideFilteredActions() {
    // Show the original accordion/objective view
    document.getElementById('accordion-view-container').style.display = ''; 
    // Hide the filtered table view
    document.getElementById('filtered-table-view-container').style.display = 'none';
    // Update the modal title if needed, or close the modal if you prefer
    // document.getElementById('modalThemeTitle').textContent = "Meath Digital Strategy"; 
}

// --- All your other existing code below this line is unchanged ---
function fetchAndDisplayActions(status) {
    // Note: The URL must match the Django URL pattern you set up earlier: 
    // path('api/actions/filter/<str:status>/', ...)
    const url = `/api/actions/filter/${status.toLowerCase()}/`; 

    // Target the specific containers within the modal
    const accordionArea = document.getElementById('accordion-view-container');
    const tableArea = document.getElementById('filtered-table-view-container');
    const modalTitle = document.getElementById('modalThemeTitle');
    
    if (!accordionArea || !tableArea || !modalTitle) {
        console.error("Modal content areas not found. Ensure IDs are correct.");
        return; 
    }

    // Set loading state and switch view
    modalTitle.textContent = `Loading ${capitalizeEachWord(status.replace('_', ' '))} Actions...`;
    accordionArea.style.display = 'none'; // Hide the default view
    tableArea.style.display = ''; // Show the new area

    fetch(url)
        .then(response => response.json())
        .then(data => {
            // Build the HTML table structure that mimics your original HTML style
            let htmlOutput = `
                <h2>${capitalizeEachWord(data.status_title)} Actions (${data.count})</h2>
                <p><button class="btn btn-secondary" onclick="hideFilteredActions()">← Back to Objective Accordions</button></p>
                
                <div class="action-table-container">
                    <table class="action-table">
                        <thead>
                            <tr>
                                <!-- "Status" column removed as requested -->
                                <th>Action</th>
                                <th>Objective</th>
                                <th class="text-right">Details</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            data.actions.forEach(action => {
                // Determine if 'NOT_STARTED' check is needed for update section (JS equivalent of Django template logic)
                const needsUpdateSection = action.status.toLowerCase() !== 'not_started';
                const updateHtml = needsUpdateSection ? `
                    <hr class="bg-light">
                    <h5>Latest Update:</h5>
                    <p>${action.description || 'No update available.'}</p>
                ` : '';

                // Build the summary row and the hidden details row
                htmlOutput += `
                    <!-- Summary Row: Use the status class for the left border CSS we defined -->
                    <tr class="action-summary-row status-${action.status.toLowerCase()}" data-action-id="${action.id}"> 
                        <td class="title-col">
                            <strong>${action.title}</strong><br>
                            <p class="text-muted">${action.small_description}</p>
                        </td>
                        <td class="objective-col">
                            ${action.objective_title}
                        </td>
                        <td class="details-col text-right">
                            <!-- Buttons rely on your existing handleDetailsToggle JS function -->
                            <button class="btn btn-sm toggle-details view-button universal-action-button" onclick="handleDetailsToggle(this)">Show More</button>
                            <button class="btn btn-sm toggle-details close-button universal-action-button" style="display: none;" onclick="handleDetailsToggle(this)">&minus;</button>
                        </td>
                    </tr>
                    
                    <!-- Details Content (Hidden TR): Use same classes -->
                    <tr class="full-details" style="display: none;">
                        <td colspan="3">
                            <div class="details-content">
                                <h5>Action Description:</h5>
                                <p>${action.description}</p>
                                ${updateHtml}
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            // Close the table and containers
            htmlOutput += '</tbody></table></div>'; 

            // Inject the finished HTML
            modalTitle.textContent = `${capitalizeEachWord(data.status_title)} Actions`;
            tableArea.innerHTML = htmlOutput;
        })
        .catch(error => {
            console.error('Error fetching filtered actions:', error);
            tableArea.innerHTML = '<p>Error loading content.</p><button onclick="hideFilteredActions()">Go Back</button>';
        });
}
// ggggggggggggggggggggggggggggg
document.addEventListener('DOMContentLoaded', (event) => {
//    new code

const portfolioModal = document.getElementById('portfolioModal');

    if (portfolioModal) {
        // Listen for clicks that happen anywhere inside the modal
        portfolioModal.addEventListener('click', function(e) {
            // Check if the actual element clicked, or any of its parents, has the .status-card class
            const clickedCard = e.target.closest('.status-card');
            
            if (clickedCard) {
                const status = clickedCard.getAttribute('data-status');
                if (status) {
                    // Call the function using the status found in the data attribute
                    fetchAndDisplayActions(status);
                }
            }
        });
    }
    // NEW CODE BLOCK FOR THE MODAL THEME DETAILS FETCHING
    
    // ////FINISH CODE BLOCK FOR THE MODAL THEME DETAILS FETCHING
    
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