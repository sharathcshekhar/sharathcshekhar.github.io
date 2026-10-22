/**
 * Beer Recipe Viewer & BeerXML Parser
 * sch-home vanilla JS
 */

document.addEventListener('DOMContentLoaded', () => {
  initRecipeSearchAndFilters();
  initRecipeToggles();
  initBackToTop();
});

/**
 * Live Recipe Search and Category Tag Filtering
 */
function initRecipeSearchAndFilters() {
  const searchInput = document.getElementById('recipe-search');
  const clearBtn = document.getElementById('clear-search');
  const styleTags = document.querySelectorAll('#style-filters .style-tag');
  const recipeCards = document.querySelectorAll('.recipe-card');

  if (!searchInput || recipeCards.length === 0) return;

  let currentStyle = 'all';
  let currentQuery = '';

  function filterRecipes() {
    recipeCards.forEach(card => {
      const name = (card.getAttribute('data-name') || '').toLowerCase();
      const style = (card.getAttribute('data-style') || '').toLowerCase();
      const desc = (card.querySelector('.recipe-desc')?.textContent || '').toLowerCase();

      const matchesSearch = !currentQuery || name.includes(currentQuery) || style.includes(currentQuery) || desc.includes(currentQuery);
      const matchesStyle = currentStyle === 'all' || style.includes(currentStyle.toLowerCase()) || name.includes(currentStyle.toLowerCase());

      card.classList.toggle('hidden', !(matchesSearch && matchesStyle));
    });
  }

  searchInput.addEventListener('input', (e) => {
    currentQuery = e.target.value.trim().toLowerCase();
    clearBtn.classList.toggle('hidden', !currentQuery);
    filterRecipes();
  });

  clearBtn.addEventListener('click', () => {
    searchInput.value = '';
    currentQuery = '';
    clearBtn.classList.add('hidden');
    filterRecipes();
    searchInput.focus();
  });

  styleTags.forEach(tag => {
    tag.addEventListener('click', () => {
      styleTags.forEach(t => t.classList.remove('active'));
      tag.classList.add('active');
      currentStyle = tag.getAttribute('data-style');
      filterRecipes();
    });
  });
}

/**
 * Expandable Recipe XML Loading & Display
 */
function initRecipeToggles() {
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.toggle-recipe-btn');
    if (!btn) return;

    const recipe = btn.getAttribute('data-recipe');
    if (!recipe) return;

    const panel = document.getElementById(`${recipe}_div`);
    if (!panel) return;

    const isHidden = panel.classList.contains('hidden');
    if (isHidden) {
      panel.classList.remove('hidden');
      btn.querySelector('span').textContent = 'Hide Ingredients';
      loadXMLRecipe(recipe);
    } else {
      panel.classList.add('hidden');
      btn.querySelector('span').textContent = 'View Ingredients';
    }
  });
}

const loadedRecipesCache = {};

function loadXMLRecipe(recipe) {
  if (loadedRecipesCache[recipe]) {
    displayRecipe(loadedRecipesCache[recipe], recipe);
    return;
  }

  const xmlUrl = `assets/recipes/${recipe}.xml`;
  fetch(xmlUrl)
    .then(response => {
      if (!response.ok) throw new Error('Recipe XML not found');
      return response.text();
    })
    .then(str => {
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(str, 'text/xml');
      loadedRecipesCache[recipe] = xmlDoc;
      displayRecipe(xmlDoc, recipe);
    })
    .catch(err => {
      const sumEl = document.getElementById(`${recipe}_sum`);
      if (sumEl) sumEl.innerHTML = `<span style="color:var(--text-muted);">Recipe details available for download in BeerXML.</span>`;
    });
}

