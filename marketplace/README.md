# "The hardest app to build": two-sided marketplaces

A 51.3 s vertical (1080×1920, 30 fps) 3D explainer for JT Builds. The hardest app to build is the one that needs two groups of people at once. Uber and DoorDash solved it one city at a time, and a marketplace like DetailDash has to do the same.

This is a JT Builds video. It shares no sets, characters, cameras or graphics with the Baseball Decoded videos in this repo.

- **Look:** a night-time architect's scale model.
  - Charcoal sets with mirror floors, bloom and filmic tone mapping.
  - People are matte scale figures at real human proportions (1.75 m), not photoreal characters.
  - **One colour rule carries the story:** the demand side (customers, riders) is ivory, and the supply side (drivers, cooks, detailers) is amber. Every scene, map pin and app screen uses it.
  - Charcoal, white and one amber accent, set in Montserrat.
- **Text on screen:** the hook title ("The hardest app to build") for the first 3.5 s, word-by-word captions in a lower pill, and the closing line "ONE MARKET FIRST. THEN EXPAND.", which lands word for word with the voice and holds to the end. There is no logo. Everything else is told by the picture or by the app screens.
- **Voiceover:**
  - Your script, voiced with HyperFrames' local Kokoro TTS (voice `am_michael`, 1.7×). The text is in `transcript.txt`.
  - The speech alone runs about 43 s at that speed. With pauses for the ride and the orders to connect, and 2.5 s for the end card, the video is 51.3 s.
  - Shots and screens are keyed to the words:
    - The phone goes from code to an empty marketplace after "complicated code".
    - The two crowds light up on "two" and "different".
    - "No drivers nearby" appears on "no drivers".
    - The one city lights on "one city".
    - The booking is tapped on "car detailing".
    - Detailers light on "detailers" and customers on "enough customers".
    - The last line is not captioned: "one market first" and "then expand" land as the title as they are said.
  - `CUES.md` lists when each line starts, so you can record your own read over `assets/mix-novo.wav`.
- **Scenes** (times in `CUES.md`):
  1. **Hook:** a 9 m phone on a dark stage, customers on the left and providers on the right, an empty marketplace between them. Links try to cross and fail. The camera dives into the screen.
  2. **Ride-hailing:** a rider at the kerb in a night city; their app finds no cars; drivers parked with no requests; then a request, an accept, and the car pulls up.
  3. **Delivery:** a restaurant pass with bagged orders and an empty order screen; a customer's app with no restaurants; then the orders arrive.
  4. **Solution:** a dark US map with one city lit; into that city as connections build; back out as the network spreads across the country.
  5. **DetailDash:** the app (detailers near you, a booking), a detailing bay with a car being polished, and the booking landing on the detailer's phone.
  6. **Challenge:** the stage again, with the DetailDash map at zero detailers and zero customers; each side fills, then the bookings connect.
  7. **Close:** one neighbourhood fills with connections, the network expands, and a phone shows the DetailDash marketplace.
- **Sound:** a `make_bed` bed (style "glow") ducked under the voice, whooshes on the cuts, taps and pop-ups on the app events, risers into the map and the end card.
- **Mixes:**
  - `assets/mix.wav` is mastered to about −14 LUFS.
  - `assets/mix-novo.wav` is the music and effects without the voice.

## Accuracy notes

- Uber launched in San Francisco in 2010. DoorDash started in Palo Alto in 2013. The lit city on the map is the San Francisco Bay Area for both.
- The order in which other cities light up on the map is illustrative, not either company's real expansion order.
- No Uber or DoorDash logos, screens or brand colours are reproduced. The ride and delivery apps are generic.
- The DetailDash screens are illustrative: the detailers' names, ratings, prices and earnings are invented.

## Code

- `assets/js/core.js`: renderer, bloom, camera, figures and poses, the phone, the car, connection arcs.
- `assets/js/ui.js`: every app screen, drawn on a canvas.
- `assets/js/stage.js`, `city.js`, `kitchen.js`, `usmap.js`, `bay.js`: the five sets.
- `assets/js/main.js`: picks the set and camera for each shot.
- `build.py`: the shot list, captions, titles, sound cues and mix.

```bash
export HYPERFRAMES_PYTHON=<python with kokoro-onnx, soundfile, onnx>
$HYPERFRAMES_PYTHON tools/vo.py && python3 tools/assemble.py   # voiceover + per-word timing
python3 build.py                                               # index.html + assets/mix.wav (+ mix-novo.wav) + CUES.md
node tools/render_chunks.js . <chunk dir> 30 51.32 90 <port>   # resumable render, 90 frames per chunk
```

The bloom and mirror floors make each frame slow to draw (about 2.5 s), so the render runs in resumable chunks instead of `hyperframes render`.
