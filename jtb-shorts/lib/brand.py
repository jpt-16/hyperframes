"""JT Builds Co visual identity for the shorts system: tokens, base CSS, icons.

Charcoal / white / warm grey come straight from the logo (#201E1D, #FFFFFF,
#A09D9B); Montserrat matches the wordmark. One signature accent (amber) for
emphasis. Green / red are reserved for good / bad inside mockups.
"""
C = dict(
    bg="#121110", bg2="#1C1A19", tile="#201E1D", line="rgba(255,255,255,.08)",
    white="#F7F6F4", grey="#A09D9B", muted="#8A8580",
    accent="#FFB547", accent_ink="#1A1206",
    good="#3DD68C", bad="#FF6161",
)

FONTS = """
@font-face { font-family:"Montserrat"; font-weight:100 900; font-display:block; src:url("assets/fonts/Montserrat-var-latin.woff2") format("woff2"); }
@font-face { font-family:"Inter"; font-weight:400; font-display:block; src:url("assets/fonts/Inter-400-latin.woff2") format("woff2"); }
@font-face { font-family:"Inter"; font-weight:600; font-display:block; src:url("assets/fonts/Inter-600-latin.woff2") format("woff2"); }
@font-face { font-family:"Inter"; font-weight:700; font-display:block; src:url("assets/fonts/Inter-700-latin.woff2") format("woff2"); }
@font-face { font-family:"Fraunces"; font-weight:300 900; font-display:block; src:url("assets/fonts/Fraunces-var-latin.woff2") format("woff2"); }
"""

BASE_CSS = FONTS + f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:{C['bg']}; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"Inter", sans-serif; color:{C['white']};
         -webkit-font-smoothing:antialiased;
         background:radial-gradient(ellipse 110% 60% at 50% 34%, {C['bg2']} 0%, {C['bg']} 72%); }}
#grid {{ position:absolute; inset:-40px; opacity:.55; pointer-events:none;
         background-image:linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px);
         background-size:72px 72px; mask-image:radial-gradient(ellipse 80% 60% at 50% 40%, #000 30%, transparent 75%); }}
#glow {{ position:absolute; left:50%; top:30%; width:1100px; height:1100px; margin:-550px 0 0 -550px; border-radius:50%; pointer-events:none;
         background:radial-gradient(circle, rgba(255,181,71,.10), rgba(255,181,71,0) 62%); }}
.scene {{ position:absolute; inset:0; opacity:0; }}
.eyebrow {{ display:inline-flex; align-items:center; gap:12px; font-family:"Montserrat", sans-serif; font-weight:700; font-size:26px;
            letter-spacing:.24em; color:{C['grey']}; }}
.eyebrow i {{ width:12px; height:12px; border-radius:3px; background:{C['accent']}; display:inline-block; }}
.eyebrow.bad i {{ background:{C['bad']}; }} .eyebrow.good i {{ background:{C['good']}; }}
.head {{ position:absolute; left:70px; right:70px; top:262px; }}
.head h2 {{ font-family:"Montserrat", sans-serif; font-weight:800; font-size:70px; line-height:1.04; letter-spacing:-.015em; margin-top:16px; text-wrap:balance; }}
.head h2 em {{ font-style:normal; color:{C['accent']}; white-space:nowrap; }}
.chip {{ position:absolute; display:flex; align-items:center; gap:14px; padding:18px 26px; border-radius:22px; white-space:nowrap;
         background:rgba(28,26,25,.94); border:1px solid {C['line']}; box-shadow:0 20px 50px rgba(0,0,0,.45);
         font-weight:700; font-size:34px; color:{C['white']}; opacity:0; z-index:20; }}
.chip .ic {{ width:46px; height:46px; border-radius:14px; display:flex; align-items:center; justify-content:center; flex:none; }}
.chip.good .ic {{ background:rgba(61,214,140,.16); }} .chip.bad .ic {{ background:rgba(255,97,97,.16); }}
.chip.acc .ic {{ background:rgba(255,181,71,.16); }}
#brandbar {{ position:absolute; left:0; right:0; top:200px; display:flex; justify-content:center; align-items:center; gap:12px; z-index:30;
             font-family:"Montserrat", sans-serif; font-weight:800; font-size:22px; letter-spacing:.22em; color:{C['grey']}; opacity:0; }}
