"""Photo-style scene art for the example sites (inline SVG, drawn in code).

Real local-business sites lead with a photo of the work, not an icon in a
gradient blob. These scenes stand in for that photo: soft daylight, depth,
texture and a little grain, in each niche's world. scene(key, variant, uid)
returns an <svg> that fills its box (object-fit: cover behaviour).

When you have real photos or screenshots, drop them in brand/photos/ and use
an <img> instead; the layouts don't care which.
"""

def _grain(uid, opacity=0.07):
    return (f'<filter id="gr{uid}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="4"/>'
            f'<feColorMatrix values="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 {opacity * 6} 0"/></filter>')

def _wrap(uid, defs, body, light=True, grain=True):
    lt = (f'<radialGradient id="lt{uid}" cx="22%" cy="8%" r="85%"><stop offset="0" stop-color="#FFF6E0" stop-opacity=".55"/>'
          f'<stop offset=".55" stop-color="#FFF6E0" stop-opacity="0"/></radialGradient>')
    over = (f'<rect width="390" height="330" fill="url(#lt{uid})"/>' if light else "")
    gr = (f'<rect width="390" height="330" filter="url(#gr{uid})" opacity=".55"/>' if grain else "")
    return (f'<svg viewBox="0 0 390 330" preserveAspectRatio="xMidYMid slice" width="100%" height="100%" aria-hidden="true">'
            f'<defs>{defs}{lt}{_grain(uid)}</defs>{body}{over}{gr}</svg>')

def _lin(id_, stops, x2=0, y2=1):
    s = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in stops)
    return f'<linearGradient id="{id_}" x1="0" y1="0" x2="{x2}" y2="{y2}">{s}</linearGradient>'

def _sky(uid, top="#BCD9EE", bot="#EEF4EC"):
    return _lin(f"sk{uid}", [(0, top), (1, bot)]), f'<rect width="390" height="330" fill="url(#sk{uid})"/>'

def _treeline(y, color, seed, n=16, r0=18, r1=30):
    out = []
    for i in range(n):
        x = -10 + i * 410 / (n - 1)
        r = r0 + (r1 - r0) * ((i * 7 + seed * 3) % 10) / 10
        out.append(f'<circle cx="{x:.1f}" cy="{y - ((i * 13 + seed) % 7) * 2}" r="{r:.1f}" fill="{color}"/>')
    return "".join(out) + f'<rect x="-10" y="{y}" width="410" height="60" fill="{color}"/>'

def _stripes(uid, y0, vp=(195, 120), c1="#6DAA4B", c2="#5F9C41"):
    """Mower stripes in perspective, clipped to the lawn below y0."""
    clip = f'<clipPath id="ln{uid}"><rect x="0" y="{y0}" width="390" height="{330 - y0}"/></clipPath>'
    polys = [f'<rect x="0" y="{y0}" width="390" height="{330 - y0}" fill="{c1}"/>']
    for k in range(-8, 9, 2):
        x0, x1 = 195 + k * 70, 195 + (k + 1) * 70
        polys.append(f'<polygon points="{vp[0]},{vp[1]} {x0},380 {x1},380" fill="{c2}"/>')
    return clip, f'<g clip-path="url(#ln{uid})">{"".join(polys)}</g>'

def _shrub(x, y, r, c="#3F7A3A", hi="#5C9A45"):
    return (f'<ellipse cx="{x}" cy="{y + r * .8}" rx="{r * 1.1}" ry="{r * .25}" fill="#000" opacity=".18"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/><circle cx="{x - r * .3}" cy="{y - r * .3}" r="{r * .55}" fill="{hi}" opacity=".7"/>')

def _flowers(x, y, w, colors=("#E8A33D", "#D9534F", "#F4E1A1", "#C86FA8")):
    return "".join(f'<circle cx="{x + i * w / 9:.1f}" cy="{y + (i * 5) % 7}" r="3.2" fill="{colors[i % len(colors)]}"/>' for i in range(10))

