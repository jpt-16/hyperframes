// Line icons drawn for this demo (24px grid, 1.7 stroke). No icon font, no emoji.
const s = (d, extra = "") => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"${extra}>${d}</svg>`;

export const ICON = {
  leak: s('<path d="M12 3.5c3 3.6 5 6.4 5 9a5 5 0 0 1-10 0c0-2.6 2-5.4 5-9Z"/><path d="M9.6 13.4a2.4 2.4 0 0 0 2.4 2.4"/>'),
  drain: s('<circle cx="12" cy="12" r="8.2"/><path d="M12 7.8a4.2 4.2 0 1 1-4.2 4.2"/><path d="M12 10.4a1.6 1.6 0 1 1-1.6 1.6"/>'),
  "water-heater": s('<rect x="6.8" y="3.2" width="10.4" height="16" rx="3"/><path d="M6.8 8.6h10.4M10 21v-1.6M14 21v-1.6"/><path d="M12 12.6c1 1 1.5 1.8 1.5 2.6a1.5 1.5 0 0 1-3 0c0-.8.5-1.6 1.5-2.6Z"/>'),
  sewer: s('<path d="M2.8 8.5h10.4a4.3 4.3 0 0 1 4.3 4.3V21"/><path d="M2.8 13.6h9a1.2 1.2 0 0 1 1.2 1.2V21"/><circle cx="18.6" cy="5.4" r="2.4"/><path d="M16.2 5.4h-2"/>'),
  fixtures: s('<path d="M3.8 10.2h8.4a4 4 0 0 1 4 4v1.2"/><path d="M3.8 7.4v5.6"/><path d="M8 7.4V4.6h4.4"/><path d="M16.2 18.2v.6M16.2 20.9v.4"/>'),
  repipe: s('<path d="M2.8 7h6.4a3 3 0 0 1 3 3v4a3 3 0 0 0 3 3h6"/><path d="M2.8 4.4v5.2M21.2 14.4v5.2"/>'),
  sump: s('<rect x="5.6" y="11.2" width="12.8" height="9" rx="2"/><path d="M12 11.2V4.4h5.2"/><path d="M15.4 2.6l1.8 1.8-1.8 1.8"/><path d="M9 15.8h6"/>'),
  emergency: s('<path d="M13.2 2.8 5.8 13.2h5.4l-1 8 7.4-10.4h-5.4l1-8Z"/>'),
  phone: s('<path d="M6.6 3.6h2.9l1.5 3.9-1.9 1.3a10.6 10.6 0 0 0 6 6l1.3-1.9 3.9 1.5v2.9a2 2 0 0 1-2.2 2A16.4 16.4 0 0 1 4.6 5.8a2 2 0 0 1 2-2.2Z"/>'),
  chat: s('<path d="M5 4.8h14a2 2 0 0 1 2 2v8.4a2 2 0 0 1-2 2h-7.2l-4.6 3.4v-3.4H5a2 2 0 0 1-2-2V6.8a2 2 0 0 1 2-2Z"/>'),
  send: s('<path d="M4.6 12h14M13.4 6.2l5.8 5.8-5.8 5.8"/>', ' stroke-width="2"'),
  close: s('<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>'),
  check: s('<path d="M5 12.6l4.4 4.4L19 7.4"/>', ' stroke-width="2.2"'),
  clock: s('<circle cx="12" cy="12" r="8.4"/><path d="M12 7.6V12l3 2"/>'),
  pin: s('<path d="M12 21s-6.5-6-6.5-11a6.5 6.5 0 0 1 13 0c0 5-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>'),
  shield: s('<path d="M12 3.2 5 6v5.4c0 4.4 3 8 7 9.4 4-1.4 7-5 7-9.4V6l-7-2.8Z"/><path d="M9 12l2.2 2.2L15.2 10"/>'),
  doc: s('<path d="M7 3.5h7l4 4V20a.6.6 0 0 1-.6.6H7a.6.6 0 0 1-.6-.6V4.1a.6.6 0 0 1 .6-.6Z"/><path d="M13.6 3.5v4.2H18M9.4 12h5.2M9.4 15.4h5.2"/>'),
  arrowUpRight: s('<path d="M7 17 17 7M9 7h8v8"/>'),
  mail: s('<rect x="3.4" y="5.4" width="17.2" height="13.2" rx="2"/><path d="m4 7 8 6 8-6"/>'),
  user: s('<circle cx="12" cy="8.4" r="3.6"/><path d="M4.8 20a7.2 7.2 0 0 1 14.4 0"/>'),
  menu: s('<path d="M4 7h16M4 12h16M4 17h10"/>'),
};

export const LOGO = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.6c3.7 4.4 6.2 7.8 6.2 11a6.2 6.2 0 0 1-12.4 0c0-3.2 2.5-6.6 6.2-11Z" fill="#fff"/><path d="M7.5 14.3c1.5-1.15 3-1.15 4.5 0s3 1.15 4.5 0" stroke="#0d1f3c" stroke-width="1.7" fill="none" stroke-linecap="round"/></svg>`;
