

/**
 * Capitalizes the first letter of each word for clean display titles.
 */
function capitalizeEachWord(str) {
    if (!str) {
        return '';
    }

    return str.replace(/\b\w/g, char => char.toUpperCase());
}

/**
 * Ensures external links open in a new tab and apply security rel attributes.
 */
function processExternalLinks(targetElement) {
    const links = targetElement.querySelectorAll('a');

    links.forEach(link => {
        if (link.hostname !== window.location.hostname) {
            link.setAttribute('target', '_blank');
            link.setAttribute('rel', 'noopener noreferrer');
        }
    });
}

/* =====================================================
   Counter Animation
   ===================================================== */

/**
 * Animates counter values when the strategy counter section is visible.
 */
function animateCounter(entries, observer) {
    entries.forEach(entry => {
        if (!entry.isIntersecting) {
            return;
        }

        const counters = document.querySelectorAll('.counter-value');
        counters.forEach(counter => {
            const target = +counter.getAttribute('data-target');
            let current = 0;
            const increment = target / 40;

            const updateCounter = () => {
                if (current < target) {
                    current += increment;
                    counter.innerText = Math.ceil(current);
                    requestAnimationFrame(updateCounter);
                } else {
                    counter.innerText = target;
                }
            };

            updateCounter();
        });

        observer.unobserve(entry.target);
    });
}

const counterSection = document.getElementById('strategy-counter');
if (counterSection) {
    const observerOptions = { root: null, threshold: 0.5 };
    const observer = new IntersectionObserver(animateCounter, observerOptions);
    observer.observe(counterSection);
}

/* =====================================================
   Accordion: Objectives
   ===================================================== */

/**
 * Toggles an objective accordion panel while closing all others and resetting details rows.
 */
function toggleAccordion(element) {
    const currentContent = element.nextElementSibling;
    const allContents = document.querySelectorAll('.accordion-content');
    const allTitles = document.querySelectorAll('.accordion-title');
    const isOpening = !currentContent.classList.contains('show');

    // 1) Close everything and reset internal action details.
    allContents.forEach(content => {
        const internalDetails = content.querySelectorAll('.full-details');
        const viewButtons = content.querySelectorAll('.view-button');
        const closeButtons = content.querySelectorAll('.close-button');

        internalDetails.forEach(detail => {
            detail.style.display = 'none';
        });

        viewButtons.forEach(btn => {
            btn.style.display = 'inline-block';
        });

        closeButtons.forEach(btn => {
            btn.style.display = 'none';
        });

        content.classList.remove('show');
        content.style.maxHeight = '0px';
        content.style.display = 'none';
    });

    allTitles.forEach(title => title.classList.remove('active'));

    // 2) Open only the clicked section.
    if (isOpening) {
        element.classList.add('active');
        currentContent.classList.add('show');
        currentContent.style.display = 'block';

        // Dynamic scrollHeight + buffer for 2026 table growth.
        currentContent.style.maxHeight = `${currentContent.scrollHeight + 1000}px`;
    }
}

/**
 * Toggles an action's details row and swaps the view/close buttons.
 */
