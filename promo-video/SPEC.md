# SPEC: "The number that comes twice"

GOAL:    a stranger leaves knowing "European bank figures on a map, each traced to its filing,
         and when filings disagree you see both", and wants to click "Open the interactive plate".
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, silent (embedded muted on docs/index.html).
TIME:    33.5 s x 30 = 1005 frames. No music, so no beat grid; something new every 2-4 s.
LOOK:    Atlas Plate I, from DESIGN.md.
         Ground paper #ffffff, no texture. Ink #141413; secondary ink #45453f; hairline #d4d8d2.
         Land greens #cdeadd / #9fd2b7 / #5ea883 / #2a7a55; unbanked land #e9ece8.
         Plate green #0f5a3c: the button, the claim's colour flood, the end card mark. Nowhere else.
         Amber (#8a5a00 text, #d9a441 rule, #fff8ec wash, #b07410 ring): ONLY on disagreement
         (the two figure pairs, Austria's ring, the dashboard's amber cells).
         Face: Archivo (variable, wdth 62-125, from docs/fonts). Figures 168 px / 720 / wdth 90,
         tabular; headline 76 px / 760 / wdth 112 / -0.012em; labels 30 px / 600 / wdth 125 /
         0.14em caps; body 34 px / 400.
         Medium: a printed statistical atlas plate. Ink is printed, not glowing: no shadows except
         the page's own button shadow (0 6 16 -8 rgba(15,90,60,.55)); screenshots sit on paper
         with a 1 px hairline, radius 2.
OBJECTS: the two figures (big tabular numerals with their template tag, EU OV1 / EU KM1);
         the amber rule between them; the atlas map of Europe (the page's own SVG) with 28 numbered
         markers; the dashboard (its real screenshots); the green button "Open the interactive plate →".
MOTION:  enter expo.out 0.5-0.7 s; camera power2.inOut 1.4-1.8 s; exit power3.in 0.25 s;
         per-word blur-in 0.13 s, 0.067 s apart; markers stagger 28 ms (the page's own reveal).
         Titles land and hold dead still.
SHOTS:
  0-8 s     twice:  Erste label + 149.7 (EU OV1) lands; 147.5 (EU KM1) lands beside it; amber rule
                    draws between, "1.5% apart" in amber; Raiffeisen row 101.3 / 100.9 / 0.3%.
                    Hand-off: figures blur out, Austria's amber ring is all that's left (carry across).
  8-15.5 s  plate:  camera starts at 4x on Austria's ring, pulls back to the whole plate; land tints
                    ink in by country; 28 markers pop; the page's headline lands at upper left.
                    Hand-off: dip to paper, then the dashboard's map arrives (match on Europe).
  15.5-26 s dash:   real screenshots: map with basket (3.2 s) → concept picker (3.0 s) → results
                    table (1.6 s) → punch-in 1.9x on the RWA row's amber cells (2.7 s), amber
                    outline draws round them.
  26-29 s   claim:  colour flood to plate green; "28 banks, every figure traced to its filing." in paper.
  29-33.5 s end:    flood recedes to paper; "Bank_Data" wipes in; the button presses in; the URL
                    types in beneath; hold 2.5 s.
CAPTIONS: one captions host, one group at a time, plate-ink box sized to the text, paper text
          40 px / 560, 96 px from the bottom, inside title-safe. The captions are the narration;
          titles show figures and the page's own copy, never the caption repeated word for word.
BANNED:  dark void; glow, particles; purple/blue gradients; cream paper + serif; mono caps
         labels; "01/02" step numerals; three cards in a row; KPI grid; title over a dimmed
         screenshot; docked logo; everything fade-and-slide-up; titles drifting after landing;
         amber used for anything but disagreement; invented UI or numbers; tilted 3D screenshots.
QA:      t=0.2 (thumbnail not empty), 3.0 (both Erste figures), 6.5 (Raiffeisen row),
         9.0 (zoom-out mid-move), 13.5 (full plate + headline), 17 (map), 20.5 (concepts),
         24.5 (amber punch-in readable), 27.5 (claim), 32.5 (end card + button + URL).
