(function (globalScope) {
  function normalizeText(value) {
    return typeof value === 'string' ? value.trim() : '';
  }

  function reconcileMarketFilters(state, trigger) {
    const next = {
      searchTerm: normalizeText(state && state.searchTerm),
      course: normalizeText(state && state.course),
    };

    if ((trigger === 'search' || trigger === 'compositionend') && next.searchTerm) {
      next.course = '';
    }

    if (trigger === 'course' && next.course) {
      next.searchTerm = '';
    }

    return next;
  }

  function buildMaterialListQuery(options) {
    const page = Number(options && options.page) || 1;
    const pageSize = Number(options && options.pageSize) || 20;
    const searchTerm = normalizeText(options && options.searchTerm);
    const course = normalizeText(options && options.course);
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });

    if (searchTerm) {
      params.set('search', searchTerm);
    }

    if (course) {
      params.set('course', course);
    }

    return params.toString();
  }

  const api = {
    reconcileMarketFilters,
    buildMaterialListQuery,
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }

  globalScope.marketFilters = api;
})(typeof window !== 'undefined' ? window : globalThis);
