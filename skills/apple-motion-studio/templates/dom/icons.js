// simple line icons (original), stroke = currentColor
const ICONS = {
  agenda: '<rect x="4" y="6" width="24" height="22" rx="5"/><path d="M4 13h24M11 3v6M21 3v6"/><circle cx="16" cy="20" r="2.4" fill="currentColor" stroke="none"/>',
  clientes: '<circle cx="12" cy="12" r="5"/><path d="M3 27c1.5-5 5-7.5 9-7.5s7.5 2.5 9 7.5"/><circle cx="23" cy="10" r="3.6"/><path d="M22 18c3.6.3 6 2.6 7 6"/>',
  financeiro: '<rect x="3" y="8" width="26" height="17" rx="4"/><path d="M3 14h26"/><path d="M8 20h6"/>',
  estoque: '<path d="M16 3l12 6v14l-12 6-12-6V9z"/><path d="M4 9l12 6 12-6M16 15v14"/>',
  mensagens: '<path d="M5 6h22a3 3 0 013 3v11a3 3 0 01-3 3H13l-6 5v-5H5a3 3 0 01-3-3V9a3 3 0 013-3z"/>',
  relatorios: '<path d="M5 27V15M12 27V8M19 27V18M26 27V4"/>',
  site: '<circle cx="16" cy="16" r="12"/><path d="M4 16h24M16 4c4 4 5 8 5 12s-1 8-5 12M16 4c-4 4-5 8-5 12s1 8 5 12"/>',
  pagamentos: '<rect x="3" y="7" width="26" height="18" rx="4"/><circle cx="16" cy="16" r="4"/>',
  equipe: '<circle cx="16" cy="10" r="5"/><path d="M6 28c1.5-6 5.5-9 10-9s8.5 3 10 9"/>',
  bell: '<path d="M8 22V14a8 8 0 0116 0v8l2 3H6z"/><path d="M13 28a3 3 0 006 0"/>',
  check: '<path d="M7 16.5l6 6 12-13"/>',
};
const icon = (k, size = 40, color = 'currentColor', sw = 2.4) => `<svg width="${size}" height="${size}" viewBox="0 0 32 32" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round">${ICONS[k]}</svg>`;
