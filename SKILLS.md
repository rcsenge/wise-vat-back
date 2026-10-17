# Skills

This file stores the shared agent skills of the monorepo. Each skill has its own section.

## wise-design

- Name: `wise-design`
- Trigger: `/wise-design`
- Description: Mobil app frontendet a Wise app vizuális nyelvére hangol (élénkzöld + erdőzöld paletta, óriási csupa-nagybetűs display címek, pill gombok, lebegő tab bar, kevés szöveg, festett 3D illusztrációk). Használd, ha a felhasználó /wise-design-t ír, vagy azt kéri, hogy egy app UI „Wise-szerű”, „Wise stílusú” legyen, illetve ha egy képernyőt, komponenst vagy egész frontendet ebbe a stílusba kell átdolgozni vagy így kell megépíteni. Bármilyen stackkel működik (React Native/Expo, Flutter, SwiftUI, Jetpack Compose, mobil-web React/Tailwind).


### Wise design – mobil app stílus

Cél: a felhasználó appja **pontosan olyan érzetű** legyen, mint a Wise iOS/Android appja: fehér, levegős képernyők, egyetlen élénkzöld akcentszín, sötét erdőzöld szöveg a zöldön, hatalmas tömör csupa-nagybetűs címek, teljesen lekerekített (pill) gombok, nagyon kevés szöveg. Csak mobil app nézetre készül (kb. 360–430 px / pt széles képernyő), desktop layoutot ne tervezz.

> A stílust vesszük át, a márkát nem: **ne** használd a Wise logót, nevét, a „7”-es zászló jelet vagy a Wise Sans fájlokat, hacsak a felhasználó nem saját licenccel adja meg. A saját app nevét/logóját tedd a helyükre.

#### Munkamenet