# ----------------------------------------------------------------- landscaping
def landscaping(uid, v=0):
    d_sky, sky = _sky(uid)
    trees = _treeline(118, "#2F5D3A", 1) + _treeline(132, "#3B6E42", 4, 14, 14, 24)
    if v == 1:   # patio: pavers in perspective, low wall, planters
        rows, y, h = [], 150, 9
        while y < 330:
            rows.append((y, h)); y += h; h *= 1.22
        pav = f'<rect x="0" y="150" width="390" height="180" fill="#CDBB9E"/>'
        for i, (yy, hh) in enumerate(rows):
            pav += f'<line x1="0" y1="{yy:.1f}" x2="390" y2="{yy:.1f}" stroke="#A8957A" stroke-width="{.6 + i * .25:.2f}"/>'
            off = (i % 2) * 0.5
            for k in range(-9, 10):
                xa = 195 + (k + off) * (24 + i * 9)
                pav += f'<line x1="{xa:.1f}" y1="{yy:.1f}" x2="{195 + (xa - 195) * 1.2:.1f}" y2="{yy + hh:.1f}" stroke="#A8957A" stroke-width="{.6 + i * .25:.2f}"/>'
        wall = "".join(f'<rect x="{x}" y="{136 + (x // 38) % 2 * 0}" width="36" height="16" rx="2" fill="{["#9C8F7E", "#A99B88", "#928574"][x // 38 % 3]}"/>' for x in range(-4, 400, 38))
        body = sky + trees + _shrub(60, 128, 22) + _shrub(320, 126, 26) + _shrub(200, 130, 18, "#4C8740") + wall + pav + \
            f'<ellipse cx="270" cy="250" rx="58" ry="16" fill="#5A534B"/><ellipse cx="270" cy="244" rx="50" ry="12" fill="#3B3632"/>' \
            f'<ellipse cx="270" cy="240" rx="18" ry="6" fill="#E8833A" opacity=".85"/>' + \
            f'<rect x="40" y="210" width="44" height="40" rx="4" fill="#6E6258"/>' + _shrub(62, 205, 20, "#4C8740", "#79B55A")
        return _wrap(uid, d_sky, body)
    if v == 2:   # garden bed: mulch curve, layered shrubs, flowers
        c, lawn = _stripes(uid, 200)
        body = sky + trees + lawn + \
            f'<path d="M-10 175 C80 150 300 160 400 178 L400 250 C300 228 100 236 -10 262 Z" fill="#5B3E2B"/>' \
            f'<path d="M-10 262 C100 236 300 228 400 250" stroke="#B8B0A2" stroke-width="6" fill="none"/>' + \
            "".join(_shrub(x, 182 + (x % 3) * 6, 24 - (x % 4) * 2) for x in range(20, 400, 58)) + \
            "".join(_shrub(x, 214 + (x % 2) * 4, 13, "#6E9F3D", "#A3C76A") for x in range(45, 400, 58)) + \
            _flowers(10, 234, 380)
        return _wrap(uid, d_sky + c, body)
    # v0 (house + lawn) and v3 (path, no house)
    c, lawn = _stripes(uid, 182)
    stones = "".join(f'<ellipse cx="{130 + i * 13 - i * i * .9:.1f}" cy="{322 - i * 15}" rx="{26 - i * 2.1:.1f}" ry="{9 - i * .6:.1f}" fill="#D4CDBF"/>'
                     f'<ellipse cx="{130 + i * 13 - i * i * .9:.1f}" cy="{324 - i * 15}" rx="{26 - i * 2.1:.1f}" ry="{9 - i * .6:.1f}" fill="#000" opacity=".12"/>'
                     for i in range(9))
    house = ""
    if v == 0:
        house = (f'<rect x="250" y="62" width="150" height="128" fill="#ECE4D6"/>'
                 + "".join(f'<line x1="250" y1="{y}" x2="400" y2="{y}" stroke="#DCD1BF" stroke-width="1.2"/>' for y in range(70, 190, 9))
                 + f'<polygon points="236,64 330,18 410,64" fill="#4A4743"/><rect x="272" y="96" width="44" height="52" fill="#9DB7C9" stroke="#fff" stroke-width="4"/>'
                 f'<line x1="294" y1="96" x2="294" y2="148" stroke="#fff" stroke-width="3"/><rect x="340" y="120" width="30" height="70" fill="#5B4636"/>')
    hedge = "".join(_shrub(x, 178, 16, "#3F7A3A", "#5C9A45") for x in range(-6, 250 if v == 0 else 400, 26))
    body = sky + trees + house + lawn + hedge + _flowers(0, 192, 240 if v == 0 else 390) + stones
    return _wrap(uid, d_sky + c, body)