function handleDetailsToggle(clickedElement) {
    const summaryRow = clickedElement.closest('tr.action-summary-row');
    const detailsRow = summaryRow.nextElementSibling;
    const viewButton = summaryRow.querySelector('.view-button');
    const closeButton = summaryRow.querySelector('.close-button');
    const isHidden = window.getComputedStyle(detailsRow).display === 'none';

    if (isHidden) {
        detailsRow.classList.add('expanded');

        // Dynamic display: use 'table-row' for desktop, 'block' for mobile.
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

/* =====================================================
   Filtered Actions
   ===================================================== */

/**
 * Resets the accordion state and returns the user to the main objectives view.
 */
function hideFilteredActions() {
    // Force all objectives to close before returning for a fresh start.
    document.querySelectorAll('.accordion-content').forEach(content => {
        content.classList.remove('show');
        content.style.display = 'none';
        content.style.maxHeight = '0';
    });

    document.querySelectorAll('.accordion-title').forEach(title => {
        title.classList.remove('active');
    });

    // Switch the view back to the main list.
    document.getElementById('accordion-view-container').style.display = 'block';
    document.getElementById('filtered-table-view-container').style.display = 'none';

    // Reset scroll so the user returns to the top of the modal.
    const modalBody = document.querySelector('.modal-body');
    if (modalBody) {
        modalBody.scrollTop = 0;
    }
}

/**
 * Fetches and renders filtered action rows for a given status and page.
 * Bilingual UI note: this function reads the js-table-labels dataset to
 * inject language-specific labels into the generated markup.
 */
function fetchAndDisplayActions(status, page = 1) {
    const labels = document.getElementById('js-table-labels').dataset;
    const currentLang = document.documentElement.lang || 'en';
    const themeQuery = currentThemeId ? `&theme_id=${currentThemeId}` : '';
    const url = `/${currentLang}/api/actions/filter/${status.toLowerCase()}/?page=${page}${themeQuery}`;

    const tableArea = document.getElementById('filtered-table-view-container');
    const accordionArea = document.getElementById('accordion-view-container');

    // Show initial loading state from bridge.
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
                    </div>
                `;
                return;
            }

            const statusHeaderClass = `header-${status.toLowerCase()}`;

            // Build table headers using the bridge labels.
            let htmlOutput = `
                <div class="action-table-container">
                    <table class="action-table">
                        <thead class="${statusHeaderClass}">
                            <tr>
                                <th>${labels.actionHeader}</th>
                                <th>${labels.descriptionHeader}</th>
                                <th class="text-center">${labels.detailsHeader}</th>
                            </tr>
                        </thead>
                        <tbody>
            `;

            // Loop through actions and render rows.
            data.actions.forEach(action => {
                const statusLower = status.toLowerCase().replace(/\s+/g, '_');
                const showUpdates = statusLower === 'in_progress' || statusLower === 'completed';

                htmlOutput += `
                    <tr class="action-summary-row status-${statusLower}">
                        <td class="title-col"><strong>${action.title}</strong></td>
                        <td class="objective-col">${action.small_description}</td>
                        <td class="details-col text-center">
                            <button class="btn btn-sm toggle-details view-button universal-action-button" onclick="handleDetailsToggle(this)">${labels.view}</button>
                            <button class="btn btn-sm toggle-details close-button universal-action-button" style="display: none;" onclick="handleDetailsToggle(this)">&minus;</button>
                        </td>
                    </tr>
                    <tr class="full-details" style="display: none;">
                        <td colspan="3">
                            <div class="details-content">
                                <p class="fw-bold details-heading">${labels.actionDesc}</p>
                                <div>${action.description}</div>
                                ${showUpdates ? `
                                    <hr class="bg-light">
                                    <p class="fw-bold details-heading">${labels.latestUpdate}</p>
                                    <div>${action.update || labels.noUpdate}</div>
                                ` : ''}
                            </div>
                        </td>
                    </tr>
                `;
            });

            htmlOutput += '</tbody></table></div>';

            // Pagination.
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

            // Centered "Go Back" button from bridge.
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

/* =====================================================
   Modal Events & Theme Fetching
   ===================================================== */

let currentModalThemeTitle = '';
let currentThemeId = null;

document.addEventListener('DOMContentLoaded', () => {
    const portfolioModal = document.getElementById('portfolioModal');

    if (portfolioModal) {
        // Listen for clicks that happen anywhere inside the modal.
        portfolioModal.addEventListener('click', event => {
            const clickedCard = event.target.closest('.status-card');

            if (clickedCard) {
                const status = clickedCard.getAttribute('data-status');
                if (status) {
                    fetchAndDisplayActions(status);
                }
            }
        });
    }

    document.querySelectorAll('a[data-theme-id]').forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault();

            const themeId = this.getAttribute('data-theme-id');
            currentThemeId = themeId;

            const urlTemplate = document.getElementById('api-url-template').getAttribute('data-url-template');
            const url = urlTemplate.replace('__ID__', themeId);

            document.getElementById('modalThemeTitle').textContent = 'Loading...';
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

/**
 * Closes the modal using the Bootstrap instance.
 */
function closeMCCModal() {
    const modalElement = document.getElementById('portfolioModal');
    const modal = bootstrap.Modal.getOrCreateInstance(modalElement);
    modal.hide();
}

/* =====================================================
   Scroll To Top
   ===================================================== */

// Cache the scroll-to-top button.
const scrollToTopBtn = document.getElementById('scrollToTopBtn');

// Toggle visibility on scroll.
window.onscroll = function() {
    if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
        scrollToTopBtn.style.display = 'block';
    } else {
        scrollToTopBtn.style.display = 'none';
    }
};

/**
 * Smoothly scrolls the page back to the top.
 */
function scrollToTopFunction() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

