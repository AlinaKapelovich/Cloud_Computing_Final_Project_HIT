/* Reusable consultation widget: POSTs a query to a JSON API endpoint and renders
   the search / side-effects / clinical-trials results returned by our services. */

function medcloudConsult(endpoint, inputId, outId) {
  const input = document.getElementById(inputId);
  const out = document.getElementById(outId);
  const query = (input.value || '').trim();
  if (!query) {
    out.innerHTML = '<div class="alert alert-warning">Please enter a query first.</div>';
    return;
  }
  out.innerHTML = '<p class="muted">Consulting cloud services…</p>';
  const token = document.querySelector('meta[name=csrf-token]').getAttribute('content');

  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': token },
    body: JSON.stringify({ query: query })
  })
    .then(function (r) { return r.json(); })
    .then(function (data) { renderConsult(out, data); })
    .catch(function () {
      out.innerHTML = '<div class="alert alert-danger">Consultation failed. Please try again.</div>';
    });
}

function renderConsult(out, data) {
  const blocks = [];
  if (data.search) blocks.push(resultSection('Search · ' + data.search.source, data.search));
  if (data.side_effects) blocks.push(resultSection('Side effects · ' + data.side_effects.source, data.side_effects));
  if (data.trials) blocks.push(trialsSection('Clinical trials · ' + data.trials.source, data.trials));
  out.innerHTML = blocks.join('') || '<div class="alert alert-info">No data returned.</div>';
}

function resultSection(title, block) {
  let html = '<div class="card-title" style="margin-top:12px;">' + esc(title) + '</div>';
  if (block.message) html += '<div class="alert alert-info">' + esc(block.message) + '</div>';
  (block.results || []).forEach(function (r) {
    html += '<div class="result-item"><h4>' + esc(r.title) + '</h4>' +
      '<p class="small muted">' + esc(r.snippet) + '</p>' +
      (r.url ? '<a class="source-tag" href="' + esc(r.url) + '" target="_blank" rel="noopener">source ↗</a>' : '') +
      '</div>';
  });
  return html;
}

function trialsSection(title, block) {
  let html = '<div class="card-title" style="margin-top:12px;">' + esc(title) + '</div>';
  if (block.message) html += '<div class="alert alert-info">' + esc(block.message) + '</div>';
  (block.results || []).forEach(function (r) {
    html += '<div class="result-item"><h4>' + esc(r.title) + '</h4>' +
      '<span class="badge badge-neutral">' + esc(r.status) + '</span> ' +
      '<a class="source-tag" href="' + esc(r.url) + '" target="_blank" rel="noopener">' + esc(r.nct_id || 'view') + ' ↗</a>' +
      '</div>';
  });
  return html;
}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}
