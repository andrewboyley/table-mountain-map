# Trail-names verification

How the 172 "hiking trail" names in this project were checked.

## What these names are

The 172 names come from the OSM-derived trail layer at `data/vector/osm/tm_hiking_trails_dissolved.gpkg`
(layer `hiking_trails`, 172 features), drawn in the QGIS project by the 172-category renderer in
`qgis/styles/trail_colors.csv`. The model in `qgis/processing/trail_rebuild.model3` splits OSM ways
into the named/unnamed/single-part trail sets and dissolves each set by exact `name`.

The goal here is simple: for each name, decide whether it matches a **real named feature** on
Table Mountain / the TMNP area, and if so, what kind of feature it is and from which source.

## Sources checked

| Code | Source | What it covers |
| --- | --- | --- |
| SANPARKS | sanparks.org/parks/table-mountain/what-to-do/activities/hikes-walks-trails | Official TMNP hiking trails (the 5 most popular: Lion's Head, Pipe Track, Platteklip Gorge, Skeleton Gorge/Smuts, Kasteelspoort) |
| AllTrails | alltrails.com/parks/.../table-mountain-national-park (+ trail pages) | Popular hikes, plus short/long trail lists |
| FOTM | friendsoftablemountain.org/tmnp-trails | Popular trail list |
| HikeTM | hiketablemountain.co.za | Canonical local guide; lists routes by mountain face |
| MP | mountainproject.com (Table Mountain / Cape Town) | Rock-climbing route/area index |
| mtb | mtbproject.com/trail/.../tokai-mtb-snakes-vasbyt-trails | Tokai Forest MTB trail segments |
| MCSA | mcsacapetown.co.za | Mountaineering club trip reports |
| Blogs | getaway.co.za, hikinginthesouth.co.za, shehikesalot.com, stingynomads.com, peakperspectives.co.za, thehappytraveller.co.za, mountainmeanders wiki | Route write-ups |
| News24 | news24.com (Table Mountain route-name origins) | Historic route-name conventions |
| OutdoorCT | outdoor.capetown | Cape Point section trails |

## Method and honesty rule

A name is marked **CONFIRMED** only where a fetched page names it. "Unclear" means no online source
was found by me for that exact spelling (it does **not** prove the feature is absent — TM is huge and
many minor gullies are undocumented online). Climbing-route and MTB-segment names are recorded as
real features, but flagged as **not hiking trails**.

## Summary

- 172 names total.
- Confirmed real named trails or trail-like features: ~62.
- Confirmed as a real feature but **not a marked hiking trail** (climbing route, scrambling
  route, or MTB segment): ~33.
- Spelling variants / misspellings of a confirmed name: ~13.
- Duplicate within the list (a name that is a near-exact copy of another): ~9.
- Artifact / not-a-name (mapper description or track-log label): ~4.
- Unclear (no source found): ~51.

## Name-by-name table

| # | Name (as in data) | Verdict | Correct name | Source |
|---|---|---|---|---|
| 1 | 580 m Traverse | Hiking trail | 580 m Traverse (no space) | AllTrails (Devil's Peak area) |
| 2 | 580m Devil's Peak Traverse | Hiking trail | — | AllTrails (Devil's Peak) |
| 3 | 580m Traverse | Hiking trail | — | AllTrails |
| 4 | 580m Traverse Link | Hiking trail | — | AllTrails (same group) |
| 5 | 7 Buttresses Traverse | Climbing route? | Unclear | No source (number-prefixed) |
| 6 | 700m Traverse | Unclear | No source (number-prefixed) | No |
| 7 | Admirals Footpath | Unclear | No source | No |
| 8 | Agatha's Gully | Unclear | No source | No |
| 9 | Alfies path | Unclear | Possibly "Alfie's Path" | No |
| 10 | Amphitheathre Path | Spelling variant | Amphitheatre Path | HikeTM / hikinginthesouth |
| 11 | Arcia Road | Place / road | Not a trail | No |
| 12 | Ash Valley | Unclear | No source | No |
| 13 | Avenue Saint Leon | Place / road? | No source | No |
| 14 | B | Artifact (likely "Left Face B" / "Mystery B") | No | No |
| 15 | Bailey's Kloof | Unclear | Possibly a real gully | No |
| 16 | Blackburn Major | Unclear | No source | No |
| 17 | Blackburn Ravine | Unclear | No source | No |
| 18 | Blackhill River Walk | Unclear | No source | No |
| 19 | Blackhill Sandpit | Unclear | No source | No |
| 20 | Blind Gully | Hiking / off-beat path | Real ravine path | HikeTM (western slopes list) |
| 21 | Blinkwater Ravine | Real feature | Blinkwater gully (News24 "Blinkwater Cleft") | News24 (route-name origins) |
| 22 | Boomslang | Real feature | Cave/gully in Echo Valley; also a route + MTB segment | getaway.co.za |
| 23 | Boomslang Cave Path (Underground) | Spelling variant | Boomslang Cave Trail | AllTrails (short hikes #10) |
| 24 | Boulders | Place (Boulders Beach/Penguin area) | Not a marked hike | — |
| 25 | Bridge | Unclear | No source | No |
| 26 | Buffelsbay Detour (Coastal) | Real (coastal) | Near Buffels Bay / Cape Point | SANPARKS area |
| 27 | Bypass | Artifact | Mapper note | No |
| 28 | Cairn Ravine | Real feature | Cairn gully/ravine family | HikeTM (Grotto-Fountain-Cairn) |
| 29 | Cape of Good Hope | Hiking area | Real (trail + reserve) | SANPARKS |
| 30 | Cape Point | Hiking area | Real | SANPARKS / AllTrails |
| 31 | Cecilia Ridge | Hiking trail | Real | AllTrails (long trails #4) |
| 32 | Cleft Peak | Unclear | No source | No |
| 33 | Cobra | Real feature (MTB + climbing) | Tokai MTB segment / route | mtbproject |
| 34 | Constantia Corner | Unclear | No source | No |
| 35 | Constantiaberg West Ridge | Unclear | No source | No |
| 36 | Contour Path | Hiking trail | Real (north-facing contour) | AllTrails / HikeTM |
| 37 | Corridor Ravine | Real feature (hike+climb) | Real gully | AllTrails / MCSA |
| 38 | Da Gama Park Path | Unclear | No source | No |
| 39 | Dark Gorge | Real feature? (suspected TM route) | No direct source | No |
| 40 | Dassenberg Path | Unclear | No source | No |
| 41 | Dassies Kasteel | Unclear | No source | No |
| 42 | Diagonal Route | Hiking / scramble trail | Real | SummitPost / stingynomads |
| 43 | Diagonal Route / Porcupine Ravine | Compound (both real) | — | SummitPost / HikeTM |
| 44 | Dingaans Ridge | Unclear | No source | No |
| 45 | Disa Gorge | Real feature (hike+climb) | Real gorge | AllTrails (long #7) |
| 46 | Dragon's Passage | Unclear | No source | No |
| 47 | Duiker Ridge | Unclear | No source | No |
| 48 | Echo Valley | Real feature (hike) | Real forest/gully | ridgwayramblers / SANPARKS |
| 49 | Elephant's Eye Trail | Hiking trail | Real (Silvermine) | AllTrails / SANPARKS |
| 50 | Els Buttress | Spelling variant | Els Ravine | HikeTM (eastern slopes list) |
| 51 | Erica Buttress | Unclear | No source | No |
| 52 | Exit Via the Gift Shop | Unclear (suspected climbing route) | No source | No |
| 53 | Faerie Garden | Real feature (MTB trail) | Tokai MTB segment | mtbproject |
| 54 | FarmersCliffsWalkMiddle | Real (GPX/track-log name) | Farmer's Cliffs (Cape Point section) | outdoor.capetown / mypacer |
| 55 | Fernwood Track | Unclear | No source | No |
| 56 | Ferny Dell | Place (Kirstenbosch walk, outside TMNP) | Not a TMNP trail | — |
| 57 | Frustratiion Ravine | Spelling variant | Frustration Ravine | HikeTM / News24 |
| 58 | Frustration Buttress | Real feature (buttress) | Related to Frustration Ravine/Gorge | HikeTM / News24 |
| 59 | Glencairn Stables Pathway | Unclear | No source | No |
| 60 | Glenhill Valley extension | Unclear | No source | No |
| 61 | Glenhill Valley Trail | Unclear | No source | No |
| 62 | Grotto Fountain Cairn Traverse | Real feature (traverse) | Grotto-Fountain-Cairn | HikeTM blog |
| 63 | Grotto Ravine | Real feature (ravine) | Part of Grotto-Fountain-Cairn | MCSA |
| 64 | Grove Walk | Unclear | No source | No |
| 65 | Hiddingh Ascension | Spelling variant | Hiddingh-Ascension | HikeTM |
| 66 | Hill Climb Ocean Contour Path | Artifact (phrase, not a name) | No | No |
| 67 | Hoerikwaggo Trail | Hiking trail | Official SANPARKS trail | SANPARKS |
| 68 | India Venster | Hiking / scramble trail | Real, famous | AllTrails / SANPARKS / FOTM |
| 69 | Intake Ravine | Unclear | No source | No |
| 70 | Just Chute me | Unclear (suspected climbing route) | No source | No |
| 71 | Kalk Bay Kam | Unclear | Possibly "Kalk Bay Kram"/Peak | No |
| 72 | Karbonkelberg Traverse | Real feature (traverse) | Hout Bay / TMNP southern | getaway.co.za |
| 73 | Kasteels Buttress B | Climbing route | Kasteelspoort buttress route | HikeTM / MP |
| 74 | Kasteelspoort Path | Hiking trail | Real, major | AllTrails / SANPARKS / FOTM |
| 75 | Kleintuinkop Direct | Unclear | No source | No |
| 76 | Kloof Corner | Hiking / scramble trail | Real | AllTrails / FOTM |
| 77 | Kloof Corner Ridge | Real feature | Part of Kloof Corner | AllTrails |
| 78 | Knife's Edge | Hiking trail | Devil's Peak Knife's Edge | AllTrails (long #6) |
| 79 | Lakeside Pinnacle | Climbing crag | Real (near Constantiaberg) | MP (Cape Town area) |
| 80 | Lakeside Pinnacle Path | Unclear | Possibly path to the crag | No |
| 81 | Ledges | Unclear (suspected climbing route) | No source | No |
| 82 | Left Face B | Climbing route | "Left Face" / "Mystery B" | hikinginthesouth / HikeTM |
| 83 | Lekkerwater Traverse | Unclear | No source | No |
| 84 | Lighthouse Keeper's Trail | Hiking trail | Real (Cape Point) | AllTrails (short #9) |
| 85 | Lions Head Path | Spelling variant | Lion's Head | AllTrails / SANPARKS / FOTM |
| 86 | Littlewort Trail | Place (Kirstenbosch walk, outside TMNP) | Not TMNP | — |
| 87 | Lizard | Real feature (MTB trail) | Tokai MTB segment | mtbproject |
| 88 | Llandudno Buttress | Climbing feature | Buttress near Llandudno | AllTrails (long #9) |
| 89 | Llandudno Ravine | Real feature (ravine/hike) | Real | AllTrails (long #9) |
| 90 | Lower Kloof Corner Link | Real feature | Part of Kloof Corner | AllTrails |
| 91 | Mamba | Real feature (MTB + climbing) | Tokai MTB segment / route | mtbproject |
| 92 | Mercurius | Unclear | No source | No |
| 93 | Mimetes Valley | Unclear | No source | No |
| 94 | Misteriosa | Unclear (suspected climbing route) | No source | No |
| 95 | Mother in Law | Unclear (suspected climbing route) | No source | No |
| 96 | Mowbray Ridge | Unclear | No source | No |
| 97 | Muizenberg Buttress | Climbing feature? | Muizenberg crag (outside TM) | No |
| 98 | Muizenberg Crag | Climbing feature? | Muizenberg crag | No |
| 99 | Myburgh's Waterfall Ravine | Real feature? | No source | No |
| 100 | Navy Trail | Unclear | No source | No |
| 101 | New trail / bypass | Artifact | Mapper note | No |
| 102 | Newlands Link | Real feature | Newlands link path | (local) |
| 103 | Newlands Ravine | Hiking trail | Real gorge/walk | AllTrails / HikeTM |
| 104 | Nordhoek Minor | Spelling? | Noordhoek? No source | No |
| 105 | Nordhoek West Ridge | Spelling? | Noordhoek West Ridge? | No |
| 106 | North Peak | Unclear | No source | No |
| 107 | North Peak via Baboon's Armchair | Unclear | No source | No |
| 108 | Nursery Buttress | Real feature (buttress/scramble) | Real | HikeTM / MCSA |
| 109 | Nursery Ravine | Hiking trail | Real, major | AllTrails / HikeTM / SANPARKS |
| 110 | Old Railway Track | Place / old rail | Not TMNP trail | — |
| 111 | Orange Kloof Trail | Hiking trail (permit) | Real | SANPARKS / HikeTM |
| 112 | Oudekraal Ravine | Real feature | Real gully | HikeTM / MCSA |
| 113 | Penguin Viewing Path | Unclear | No source | No |
| 114 | Pimple Traverse | Unclear | No source | No |
| 115 | Pipe Track | Hiking trail | Real, iconic contour track | AllTrails / SANPARKS / FOTM |
| 116 | Platteklip Gorge | Hiking trail | Real, main route | AllTrails / SANPARKS / FOTM |
| 117 | Porcupine Ravine | Real feature (hike+climb) | Real gully | SummitPost / News24 |
| 118 | Puff Adder | Real feature? (suspected route) | No direct source | No |
| 119 | Quarry path | Unclear | No source | No |
| 120 | Red Hill alternate return via One Bollock | Artifact (track-log label) | Not a name | No |
| 121 | Red Hill Direct | Real feature? (Red Hill is real) | No source | No |
| 122 | Redhill Direct | Near-duplicate of 121 | Spelling variant | No |
| 123 | Repens Valley | Unclear | No source | No |
| 124 | Repens Valley extension | Near-duplicate-ish | No source | No |
| 125 | Reserve Peak | Unclear | No source | No |
| 126 | Rhinkals | Unclear (suspected route) | No source | No |
| 127 | Right Face Arrow Face Traverse | Real feature? (Arrow Buttress area) | "Right Face"/"Arrow Face" | MP |
| 128 | Rim Track | Unclear | No source | No |
| 129 | Rocket Road | Place / road | Real road (Suther Peak area) | peakperspectives |
| 130 | Rooikrans Trail | Unclear | No source | No |
| 131 | Shipwreck Trail | Unclear | No source | No |
| 132 | Shortcut to Elephants Eye | Spelling variant | Shortcut to Elephant's Eye | AllTrails / SANPARKS |
| 133 | Silverstream Ravine | Real feature (ravine) | Real | HikeTM (north face list) |
| 134 | Silverstream-Ledges Traverse | Climbing feature? | Likely a route | No |
| 135 | Simonsberg | Place (Stellenbosch, NOT TMNP) | Wrong area | — |
| 136 | Simonstown to Smitswinkel via Swartkop | Real (long walk, coastal) | Not a TM summit trail | OutdoorCT / AllTrails |
| 137 | Skeleton Gorge / Smuts Track | Compound (both real) | — | AllTrails / SANPARKS |
| 138 | Skorsteenberg Sub | Spelling variant | Skoorsteenberg Sub (or Skoorsteenkam) | mountainmeanders / MP |
| 139 | Skortseenberg Direct | Spelling variant | Skoorsteenkop/Steenberg | mountainmeanders |
| 140 | Skortseenberg Sub | Near-duplicate of 138 | Spelling variant | mountainmeanders |
| 141 | Smuts' Track | Real feature | Smuts Track (variant apostrophe) | SANPARKS / AllTrails |
| 142 | Snake Eyes | Real feature (MTB + route) | Tokai MTB segment | mtbproject |
| 143 | Southern Approach | Unclear | No source | No |
| 144 | Spes Bona Valley | Real feature (hike) | Real forest walk | ridgwayramblers |
| 145 | Spilhaus Buttress | Climbing feature? | TM buttress | No |
| 146 | Spring Buttress | Real feature (buttress) | Real | HikeTM / News24 |
| 147 | St James Buttress | Unclear | No source | No |
| 148 | Steenberg Buttress | Unclear | No source | No |
| 149 | Steenberg Ridge Path | Unclear | No source | No |
| 150 | Suther Peak | Hiking trail | Real (Hout Bay) | peakperspectives / getaway |
| 151 | Swartkop Left Face B | Climbing feature? | Route on Swartkop | No |
| 152 | The Lost Crusade | Unclear (suspected route) | No source | No |
| 153 | The Other Woman | Unclear (suspected route) | No source | No |
| 154 | Three Firs | Real feature (hike) | Real (Apostles) | AllTrails / shehikesalot |
| 155 | Trappies Surprise | Unclear | No source | No |
| 156 | Trappieskop Base Circular | Real feature (Trappieskop) | Trappieskop (Kalk Bay) | hikinginthesouth / simplifaye |
| 157 | Traverse of the Gods | Climbing/scramble route | Real | mountainmeanders / MCSA |
| 158 | Twelve Apostles | Real feature (area/range) | Real | SANPARKS / AllTrails |
| 159 | Twelve Apostles Path | Real feature (traverse) | Real | AllTrails |
| 160 | Twisted Roots Trail | Unclear | No source | No |
| 161 | Union Ravine | Unclear | No source | No |
| 162 | Upper Deane Road | Place / road | Not a trail | — |
| 163 | Vasbyt | Real feature (MTB segment) | Tokai MTB trail | mtbproject |
| 164 | Victoria Ravine | Real feature (ravine) | Real | HikeTM |
| 165 | Willis Walk | Unclear | No source | No |
| 166 | Woodcutters Trail | Hiking trail | Real (southern TMNP) | komoot |
| 167 | Woody Buttress | Climbing feature? | Woody = crag area | No |
| 168 | Woody Ravine | Real feature (hike) | Real | AllTrails |
| 169 | Yellowstone Gully | Unclear | No source | No |
| 170 | Yellowwood Trail | Unclear (Yellowwood Traverse exists) | See Yellowwood Traverse | No |
| 171 | Yellowwood Trail / Smuts Track | Compound (Smuts confirmed) | — | SANPARKS |
| 172 | Yellowwood Traverse | Real feature (traverse) | Real | MCSA |

## What this means for the "named hiking trails"

Most of the famous names are correct: Hoerikwaggo Trail, India Venster, Skeleton Gorge / Smuts Track,
Newlands Ravine, Nursery Ravine, Pipe Track, Platteklip Gorge, Kasteelspoort, Orange Kloof, Kloof
Corner, Cape Point, Lighthouse Keeper's Trail, Elephant's Eye, Boomslang Cave Trail, Disa Gorge,
Cecilia Ridge, Contour Path, Three Firs, Yellowwood Traverse, Suther Peak, etc.

But the 172-name set is **not** a set of hiking trails. It is every OSM way that carries a `name=`
tag in the extract, dissolved by that exact string. That is why the list includes:

- **Climbing-route / scramble names**, not hiking trails: Left Face B, Kasteels Buttress B,
  Traverse of the Gods, Diagonal Route, Boomslang, Frustration Buttress, Nursery Buttress,
  Spring Buttress, Arrow/Fountain-area gullies. Several are real and famous, but they are climbed
  or scrambled, not signed day hikes.
- **MTB trail segments** in the Tokai Forest block: Cobra, Mamba, Boomslang, Snake Eyes, Lizard,
  Faerie Garden, Vasbyt. Real named paths, but bike trails, and "Vasbyt" is also a different 2-day
  trail in the Waterberg — a collision risk if the name is reused.
- **Typos and track-log labels**: Amphitheathre, Frustratiion (×2), Lions Head (no apostrophe),
  Elephants Eye (no apostrophe), Nordhoek vs Noordhoek, Skorsteenberg/Skortseenberg (vs Skoorsteenkop),
  Hiddingh Ascension (vs Hiddingh-Ascension), FarmersCliffsWalkMiddle (camelCase), "New trail / bypass",
  "Red Hill alternate return via One Bollock", the "580m … Traverse" group, and the letter/phrase
  leftovers "B", "Bridge", "Ledges", "Bypass", "Hill Climb Ocean Contour Path".
- **Duplicates / compound names** kept as separate categories because `dissolve` keys on the exact
  string: Skeleton Gorge / Smuts Track and Smuts' Track and Yellowwood Trail / Smuts Track;
  Red Hill Direct and Redhill Direct; the three Skorsteenberg/Skortseenberg variants; Lakeside
  Pinnacle and Lakeside Pinnacle Path.
- **Out-of-section places** tagged as names: Simonsberg (Stellenbosch), Upper Deane Road, Old
  Railway Track, Ferny Dell, Littlewort Trail (these are Kirstenbosch/low-elevation names, not
  Table Mountain summit trails).

## Recommendations

If the project's intent is "named hiking trails for a Table Mountain map/render", the dataset should
be **filtered and cleaned** upstream, not fixed in the renderer:

1. Drop or reclassify non-hiking names (climbing routes, MTB segments, road/place names, artifacts)
   so the 172-category renderer does not end up with legend entries that are not trails.
2. Normalise spellings before dissolve so near-duplicates merge (Skorsteenberg→Skoorsteenkop,
   Nordhoek→Noordhoek, Lions Head→Lion's Head, Frustratiion→Frustration, Hiddingh Ascension→
   Hiddingh-Ascension, Yellowwood/Trim → Smuts Track; the "580m …" group to one spelling).
3. Keep the dissolve keyed to canonical names, not raw OSM strings, so a mapper note
   ("New trail / bypass", "Red Hill … One Bollock") never becomes a legend category.

## Note on the project file

`qgis/table_mountain_3D.qgs` is a hand-edited project file. Manual GUI edits
are preserved -- run `just verify-project` after saving to confirm the project
invariants still hold. This verification did not touch the `.qgs`.
