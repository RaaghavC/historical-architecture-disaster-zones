// Script to analyze Archnet search results structure
// Run this in the browser console on https://www.archnet.org/search?q=Alhambra

console.log("=== Analyzing Archnet Search Results Structure ===");

// Look for common search result patterns
const selectors = [
    // Common class/id patterns for search results
    '[class*="search-result"]',
    '[class*="search-item"]',
    '[class*="result-item"]',
    '[class*="search-listing"]',
    '[class*="listing-item"]',
    '[class*="card"]',
    '[class*="result"]',
    '[id*="search-results"]',
    '[id*="results"]',
    
    // Common HTML5 semantic elements
    'article',
    'section[class*="result"]',
    'section[class*="search"]',
    'div[class*="result"]',
    'div[class*="search"]',
    'li[class*="result"]',
    'li[class*="search"]',
    
    // Data attributes
    '[data-result]',
    '[data-search]',
    '[data-item]'
];

console.log("\n--- Checking for search result containers ---");
selectors.forEach(selector => {
    const elements = document.querySelectorAll(selector);
    if (elements.length > 0) {
        console.log(`Found ${elements.length} elements matching: ${selector}`);
        if (elements.length <= 5) {
            elements.forEach((el, index) => {
                console.log(`  Element ${index + 1}:`, {
                    tagName: el.tagName,
                    className: el.className,
                    id: el.id || 'no-id',
                    childrenCount: el.children.length,
                    textPreview: el.textContent.substring(0, 100).trim() + '...'
                });
            });
        } else {
            // Just show first element as sample
            console.log(`  Sample element:`, {
                tagName: elements[0].tagName,
                className: elements[0].className,
                id: elements[0].id || 'no-id',
                innerHTML: elements[0].innerHTML.substring(0, 200) + '...'
            });
        }
    }
});

// Look for main content area
console.log("\n--- Looking for main content area ---");
const mainSelectors = ['main', '[role="main"]', '#main', '.main-content', '#content', '.content'];
mainSelectors.forEach(selector => {
    const element = document.querySelector(selector);
    if (element) {
        console.log(`Found main content area: ${selector}`);
        console.log('Children elements:', Array.from(element.children).map(child => ({
            tagName: child.tagName,
            className: child.className,
            id: child.id || 'no-id'
        })));
    }
});

// Analyze page structure
console.log("\n--- Page Structure Analysis ---");
const allDivs = document.querySelectorAll('div');
const classFrequency = {};
allDivs.forEach(div => {
    if (div.className) {
        div.className.split(' ').forEach(className => {
            if (className) {
                classFrequency[className] = (classFrequency[className] || 0) + 1;
            }
        });
    }
});

// Show classes that appear multiple times (likely repeating elements)
console.log("Classes appearing multiple times (potential result items):");
Object.entries(classFrequency)
    .filter(([className, count]) => count > 3)
    .sort((a, b) => b[1] - a[1])
    .forEach(([className, count]) => {
        console.log(`  .${className}: appears ${count} times`);
    });

// Try to find any repeating structures
console.log("\n--- Looking for repeating structures ---");
const potentialContainers = document.querySelectorAll('div, section, article, ul, ol');
potentialContainers.forEach(container => {
    if (container.children.length > 3) {
        const firstChildClass = container.children[0].className;
        const firstChildTag = container.children[0].tagName;
        
        // Check if all children have the same structure
        let allSimilar = true;
        for (let i = 1; i < container.children.length; i++) {
            if (container.children[i].tagName !== firstChildTag || 
                container.children[i].className !== firstChildClass) {
                allSimilar = false;
                break;
            }
        }
        
        if (allSimilar && firstChildClass) {
            console.log(`Found repeating structure in ${container.tagName}.${container.className}:`);
            console.log(`  - ${container.children.length} items with class: ${firstChildClass}`);
            console.log(`  - Sample HTML:`, container.children[0].outerHTML.substring(0, 300) + '...');
        }
    }
});

console.log("\n=== Analysis Complete ===");
console.log("To extract specific elements, use the selectors found above in your code.");