# ----------------------------------------------------------------- plumbing: a finished bathroom vanity
def plumbing(uid, v=0):
    tiles = "".join(f'<rect x="{(c * 42) - (r % 2) * 21}" y="{r * 21}" width="42" height="21" fill="none" stroke="#D5DCE1" stroke-width="1"/>'
                    for r in range(10) for c in range(11))
    defs = (_lin(f"wl{uid}", [(0, "#F4F6F7"), (1, "#E4E9EC")]) + _lin(f"ch{uid}", [(0, "#8C969E"), (.45, "#F4F6F8"), (1, "#8A949C")], 1, 0)
            + _lin(f"mr{uid}", [(0, "#DCE6EC"), (1, "#F7FAFB")], 1, 1) + _lin(f"wd{uid}", [(0, "#7A5638"), (1, "#5E4029")]))
    body = (f'<rect width="390" height="330" fill="url(#wl{uid})"/>{tiles}'
            f'<rect x="104" y="22" width="182" height="128" rx="14" fill="url(#mr{uid})" stroke="#B9C3CA" stroke-width="3"/>'
            f'<path d="M126 40 L166 40 L130 110 Z" fill="#fff" opacity=".45"/>'
            f'<rect x="-10" y="196" width="410" height="14" fill="url(#wd{uid})"/>'
            f'<rect x="-10" y="210" width="410" height="130" fill="#34404B"/>'
            + "".join(f'<rect x="{x}" y="222" width="118" height="100" rx="4" fill="none" stroke="#45525E" stroke-width="3"/>'
                      f'<rect x="{x + 50}" y="232" width="18" height="4" rx="2" fill="#C9A86A"/>' for x in (10, 136, 262))
            + f'<ellipse cx="195" cy="198" rx="78" ry="6" fill="#000" opacity=".18"/>'
            f'<path d="M118 196 C118 146 272 146 272 196 Z" fill="#FFFFFF" stroke="#E3E8EB" stroke-width="2"/>'
            f'<ellipse cx="195" cy="156" rx="74" ry="11" fill="#E6ECEF" stroke="#FFFFFF" stroke-width="3"/>'
            f'<path d="M132 176 C140 190 170 194 186 192" stroke="#E9EEF1" stroke-width="6" fill="none" stroke-linecap="round"/>'
            f'<rect x="232" y="100" width="11" height="58" rx="4" fill="url(#ch{uid})"/>'
            f'<path d="M237 104 C237 86 210 86 206 100 L206 126" stroke="url(#ch{uid})" stroke-width="9" fill="none" stroke-linecap="round"/>'
            f'<rect x="250" y="142" width="16" height="7" rx="3" fill="url(#ch{uid})"/>'
            f'<rect x="38" y="146" width="40" height="50" rx="6" fill="#E9E2D6"/>'
            + "".join(f'<path d="M58 148 C{40 + k * 9} {100 + k * 4} {30 + k * 12} {96 + k * 3} {30 + k * 13} {92}" stroke="#4E8A4A" stroke-width="6" fill="none" stroke-linecap="round"/>' for k in range(5))
            + f'<rect x="310" y="150" width="46" height="46" rx="6" fill="#F7F4EE" stroke="#E2DCD0" stroke-width="2"/>'
            f'<rect x="318" y="160" width="30" height="5" rx="2" fill="#B9C3CA"/>')
    return _wrap(uid, defs, body)

