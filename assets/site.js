(function () {
  const search = document.getElementById('search');
  const filterBtns = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('.card');
  const noResults = document.getElementById('no-results');

  let activeCategory = 'all';

  function applyFilters() {
    const q = (search.value || '').trim().toLowerCase();
    let visibleCount = 0;

    cards.forEach((card) => {
      const matchesCategory =
        activeCategory === 'all' || card.dataset.category === activeCategory;
      const matchesSearch = q === '' || (card.dataset.search || '').includes(q);
      const show = matchesCategory && matchesSearch;
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
      applyFilters();
    });
  });
})();
