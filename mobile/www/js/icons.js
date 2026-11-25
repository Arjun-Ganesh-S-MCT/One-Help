// 24x24 line icons (same set as the Linux app and the design).
const P = {
  camera: '<rect x="3" y="7" width="18" height="13" rx="2"/><circle cx="12" cy="13.5" r="3.5"/><path d="M8 7l1.5-2.5h5L16 7"/>',
  leaf: '<path d="M5 19C5 10 11 5 20 4c0 9-5 15-14 15z"/><path d="M5 19L14 10"/>',
  list: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4h6v3H9z"/><path d="M8.5 12h7M8.5 16h5"/>',
  phone: '<path d="M6 3h4l2 5-2.5 1.5a11 11 0 005 5L16 12l5 2v4a2 2 0 01-2 2A16 16 0 014 5a2 2 0 012-2z"/>',
  back: '<path d="M15 5l-7 7 7 7"/>',
  road: '<path d="M7 21L10 3M17 21L14 3"/><path d="M12 5v3M12 11v3M12 17v3"/>',
  trash: '<path d="M5 7h14M10 7V4h4v3M7 7l1 13h8l1-13M10 11v6M14 11v6"/>',
  drain: '<rect x="3" y="8" width="18" height="8" rx="1"/><path d="M7 8v8M11 8v8M15 8v8"/>',
  bulb: '<path d="M9 18h6M10 21h4M12 3a6 6 0 00-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0012 3z"/>',
  water: '<path d="M12 3C8 9 6 12 6 15a6 6 0 0012 0c0-3-2-6-6-12z"/>',
  bolt: '<path d="M13 2L5 14h6l-1 8 9-13h-6z"/>',
  paw: '<circle cx="6.5" cy="10" r="1.8"/><circle cx="10.5" cy="6.5" r="1.8"/><circle cx="14.5" cy="6.5" r="1.8"/><circle cx="18" cy="10" r="1.8"/><path d="M12 11.5c-3 0-5 3-5 5 0 2 2 2.5 5 1.3 3 1.2 5 .7 5-1.3 0-2-2-5-5-5z"/>',
  dots: '<circle cx="6" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="18" cy="12" r="1.6"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0013 0M12 17.5V21M9 21h6"/>',
  send: '<path d="M4 12L20 4l-5 16-3.5-6.5z"/><path d="M11.5 13.5L20 4"/>',
  speaker: '<path d="M4 9.5h3.5L12 6v12l-4.5-3.5H4z"/><path d="M15.5 9a4 4 0 010 6M18 6.5a8 8 0 010 11"/>',
  speaker_off: '<path d="M4 9.5h3.5L12 6v12l-4.5-3.5H4z"/><path d="M16 9.5l5 5M21 9.5l-5 5"/>',
  copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 00-2-2H6a2 2 0 00-2 2v8a2 2 0 002 2h2"/>',
  save: '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.1"/>',
  x: '<path d="M6 6l12 12M18 6L6 18"/>',
  gear: '<circle cx="12" cy="12" r="3"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"/>',
  refresh: '<path d="M20 5v5h-5M4 19v-5h5"/><path d="M6.5 9A7 7 0 0118 8.5M17.5 15A7 7 0 016 15.5"/>',
};

export function icon(name, size = 24, color = "#2B2A2E", sw = 1.9) {
  return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="${color}" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${P[name] || ""}</svg>`;
}
