(function () {
  const search = document.getElementById('search');
  const filterBtns = document.querySelectorAll('.filter-btn');
  const subFilterContainer = document.getElementById('subcategory-filters');
  const cards = document.querySelectorAll('.card');
  const noResults = document.getElementById('no-results');

  const subcatsScript = document.getElementById('category-subcats');
  const categorySubcats = subcatsScript ? JSON.parse(subcatsScript.textContent || '{}') : {};

  let activeCategory = 'all';
  let activeSubcategory = 'all';

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function renderSubcategoryFilters() {
    const subs = categorySubcats[activeCategory];
    activeSubcategory = 'all';

    if (activeCategory === 'all' || !subs || subs.length === 0) {
      subFilterContainer.innerHTML = '';
      subFilterContainer.hidden = true;
      return;
    }

    subFilterContainer.hidden = false;
    const buttonsHtml = ['<button class="subfilter-btn active" data-subfilter="all">All</button>']
      .concat(subs.map((s) => `<button class="subfilter-btn" data-subfilter="${escapeHtml(s)}">${escapeHtml(s)}</button>`))
      .join('');
    subFilterContainer.innerHTML = buttonsHtml;

    subFilterContainer.querySelectorAll('.subfilter-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        subFilterContainer.querySelectorAll('.subfilter-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        activeSubcategory = btn.dataset.subfilter;
        applyFilters();
      });
    });
  }

  function applyFilters() {
    const q = (search.value || '').trim().toLowerCase();
    let visibleCount = 0;

    cards.forEach((card) => {
      const matchesCategory =
        activeCategory === 'all' || card.dataset.category === activeCategory;
      const matchesSubcategory =
        activeSubcategory === 'all' || card.dataset.subcategory === activeSubcategory;
      const matchesSearch = q === '' || (card.dataset.search || '').includes(q);
      const show = matchesCategory && matchesSubcategory && matchesSearch;
      card.style.display = show ? '' : 'none';
      if (show) visibleCount++;
    });

    noResults.hidden = visibleCount !== 0;
  }

  search.addEventListener('input', applyFilters);

  filterBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      filterBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      activeCategory = btn.dataset.filter;
      renderSubcategoryFilters();
      applyFilters();
    });
  });
})();
