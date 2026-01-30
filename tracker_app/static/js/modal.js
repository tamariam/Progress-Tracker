

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
function toggleAccordion(element) {
    const currentContent = element.nextElementSibling;
    const allContents = document.querySelectorAll('.accordion-content');
    const allTitles = document.querySelectorAll('.accordion-title');

    const isOpening = !currentContent.classList.contains('show');

    // 1. CLOSE EVERYTHING 
    allContents.forEach(content => {
        // --- NEW RESET LOGIC FOR INTERNAL ACTIONS ---
        // Find every detail row inside this specific objective and hide it
        const internalDetails = content.querySelectorAll('.full-details');
        const viewButtons = content.querySelectorAll('.view-button');
        const closeButtons = content.querySelectorAll('.close-button');

        internalDetails.forEach(detail => {
            detail.style.display = 'none'; // Hide the expanded row
        });
        
        viewButtons.forEach(btn => {
            btn.style.display = 'inline-block'; // Show "Show More"
        });

        closeButtons.forEach(btn => {
            btn.style.display = 'none'; // Hide the minus icon
        });
        // --- END OF INTERNAL RESET ---

        content.classList.remove('show');
        content.style.maxHeight = "0px";
        content.style.display = "none";
    });

    allTitles.forEach(title => title.classList.remove('active'));

    // 2. OPEN ONLY THE CLICKED ONE
    if (isOpening) {
        element.classList.add('active');
        currentContent.classList.add('show');
        currentContent.style.display = "block";
        
        // Dynamic scrollHeight + buffer for 2026 table growth
        currentContent.style.maxHeight = (currentContent.scrollHeight + 1000) + "px";
    }
}





function handleDetailsToggle(clickedElement) {
    const summaryRow = clickedElement.closest('tr.action-summary-row'); 
    const detailsRow = summaryRow.nextElementSibling; 

    const viewButton = summaryRow.querySelector('.view-button');
    const closeButton = summaryRow.querySelector('.close-button');
    
    // Check computed style for accuracy
    const isHidden = window.getComputedStyle(detailsRow).display === 'none';
    
    if (isHidden) {
        detailsRow.classList.add('expanded');
        // Dynamic display: use 'table-row' for desktop, 'block' for mobile
        const isMobile = window.innerWidth <= 541;
        detailsRow.style.display = isMobile ? 'block' : 'table-row'; 
        
        viewButton.style.display = 'none';
        closeButton.style.display = 'inline-block';
    } else {
        detailsRow.classList.remove('expanded');
        detailsRow.style.display = 'none';
        
        viewButton.style.display = 'inline-block';
        closeButton.style.display = 'none';
    }
}






function hideFilteredActions() {
    // 1. THE RESET: Force all objectives to close before returning
    // This ensures a "fresh start" for the user
    

    document.querySelectorAll('.accordion-content').forEach(content => {
        content.classList.remove('show');
        content.style.display = 'none'; // Re-hides the container
        content.style.maxHeight = '0';   // Resets the height to match your CSS
    });

    document.querySelectorAll('.accordion-title').forEach(title => {
        title.classList.remove('active'); // Removes the #f1f1f1 highlight
    });

    // 2. Switch the view back to the main list
    document.getElementById('accordion-view-container').style.display = 'block'; 
    document.getElementById('filtered-table-view-container').style.display = 'none';

    // 3. Reset Scroll: Keeps the user at the top of the modal
    const modalBody = document.querySelector('.modal-body');
    if (modalBody) modalBody.scrollTop = 0;
}


// filtered acitons


