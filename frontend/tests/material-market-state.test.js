const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const context = {
  URLSearchParams,
};
context.globalThis = context;
vm.createContext(context);
vm.runInContext(
  fs.readFileSync(path.join(__dirname, '..', 'market-filters.js'), 'utf8'),
  context
);

const {
  reconcileMarketFilters,
  buildMaterialListQuery,
} = context.marketFilters;

test('compositionend keeps the search term and clears a stale course filter', () => {
  const next = reconcileMarketFilters(
    { searchTerm: '操作系统', course: 'MATH101' },
    'compositionend'
  );

  assert.equal(next.searchTerm, '操作系统');
  assert.equal(next.course, '');
});

test('building market query after typing search text omits course filter', () => {
  const synced = reconcileMarketFilters(
    { searchTerm: '操作系统', course: 'MATH101' },
    'compositionend'
  );

  const query = buildMaterialListQuery({
    page: 1,
    pageSize: 20,
    searchTerm: synced.searchTerm,
    course: synced.course,
  });

  assert.equal(query, 'page=1&page_size=20&search=%E6%93%8D%E4%BD%9C%E7%B3%BB%E7%BB%9F');
});

test('choosing a course clears an old keyword search', () => {
  const next = reconcileMarketFilters(
    { searchTerm: '操作系统', course: 'CS301' },
    'course'
  );

  assert.equal(next.searchTerm, '');
  assert.equal(next.course, 'CS301');
});
