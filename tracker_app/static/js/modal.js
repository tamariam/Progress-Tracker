

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

function fetchAndDisplayActions(status, page = 1) {
    // Include page number in the API request
    const url = `/api/actions/filter/${status.toLowerCase()}/?page=${page}`; 
    
    const tableArea = document.getElementById('filtered-table-view-container');
    const accordionArea = document.getElementById('accordion-view-container');
    const modalTitle = document.getElementById('modalThemeTitle');

    // Initial UI state
    accordionArea.style.display = 'none'; 
    tableArea.style.display = ''; 

    fetch(url)
        .then(response => response.json())
        .then(data => {
            const statusHeaderClass = `header-${status.toLowerCase()}`;
            
            // 1. Build the Table Structure
            let htmlOutput = `
                <div class="action-table-container">
                    <table class="action-table">
                        <thead class="${statusHeaderClass}">
                            <tr>
                                <th>Action</th>
                                <th>Description</th>
                                <th class="text-right">Details</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            // 2. Loop through Actions
            data.actions.forEach(action => {
                const statusLower = action.status.toLowerCase();
                const showUpdates = statusLower === 'in_progress' || statusLower === 'completed';
                htmlOutput += `
                    <tr class="action-summary-row status-${statusLower}">
                        <td class="title-col"><strong>${action.title}</strong></td>
                        <td class="objective-col">${action.small_description}</td>
                        <td class="details-col text-right">
                            <button class="btn btn-sm view-button" onclick="handleDetailsToggle(this)">Show More</button>
                            <button class="btn btn-sm toggle-details close-button universal-action-button" style="display: none;" onclick="handleDetailsToggle(this)">&minus;</button>
                        </td>
                    </tr>
                    <tr class="full-details" style="display: none;">
                        <td colspan="3">
                            <div class="details-content">
                                <h5>Action Description:</h5>
                                <div>${action.description}</div>
                    ${showUpdates ? `
                        <hr class="bg-light">
                        <h5>Latest Update:</h5>
                        <div>${action.update || 'No update recorded yet.'}</div>
                    ` : ''} <!-- Fixed: Backtick before the colon -->
                </div>
            </td>
        </tr>
    `;
});
                 
            
            htmlOutput += '</tbody></table></div>';
   
            // 3. Add Pagination Controls (if more than 1 page)
            if (data.total_pages > 1) {
                htmlOutput += `<div class="pagination-controls text-center mt-3">`;
                if (data.has_previous) {
                    htmlOutput += `<button class="btn btn-sm btn-outline-secondary mx-1" onclick="fetchAndDisplayActions('${status}', ${data.current_page - 1})">Previous</button>`;
                }
                htmlOutput += `<span class="mx-2">Page ${data.current_page} of ${data.total_pages}</span>`;
                if (data.has_next) {
                    htmlOutput += `<button class="btn btn-sm btn-outline-secondary mx-1" onclick="fetchAndDisplayActions('${status}', ${data.current_page + 1})">Next</button>`;
                }
                htmlOutput += `</div>`;
            }
            
            // 4. Add the Centered "Go Back" Button
            htmlOutput += `
                <p class="text-center">
                    <button class="btn mcc-blue text-white mt-3 btn-back" onclick="hideFilteredActions()">← Back</button>
                </p>
            `;
            
            // 5. Inject final HTML and update title
            tableArea.innerHTML = htmlOutput;
           
        })
        .catch(error => {
            console.error('Error fetching filtered actions:', error);
            tableArea.innerHTML = `
                <div class="text-center py-4">
                    <p class="text-danger">Error loading content. Please try again.</p>
                    <button class="btn btn-secondary btn-back" onclick="history.back()">Back</button>
                </div>
            `;
        });
}

let currentModalThemeTitle = ''; 
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

// Scroll to Top Button Functionality
// 1. Get the button element
const scrollToTopBtn = document.getElementById("scrollToTopBtn");

// 2. Handle visibility on scroll
window.onscroll = function() {
    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
        scrollToTopBtn.style.display = "block";
    } else {
        scrollToTopBtn.style.display = "none";
    }
};

// 3. Smooth scroll logic
function scrollToTopFunction() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