#brandbar img {{ width:30px; height:25px; }}
#brandbar b {{ color:{C['white']}; font-weight:800; }}
"""

def icon(name, size=32, color="currentColor", sw=2.2):
    p = {
        "check": '<path d="M5 12.5l4.2 4.2L19 7"/>',
        "x":     '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
        "phone": '<path d="M6.5 3.5h3l1.5 4-2 1.3a11 11 0 0 0 6.2 6.2l1.3-2 4 1.5v3a2 2 0 0 1-2.2 2A16.5 16.5 0 0 1 4.5 5.7a2 2 0 0 1 2-2.2Z"/>',
        "star":  '<path d="M12 3.6l2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8Z"/>',
        "pin":   '<path d="M12 21s-6.5-6.1-6.5-11a6.5 6.5 0 0 1 13 0c0 4.9-6.5 11-6.5 11Z"/><circle cx="12" cy="10" r="2.3"/>',
        "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
        "search":'<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
        "menu":  '<path d="M4 7h16M4 12h16M4 17h16"/>',
        "bolt":  '<path d="M13 3 5 13.5h6L10.5 21 19 10.5h-6Z"/>',
        "chart": '<path d="M4 19V5M4 19h16"/><path d="M7.5 15l3.5-4 3 2.5 4.5-6"/>',
        "camera":'<path d="M4 8h3.5l1.8-2.5h5.4L16.5 8H20v11H4Z"/><circle cx="12" cy="13.2" r="3.4"/>',
        "msg":   '<path d="M5 5h14v10H9l-4 4Z"/>',
        "globe": '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.6 2.5 2.6 14.5 0 17M12 3.5c-2.6 2.5-2.6 14.5 0 17"/>',
        "dir":   '<path d="M12 3l9 9-9 9-9-9Z"/><path d="M9.5 13.5v-2.5h4.5M12.5 9l2 2-2 2"/>',
        "car":   '<path d="M4 15.5V12l2-5h12l2 5v3.5"/><path d="M3.5 12h17v4.5h-17Z"/><circle cx="7.5" cy="17" r="1.6"/><circle cx="16.5" cy="17" r="1.6"/>',
        "leaf":  '<path d="M5 19c0-8 5-13 14-14 0 9-5 14-12 14"/><path d="M5 19l7-7"/>',
        "wrench":'<path d="M14.7 6.3a4 4 0 0 0 5 5l-8.4 8.4a2.1 2.1 0 0 1-3-3l8.4-8.4a4 4 0 0 0-2-2Z"/><path d="M14.7 6.3 17 4"/>',
        "tooth": '<path d="M8 3.5c-2.5 0-4 2-4 4.5 0 3 1.5 4.5 2 7 .5 3 1 5.5 2.5 5.5S10 18 12 18s2 2.5 3.5 2.5S17.5 18 18 15c.5-2.5 2-4 2-7 0-2.5-1.5-4.5-4-4.5-1.6 0-2.4 1-4 1s-2.4-1-4-1Z"/>',
        "snow":  '<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9"/><path d="M9.5 4.5 12 6l2.5-1.5M9.5 19.5 12 18l2.5 1.5"/>',
        "home":  '<path d="M4 11l8-6.5 8 6.5"/><path d="M6.5 9.5V19h11V9.5"/>',
        "spark": '<path d="M12 3.5l1.8 5.2 5.2 1.8-5.2 1.8L12 17.5l-1.8-5.2L5 10.5l5.2-1.8Z"/>',
        "img":   '<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M4 16l4.5-4.5 4 4 3-3L20 17"/><circle cx="15.5" cy="9.5" r="1.4"/>',
        "user":  '<circle cx="12" cy="8.5" r="3.6"/><path d="M5 20a7 7 0 0 1 14 0"/>',
        "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    }[name]
    fill = "none"
    if name == "star": fill = color
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{p}</svg>')