# ----------------------------------------------------------------- dental: a bright treatment room
def dental(uid, v=0):
    defs = (_lin(f"wl{uid}", [(0, "#E5F2F1"), (1, "#F6FBFA")]) + _lin(f"win{uid}", [(0, "#FFFFFF"), (1, "#DCEFF3")])
            + _lin(f"up{uid}", [(0, "#5FBDB5"), (1, "#3E9A93")]) + _lin(f"fl{uid}", [(0, "#DCD5CA"), (1, "#C9C1B4")]))
    blinds = "".join(f'<line x1="18" y1="{y}" x2="142" y2="{y}" stroke="#E6EEF0" stroke-width="2"/>' for y in range(34, 226, 12))
    body = (f'<rect width="390" height="330" fill="url(#wl{uid})"/><rect x="0" y="262" width="390" height="70" fill="url(#fl{uid})"/>'
            f'<rect x="12" y="24" width="136" height="210" rx="6" fill="url(#win{uid})" stroke="#CFDDE0" stroke-width="5"/>{blinds}'
            f'<polygon points="148,40 260,262 148,262" fill="#FFFFFF" opacity=".35"/>'
            f'<rect x="300" y="150" width="96" height="112" rx="6" fill="#FFFFFF" stroke="#E1E8EA" stroke-width="2"/>'
            + "".join(f'<rect x="306" y="{158 + k * 34}" width="84" height="28" rx="3" fill="none" stroke="#E1E8EA" stroke-width="2"/>'
                      f'<rect x="338" y="{170 + k * 34}" width="20" height="3" rx="1.5" fill="#B5C2C6"/>' for k in range(3))
            + f'<ellipse cx="205" cy="276" rx="92" ry="10" fill="#000" opacity=".12"/>'
            f'<rect x="196" y="236" width="20" height="38" rx="6" fill="#C9D3D6"/><rect x="168" y="268" width="76" height="10" rx="5" fill="#B7C3C7"/>'
            f'<path d="M118 214 C120 200 150 196 176 200 L262 206 C278 208 286 222 276 232 L132 236 C120 236 116 224 118 214 Z" fill="url(#up{uid})"/>'
            f'<path d="M262 206 L300 160 C306 152 318 156 314 166 L284 222 Z" fill="url(#up{uid})"/>'
            f'<rect x="302" y="132" width="30" height="20" rx="9" fill="#4DADA5" transform="rotate(35 317 142)"/>'
            f'<path d="M196 236 L196 120 L250 92" stroke="#C3CDD1" stroke-width="6" fill="none" stroke-linecap="round"/>'
            f'<rect x="236" y="74" width="58" height="26" rx="12" fill="#F3F6F7" stroke="#D3DADD" stroke-width="2"/>'
            f'<rect x="246" y="96" width="38" height="5" rx="2" fill="#FFF8D8"/>'
            f'<rect x="40" y="226" width="34" height="40" rx="5" fill="#EDE6DA"/>'
            + "".join(f'<path d="M57 228 C{44 + k * 7} {186 + k * 3} {36 + k * 9} {182} {34 + k * 11} {178}" stroke="#4E8A4A" stroke-width="6" fill="none" stroke-linecap="round"/>' for k in range(5)))
    return _wrap(uid, defs, body)

