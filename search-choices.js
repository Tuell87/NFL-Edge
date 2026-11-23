'use strict';

function updateSearchChoices(rows, fields) {
  const select = document.getElementById('search-choice');
  if (!select) return;
  const input = document.getElementById('search');
  const previous = select.value;
  const names = new Set();
  for (const row of rows) {
    for (const field of fields) {
      const name = row[field];
      if (typeof name === 'string' && name.trim()) names.add(name.trim());
    }
  }

  select.replaceChildren(
    new Option(select.dataset.defaultLabel, ''),
    new Option('Custom search…', 'custom'),
    ...Array.from(names).sort((a, b) => a.localeCompare(b))
      .map(name => new Option(name, 'name:' + name))
  );
  if ([...select.options].some(option => option.value === previous)) {
    select.value = previous;
  } else {
    input.value = '';
  }

  select.onchange = () => {
    const custom = select.value === 'custom';
    input.hidden = !custom;
    if (custom) {
      input.focus();
      input.select();
    } else {
      input.value = select.value.slice('name:'.length);
    }
    input.dispatchEvent(new Event('input', {bubbles: true}));
  };
}
