Otthoni energiafogyasztás-elemző

Hallgató
Koncz Dávid
AK4CNT
Feladat leírása
Grafikus Python-alkalmazás a háztartás havi villamosenergia- és gázfogyasztásának rögzítésére, megjelenítésére és statisztikai elemzésére. A felhasználó havi adatokat vihet fel, módosíthat és törölhet, illetve CSV-fájlból betöltheti és abba mentheti azokat. A program a tkinter Canvas segítségével oszlopdiagramon mutatja be a legutóbbi 12 rögzített hónapot, és kiszámítja az összesítést, átlagot, mediánt, szórást, minimumot és maximumot. A kiválasztott évre összehasonlítja az adatokat az előző év azonos hónapjaival, figyelmeztet a 30%-ot meghaladó kiugrásra, megadott éves áram- és gázkereteket figyel, és legalább három rögzített hónap esetén az eddigi havi átlagból éves becslést készít.

Szükséges környezet
- Python 3.10 vagy újabb
- `tkinter` (a Windowsra telepített normál Python része)
- Nincs szükség külső Python-csomagra

Telepítés és indítás
A projekt mappájában terminálból:



Használat
1. Válaszd ki az évet és a hónapot.
2. Add meg az áramfogyasztást kWh-ban és a gázfogyasztást m³-ben. Tizedesvessző és tizedespont is használható.
3. Kattints a **Mentés / módosítás** gombra. Azonos év és hónap esetén a korábban tárolt értékek frissülnek.
4. A táblázatban egy sorra kattintva betöltheted az értékeit a mezőkbe.
5. A **Kijelölt törlése** gomb eltávolítja az adott havi adatot.
6. A **Grafikon és statisztika** fülön kiválasztható az áram- vagy a gázfogyasztás.
7. A felső **Éves elemzés külön ablakban** gombbal külön, átméretezhető, görgethető elemzőablak nyílik; az **Éves fogyasztásfigyelő** fülön megadható a két éves keret, majd az **Év elemzése** gombbal az Év mezőben megadott évre készül elemzés. Az elemzés szövege külön görgethető, ezért kisebb ablakban sem vész el a vége.
8. A **CSV megnyitása** gombbal másik fájl tölthető be, a **Mentés másként** gombbal másolat készíthető.

A program a kiválasztott típusból a legutóbbi 12 hónapot rajzolja ki, a statisztikát minden betöltött hónapból számolja. A program indításkor a projekt mappájában lévő `fogyasztas.csv` fájlt tölti be, ha létezik. Az alapértelmezett CSV mintadatokat tartalmaz, nem tényleges fogyasztási méréseket. Az új adatok és módosítások a megnyitott adatfájlba mentődnek. A statisztikák a rögzített hónapokra vonatkoznak, nem feltétlenül egy teljes évre.

Elemzőfunkciók
- Az előző év azonos hónapjához képest százalékos változást számít, ha mindkét érték rendelkezésre áll és a bázis nem nulla.
- Kiugrásnak jelöli a 30%-ot meghaladó emelkedést az előző év azonos hónapjához képest; ha ilyen összehasonlítás nem készíthető, három közvetlenül megelőző hónap átlagához hasonlít.
- Éves becslés: legalább három rendelkezésre álló hónap átlaga szorozva tizenkettővel. Ez egyszerű becslés, főleg a gázfogyasztás szezonális ingadozásánál pontatlan lehet.
- Az éves áram- és gázkeret az alkalmazásban megadható; a program figyelmeztet, ha a már rögzített összeg vagy az éves becslés nagyobb a keretnél. A keretértékeket a program nem menti el, újraindításkor az alapértékek jelennek meg.
- A mintafájl 2026-os adatokat tartalmaz; az előző éves összehasonlításhoz 2025-ös hónapok is szükségesek.

Felhasznált modulok és függvények

| Modul | Szerep | Használt függvények / elemek |
|---|---|---|
| `tkinter`, `tkinter.ttk` | Tanult modul; grafikus kezelőfelület és eseménykezelés | `Tk()`, `StringVar()`, `Button()`, `Treeview()`, `Combobox()` |
| `statistics` | Bemutatandó modul; statisztikai számítások | `mean()`, `median()`, `pstdev()` |
| `kd_energy` | Saját modul; adatok, számítások és CSV-fájlkezelés | `kd_calculate_statistics()`, `kd_analyze_year()`, `kd_load_csv()`, `kd_save_csv()` |
| `tkinter.Canvas` | Grafikus elem; diagramok | `create_rectangle()`, `create_line()`, `create_text()` |
| `csv` | Szabványos fájlkezelő modul | `DictReader()`, `writer()` |