function fetchAndDisplayActions(status, page = 1) {
    // 1. BRIDGE: Access your existing HTML data bridge
    const labels = document.getElementById('js-table-labels').dataset;
    const currentLang = document.documentElement.lang || 'en';
    
    // 2. URL: Prepend language code to ensure Irish database content is returned
    const themeQuery = currentThemeId ? `&theme_id=${currentThemeId}` : '';
    const url = `/${currentLang}/api/actions/filter/${status.toLowerCase()}/?page=${page}${themeQuery}`; 
    
    const tableArea = document.getElementById('filtered-table-view-container');
    const accordionArea = document.getElementById('accordion-view-container');

    // Show initial loading state from bridge
    tableArea.innerHTML = `<div class="text-center py-4"><p>${labels.loading}</p></div>`;
    accordionArea.style.display = 'none'; 
    tableArea.style.display = ''; 

    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (!data.actions || data.actions.length === 0) {
                tableArea.innerHTML = `
                    <div class="text-center bg-light rounded border p-4">
                        <i class="fas fa-folder-open fa-3x  "></i>
                        <p class="lead text-danger text-center text-bold">${labels.noActions}</p>
                        <p class="text-center">
                    <button class="btn mcc-blue text-white btn-back" onclick="hideFilteredActions()">${labels.back}</button>
                </p>
                    </div>`;
                return;
            }
            const statusHeaderClass = `header-${status.toLowerCase()}`;
            
            // 3. Build Table Headers using BRIDGE
            let htmlOutput = `
                <div class="action-table-container">
                    <table class="action-table filtered-action-table">
                        <thead class="${statusHeaderClass}">
                            <tr>
                                <th>${labels.actionHeader}</th>
                                <th>${labels.descriptionHeader}</th>
                                <th>${labels.detailsHeader}</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            // 4. Loop through Actions
            data.actions.forEach(action => {
                const statusLower = status.toLowerCase().replace(/\s+/g, '_');
                const showUpdates = statusLower === 'in_progress' || statusLower === 'completed';

                htmlOutput += `
                    <tr class="action-summary-row status-${statusLower}">
                        <td class="title-col"><strong>${action.title}</strong></td>
                        <td class="objective-col">${action.small_description}</td>
                        <td class="details-col">
                            <button class="btn btn-sm view-button" onclick="handleDetailsToggle(this)">${labels.view}</button>
                            <button class="btn btn-sm toggle-details close-button" style="display: none;" onclick="handleDetailsToggle(this)">&minus;</button>
                        </td>
                    </tr>
                    <tr class="full-details" style="display: none;">
                        <td colspan="3">
                            <div class="details-content">
                                <h5>${labels.actionDesc}</h5>
                                <div>${action.description}</div>
                                ${showUpdates ? `
                                    <hr class="bg-light">
                                    <h5>${labels.latestUpdate}</h5>
                                    <div>${action.update || labels.noUpdate}</div>
                                ` : ''}
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            htmlOutput += '</tbody></table></div>';
   
            // 5. Pagination
            if (data.total_pages > 1) {
                htmlOutput += `<div class="pagination-controls text-center mt-3">`;
                if (data.has_previous) {
                    htmlOutput += `<button class="btn btn-sm btn-outline-secondary mx-1" onclick="fetchAndDisplayActions('${status}', ${data.current_page - 1})">${currentLang === 'ga' ? 'Roimhe seo' : 'Previous'}</button>`;
                }
                htmlOutput += `<span class="mx-2">${currentLang === 'ga' ? 'Leathanach' : 'Page'} ${data.current_page} / ${data.total_pages}</span>`;
                if (data.has_next) {
                    htmlOutput += `<button class="btn btn-sm btn-outline-secondary mx-1" onclick="fetchAndDisplayActions('${status}', ${data.current_page + 1})">${currentLang === 'ga' ? 'Ar aghaidh' : 'Next'}</button>`;
                }
                htmlOutput += `</div>`;
            }
            
            // 6. Centered "Go Back" Button from BRIDGE
            htmlOutput += `
                <p class="text-center">
                    <button class="btn mcc-blue text-white mt-3 btn-back" onclick="hideFilteredActions()">${labels.back}</button>
                </p>
            `;
            
            tableArea.innerHTML = htmlOutput;
        })
        .catch(error => {
            console.error('Error fetching filtered actions:', error);
            tableArea.innerHTML = `<div class="text-center py-4"><p class="text-danger">${labels.error}</p></div>`;
        });
}




let currentModalThemeTitle = ''; 
let currentThemeId = null;
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
            currentThemeId = themeId;
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