# ----------------------------------------------------------------- HVAC: a condenser beside the house
def hvac(uid, v=0):
    defs = (_lin(f"sd{uid}", [(0, "#DDE4E9"), (1, "#CBD4DA")]) + _lin(f"un{uid}", [(0, "#DADFE2"), (1, "#AEB6BC")], 1, 1))
    siding = "".join(f'<line x1="0" y1="{y}" x2="390" y2="{y}" stroke="#BCC6CD" stroke-width="1.4"/>' for y in range(10, 250, 13))
    fins = "".join(f'<line x1="{x}" y1="186" x2="{x}" y2="282" stroke="#8F989F" stroke-width="1.6"/>' for x in range(160, 292, 6))
    spokes = "".join(f'<line x1="225" y1="234" x2="{225 + 40 * __import__("math").cos(a)}" y2="{234 + 40 * __import__("math").sin(a)}" stroke="#2F3438" stroke-width="5"/>'
                     for a in (0.3, 1.87, 3.44, 5.01))
    body = (f'<rect width="390" height="330" fill="url(#sd{uid})"/>{siding}'
            f'<rect x="40" y="40" width="96" height="92" fill="#A9C4D6" stroke="#fff" stroke-width="7"/><line x1="88" y1="40" x2="88" y2="132" stroke="#fff" stroke-width="5"/>'
            f'<rect x="0" y="250" width="390" height="80" fill="#6B4E3A"/>'
            f'<rect x="132" y="282" width="190" height="20" rx="3" fill="#B9B6B0"/>'
            f'<path d="M300 200 L340 200 L340 120" stroke="#2E2E2E" stroke-width="12" fill="none"/><path d="M300 214 L352 214 L352 120" stroke="#8A6F4E" stroke-width="5" fill="none"/>'
            f'<rect x="150" y="176" width="150" height="110" rx="8" fill="url(#un{uid})"/>{fins}'
            f'<circle cx="225" cy="234" r="44" fill="#3A4045"/><circle cx="225" cy="234" r="42" fill="none" stroke="#6D757B" stroke-width="3"/>{spokes}'
            f'<circle cx="225" cy="234" r="8" fill="#6D757B"/><rect x="150" y="170" width="150" height="10" rx="4" fill="#C7CDD1"/>'
            f'<rect x="262" y="190" width="28" height="14" rx="2" fill="#F2F4F5"/>'
            + _shrub(70, 262, 26) + _shrub(110, 270, 18, "#4C8740", "#79B55A") + _shrub(348, 266, 24))
    return _wrap(uid, defs, body)

# ----------------------------------------------------------------- auto detailing: a glossy car in a studio bay
def detailing(uid, v=0):
    defs = (_lin(f"bg{uid}", [(0, "#2B2F36"), (1, "#14171B")]) + _lin(f"car{uid}", [(0, "#2E5BDB"), (.5, "#1D3FA8"), (1, "#0F2466")])
            + _lin(f"fl{uid}", [(0, "#22262B"), (1, "#0E1013")]))
    body = (f'<rect width="390" height="330" fill="url(#bg{uid})"/>'
            + "".join(f'<rect x="{x}" y="18" width="70" height="6" rx="3" fill="#FFFFFF" opacity=".85"/>' for x in (40, 160, 280))
            + f'<rect x="0" y="232" width="390" height="100" fill="url(#fl{uid})"/>'
            f'<path d="M30 226 C34 196 64 188 100 184 L140 150 C150 142 166 138 184 138 L262 138 C282 138 298 148 312 164 L330 184 C356 188 372 200 368 226 Z" fill="url(#car{uid})"/>'
            f'<path d="M150 156 L176 146 L250 146 L268 156 L262 180 L144 180 Z" fill="#0B1220" opacity=".85"/>'
            f'<path d="M60 196 C140 186 260 186 350 198" stroke="#FFFFFF" stroke-width="2" opacity=".55" fill="none"/>'
            f'<circle cx="104" cy="228" r="26" fill="#0B0C0E"/><circle cx="104" cy="228" r="13" fill="#9AA3AD"/>'
            f'<circle cx="298" cy="228" r="26" fill="#0B0C0E"/><circle cx="298" cy="228" r="13" fill="#9AA3AD"/>'
            f'<path d="M30 236 C34 266 364 266 368 236 Z" fill="url(#car{uid})" opacity=".18"/>')
    return _wrap(uid, defs, body, light=False)

SCENES = {"landscaping": landscaping, "plumbing": plumbing, "dental": dental, "hvac": hvac, "auto-detailing": detailing}

def scene(key, uid, v=0):
    return SCENES.get(key, detailing)(uid, v)
