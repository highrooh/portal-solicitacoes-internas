const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
let user = null;
let csrfToken = $('meta[name="csrf-token"]').content;
let toastTimer;

const escapeHtml = (value = '') => String(value).replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const initials = name => String(name || '').split(/\s+/).slice(0, 2).map(part => part[0] || '').join('').toUpperCase();
const dateLabel = value => {
  if (!value) return '—';
  const [year, month, day] = value.slice(0, 10).split('-');
  return `${day}/${month}/${year}`;
};
const shortName = name => (name || '').trim().split(/\s+/)[0] || 'pessoa';

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (['POST', 'PATCH', 'DELETE'].includes(options.method)) headers['X-CSRF-Token'] = csrfToken;
  const response = await fetch(path, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && path !== '/api/login') showLogin();
    throw new Error(payload.error || 'Não foi possível concluir a ação.');
  }
  if (payload.csrf_token) csrfToken = payload.csrf_token;
  return payload;
}

function showLogin() {
  user = null;
  $('#app-view').hidden = true;
  $('#login-view').hidden = false;
}

function showApp(account) {
  user = account;
  $('#login-view').hidden = true;
  $('#app-view').hidden = false;
  $('#profile-name').textContent = account.name;
  $('#profile-role').textContent = account.role === 'gestor' ? 'Gestor' : 'Solicitante';
  $('#welcome-name').textContent = shortName(account.name);
  $('#avatar').textContent = initials(account.name);
  $('#top-avatar').textContent = initials(account.name);
  const today = new Intl.DateTimeFormat('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date());
  $('#today-label').textContent = today.charAt(0).toUpperCase() + today.slice(1);
  loadDashboard();
  loadRequests();
}

function showToast(message) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.classList.add('visible');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 2800);
}

async function loadDashboard() {
  try {
    const data = await api('/api/dashboard');
    $('#stat-total').textContent = data.total;
    $('#stat-open').textContent = data.by_status['Aberto'];
    $('#stat-progress').textContent = data.by_status['Em Atendimento'];
    $('#stat-done').textContent = data.by_status['Concluído'];
  } catch (error) { showToast(error.message); }
}

function buildQuery() {
  const params = new URLSearchParams();
  [['q', '#filter-q'], ['category', '#filter-category'], ['status', '#filter-status'], ['start', '#filter-start'], ['end', '#filter-end']].forEach(([key, selector]) => {
    const value = $(selector).value.trim();
    if (value) params.set(key, value);
  });
  return params.toString();
}

async function loadRequests() {
  try {
    const query = buildQuery();
    const data = await api(`/api/requests${query ? `?${query}` : ''}`);
    renderRequests(data.requests);
  } catch (error) { showToast(error.message); }
}

function renderRequests(requests) {
  const body = $('#request-rows');
  const empty = $('#empty-state');
  body.innerHTML = '';
  empty.hidden = requests.length > 0;
  if (!requests.length) return;
  body.innerHTML = requests.map(item => {
    const code = `SOL-${String(item.id).padStart(4, '0')}`;
    const dot = item.status === 'Aberto' ? 'open' : item.status === 'Em Atendimento' ? 'progress' : 'done';
    return `<tr data-id="${item.id}"><td><button class="request-title" data-action="detail" data-id="${item.id}"><span class="request-code">${code}</span><strong>${escapeHtml(item.title)}</strong></button></td><td><span class="category-pill">${escapeHtml(item.category)}</span></td><td>${escapeHtml(item.requester)}</td><td class="date-cell">${dateLabel(item.created_at)}</td><td><span class="status-pill status-${dot}"><i></i>${escapeHtml(item.status)}</span></td><td><button class="row-menu" data-action="detail" data-id="${item.id}" aria-label="Ver ${code}">···</button></td></tr>`;
  }).join('');
}

async function showDetail(id) {
  try {
    const { request: item } = await api(`/api/requests/${id}`);
    const dot = item.status === 'Aberto' ? 'open' : item.status === 'Em Atendimento' ? 'progress' : 'done';
    $('#detail-content').innerHTML = `<div class="dialog-heading"><div><p class="eyebrow">SOL-${String(item.id).padStart(4, '0')} · ${escapeHtml(item.category.toUpperCase())}</p><h2>${escapeHtml(item.title)}</h2></div><button type="button" class="icon-button close-dialog" aria-label="Fechar">×</button></div><div class="detail-meta"><span class="status-pill status-${dot}"><i></i>${escapeHtml(item.status)}</span><span>Aberta em ${dateLabel(item.created_at)}</span><span>Por ${escapeHtml(item.requester)}</span></div><div class="detail-description">${escapeHtml(item.description).replace(/\n/g, '<br>')}</div>`;
    const actions = $('#detail-actions');
    const canEdit = item.status === 'Aberto' && (item.user_id === user.id || user.role === 'gestor');
    actions.innerHTML = `${canEdit ? `<button class="button button-quiet" data-action="edit" data-id="${item.id}">Editar</button><button class="button button-danger-quiet" data-action="delete" data-id="${item.id}">Excluir</button>` : ''}${user.role === 'gestor' && item.status !== 'Concluído' ? `<button class="button button-primary" data-action="advance" data-id="${item.id}" data-status="${item.status === 'Aberto' ? 'Em Atendimento' : 'Concluído'}">${item.status === 'Aberto' ? 'Iniciar atendimento' : 'Concluir pedido'}</button>` : ''}`;
    $('#detail-dialog').showModal();
  } catch (error) { showToast(error.message); }
}