function displayRecipe(xmlDoc, recipe) {
  const sumEl = document.getElementById(`${recipe}_sum`);
  const tableEl = document.getElementById(`${recipe}_table`);
  if (!sumEl || !tableEl) return;

  const recNode = xmlDoc.getElementsByTagName('RECIPE')[0];
  if (!recNode) return;

  const getNodeVal = (parent, tag, def = '') => {
    const el = parent.getElementsByTagName(tag)[0];
    return el && el.childNodes.length > 0 ? el.childNodes[0].nodeValue : def;
  };

  const name = getNodeVal(recNode, 'NAME', recipe);
  const rawSize = parseFloat(getNodeVal(recNode, 'BATCH_SIZE', '0'));
  const sizeGal = (rawSize / 3.7854).toFixed(2);
  const type = getNodeVal(recNode, 'TYPE', 'All Grain');
  const og = getNodeVal(recNode, 'OG', 'N/A');

  sumEl.innerHTML = `
    <strong>Batch Size:</strong> ${sizeGal} Gal &nbsp;|&nbsp;
    <strong>Type:</strong> ${type} &nbsp;|&nbsp;
    <strong>Estimated OG:</strong> ${og}
  `;

  let tableHtml = `
    <thead>
      <tr>
        <th>Ingredient</th>
        <th>Quantity / Schedule</th>
      </tr>
    </thead>
    <tbody>
  `;

  // Fermentables
  const fermentables = recNode.getElementsByTagName('FERMENTABLE');
  if (fermentables.length > 0) {
    tableHtml += `<tr class="recipe-category-header"><td colspan="2">🌾 Fermentables & Grains</td></tr>`;
    for (let i = 0; i < fermentables.length; i++) {
      const fName = getNodeVal(fermentables[i], 'NAME');
      const rawAmt = parseFloat(getNodeVal(fermentables[i], 'AMOUNT', '0'));
      const amtLbs = (rawAmt * 2.20462).toFixed(2);
      tableHtml += `<tr><td>${fName}</td><td>${amtLbs} lbs</td></tr>`;
    }
  }

  // Hops
  const hops = recNode.getElementsByTagName('HOP');
  if (hops.length > 0) {
    tableHtml += `<tr class="recipe-category-header"><td colspan="2">🌿 Hops & Additions</td></tr>`;
    for (let i = 0; i < hops.length; i++) {
      const hName = getNodeVal(hops[i], 'NAME');
      const rawAmt = parseFloat(getNodeVal(hops[i], 'AMOUNT', '0'));
      const amtOz = (rawAmt * 35.274).toFixed(2);
      const use = getNodeVal(hops[i], 'USE', 'Boil');
      const time = getNodeVal(hops[i], 'TIME', '0');

      let schedule = `${amtOz} oz`;
      if (use === 'Boil') {
        schedule += ` (${time} min boil)`;
      } else if (use === 'Dry Hop') {
        schedule += ` (Dry Hop · ${time} days)`;
      } else {
        schedule += ` (${use})`;
      }

      tableHtml += `<tr><td>${hName}</td><td>${schedule}</td></tr>`;
    }
  }

  // Yeast
  const yeasts = recNode.getElementsByTagName('YEAST');
  if (yeasts.length > 0) {
    tableHtml += `<tr class="recipe-category-header"><td colspan="2">🧪 Yeast</td></tr>`;
    for (let i = 0; i < yeasts.length; i++) {
      const yName = getNodeVal(yeasts[i], 'NAME');
      const yForm = getNodeVal(yeasts[i], 'FORM', 'Dry');
      tableHtml += `<tr><td>${yName}</td><td>${yForm} Yeast</td></tr>`;
    }
  }

  // Miscs
  const miscs = recNode.getElementsByTagName('MISC');
  if (miscs.length > 0) {
    tableHtml += `<tr class="recipe-category-header"><td colspan="2">✨ Spices & Other Additions</td></tr>`;
    for (let i = 0; i < miscs.length; i++) {
      const mName = getNodeVal(miscs[i], 'NAME');
      const amt = getNodeVal(miscs[i], 'DISPLAY_AMOUNT', getNodeVal(miscs[i], 'AMOUNT'));
      const time = getNodeVal(miscs[i], 'DISPLAY_TIME', '');
      const use = getNodeVal(miscs[i], 'USE', 'Boil');
      tableHtml += `<tr><td>${mName}</td><td>${amt} (${use}${time ? ', ' + time : ''})</td></tr>`;
    }
  }

  tableHtml += `</tbody>`;
  tableEl.innerHTML = tableHtml;
}

/**
 * Scroll to Top Button for long recipe catalog
 */
function initBackToTop() {
  const topBtn = document.getElementById('back-to-top');
  if (!topBtn) return;

  window.addEventListener('scroll', () => {
    if (window.scrollY > 400) {
      topBtn.style.display = 'flex';
    } else {
      topBtn.style.display = 'none';
    }
  });

  topBtn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}