1. **Stack felderítése.** Nézd meg a repót (package.json, pubspec.yaml, *.xcodeproj, build.gradle, tailwind.config, meglévő theme fájl). Határozd meg: hol élnek a design tokenek, milyen ikon- és font-betöltési megoldás van.
2. **Tokenek bevezetése egy helyen.** Olvasd el: [references/tokens.md](#design-tokenek). Másold/fordítsd le a megfelelő kész fájlt:
   - web / Tailwind / CSS-in-JS → [assets/tokens.css](#tokenscss)
   - React Native / Expo / bármilyen TS → [assets/tokens.ts](#tokensts)
   - Flutter / SwiftUI / Compose → a tokens.ts értékeit fordítsd le a platform theme-jére (ThemeData, Color extension, MaterialTheme). Az értékek ugyanazok.
   Meglévő theme-et **cserélj le / képezz le**, ne hozz létre mellé egy másodikat. Hardcode-olt színeket, méreteket a komponensekben cserélj tokenre.
3. **Fontok.** Body: **Inter** (400/500/600/700). Display: lásd tokens.md „Betűtípusok” – ha nincs saját licencelt Wise Sans, a megadott ingyenes helyettesítőt töltsd be. Állíts be fallback stacket.
4. **Komponensek.** Olvasd el: [references/components.md](#komponensek). Építsd meg / igazítsd a közös primitíveket (Button, Chip, ListItem, Card, Avatar, IconCircle, TabBar, Input, Sheet, Toast) – a képernyők csak ezeket használják.
5. **Képernyők.** Olvasd el: [references/screens.md](#képernyő-minták-és-szövegmennyiség). Minden képernyőt a hozzá illő mintára húzz rá (Home/dashboard, Empty state/feature intro, Lista, Űrlap/amount, Siker), és **húzd meg a szöveget** a copy-szabályok szerint.
6. **Ellenőrzés.** Ha futtatható (iOS Simulator, Expo, böngésző mobil viewporttal), nyisd meg és vesd össze az alábbi checklisttel. Ha nem, nézd át a kódot ugyanezzel.

#### A 12 legfontosabb szabály (ha csak ennyit olvasol)

1. **Háttér mindig tiszta fehér** (`#FFFFFF`). Szürke csak kártyák/szekciók kitöltésére (`#F2F4EF` neutrális). Nincs színátmenet a UI-ban.
2. **Egy akcentszín: Bright Green `#9FE870`.** Rajta a szöveg/ikon **mindig Forest Green `#163300`**, soha nem fehér, soha nem fekete.
3. **Halvány zöld `#E2F6D5`** a másodlagos gombok/chipek háttere, szöveg rajta szintén `#163300`.
4. **Szövegszín majdnem-fekete `#0E0F0C`**, másodlagos `#454745`, harmadlagos `#6A6C6A`. Tiszta `#000` nincs.
5. **Display címek:** csupa nagybetű, extra vastag (900), nagyon szoros sorköz (0.85) és betűköz (-1…-2%), középre igazítva hero/empty state-en. 2–6 szó. Csak képernyőnként egy.
6. **Normál címek** (pl. „Payments”, „Transactions”) Inter 600–700, nem csupa nagybetű, balra igazítva.
7. **Gombok pill alakúak** (radius 9999). Nagy CTA 56 magas, teljes szélesség; chip/kis gomb 40–48 magas. Felirat Inter 600, 16–18.
8. **Képernyő-margó 16 (–20)**, elemek között 8/12/16/24/32 lépcső. Bőkezű függőleges levegő.
9. **Kártyák lekerekítése 24** (nagy konténer), 16 (lista kártya), árnyék nélkül – lapos szürke kitöltés vagy 1px halvány keret. Árnyékot csak a lebegő tab bar és a felugró elemek kapnak.
10. **Lebegő alsó tab bar:** fehér pill, lágy árnyék, alul margóval lebeg; aktív tab mögött szürke pill; 4 tab, outline ikon + 12-es címke.
11. **Ikonok vékony vonalas (outline) 24px, 1.5–2 stroke**, gyakran 48–56-os körben (halvány keret), „hozzáadás” esetén kis zöld + jelvénnyel.
12. **Kevés szöveg:** egy display cím + egy 1–2 mondatos alcím + max. 3 felsorolás (ikon + félkövér cím + 1 soros leírás) + CTA. Ha több kell, vágd.

#### Kerülendő (ezektől lesz „nem Wise”)

- Kék/lila akcentszín, több versengő akcentszín, gradiens gombok.
- Fehér szöveg zöld gombon; fekete szöveg zöld gombon.
- Kis radiusú (4–8) szögletes gombok, outline-only primary gomb.
- Erős drop shadow kártyákon, material elevation.
- Hosszú bekezdések, sok kis betűs magyarázat, mondatvégi felkiáltójelek.
- Emoji ikonok, filled (kitöltött) ikonszett, színes ikonok.
- Top app bar címsorral + hamburger menü (Wise-ban nincs hagyományos nav bar a tab-gyökérképernyőkön).
- Szűk margók, zsúfolt listák elválasztó vonalakkal minden sor között.

#### Ellenőrző lista

- [ ] Minden szín token, nincs elszórt hex a komponensekben.
- [ ] Zöld felületeken `#163300` a tartalom.
- [ ] Képernyőnként max. 1 primary (zöld) gomb; a másodlagos halványzöld vagy szürke.
- [ ] Display cím: uppercase, 900, line-height ≤ 0.9, középre (hero/empty).
- [ ] CTA-k alul rögzítve, teljes szélességben, safe area felett; több CTA egymás alatt 12–16 réssel.
- [ ] Tab bar lebeg, pill, aktív állapot szürke pill.
- [ ] Linkek: aláhúzott, `#163300`, 600.
- [ ] Összegek: nagy, vastag, tabular számok; pénznem kód mellette.
- [ ] Szövegmennyiség a screens.md copy-szabályai szerint.
- [ ] Érintési célpont ≥ 44×44, kontraszt AA.

### Design tokenek

Minden méret **pt / dp / CSS px** (1:1, mobil viewport 375–430 széles). A kész fájlok: [../assets/tokens.css](#tokenscss), [../assets/tokens.ts](#tokensts).

#### Színek

##### Márka / akcentus
| Token | Hex | Mire |
|---|---|---|
| `brand.brightGreen` | `#9FE870` | Primary gomb, aktív chip („Send”), kiemelt badge, + jelvény, progress |
| `brand.brightGreenPressed` | `#80E142` | Primary gomb lenyomva / hover |
| `brand.forestGreen` | `#163300` | Tartalom (szöveg, ikon) zöld és halványzöld felületen; linkek; sötét hero blokk |
| `brand.lightGreen` | `#E2F6D5` | Secondary gomb / chip háttér („Add money”, „Customise settings”) |
| `brand.lightGreenPressed` | `#CDEFB8` | Secondary lenyomva |

##### Kiegészítő (csak illusztráció, marketing kártyák, kategória-színek – UI vezérlőn soha)
| Token | Hex |
|---|---|
| `accent.brightOrange` | `#FFC091` |
| `accent.brightYellow` | `#FFEB69` |
| `accent.brightBlue` | `#A0E1E1` |
| `accent.brightPink` | `#FFD7EF` |
| `accent.darkPurple` | `#260A2F` |
| `accent.darkGold` | `#3A341C` |
| `accent.darkMaroon` | `#320707` |
| `accent.darkCharcoal` | `#21231D` |

Párosítás (sötét háttér ↔ világos tartalom): forestGreen↔brightGreen, darkPurple↔brightPink, darkMaroon↔brightPink, darkGold↔brightYellow, darkCharcoal↔brightOrange.

##### Tartalom (szöveg, ikon)
| Token | Hex | Mire |
|---|---|---|
| `content.primary` | `#0E0F0C` | Címek, fő szöveg, összegek, ikonok |
| `content.secondary` | `#454745` | Leírások, alcímek, body szöveg képernyő-intrókban |
| `content.tertiary` | `#6A6C6A` | Placeholder, meta (dátum), inaktív tab ikon |
| `content.link` | `#163300` | Aláhúzott linkek („See all”, „Sync now”) |
| `content.onAccent` | `#163300` | Zöld/halványzöld felületen |
| `content.inverse` | `#FFFFFF` | Sötét (forest/charcoal) felületen |

##### Háttér, felület, keret
| Token | Hex | Mire |
|---|---|---|
| `bg.screen` | `#FFFFFF` | Minden képernyő háttere |
| `bg.neutral` | `#F2F4EF` | Kártya/szekció kitöltés (pl. „Main account” kártya, kiemelt lista elem) |
| `bg.neutralPressed` | `#E8EBE5` | Lenyomott kártya / sor; aktív tab pill |
| `bg.overlay` | `rgba(14,15,12,0.40)` | Bottom sheet/modál mögött |
| `border.neutral` | `#E0E2DE` | Input keret, ikon-kör keret, elválasztó |
| `border.subtle` | `#ECEDEA` | Szaggatott „üres/hozzáadható” kártya keret |
| `border.focus` | `#163300` | Fókuszált input (2px) |

##### Szentiment
| Token | Hex | Mire |
|---|---|---|
| `sentiment.positive` | `#2F5711` | Bejövő összeg (+), siker szöveg |
| `sentiment.positiveBg` | `#E2F6D5` | Siker banner |
| `sentiment.negative` | `#A8200D` | Hiba szöveg, input hiba keret |
| `sentiment.negativeBg` | `#FFE6E1` | Hiba banner |
| `sentiment.warning` | `#EDC843` | Figyelmeztető ikon |
| `sentiment.warningBg` | `#FFF6D1` | Figyelmeztető banner |
| `sentiment.notification` | `#E8443A` | Értesítési pötty az avataron |

Sötét mód: a Wise app alapvetően világos. Ha a felhasználó kéri: `bg.screen #121511`, `bg.neutral #21231D`, `content.primary #F2F4EF`, `content.secondary #C9CBC6`, akcentus marad `#9FE870`, rajta továbbra is `#163300`.

#### Betűtípusok

| Szerep | Eredeti | Ingyenes helyettesítő (Google Fonts) | Fallback |
|---|---|---|---|
| Display (óriás címek) | Wise Sans Heavy (zárt licenc) | **Archivo** wght 900, wdth 88–92 (vagy Archivo Black) | `"Inter Tight" 900`, system-ui |
| UI / body | Inter | **Inter** 400/500/600/700 | -apple-system, "SF Pro Text", Roboto, system-ui |

- Display: mindig `text-transform: uppercase`, `font-weight: 900`, `line-height: 0.85–0.9`, `letter-spacing: -0.01em…-0.02em`. A betűk szinte összeérnek – ez szándékos.
- Ha a felhasználó saját Wise Sans fájlt ad, azt tedd az első helyre a display stackben.
- Számok (összegek, egyenleg): `font-variant-numeric: tabular-nums` / `fontVariant: ['tabular-nums']`.

#### Típusskála

| Token | Méret / sor | Súly | Font | Példa |
|---|---|---|---|---|
| `display.xl` | 52 / 46 | 900 | Display, UPPER | Onboarding hero |
| `display.lg` | 44 / 38 | 900 | Display, UPPER | „GET PAID EASILY, NO BANK DETAILS NEEDED” |
| `display.md` | 36 / 32 | 900 | Display, UPPER | „GLOBAL SPENDING MADE SIMPLE”, siker képernyő |
| `display.sm` | 28 / 26 | 900 | Display, UPPER | Promó kártya címe |
| `title.screen` | 32 / 38 | 700 | Inter | „Payments” (tab gyökér címe) |
| `amount.lg` | 40 / 46 | 700 | Inter, tabular | „0 HUF” egyenleg |
| `title.section` | 24 / 30 | 700 | Inter | „Transactions”, „Main account” |
| `title.item` | 18 / 24 | 600 | Inter | Lista elem címe, feature bullet címe |
| `body.lg` | 18 / 26 | 400 | Inter | Intro leírás hero alatt |
| `body.md` | 16 / 24 | 400 | Inter | Alap szöveg, lista leírás |
| `body.sm` | 14 / 20 | 400 | Inter | Meta, segítő szöveg input alatt |
| `label.button.lg` | 18 / 24 | 600 | Inter | Nagy CTA |
| `label.button.md` | 16 / 22 | 600 | Inter | Chip, kis gomb |
| `label.tab` | 12 / 16 | 500 (aktív 600) | Inter | Tab bar címke |
| `link` | 16 / 24 | 600 | Inter, aláhúzva | „See all”, „Learn more” |

Szabály: egy képernyőn legfeljebb 3 különböző méret a display címen kívül.

#### Térköz (4-es rács)
`0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64`

- Képernyő oldalmargó: **16** (kis kijelzőn is), nagyobb telefonon max. 20.
- Szekciók között: **32–40**.
- Cím → leírás: **12–16**. Leírás → lista: **24**.
- Lista elemek között (kártya listában): **12–16**.
- CTA-k egymás között: **12–16**; CTA blokk felett hajszálvonal + 16 padding.
- Chip sor elemei között: **8**.

#### Lekerekítés
| Token | Érték | Mire |
|---|---|---|
| `radius.sm` | 8 | Kis badge, input belső elemek |
| `radius.md` | 16 | Input, lista kártya, toast |
| `radius.lg` | 24 | Nagy kártya (account kártya, feature kártya), bottom sheet teteje |
| `radius.xl` | 32 | Tab bar, illusztrációs kártyák |
| `radius.pill` | 9999 | Minden gomb, chip, avatar, ikon-kör |

#### Árnyék / elevation
| Token | Érték | Mire |
|---|---|---|
| `shadow.none` | – | Kártyák (alapértelmezett!) |
| `shadow.floating` | `0 8 24 rgba(14,15,12,0.10)` + `0 1 3 rgba(14,15,12,0.06)` | Tab bar, lebegő pill („Open +”), FAB |
| `shadow.sheet` | `0 -8 32 rgba(14,15,12,0.12)` | Bottom sheet |

#### Méretek
- Primary/secondary nagy gomb magasság: **56** (min. 52).
- Chip / kis gomb magasság: **40–48** (balance chipek: 48).
- Input magasság: **56**.
- Lista sor min. magasság: **72** (ikon-kör 48 + 12 függőleges padding).
- Avatar: **48** (header), **40** (lista), **72–88** (profil).
- Ikon: **24** (alap), **20** (chipben), **16** (badge-ben).
- Ikon-kör: **48–56**, 1px `border.neutral`.
- Tab bar: magasság **64**, oldalmargó 16, alsó margó a safe area felett **8**.

#### Animáció
- Időtartam: 150 ms (press), 250 ms (sheet, tab váltás), 350 ms (képernyő push).
- Easing: `cubic-bezier(0.2, 0, 0, 1)` (standard), sheet-nél rugó (damping ~20).
- Gomb lenyomás: `scale(0.97)` + pressed szín. Nincs ripple.

### Komponensek

Minden érték a [tokens.md](#design-tokenek) tokenjeire hivatkozik. Állapotok: default, pressed (scale 0.97 + pressed szín), disabled (opacity 0.4), loading (spinner a felirat helyén, szélesség nem változik).

#### Button

| Variáns | Háttér | Szöveg | Mire |
|---|---|---|---|
| `primary` | `brightGreen` → pressed `brightGreenPressed` | `forestGreen` | Fő akció: „Confirm”, „Send”, „Add recipient”, „Order a card” |
| `secondary` | `lightGreen` → pressed `lightGreenPressed` | `forestGreen` | Alternatív akció: „Customise settings”, „Add money” |
| `neutral` | `bg.neutral` → pressed `bg.neutralPressed` | `content.primary` | Semleges/harmadlagos: „Pay with QR code”, „Not now” |
| `tertiary` | átlátszó | `content.link`, aláhúzva | Szöveges link-gomb |
| `negative` | `sentiment.negativeBg` | `sentiment.negative` | „Cancel transfer”, „Delete” |
| `dark` | `forestGreen` | `brightGreen` | Ritkán: sötét hero blokkon |

Méretek:
- `lg`: magasság 56, vízszintes padding 24, `label.button.lg`, **teljes szélesség** (képernyő alján).
- `md` / chip: magasság 44–48, padding 20, `label.button.md`, tartalomhoz méretezve.
- `sm`: magasság 32, padding 12, 14/600.
- Radius mindig `pill`. Nincs keret, nincs árnyék.
- Ikon a felirat előtt 20-as, 8 rés („⊞ Scan”, „🎁 Invite” helyett outline ikon).

Szabály: képernyőnként **egy** primary. Két CTA esetén: primary felül, secondary/neutral alatta, 12–16 rés.

#### Action chip sor (Home tetején)

Vízszintes, görgethető sor: `Send` (primary), `Add money`, `Request`, `Scan` (secondary). Magasság 48, rés 8, első elem a képernyőmargónál kezdődik, a sor túlfuthat jobbra (horizontális scroll, margó a végén is).

#### Pill header gombok

- **Avatar** (bal felső): 48 kör, `bg.neutral`, monogram 18/600 `content.primary`. Értesítés: 12-es `sentiment.notification` pötty jobb felül, 2px fehér kerettel.
- **Promo pill** (középen): primary zöld pill, 48 magas, „Earn 22 500 Ft” típusú rövid szöveg.
- **„Open +” pill** (jobb): fehér pill, `shadow.floating`, 48 magas, szöveg 18/500 + 20-as „+” ikon.

#### IconCircle

48–56 kör, 1px `border.neutral` keret, fehér/átlátszó kitöltés, közepén 24-es outline ikon `content.primary`.
- „Hozzáadható” jelvény: 20-as `brightGreen` kör jobb alul, benne 14-es „+” `forestGreen`, 2px fehér kerettel.
- Kiemelt változat: kitöltés `brightGreen`, ikon `forestGreen` (pl. kereső kör a discoverability képernyőn).
- Zászló/pénznem: 32–40 kör, teljes kitöltésű zászló kép.

#### ListItem (sor)

```
[IconCircle/Avatar/Flag]  Cím (title.item 18/600)            [jobb oldal: összeg / ›]
                          Leírás (body.md 16/400 secondary, max 2 sor)
```
- Min. magasság 72, vízszintes padding 16 (kártyán belül) vagy 0 (képernyőn közvetlenül), függőleges 12.
- Bal elem → szöveg rés 16.
- Jobb oldal: chevron `›` 24, `content.primary`; vagy összeg 16/600 tabular (bejövő: `+ 1 200 Ft` `sentiment.positive`).
- **Nincs elválasztó vonal** a sorok között; a ritmust a térköz adja.
- Tranzakció sor: cím = partner neve, leírás = „Sent · Yesterday” típusú meta, jobbra összeg + alatta pénznem összeg `content.tertiary`.

#### Card

- **Neutral card**: `bg.neutral`, radius 24, padding 20–24, árnyék nincs. Pl. „Main account” kártya: cím `title.section`, alatta egyenleg `body.lg` secondary, majd pénznem-sorok (zászló 40 + összeg 18/400 + chevron), alul `Account details` neutral sm gomb (ikonnal, `bg.neutralPressed` háttér).
- **Action card** (Payments lista): `bg.neutral` vagy fehér + 1px keret, radius 24, padding 20, tartalom = ListItem (IconCircle + cím + 2 soros leírás + chevron). Kártyák között 16.
- **Empty/add card**: fehér, **1.5px szaggatott** `border.neutral` keret, radius 24 – olyan funkciókhoz, amik még nincsenek beállítva („Scheduled transfers”, „Direct Debits”).
- **Promo/feature kártya**: telített kiegészítő háttér (pl. `darkPurple`), rajta a párja (`brightPink`) display szöveggel, radius 32, illusztrációval.
- **Carousel**: account kártyák vízszintesen lapozva, a következő kártya 16-ot kilóg jobbra; alatta pötty indikátor (8-as pöttyök, aktív `content.primary`, inaktív `#C9CBC6`, rés 8).

#### Floating TabBar

- Pozíció: abszolút, alul, oldalmargó 16, alsó margó safe area + 8.
- Konténer: fehér, radius 32 (pill), magasság 64–72, `shadow.floating`, belső padding 6.
- 4 tab, egyenlő szélesség: Home, Cards, Recipients, Payments (a saját app tabjaira cseréld, max. 5).
- Tab: outline ikon 24 + címke `label.tab` 12/500, `content.primary` (inaktív ikon is sötét, csak a súly más).
- Aktív tab: `bg.neutral` pill háttér a tab teljes magasságában (radius 9999), címke 600.
- A görgethető tartalom alján legyen annyi padding (≈ 100), hogy a tab bar ne takarjon.
- Egyes képernyőkön (pl. Recipients empty state) a tab bar mögött halvány zöld glow lehet – opcionális díszítés.

#### Input / TextField

- Felette címke 14/500 `content.secondary`, rés 8.
- Mező: magasság 56, radius 16, 1px `border.neutral`, fehér háttér, padding 16, szöveg 16/400.
- Fókusz: 2px `border.focus` (forest green). Hiba: 2px `sentiment.negative` + alatta 14-es hibaszöveg ikonnal.
- Kereső: `bg.neutral` kitöltés keret nélkül, radius pill, bal oldalt 20-as nagyító ikon, placeholder „Search”.
- **Amount input** (küldés): két nagy blokk egymás alatt („You send” / „Recipient gets”), mindegyik radius 16 keretes mező, bal oldalt összeg 32/700 tabular, jobb oldalt pénznem pill (zászló 24 + kód 16/600 + chevron) `bg.neutral` háttérrel. Közöttük árfolyam/díj sorok 14/400 kis ikon-pöttyökkel.

#### Segmented control / Tabs (képernyőn belül)

Chip sor: aktív = primary zöld pill, inaktív = secondary halványzöld pill (lásd „Send / Request” a Payments képernyőn). Nem aláhúzott tab.

#### Bottom Sheet / Modal

- Fehér, felső sarkok radius 24–32, `shadow.sheet`, overlay `bg.overlay`.
- Felül 36×4 húzó fogantyú `#C9CBC6`, 8 margóval.
- Tartalom: opcionális illusztráció középen → `title.section` vagy `display.sm` cím → 1–2 mondat → CTA(k) teljes szélességben.
- Bezárás: jobb felül 40-es kör `bg.neutral` × ikonnal.

#### Navigation header (push-olt képernyőkön)

- Nincs színes app bar. Fehér, bal felül 40-es kör vissza gomb (`bg.neutral`, ← 24 ikon), opcionálisan jobb felül kör ikon-gomb (súgó „?”, ×).
- A cím **nem** a headerben van, hanem alatta nagyban (`title.screen` vagy display), balra igazítva.

#### Avatar / Recipient

- Kör, 40–56. Fotó, vagy monogram `bg.neutral` + 16–18/600.
- Sarokban kis jelvény (20) a fizetési módhoz: pl. zöld kör a márka-ikonnal vagy zászló.
- Átfedő avatar-csoport: körök fehér 4px kerettel, -12 átfedés; középen lehet `brightGreen` ikon-kör.

#### Badge / Tag

Pill, magasság 24, padding 8, 12/600. Variánsok: `lightGreen`+`forestGreen` (info/új), `sentiment.warningBg`+`content.primary`, `sentiment.negativeBg`+`sentiment.negative`.

#### Toast / Snackbar

Alul a tab bar felett, `content.primary` (#0E0F0C) háttér, fehér 16/500 szöveg, radius 16, padding 16, opcionális bal oldali zöld pipa ikon `brightGreen`. 3 s.

#### Link

`link` stílus: 16/600, `content.link`, aláhúzva (offset 3). Szekció címek jobb oldalán „See all”; leírások alatt „Learn more”, „Sync now”.

#### Ikonok

- Outline ikonszett, 24, stroke 1.5–2, lekerekített végek. Ajánlott: **Lucide** / Phosphor (regular) / SF Symbols (regular). Ugyanazt a szettet használd mindenhol.
- Szín: `content.primary`, zöld felületen `forestGreen`. Színes ikon nincs.

#### Illusztrációk és képek

- Hero/empty state: **egy** nagy, 3D-s, festett textúrájú tárgy (szív, földgömb, papírrepülő, kártya) középen, ~200–280 széles, árnyék nélkül, fehér háttéren lebegve.
- Ha nincs saját illusztráció: placeholder egy `brightGreen`/`brightBlue` színes, radius-os forma vagy emberekről készült kör-kivágott fotók (`bg.neutral` 8–12-es keretgyűrűvel).
- Fotók: valódi emberek, meleg természetes fény, körbe vagy radius 24 kártyába vágva.

### Képernyő-minták és szövegmennyiség

Alap váz minden képernyőn:
- Fehér háttér, safe area, oldalmargó 16.
- Tartalom felülről lefelé; CTA blokk **alul rögzítve** (nem görög el), felette 1px `border.subtle` hajszálvonal csak ha a tartalom görgethető.
- Tab gyökérképernyőkön lebegő tab bar; push-olt / flow képernyőkön nincs tab bar, helyette kör alakú vissza gomb.

#### 1. Home / dashboard

```
[Avatar•]        [ Earn 22 500 Ft ]   [ Open + ]      ← header pillek, 48 magas, top 8
                                                        ↓ 32
Total balance                                          body.lg secondary
0 HUF  (◔ kis kör ikon-gomb)                           amount.lg
                                                        ↓ 20
[Send] [Add money] [Request] [Scan] →                  action chip sor
                                                        ↓ 24
┌ Main account ─────────────────── › ┐                 Neutral card, carousel
│ 0 Ft                               │
│ (EU) €0.00                      ›  │
│ (HU) 0 Ft                       ›  │
│ [🏛 Account details]               │
└────────────────────────────────────┘  ┌ következő kártya kilóg
              ● ○                                       ↓ 40
Transactions                          See all          title.section + link
(◷)  No transactions yet                               ListItem / empty sor
                                                        ↓ (tab bar helye)
[ Home | Cards | Recipients | Payments ]               floating tab bar
```

#### 2. Feature intro / empty state (a legjellegzetesebb Wise képernyő)

Használd: első belépés egy tabra, üres lista, funkció bemutatása, engedélykérés.

```
                [ 3D illusztráció ]                    ~240 széles, felső 1/3
                        ↓ 40
        ADD YOUR PEOPLE,                               display.lg / display.md
          NEAR AND FAR                                 középre, UPPER, 2–6 szó
                        ↓ 16
   Spend abroad and at home. No markups,               body.lg secondary, középre
        no transaction fees.                           (VAGY a lenti bullet lista)
                        ↓ 32
(🔍) Quickly find your people                          feature bullet: ikon 24 balra,
     Simply search or sync phone contacts.             cím title.item, leírás body.md secondary
     Sync now                                          opcionális link
(⊕) Add details your way
     ...
(📄) Upload. Autofill. Go
     ...
─────────────────────────────────────────
[            Primary CTA             ]                 56, teljes szélesség
[          Secondary CTA             ]                 opcionális
```

Variáció „Discoverability”: felül 3 átfedő kör (fotó – zöld kereső ikon – fotó), alatta display cím **balra/középre**, rövid bekezdés, ikon-lista egysoros elemekkel (ikon + link/szöveg), lábjegyzet 14/400 tertiary („Update this anytime in Settings.”), aláhúzott link, alul Confirm + Customise.

#### 3. Lista / hub képernyő (pl. Payments)

```
                                                        ↓ 56 (header nélkül)
Payments                                               title.screen, balra
                        ↓ 16
[Send] [Request]                                       chip-szegmens (primary + secondary)
                        ↓ 24
┌ (✉+) Forward invoices to email      › ┐              Action card (beállított: kitöltött)
│      Save time by emailing bills...    │
└────────────────────────────────────────┘  ↓ 16
┆ (📅+) Scheduled transfers           › ┆              Empty/add card (szaggatott keret)
┆      Set up a transfer to send later.  ┆
...
```

#### 4. Flow / űrlap képernyő (küldés, címzett hozzáadása)

- Bal felül kör vissza gomb, jobb felül opcionális × / ?.
- Lépés-indikátor helyett vékony 4-es progress bar a tetején (`brightGreen` kitöltés `bg.neutral` sávon, radius pill) – opcionális.
- Cím `title.screen` vagy `display.sm` balra, 1 kérdés képernyőnként („Who are you sending to?”, „How much?”).
- Inputok 16-os rácsban, egymás alatt; segítő szöveg 14 tertiary.
- Alul rögzített primary „Continue”, disabled amíg érvénytelen.
- Lista választás (pénznem, címzett): kereső pill felül, alatta ListItem-ek kártya nélkül, „Popular” / „All” szekciócímek 14/600 secondary.

#### 5. Siker / megerősítés

- Teljes képernyő `brightGreen` VAGY `forestGreen` háttér (a Wise itt vált színes háttérre).
- Középen illusztráció/animált pipa, alatta display.md cím a párszínnel (zöldön `forestGreen`, forest-en `brightGreen`): „YOUR MONEY'S ON ITS WAY”.
- 1 mondat body.lg, alul CTA: zöld háttéren `dark` gomb (forest + bright green szöveg), forest háttéren primary.

#### 6. Részletek (tranzakció, kártya)

- Felül nagy kör ikon/avatar 56–72, alatta összeg `amount.lg`, alatta státusz badge.
- Chip sor akciókkal (Repeat, Share, Help).
- Részletek: kulcs–érték sorok, kulcs 16/400 secondary balra, érték 16/600 jobbra, sorok között 16, szekciócímek `title.item`.

---

### Szövegmennyiség és hangnem (copy szabályok)

**Mennyiség – keményen vágj:**
| Elem | Max. |
|---|---|
| Display cím | 2–6 szó, max. 3 sor |
| Alcím / intro | 1–2 mondat, ≤ 110 karakter |
| Feature bullet | max. 3 db; cím 2–5 szó, leírás ≤ 70 karakter (≤ 2 sor) |
| Lista elem leírás | 1 mondat, ≤ 2 sor |
| Gomb | 1–3 szó, ige elöl („Add recipient”, „Order card”, „Confirm”) |
| Lábjegyzet | 1 sor, opcionális |
| Képernyőnként összesen | ~40–60 szó a hero/empty state-en, kevesebb máshol |

**Hangnem:**
- Közvetlen, egyszerű, barátságos, második személy („Add your people”, „Get paid easily”). Magyarul tegező, ha az app közönsége ezt engedi.
- Előny, nem funkció: „No markups, no transaction fees.” – ne „Our card supports multi-currency transactions.”
- Rövid mondatok, pont a végén, **felkiáltójel nincs**, emoji nincs.
- Display cím lehet vessző-ritmusú két fél: „ADD YOUR PEOPLE, NEAR AND FAR”, „GET PAID EASILY, NO BANK DETAILS NEEDED”.
- Feature bullet címek ritmusa: „Upload. Autofill. Go”.
- Számok mindig konkrétak, pénznem formátum a locale szerint (`0 Ft`, `€0.00`), tabular számjegyek.
- Normál címek mondat-kezdőbetűvel (Sentence case), nem Title Case – kivéve a display, ami CSUPA NAGY.

**Elrendezés:**
- Hero/empty/siker: **középre** igazított cím és szöveg; a feature lista balra igazított blokk középen.
- Minden más (Home, listák, űrlapok, részletek): **balra** igazított.
- Egy képernyő = egy fókusz. Ha két fő dolog van, bontsd két képernyőre vagy sheetre.

### tokens.css

```css
/* Wise-style design tokens — mobil app (web / Capacitor / mobil-web React) */
@import url("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,900&family=Inter:wght@400;500;600;700&family=Inter+Tight:wght@900&display=swap");

:root {
  /* brand */
  --color-bright-green: #9FE870;
  --color-bright-green-pressed: #80E142;
  --color-forest-green: #163300;
  --color-light-green: #E2F6D5;
  --color-light-green-pressed: #CDEFB8;

  /* accents (illusztráció / kategória, vezérlőn nem) */
  --color-bright-orange: #FFC091;
  --color-bright-yellow: #FFEB69;
  --color-bright-blue: #A0E1E1;
  --color-bright-pink: #FFD7EF;
  --color-dark-purple: #260A2F;
  --color-dark-gold: #3A341C;
  --color-dark-maroon: #320707;
  --color-dark-charcoal: #21231D;

  /* content */
  --content-primary: #0E0F0C;
  --content-secondary: #454745;
  --content-tertiary: #6A6C6A;
  --content-link: #163300;
  --content-on-accent: #163300;
  --content-inverse: #FFFFFF;

  /* background / border */
  --bg-screen: #FFFFFF;
  --bg-neutral: #F2F4EF;
  --bg-neutral-pressed: #E8EBE5;
  --bg-overlay: rgba(14, 15, 12, 0.4);
  --border-neutral: #E0E2DE;
  --border-subtle: #ECEDEA;
  --border-focus: #163300;

  /* sentiment */
  --sentiment-positive: #2F5711;
  --sentiment-positive-bg: #E2F6D5;
  --sentiment-negative: #A8200D;
  --sentiment-negative-bg: #FFE6E1;
  --sentiment-warning: #EDC843;
  --sentiment-warning-bg: #FFF6D1;
  --sentiment-notification: #E8443A;

  /* fonts */
  --font-display: "Wise Sans", "Archivo", "Inter Tight", system-ui, sans-serif;
  --font-body: "Inter", -apple-system, "SF Pro Text", Roboto, system-ui, sans-serif;

  /* type scale: size / line-height */
  --display-xl: 900 52px/46px var(--font-display);
  --display-lg: 900 44px/38px var(--font-display);
  --display-md: 900 36px/32px var(--font-display);
  --display-sm: 900 28px/26px var(--font-display);
  --title-screen: 700 32px/38px var(--font-body);
  --amount-lg: 700 40px/46px var(--font-body);
  --title-section: 700 24px/30px var(--font-body);
  --title-item: 600 18px/24px var(--font-body);
  --body-lg: 400 18px/26px var(--font-body);
  --body-md: 400 16px/24px var(--font-body);
  --body-sm: 400 14px/20px var(--font-body);
  --label-button-lg: 600 18px/24px var(--font-body);
  --label-button-md: 600 16px/22px var(--font-body);
  --label-tab: 500 12px/16px var(--font-body);

  /* spacing */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-5: 20px;
  --space-6: 24px; --space-8: 32px; --space-10: 40px; --space-12: 48px; --space-16: 64px;
  --screen-gutter: 16px;

  /* radius */
  --radius-sm: 8px; --radius-md: 16px; --radius-lg: 24px; --radius-xl: 32px; --radius-pill: 9999px;

  /* shadow */
  --shadow-floating: 0 8px 24px rgba(14, 15, 12, 0.10), 0 1px 3px rgba(14, 15, 12, 0.06);
  --shadow-sheet: 0 -8px 32px rgba(14, 15, 12, 0.12);

  /* motion */
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --dur-press: 150ms; --dur-medium: 250ms; --dur-push: 350ms;
}

html, body { background: var(--bg-screen); color: var(--content-primary); font: var(--body-md); -webkit-font-smoothing: antialiased; }

.display-xl, .display-lg, .display-md, .display-sm {
  text-transform: uppercase; letter-spacing: -0.015em; font-variation-settings: "wdth" 90; color: var(--content-primary);
}
.display-xl { font: var(--display-xl); } .display-lg { font: var(--display-lg); }
.display-md { font: var(--display-md); } .display-sm { font: var(--display-sm); }
.amount { font: var(--amount-lg); font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
.link { font: var(--label-button-md); color: var(--content-link); text-decoration: underline; text-underline-offset: 3px; }

/* Tailwind használat esetén a theme.extend-be:
  colors: { brand: { green: 'var(--color-bright-green)', forest: 'var(--color-forest-green)', light: 'var(--color-light-green)' },
            content: { DEFAULT: 'var(--content-primary)', secondary: 'var(--content-secondary)', tertiary: 'var(--content-tertiary)' },
            neutral: { bg: 'var(--bg-neutral)', pressed: 'var(--bg-neutral-pressed)', border: 'var(--border-neutral)' } },
  borderRadius: { md: '16px', lg: '24px', xl: '32px' },
  fontFamily: { display: ['Archivo', 'Inter Tight', 'system-ui'], sans: ['Inter', 'system-ui'] },
  boxShadow: { floating: 'var(--shadow-floating)', sheet: 'var(--shadow-sheet)' }
*/
```

### tokens.ts

```ts
// Wise-style design tokens — React Native / Expo / bármilyen TS frontend.
// Flutter / SwiftUI / Compose esetén ugyanezeket az értékeket fordítsd le a platform theme-jére.
// RN fontok (expo-font / @expo-google-fonts): Archivo_900Black (vagy Archivo Black), Inter_400Regular,
// Inter_500Medium, Inter_600SemiBold, Inter_700Bold. RN-ben a fontWeight helyett a konkrét fontFamily-t add meg.

export const colors = {
  brightGreen: '#9FE870',
  brightGreenPressed: '#80E142',
  forestGreen: '#163300',
  lightGreen: '#E2F6D5',
  lightGreenPressed: '#CDEFB8',

  accent: {
    brightOrange: '#FFC091',
    brightYellow: '#FFEB69',
    brightBlue: '#A0E1E1',
    brightPink: '#FFD7EF',
    darkPurple: '#260A2F',
    darkGold: '#3A341C',
    darkMaroon: '#320707',
    darkCharcoal: '#21231D',
  },

  content: {
    primary: '#0E0F0C',
    secondary: '#454745',
    tertiary: '#6A6C6A',
    link: '#163300',
    onAccent: '#163300',
    inverse: '#FFFFFF',
  },

  bg: {
    screen: '#FFFFFF',
    neutral: '#F2F4EF',
    neutralPressed: '#E8EBE5',
    overlay: 'rgba(14,15,12,0.40)',
  },

  border: {
    neutral: '#E0E2DE',
    subtle: '#ECEDEA',
    focus: '#163300',
  },

  sentiment: {
    positive: '#2F5711',
    positiveBg: '#E2F6D5',
    negative: '#A8200D',
    negativeBg: '#FFE6E1',
    warning: '#EDC843',
    warningBg: '#FFF6D1',
    notification: '#E8443A',
  },
} as const;

export const fonts = {
  display: 'Archivo_900Black', // vagy saját licencelt 'WiseSans-Heavy'
  regular: 'Inter_400Regular',
  medium: 'Inter_500Medium',
  semibold: 'Inter_600SemiBold',
  bold: 'Inter_700Bold',
} as const;

const display = (fontSize: number, lineHeight: number) => ({
  fontFamily: fonts.display,
  fontSize,
  lineHeight,
  letterSpacing: -fontSize * 0.015,
  textTransform: 'uppercase' as const,
  color: colors.content.primary,
});

export const type = {
  displayXl: display(52, 46),
  displayLg: display(44, 38),
  displayMd: display(36, 32),
  displaySm: display(28, 26),
  titleScreen: { fontFamily: fonts.bold, fontSize: 32, lineHeight: 38, letterSpacing: -0.4 },
  amountLg: { fontFamily: fonts.bold, fontSize: 40, lineHeight: 46, letterSpacing: -0.4, fontVariant: ['tabular-nums'] as const },
  titleSection: { fontFamily: fonts.bold, fontSize: 24, lineHeight: 30, letterSpacing: -0.2 },
  titleItem: { fontFamily: fonts.semibold, fontSize: 18, lineHeight: 24 },
  bodyLg: { fontFamily: fonts.regular, fontSize: 18, lineHeight: 26, color: colors.content.secondary },
  bodyMd: { fontFamily: fonts.regular, fontSize: 16, lineHeight: 24, color: colors.content.secondary },
  bodySm: { fontFamily: fonts.regular, fontSize: 14, lineHeight: 20, color: colors.content.tertiary },
  buttonLg: { fontFamily: fonts.semibold, fontSize: 18, lineHeight: 24 },
  buttonMd: { fontFamily: fonts.semibold, fontSize: 16, lineHeight: 22 },
  tab: { fontFamily: fonts.medium, fontSize: 12, lineHeight: 16 },
  link: { fontFamily: fonts.semibold, fontSize: 16, lineHeight: 24, color: colors.content.link, textDecorationLine: 'underline' as const },
} as const;

export const space = { 0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 8: 32, 10: 40, 12: 48, 16: 64, gutter: 16 } as const;

export const radius = { sm: 8, md: 16, lg: 24, xl: 32, pill: 9999 } as const;

export const size = {
  buttonLg: 56,
  chip: 44,
  input: 56,
  listRow: 72,
  avatarHeader: 48,
  avatarList: 40,
  icon: 24,
  iconSm: 20,
  iconCircle: 52,
  tabBar: 64,
} as const;

export const shadow = {
  floating: {
    shadowColor: '#0E0F0C',
    shadowOpacity: 0.1,
    shadowRadius: 24,
    shadowOffset: { width: 0, height: 8 },
    elevation: 8,
  },
  sheet: {
    shadowColor: '#0E0F0C',
    shadowOpacity: 0.12,
    shadowRadius: 32,
    shadowOffset: { width: 0, height: -8 },
    elevation: 16,
  },
} as const;

export const motion = {
  press: 150,
  medium: 250,
  push: 350,
  pressScale: 0.97,
  easing: [0.2, 0, 0, 1] as const,
} as const;

export const theme = { colors, fonts, type, space, radius, size, shadow, motion };
export type Theme = typeof theme;
```