function openRequestForm(item = null) {
  const form = $('#request-form');
  form.reset();
  $('#request-error').textContent = '';
  form.elements.id.value = item?.id || '';
  $('#dialog-title').textContent = item ? 'Editar solicitação' : 'Nova solicitação';
  form.elements.title.value = item?.title || '';
  form.elements.category.value = item?.category || '';
  form.elements.description.value = item?.description || '';
  $('#request-dialog').showModal();
}

$('#login-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  $('#login-error').textContent = '';
  try {
    const data = await api('/api/login', { method: 'POST', body: JSON.stringify({ username: form.elements.username.value, password: form.elements.password.value }) });
    form.reset();
    showApp(data.user);
  } catch (error) { $('#login-error').textContent = error.message; }
});

$('#logout-button').addEventListener('click', async () => {
  try { await api('/api/logout', { method: 'POST', body: '{}' }); window.location.reload(); }
  catch (error) { showToast(error.message); }
});

$('#new-request').addEventListener('click', () => openRequestForm());
$$('.nav-link').forEach(link => link.addEventListener('click', event => {
  const section = document.querySelector(link.getAttribute('href'));
  if (!section) return;
  event.preventDefault();
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  history.replaceState(null, '', link.getAttribute('href'));
  $$('.nav-link').forEach(item => item.classList.toggle('active', item === link));
  $('#page-title').textContent = link.textContent.trim();
}));
$('#request-form').addEventListener('submit', async event => {
  event.preventDefault();
  const form = event.currentTarget;
  const id = form.elements.id.value;
  const body = JSON.stringify({ title: form.elements.title.value, category: form.elements.category.value, description: form.elements.description.value });
  try {
    await api(id ? `/api/requests/${id}` : '/api/requests', { method: id ? 'PATCH' : 'POST', body });
    $('#request-dialog').close();
    showToast(id ? 'Solicitação atualizada.' : 'Solicitação criada.');
    await Promise.all([loadRequests(), loadDashboard()]);
  } catch (error) { $('#request-error').textContent = error.message; }
});

let filterTimer;
$('#filter-q').addEventListener('input', () => { clearTimeout(filterTimer); filterTimer = setTimeout(loadRequests, 250); });
['#filter-category', '#filter-status', '#filter-start', '#filter-end'].forEach(selector => $(selector).addEventListener('change', loadRequests));
$('#clear-filters').addEventListener('click', () => { ['#filter-q', '#filter-category', '#filter-status', '#filter-start', '#filter-end'].forEach(selector => $(selector).value = ''); loadRequests(); });

document.addEventListener('click', async event => {
  const closeButton = event.target.closest('.close-dialog');
  if (closeButton) {
    closeButton.closest('dialog').close();
    return;
  }
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const { action, id } = button.dataset;
  if (action === 'detail') return showDetail(id);
  if (action === 'edit') {
    $('#detail-dialog').close();
    try { const { request: item } = await api(`/api/requests/${id}`); openRequestForm(item); }
    catch (error) { showToast(error.message); }
  }
  if (action === 'delete') {
    if (!window.confirm('Excluir esta solicitação? Essa ação não pode ser desfeita.')) return;
    try { await api(`/api/requests/${id}`, { method: 'DELETE' }); $('#detail-dialog').close(); showToast('Solicitação excluída.'); await Promise.all([loadRequests(), loadDashboard()]); }
    catch (error) { showToast(error.message); }
  }
  if (action === 'advance') {
    try { await api(`/api/requests/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status: button.dataset.status }) }); $('#detail-dialog').close(); showToast('Status atualizado.'); await Promise.all([loadRequests(), loadDashboard()]); }
    catch (error) { showToast(error.message); }
  }
});

document.addEventListener('keydown', event => {
  if (event.key === 'Escape') $$('dialog[open]').forEach(dialog => dialog.close());
});

(async () => {
  try {
    const data = await api('/api/me');
    if (data.user) showApp(data.user); else showLogin();
  } catch (_error) { showLogin(); }
})();
