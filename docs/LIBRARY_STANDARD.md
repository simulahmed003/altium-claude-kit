# Component library standard

Version 1.1, a draft by Simul, 2026-11-02, copied unchanged from the original document ("Component Library Standard — Categories & Rules", three tabs: categories, parameters, symbols/footprints/3D).
It is integrated into the kit through rules LIB-21 to LIB-29 (`rules/09_LIBRARY_STANDARD.md`).

Read this first section before using the standard. It lists:
- where the standard and the older kit rules disagree (D1 to D12). Each item waits for Simul's decision.
- the gaps inside the draft itself (R1 to R12).

**Until an item is decided, the older kit rule named in it still applies.** Everything else in the standard applies now.

## How it fits the kit

| Standard part | Kit rule | Tool that checks it today |
|---|---|---|
| Categories, classification, new categories | LIB-22 | none yet (proposal `lib_std_check.py`) |
| Common and electrical parameters, value format | LIB-23 | none yet (proposal `lib_std_check.py`) |
| Name = MPN; legacy CMP names | LIB-14, LIB-24 | `lib_audit.py` (name) |
| Pin names, numbers, types (SYM-01..05) | LIB-01, LIB-25 | `pin_match.py` (pins = pads) |
| Symbol layout and style (SYM-10..22, style values) | LIB-02, LIB-03, LIB-11, LIB-26 | `pin_match.py --style` (to be updated after D1-D3) |
| Footprints (FP-01..26, layer map, courtyard) | LIB-05, LIB-12, LIB-27 | none yet |
| 3D bodies (3D-01..07) | LIB-13, LIB-28 | `cad_fetch.py` (box check) |
| Verification and release | LIB-18, LIB-19, LIB-29 | `lib_audit.py mark` |
| Datasheet first | RQ-01 | `parts.py check` |

## Open decisions: standard vs kit rules (Simul decides each)

| # | Topic | Kit rule says | Standard says | Recommendation |
|---|---|---|---|---|
| D1 | IC pin length | LIB-11: 200 mil (Simul, 2026-10-19) | 300 mil, 100 mil pitch | 300 mil. Copies from the DbLib/Celestial need no edit. |
| D2 | 2-pin passive pins | LIB-03: capacitor pin 80 mil and test pad 70 mil as exceptions | R/C/L/FB pin 100 mil with a 200 mil body; diodes and LEDs pin 160 mil with an 80 mil body; 400 mil span for every 2-pin part | The standard. The kit symbols are already listed for rebuild (LIB-19). |
| D3 | Visible text | LIB-02: only Designator and Comment | SYM-22: capacitors also show Voltage Rating; fixed colours, Times New Roman 10 | The standard. Update `pin_match.py --style` to match. |
| D4 | Parameter names | LIB-14 / FAB-04: Manufacturer, MPN, LCSC, Mouser, DigiKey, Datasheet | `Manufacturer 1`, `Manufacturer Part Number 1`, `Supplier 1`, `Supplier Part Number 1`, `LCSC Part Number`, `DigiKey Part Number`, `Mouser Part Number`, `Datasheet URL` | The standard names in libraries. The production BOM keeps the FAB-04 columns (JLC needs `LCSC Part #`), and `bom_check.py` maps one to the other. |
| D5 | Description | LIB-14: `R 10k 1% 0603` | `RES 10k 1% 0.1W 0603`, a pattern per Type | The standard. |
| D6 | Unknown distributor number | RQ-09: write `UNCONFIRMED` | Leave it empty; never write `N/A`, `-` or `TBD` | Leave the library parameter empty, and keep UNCONFIRMED in the part record and the report. |
| D7 | 3D source order | LIB-13: JLC/EasyEDA by LCSC number first, then the maker | 3D-01: the maker's STEP first, then our own parametric model, then a checked third-party model. 3D-03: passives and standard packages from our own class templates | The maker's STEP first, JLC second as a checked third-party model. Our own parametric models later, since the kit has no CAD tool for them yet. |
| D8 | Footprint and 3D names | LIB-13/15: STEP at `models/step/<package>/<footprint>.step` | FP-22: IPC wizard names (`SOT95P280X145-5_TI-DBV`, `JST_B2B-XH-A`); 3D-05: the model is named after the body | Adopt the FP-22 and 3D-05 names inside the existing package-type folders. Rename the 9 existing STEP files in one approved batch. |
| D9 | Category tree | LIB-15 and `library/parts/taxonomy.json`: 7 categories, 34 families, which drive the DB folders and the symbol files | 22 Types and 89 Subtypes (Altium Component Types) | Keep the taxonomy for the DB folders for now and add a family → Type/Subtype map. Move the symbol file layout to the tree later, in its own PR. |
| D10 | Who verifies | LIB-19: unchecked → checked (agent) → confirmed (person) | Author ≠ verifier. Only the verifier fills `Verified By` / `Verified Date` and sets Released | The agent is the author and its LIB-18 check makes the part "checked". Simul is the verifier: "confirmed" fills Verified By/Date. Open: who verifies a part that Simul builds by hand? |
| D11 | Datasheet link | RQ-01: maker first, LCSC copy second | `Datasheet URL` = the maker's PDF, never a distributor copy | The maker's URL only. When the maker has none, leave it empty and write the LCSC link in the revision notes. |
| D12 | Where the standard lives | LIB-20: a client's rules stay local in `standards/local/clients/<client>/`, never pushed | (the draft says "our Altium Workspace library") | Here in the public kit, because it is Simul's own standard. A client's differences go to `standards/local/clients/`. **If this document is the client's, it must leave the public repo.** |

## Review notes on the draft itself (to fix in the original document)

| # | Where | Issue | Suggested fix |
|---|---|---|---|
| R1 | Parameters, common table | "All 25 are present on every component", yet `Category` is import-only and mapped to `<Skip>` | 24 stored parameters plus `Category` at import only |
| R2 | Parameters, value rules | "No space, ASCII only", yet `Height` = `0.55mm` and `Operating Temperature` = `-55°C to 155°C` (with spaces and the non-ASCII °) | State the exceptions: ranges keep "to" with spaces; ° is allowed or written `C` |
| R3 | Parameters, sourcing | The rules say "fixed LCSC, DigiKey and Mouser part numbers", but the table says "Required if stocked" | Say what happens when a distributor does not stock the part (empty, see D6) |
| R4 | Naming, Name = MPN | MPNs with `/` or `,` in this library (MCP23017T-E/ML, BAT54H,115, SSM6J505NU,LF) | Name keeps them exactly; the CSV quotes the field; file names replace `/` with `_` |
| R5 | Category tree | Some subtypes are split by a number or by mounting, which principle 3 forbids: Resistors/Through-Hole (mounting), Capacitors/Ceramic RF (C0G is a dielectric), LED/Indicator vs Lighting (power) | Give a yes/no test, e.g. "Ceramic RF = the maker sells it as an RF / High-Q series" |
| R6 | Tie-breaks | Parts in this library with no clear home: INA226 (Sensors/Current & Power or Amplifiers?), PCM5122 audio DAC (Data Converters or Audio Codecs?), STUSB4500 USB-PD sink (Interface or Power Switches?), NFZ2MSD common mode choke (Filters & EMI or Inductors/Coupled?); PTC appears under both Sensors and Protection | Add one worked example for each |
| R7 | AI instructions | "Confidence < 0.8 → REVIEW" cannot be checked | Fixed triggers: two subtypes fit, tie-break 6 was used, no subtype fits, or no datasheet (LIB-22 adds them) |
| R8 | Merging | "Fewer than 3 parts after 12 months → merge" would empty most of the 89 default subtypes in a library of about 74 parts | Apply it only to subtypes added after v1.0 |
| R9 | Description patterns | No pattern for LED, Crystals, Filters, Protection, Switches, Sensors, Modules and Board Features; inductors use `<size>`, not `<package>`; the MOSFET pattern has no Rds On | Add the missing patterns |
| R10 | Category tree examples | The examples use `µF` and `mΩ`, but v1.1 says ASCII `u` | Write the examples in ASCII |
| R11 | Verification checklist | Step 7 needs a reference design (ERC) and a placement test board (DRC), and neither exists yet. Step 8 (1:1 print) can only be done by a person | Build the reference design and the test board once, in the kit; mark step 8 as person-only |
| R12 | Open decisions (the draft's own list) | The PCB fab capability can already be answered for JLCPCB: PCB-06 and `rules/fab-profiles` give 1.0 mm text and 0.15 mm line | Close that item for JLCPCB; the others stay open |

## Transition for the current client library (SpeakerSystemV1)

- 38 of 74 components carry Workspace `CMP-xxx` names. They keep those names until Simul approves a rename batch (LIB-24). Their `Manufacturer Part Number 1` must still be correct now.
- The map from CMP name to MPN is in the job's `_SpeakerSystemV1_audit.md`.
- MPN and manufacturer are stored under four parameter-name styles in that library: `Manufacturer_Part_Number`, `Manufacturer Part Number`, `MP` and `ManufacturerPart`. All of them move to the D4 names in the same approved batch.

---

# The standard as written (v1.1)

## Part 1. Component Library Standard — Categories & Rules

2026-11-02 · Simul

Every component in our Altium Workspace library goes into exactly one **Type / Subtype** from the default tree below; a new category is created only when the classification procedure proves nothing fits.

### Purpose and scope

This is the single source of truth for how our component library is organised. It covers categories (Altium Component Types and subtypes), component naming, required parameters and how new categories are added.

**Who it is for**

- **Human librarians and engineers** adding parts to the library, by hand or through the Library Importer.
- **AI agents** classifying parts or preparing import data. The section *AI agent instructions* restates every rule in strict, machine-checkable form.

**How to use it**

1. Read *Core principles* once.
2. For each new part, run the *Classification procedure*.
3. If the part fits an existing subtype, use it. If not, follow *Creating a new category*.
4. Fill the *Required parameters* before the part is imported or saved.

The tree is adapted from the Celestial Altium Library (170 categories, which follow Digi-Key's product taxonomy), reduced to 2 levels and with package, value and polarity moved to parameters.

### Core principles

The library is organised on six principles; every rule later in this document follows from them.

1. **One component = one manufacturer part (MPN).** The component Name is the MPN. No generic components, no multiple Part Choices for alternates. Each component has exactly one Part Choice: the part itself, so live price, stock and lifecycle data work.
2. **Categories describe what a part IS and DOES, never its numbers.** Type = function or classic component family. Subtype = the first property an engineer filters by when choosing the part.
3. **Everything measurable is a parameter.** Package, value, tolerance, voltage, current, power, polarity, channel count, mounting style, manufacturer and supplier numbers are parameters, never categories.
4. **Exactly one home per part.** Every part belongs to one Type / Subtype. Categories must not overlap; when a part could fit two, the tie-break rules decide.
5. **Two levels, shallow and stable.** Type → Subtype only. A category is created to help people find parts, so depth follows real part counts, not completeness.
6. **Same words everywhere.** The category name in Altium, the `Category` parameter in source libraries and the Workspace folder use identical spelling.

### Default category tree

The tree has 22 Types and 89 Subtypes. Use it as-is; a part goes into the first subtype whose *What goes here* matches it. The `Category` value is what you type in source libraries for the Library Importer (format `Type/Subtype`).

| Type | Subtype | What goes here | Examples |
|---|---|---|---|
| Resistors | Chip | Fixed SMD thick/thin-film resistors, any size | RC0603FR-0710KL |
| Resistors | Through-Hole | Axial/radial fixed resistors | MFR-25 series |
| Resistors | Current Sense | Low-ohm shunts, Kelvin parts | 2512 10 mΩ |
| Resistors | Arrays & Networks | Multi-resistor packages | 4×10k 0603 array |
| Resistors | Potentiometers & Trimmers | Rotary, slide and trimmer pots | 3296W-1-103 |
| Capacitors | Ceramic (MLCC) | Multilayer ceramic, general purpose | CL10B104KB8NNNC |
| Capacitors | Ceramic RF | High-Q / C0G RF-rated ceramics | GJM series |
| Capacitors | Aluminum Electrolytic | Wet aluminium, SMD or THT | 470 µF 25 V 8×12 |
| Capacitors | Aluminum Polymer | Solid polymer aluminium | OS-CON |
| Capacitors | Tantalum | MnO2 and polymer tantalum | TAJB106K016RNJ |
| Capacitors | Film | Polyester, polypropylene, X/Y safety | X2 0.1 µF |
| Capacitors | Supercapacitors | EDLC, coin and cylindrical | 5.5 V 1 F coin |
| Inductors | Power | Shielded/unshielded power inductors | SWPA4030S4R7MT |
| Inductors | RF | Chip inductors for RF/matching | 0402 nH series |
| Inductors | Arrays & Coupled | Coupled, multi-winding inductors | Dual-winding SMD |
| Filters & EMI | Ferrite Beads | Chip ferrite beads | BLM18PG600SN1D |
| Filters & EMI | Common Mode Chokes | Signal and power CMCs | ACM2012 series |
| Filters & EMI | EMI Filters | Feed-through and LC filter parts | NFM18 series |
| Diodes | Rectifier & Schottky | General rectifier, fast and Schottky | SS34, 1N4007, 1N4148W |
| Diodes | Zener | Voltage-reference Zeners | BZT52C3V3 |
| Diodes | TVS & ESD | Transient and ESD protection diodes/arrays | SMBJ5.0A, USBLC6-2SC6 |
| Diodes | Bridge Rectifiers | Full-wave bridges | MB10S |
| Transistors | MOSFETs | N- and P-channel, single or dual | AO3400A, SI2301 |
| Transistors | BJTs | NPN/PNP, digital (pre-biased), RF | MMBT3904, DTC114E |
| Transistors | IGBTs | Insulated-gate bipolar transistors | IKW40N120 |
| LED | Indicator | Single-colour indicator LEDs | 0603 red LED |
| LED | RGB & Addressable | RGB and smart LEDs | WS2812B |
| LED | Lighting | High-power white/colour LEDs | 3030 white |
| Optoelectronics | Optocouplers | Transistor/logic output optocouplers | PC817, 6N137 |
| Optoelectronics | IR Emitters & Receivers | IR LEDs, IR receiver modules | TSOP38238 |
| Optoelectronics | Photodetectors | Photodiodes, phototransistors, LDRs | BPW34 |
| Crystals & Oscillators | Crystals | Passive quartz crystals | 8 MHz 3225, 32.768 kHz |
| Crystals & Oscillators | Oscillators | Active oscillators (XO, TCXO, MEMS) | SiT8008 |
| Crystals & Oscillators | Resonators | Ceramic resonators | CSTNE16M0V |
| Integrated Circuits | Microcontrollers | MCUs (any architecture) | STM32F103C8T6 |
| Integrated Circuits | Processors, SoC & FPGA | MPUs, SoCs, FPGAs, CPLDs | RP2040, iCE40 |
| Integrated Circuits | Memory | Flash, EEPROM, SRAM, FRAM | W25Q64JV, AT24C02 |
| Integrated Circuits | Amplifiers & Comparators | Op-amps, instrumentation, audio amps, comparators | LM358, LM393 |
| Integrated Circuits | Data Converters | ADC, DAC, digital potentiometers | ADS1115 |
| Integrated Circuits | Interface | USB-UART, CAN, RS-485, Ethernet PHY, transceivers | CH340C, MAX3485 |
| Integrated Circuits | Logic & Level Shifters | Gates, buffers, flip-flops, level translators, IO expanders | 74HC595, TXS0108E |
| Integrated Circuits | Analog Switches & Mux | Analog switches, multiplexers | CD4051 |
| Integrated Circuits | Drivers | Motor, gate, LED and display drivers | DRV8833, IR2104 |
| Integrated Circuits | Clock & Timing | Clock buffers, PLLs, RTC, timers | DS3231, NE555 |
| Integrated Circuits | Sensor Interface & Audio Codecs | AFEs, codecs, touch controllers | ES8388 |
| Integrated Circuits | Supervisors & Isolators | Reset supervisors, watchdogs, digital isolators | TPS3839, ISO7721 |
| Power | Linear Regulators (LDO) | LDOs and linear regulators | AMS1117-3.3 |
| Power | Switching Regulators | Buck, boost, buck-boost ICs and controllers | MP1584EN |
| Power | Battery Chargers & Management | Chargers, protection, fuel gauges | TP4056, DW01A |
| Power | Power Switches & Ideal Diodes | Load switches, eFuses, OR-ing controllers | TPS22918 |
| Power | Voltage References | Precision references | TL431, REF3033 |
| Power | Power Modules | Board-mount AC-DC and DC-DC modules | HLK-PM01 |
| Power | PMICs | Multi-rail power management ICs | AXP192 |
| Sensors | Temperature & Humidity | IC sensors, NTC/PTC, RTD | SHT31, NTC 10k |
| Sensors | Motion & IMU | Accelerometers, gyros, magnetometers | MPU6050 |
| Sensors | Current & Power | Current/power monitor ICs and Hall sensors | INA219, ACS712 |
| Sensors | Pressure & Gas | Barometric, pressure, gas | BMP280 |
| Sensors | Optical & Biometric | Light, proximity, colour, SpO2/heart-rate | MAX30102 |
| RF & Wireless | Wireless Modules | Certified radio modules | ESP32-WROOM-32E |
| RF & Wireless | Transceiver ICs | Radio ICs and receivers | nRF24L01P, SX1278 |
| RF & Wireless | Antennas | Chip, PCB-mount, external antennas | 2.4 GHz chip antenna |
| RF & Wireless | RF Components | Baluns, RF filters, RF switches, LNAs, shields | 2450BM14A |
| Connectors | Pin Headers | Male pin headers, any pitch | 2.54 mm 1×4 |
| Connectors | Female Headers & Sockets | Female headers, IC sockets | 2.54 mm 1×8 F |
| Connectors | Wire-to-Board | JST and similar housings | JST XH 2P |
| Connectors | Terminal Blocks | Screw, spring, pluggable terminals | KF301-2P |
| Connectors | USB | USB A/B/Micro/C receptacles | USB4105-GF-A |
| Connectors | Power & Audio Jacks | Barrel and audio jacks | DC-005, PJ-320A |
| Connectors | FFC / FPC | Flat flex connectors | 0.5 mm 24P |
| Connectors | RF Coaxial | SMA, U.FL, MMCX | U.FL-R-SMT |
| Connectors | Board-to-Board & Card Edge | Mezzanine, card edge | M.2 edge |
| Connectors | Card Sockets | microSD, SIM | TF-01A |
| Connectors | Modular Jacks | RJ45/RJ11, with or without magnetics | HR911105A |
| Switches | Tactile & Pushbutton | Tactile and panel push switches | TS-1187A |
| Switches | Slide, DIP & Rocker | Slide, DIP, toggle, rocker | SS12D00 |
| Switches | Other Switches | Reed, limit, rotary encoders | EC11 |
| Electromechanical | Relays | Signal, power and solid-state relays | SRD-05VDC-SL-C |
| Electromechanical | Audio Transducers | Buzzers, speakers, microphones | MLT-8530 |
| Electromechanical | Motors & Fans | Board-mounted motors and fans | Coin vibration motor |
| Protection | Fuses & PTC | Fuses and resettable PTCs | 1206L050 |
| Protection | Fuse Holders | Clips and holders | 5×20 holder |
| Protection | Varistors & GDT | MOVs, gas discharge tubes | 14D471K |
| Displays | Display Modules | LCD, OLED, e-paper, 7-segment | SSD1306 0.96" |
| Mechanical | Hardware | Mounting holes, standoffs, heatsinks, shields, light pipes | M3 mounting hole |
| Mechanical | Batteries & Holders | Cells and holders | CR2032 holder |
| Board Features | Test Points & Jumpers | Test points, solder jumpers, net ties | TP 1.5 mm |
| Board Features | Fiducials & Logos | Fiducials, logos, graphics | 1 mm fiducial |
| Modules | Development & Breakout Modules | Pre-made boards placed as one part | Arduino Nano footprint |
| Miscellaneous | Unclassified (Review) | Temporary holding area; must be emptied weekly | — |

### Classification procedure

Every part is classified with the same flow: the default answer is always an existing subtype, and a new one is only proposed after the five gates pass.

_(diagram in the original document)_

In words, for each part:

1. **Read the datasheet** and write its primary function in one sentence ("regulates 5 V down to 3.3 V").
2. **Not a purchased part** (test point, fiducial, logo, solder jumper)? → *Board Features*.
3. **A finished module** placed as one part? → *RF & Wireless / Wireless Modules* if it is a radio, else *Modules*.
4. **Pick the Type** by function or classic family from the tree.
5. **Check each subtype's *****What goes here*****.** One fits → assign it. Two fit → apply the tie-breaks. None fits → go to the five gates in *Creating a new category*.
6. **Gates fail** → closest subtype, or *Miscellaneous / Unclassified (Review)* if unsure. **Gates pass** → propose a new subtype for approval.
7. **Fill the required parameters** and the Description pattern before import.

### Creating a new category

A new subtype is created only when the classification procedure ends with "no fit" **and** all five gates below pass. Otherwise the part goes into the closest existing subtype.

**Gates (all must pass)**

1. **No fit:** the part's primary function matches no existing subtype's *What goes here*, even broadly read.
2. **Volume:** at least 5 parts of this kind exist now or are expected within 6 months. Fewer → closest subtype, or *Miscellaneous / Unclassified (Review)* while deciding.
3. **Different selection:** engineers choose these parts by different key parameters than the closest subtype (e.g. RF parts by frequency and gain, not by supply voltage).
4. **No overlap:** the new subtype's scope sentence does not cover any part already in another subtype.
5. **Not a parameter:** the difference is not package, value, rating, polarity, channel count, mounting or brand.

**Where it goes**

- Put the new subtype under the existing Type that matches the part's family or function.
- Create a new **Type** only when no Type fits AND at least 3 subtypes are planned under it. A new one-subtype Type is not allowed (Celestial has several, such as Video and Signal; avoid this). Displays, Modules and Miscellaneous are fixed exceptions because they are distinct families readers look for by name.

**When a subtype grows too big**

Split a subtype only when it passes 300 parts **and** engineers always filter it first by the same property. Prefer saved searches and parametric filters before splitting; splitting is the last resort.

**Merging and retiring**

- A subtype with fewer than 3 parts after 12 months is merged into its nearest sibling (Preferences → Component Types → Merge; this cannot be undone, so record it in the change log first).
- A category is never deleted while any component revision uses it.

**How to add it**

1. Write the row: Type, Subtype, *What goes here* (one sentence), 2 examples.
2. Add it to the table in *Default category tree* and to the change log.
3. Create it in Altium: Preferences → Data Management → Component Types → Add (Subtype under the parent).
4. Link a component template and default folder with the same name.

### Naming conventions

Names are short, plural, Title Case and use supplier (Digi-Key / LCSC) wording so parts are easy to cross-reference.

**Types and subtypes**

- Plural nouns: `Resistors`, `Connectors`. Exceptions: established names (`LED`, `Power`, `Mechanical`).
- Title Case, words joined with `&` where two things share a subtype: `Tactile & Pushbutton`.
- Abbreviations only when universal: LED, USB, LDO, MCU, ADC, DAC, RF, EMI, IMU, PTC, TVS, ESD, FFC, FPC, SoC, FPGA, PMIC.
- No package, value, brand, rating or polarity in a category name: never `Resistors 0603`, `MOSFET N-Ch`, `Yageo`.
- Maximum 32 characters; no slashes (`/` separates Type and Subtype in the `Category` parameter).

**Components**

| Field | Rule | Example |
|---|---|---|
| Item ID | Automatic from the naming scheme; never the MPN | CMP-RES-00012 |
| Name | Exact MPN as the manufacturer writes it | RC0603FR-0710KL |
| Description | `<KIND> <key specs> <package>`, fixed order per type, under 256 characters | RES 10k 1% 0.1W 0603 |
| Comment | Value or short part name shown on schematic | 10k |

**Description patterns by type** (key specs in this order)

- Resistors: `RES <value> <tolerance> <power> <package>`
- Capacitors: `CAP <value> <voltage> <dielectric/tech> <package>`
- Inductors: `IND <value> <current> <DCR> <size>`
- Diodes: `DIODE <kind> <voltage> <current> <package>`
- Transistors: `MOSFET N-CH <Vds> <Id> <package>` / `BJT NPN <Vce> <Ic> <package>`
- ICs and Power: `<function> <key spec> <package>` e.g. `LDO 3.3V 1A SOT-223`, `MCU ARM-M3 64K LQFP-48`
- Connectors: `CONN <kind> <pitch> <rows×pins> <orientation>` e.g. `CONN HEADER 2.54mm 1x4 VERT`

**These are ALWAYS parameters, never categories**

Package/case · value · tolerance · voltage · current · power · dielectric · polarity/channel (N/P, NPN/PNP) · single/dual/quad · mounting (SMD/THT) · pitch · pin count · orientation · frequency · manufacturer · supplier · lifecycle · RoHS.

### Required parameters

Every component carries 25 common parameters plus the electrical parameters of its subtype; the full standard lives in the Parameters tab: Simul

- **Common set:** identity, sourcing (`Manufacturer 1`, `Manufacturer Part Number 1`, `Supplier 1`, `Supplier Part Number 1`, LCSC Part Number, `DigiKey Part Number`, `Mouser`` Part Number`), physical, compliance and verification.
- **Electrical set:** required and optional parameters for each of the 89 subtypes, which become each subtype's component template.
- **Value format:** SI prefix and unit symbol, no spaces (`10k`, `100nF`, `50V`); unknown values stay empty.

### Edge cases and tie-breaks

When a part could sit in two places, apply these tie-breaks in order; the first that decides wins.

1. **Primary function in OUR circuits beats construction.** A comparator is chosen like an op-amp → *Amplifiers & Comparators*, not Logic.
2. **A part that converts or regulates power goes to Power**, even if it is an IC. Everything else that is an IC goes to *Integrated Circuits*.
3. **A finished, certified module goes to its function's module subtype**, not to its main chip: ESP32-WROOM → *RF & Wireless / Wireless Modules*, not Microcontrollers.
4. **A protection part goes by its technology:** TVS/ESD diodes → *Diodes / TVS & ESD*; fuses, PTCs, varistors → *Protection*.
5. **A sensor IC goes to Sensors; a bare sensing element follows its family:** NTC thermistor → *Sensors / Temperature & Humidity*; photodiode → *Optoelectronics / Photodetectors*.
6. **Still undecided:** put it in *Miscellaneous / Unclassified (Review)* and decide at the weekly review. Never create a category to avoid deciding.

**Worked examples**

| Part | Looks like | Goes to | Rule |
|---|---|---|---|
| LM393 | Logic (digital output) | Integrated Circuits / Amplifiers & Comparators | Tie-break 1 |
| AMS1117-3.3 | IC | Power / Linear Regulators (LDO) | Tie-break 2 |
| ESP32-WROOM-32E | Microcontroller | RF & Wireless / Wireless Modules | Tie-break 3 |
| USBLC6-2SC6 | IC (6-pin) | Diodes / TVS & ESD | Tie-break 4 |
| AO3400A vs SI2301 | Two subtypes (N vs P) | Transistors / MOSFETs, Polarity parameter | Polarity is a parameter |
| CL10B104KB8NNNC vs 0805 version | Two subtypes by size | Capacitors / Ceramic (MLCC), Package parameter | Package is a parameter |
| WS2812B | LED or driver IC | LED / RGB & Addressable | Primary use is a light source |
| TP4056 module board | Charger IC | Modules / Development & Breakout Modules | Tie-break 3 |
| Solder jumper | Connector | Board Features / Test Points & Jumpers | Not a purchased part |

### AI agent instructions

An AI agent classifying parts follows the rules below exactly and never invents data; anything it cannot confirm from a datasheet or the user is left blank and flagged.

```
ROLE: You classify electronic components into this library's category tree
      and prepare their parameters for the Altium Library Importer.

INPUT: an MPN (+ optional datasheet URL or text).

STEPS
1. Identify the part from its datasheet. If you cannot find or open a
   datasheet, set status = NEEDS_DATASHEET and stop.
2. Decide PRIMARY FUNCTION in one sentence.
3. Pick Type, then Subtype, from the Default category tree table ONLY.
   Match against each subtype's "What goes here" text.
4. If two subtypes fit, apply the tie-breaks 1-6 in order.
5. If none fits, do NOT create a category. Set
   category = "Miscellaneous/Unclassified (Review)" and fill
   proposed_category with a full proposal (Type, Subtype, scope sentence,
   which of the 5 gates pass and why).
6. Fill parameters: the common set + the subtype's Required electrical
   parameters from the Parameters tab, names and value format exactly.
   Values only from the datasheet. Unknown = empty, never guessed.
7. Build Description with the Type's pattern from Naming conventions.

HARD RULES
- Category names: copy exactly from the table; never paraphrase.
- Never put package, value, rating, polarity, channel count, mounting,
  pitch or brand into a category.
- Name = exact MPN. Item ID is not set (automatic).
- One part = one category. One part = one Part Choice (itself).
- Supplier part numbers only from the supplier's own page; else empty.
- Confidence < 0.8 on the category -> status = REVIEW.

OUTPUT: one row per part in the CSV format below (or JSON, same keys).
```

**Output format**

```
Name,Description,Category,Manufacturer 1,Manufacturer Part Number 1,Supplier 1,Supplier Part Number 1,LCSC Part Number,DigiKey Part Number,Mouser Part Number,Package,Mounting,Datasheet URL,Status,Confidence,Reason,Proposed Category
AMS1117-3.3,LDO 3.3V 1A SOT-223,Power/Linear Regulators (LDO),Advanced Monolithic Systems,AMS1117-3.3,,,,,,SOT-223,SMD,https://...,OK,0.95,Fixed linear regulator; tie-break 2,
```

A JSON version has the same keys in camelCase. `Status` is one of `OK`, `REVIEW`, `NEEDS_DATASHEET`. A human approves every `REVIEW` row and every `Proposed Category` before import.

### Governance and change log

The library owner approves every category change; the tree changes at most once a month so imports and templates stay stable.

- **Weekly:** empty *Miscellaneous / Unclassified (Review)*: classify each part or approve a new category.
- **Monthly:** apply approved category changes in Altium and update this document in the same session.
- **Every change** gets a row below before it is made in Altium. Merges cannot be undone, so they are never done without a row.

| Date | Change | Reason | By |
|---|---|---|---|
| 2026-11-02 | v1.0 tree: 22 Types, 89 Subtypes, adapted from Celestial | Initial standard | Simul |
| 2026-11-02 | Merge existing Mechanical and Mechanicals into Mechanical | Duplicate types from earlier import | Simul |
| 2026-11-02 | Parameter standard v1.0 added (Parameters tab): 23 common parameters, electrical sets for all 89 subtypes | Multi-supplier company use; draft reviewed | Simul |
| 2026-11-02 | Symbols, Footprints & 3D rules v1.0 added (SYM-, FP-, 3D- rule IDs), style values measured from Celestial | Consistent look across the library; datasheet first | Simul |
| 2026-11-02 | Symbols, Footprints & 3D v1.1: review fixes (polarity table, footprint naming, EP paste, pin types, MCU pin names, origins, shared 3D models, verification process); Parameters: Datasheet Revision and Package Drawing added (25 common), ASCII u for micro | External review of v1.0 | Simul |

**Improvements over the Celestial tree in v1.0**

- Package and size moved from categories to parameters (Celestial: 16 package-size tables for resistors and capacitors).
- MOSFET N/P and single/array splits replaced by one *MOSFETs* subtype with Polarity and Channels parameters.
- One-subtype Types (Controller, Current, Signal, Video) folded into existing Types.
- Overlaps removed: signal buffers live only in *Logic & Level Shifters*; comparators only in *Amplifiers & Comparators*.
- Added what Celestial lacks: Supercapacitors, IGBTs, RGB & Addressable LEDs, PMICs, Board Features, Modules, and a Review holding area.

## Part 2. Parameter Standard

Every component carries 25 common parameters in five groups (identity, sourcing, physical, compliance, verification) plus the electrical parameters of its subtype. Names follow Altium's own supplier-link conventions so the Library Importer, ActiveBOM and BOM outputs read them without remapping.

### Review of the draft

The draft's core is standard; the changes below fix scope, naming and gaps that would hurt multi-supplier company use.

| Draft item | Verdict | Change |
|---|---|---|
| `Category` → Parameter Grouping in the importer | Correct, but import-only | Use it only in source libraries. After import Altium stores the type in its own `ComponentType` system parameter, so map `Category` to `<Skip>` to avoid a duplicate. |
| `Manufacturer 1`, `Manufacturer Part Number 1`, `Supplier 1`, `Supplier Part Number 1` | Standard | These are the names Altium's Part Choice Mapping recognises. Keep exactly. |
| `LCSC Part #` | Custom, useful | Renamed `LCSC Part Number` (no symbols in names). Kept even when LCSC is also `Supplier 1`, because JLCPCB assembly BOMs need it as its own column. |
| `Package` | Standard | Split into `Package` (EIA/JEDEC name, e.g. 0603, SOT-23) and `Package Metric` (e.g. 1608) for chip passives, so 0603 imperial and 0603 metric are never confused. |
| `Mounting` | Standard | Values fixed to `SMD`, `THT`, `Press-fit`, `Chassis`. |
| `Datasheet` | Standard | Renamed `Datasheet URL`: a link to the manufacturer's own PDF, never a distributor copy. |
| `Verified By`, `Verified Date` | Custom, useful | Kept. Verification status itself goes in the Workspace lifecycle state, not a parameter. |
| Missing | Gap | Added `Operating Temperature`, `Height`, `Pin Count`, `RoHS`, `MSL`, `Footprint Standard`, `LCSC Part Number, DigiKey Part Number, Mouser Part Number`, `Local Source`. |

### Common parameters

All 25 are present on every component; *Required* ones must have a value before import, *If applicable* ones are left empty only when they truly do not apply.

Altium fills its own system fields (Item ID, Revision, Lifecycle state, ComponentType). Never create parameters with those names.

| Group | Parameter | Need | Format | Example |
|---|---|---|---|---|
| Identity | Description | Required | Pattern from *Naming conventions*, ≤ 256 characters | RES 10k 1% 0.1W 0603 |
| Identity | Comment | Required | Text shown on the schematic | 10k |
| Identity | Category | Import only | `Type/Subtype` exactly as the tree | Resistors/Chip |
| Sourcing | Manufacturer 1 | Required | Manufacturer's short official name | Yageo |
| Sourcing | Manufacturer Part Number 1 | Required | Exact orderable MPN, incl. packaging suffix | RC0603FR-0710KL |
| Sourcing | Supplier 1 | Required | Production distributor (where the company orders) | LCSC |
| Sourcing | Supplier Part Number 1 | Required | That distributor's part number | C12345 (illustrative) |
| Sourcing | LCSC Part Number | Required if stocked | LCSC/JLCPCB number for this exact MPN | C12345 (illustrative) |
| Sourcing | DigiKey Part Number | Required if stocked | DigiKey's own part number for this exact MPN | 311-10.0KHRCT-ND (illustrative) |
| Sourcing | Mouser Part Number | Required if stocked | Mouser's own part number for this exact MPN | 603-RC0603FR-0710KL (illustrative) |
| Sourcing | Local Source | If applicable | Local market shop or note | Shop name, Dhaka |
| Sourcing | Datasheet URL | Required | Manufacturer's PDF link | https://… |
| Sourcing | Datasheet Revision | Required | Revision and date printed on the datasheet | Rev. 2.1, 2025-03 |
| Sourcing | Package Drawing | Required | Document and page the footprint was built from | Datasheet p.42, or package drawing DBV0005A |
| Physical | Package | Required | EIA/JEDEC name | 0603, SOT-23-3, LQFP-48 |
| Physical | Package Metric | Chip passives only | Metric size code | 1608 |
| Physical | Mounting | Required | SMD / THT / Press-fit / Chassis | SMD |
| Physical | Pin Count | Required | Integer, incl. exposed pad | 3 |
| Physical | Height | Required | Max seated height, mm | 0.55mm |
| Physical | Footprint Standard | Required | IPC-7351 density or Manufacturer | IPC-7351B Nominal |
| Compliance | Operating Temperature | Required | Min to max, °C | -55°C to 155°C |
| Compliance | RoHS | Required | Compliant / Non-compliant / Unknown | Compliant |
| Compliance | MSL | SMD ICs and LEDs | JEDEC level 1 to 6 | 3 |
| Verification | Verified By | Required after check | Initials | SA |
| Verification | Verified Date | Required after check | YYYY-MM-DD | 2026-11-02 |

**Why these were added**

- **Height** feeds 3D clearance checks and enclosure design.
- **Footprint Standard** tells reviewers whether a land pattern came from IPC-7351 or the manufacturer's recommendation.
- **MSL** and **Operating Temperature** are what assembly houses and medical/industrial customers ask for first.
- **Pin Count** lets the BOM and footprint checks catch a wrong package variant.

### Manufacturer and supplier rules

One component has one manufacturer, one production supplier and fixed LCSC, DigiKey and Mouser part numbers; live price and stock are never typed in, because Altium fetches them for the MPN from every enabled supplier.

- **Manufacturer stays ****`1`****.** One component = one MPN, so only `Manufacturer 1` / `Manufacturer Part Number 1` exist. The `1` suffix is kept because Altium's importer looks for it.
- **Supplier 1 = the production source** (where the company actually orders). The Library Importer builds the Part Choice from `Supplier 1` / `Supplier Part Number 1` only, so this pair must always be filled and correct.
- **Distributor numbers have their own parameters.** LCSC Part Number, DigiKey Part Number and Mouser Part Number are filled wherever that distributor stocks the exact MPN, even when it is not Supplier 1. They give BOM exports, quote requests and JLCPCB orders ready-made columns and work offline; inside the Workspace, live price and stock still come automatically.
- **Never store price, stock, MOQ or lead time as parameters.** They go stale; ActiveBOM shows them live.
- **Different manufacturer = different component.** An alternate brand is a new component with its own MPN, never a `Manufacturer 2` on the old one.

**Approved names (controlled values)**

| Parameter | Allowed values |
|---|---|
| Supplier 1 | LCSC, DigiKey, Mouser, Farnell, TME, Arrow |
| Manufacturer 1 | The manufacturer's own short name as on its datasheet cover: Texas Instruments, STMicroelectronics, Yageo, Samsung Electro-Mechanics, Murata, Nexperia, onsemi |
| Local Source | Free text: shop name and city |

Add a new supplier or manufacturer spelling to this table before using it; `TI`, `Texas Inst.` and `Texas Instruments` as three spellings break BOM grouping and search.

The suppliers Altium searches are enabled centrally in the Workspace's part source settings; keep that list equal to the approved list above.

### Value and naming rules

Values are written so Altium's unit-aware parameter types can convert them; a value it cannot parse fails the import check *Invalid parameter value*.

**Parameter names**

- Title Case, spelled out, no units in the name: `Voltage Rating`, not `Voltage(V)`. The unit belongs to the template's data type.
- Exception: a condition that changes meaning stays in the name: `Impedance @ 100MHz`, `Rds On @ 4.5V`.
- No symbols except `@`: `LCSC Part Number`, not `LCSC Part #`.
- One name per meaning across all Types: always `Voltage Rating` for a maximum working voltage, whether capacitor, diode or fuse.

**Values**

| Rule | Write | Never |
|---|---|---|
| SI prefix, no space, unit symbol | `10k`, `100nF`, `4.7``u``H`, `50V` | `10 K`, `0.1uF `, `100 nano` |
| u for micro, ASCII only | `4.7``u``F` | `4.7``µF, 4.7``mfd` |
| Decimal point, no trailing zeros | `2.2``u``F` | `2,2``u``F`, `2.20``u``F` |
| Ranges with "to" | `-40°C to 85°C`, `2.7V to 5.5V` | `-40~85` |
| Tolerance as ± percent | `1%` | `F`, `±1 %` |
| One value per parameter | `Channels` = `2` | `2 (dual)` |
| Unknown = empty | *(blank)* | `N/A`, `-`, `TBD` |

**Where values come from**

Every electrical value is copied from the manufacturer's datasheet at its stated test condition. Distributor listings are only a cross-check. If two datasheet tables disagree, use the more conservative value and note it in the component's revision notes.

### Electrical parameters by subtype

Each subtype's component template holds its *Required* parameters as mandatory, unit-aware fields; *Optional* ones are added when the datasheet gives them and they matter for selection. Parameters repeated across subtypes keep one name everywhere.

| Type | Subtype | Required | Optional |
|---|---|---|---|
| Resistors | Chip | Resistance, Tolerance, Power Rating, Temperature Coefficient | Voltage Rating, Composition (thick/thin film) |
| Resistors | Through-Hole | Resistance, Tolerance, Power Rating, Composition | Temperature Coefficient, Voltage Rating |
| Resistors | Current Sense | Resistance, Tolerance, Power Rating, Temperature Coefficient | Terminals (2 or 4-wire Kelvin) |
| Resistors | Arrays & Networks | Resistance, Tolerance, Power Rating per Element, Elements, Circuit Type (isolated/bussed) | Temperature Coefficient |
| Resistors | Potentiometers & Trimmers | Resistance, Tolerance, Power Rating, Taper, Turns | Adjustment Direction |
| Capacitors | Ceramic (MLCC) | Capacitance, Voltage Rating, Dielectric (X7R, X5R, C0G), Tolerance | Grade (automotive) |
| Capacitors | Ceramic RF | Capacitance, Voltage Rating, Dielectric, Tolerance, Q @ Frequency | Self-Resonant Frequency |
| Capacitors | Aluminum Electrolytic | Capacitance, Voltage Rating, Tolerance, ESR, Ripple Current, Lifetime @ Temperature | Diameter, Lead Spacing |
| Capacitors | Aluminum Polymer | Capacitance, Voltage Rating, Tolerance, ESR, Ripple Current, Lifetime @ Temperature | Leakage Current |
| Capacitors | Tantalum | Capacitance, Voltage Rating, Tolerance, ESR, Construction (MnO2/polymer) | Case Code |
| Capacitors | Film | Capacitance, Voltage Rating (AC and DC), Tolerance, Dielectric Material, Safety Class (X1/X2/Y1/Y2) | Lead Spacing |
| Capacitors | Supercapacitors | Capacitance, Voltage Rating, ESR, Lifetime @ Temperature | Leakage Current |
| Inductors | Power | Inductance, Tolerance, Current Rating, Saturation Current, DCR, Shielding | Self-Resonant Frequency |
| Inductors | RF | Inductance, Tolerance, Current Rating, Q @ Frequency, Self-Resonant Frequency, DCR | Core Material |
| Inductors | Arrays & Coupled | Inductance, Current Rating, Saturation Current, DCR, Windings | Coupling Factor |
| Filters & EMI | Ferrite Beads | Impedance @ 100MHz, Current Rating, DCR | Lines |
| Filters & EMI | Common Mode Chokes | Common Mode Impedance @ Frequency, Current Rating, DCR, Lines | Differential Mode Impedance |
| Filters & EMI | EMI Filters | Filter Type, Capacitance or Inductance, Current Rating, Voltage Rating | Insertion Loss |
| Diodes | Rectifier & Schottky | Diode Type (standard/fast/Schottky/switching), Reverse Voltage, Forward Current, Forward Voltage @ If | Reverse Recovery Time, Reverse Leakage @ Vr, Configuration |
| Diodes | Zener | Zener Voltage, Tolerance, Power Rating, Zener Impedance | Test Current |
| Diodes | TVS & ESD | Reverse Standoff Voltage, Breakdown Voltage, Clamping Voltage, Peak Pulse Power, Directionality (uni/bi), Channels | Capacitance |
| Diodes | Bridge Rectifiers | Reverse Voltage, Forward Current, Forward Voltage @ If | Surge Current |
| Transistors | MOSFETs | Polarity (N/P), Channels, Drain-Source Voltage, Drain Current, Rds On @ Vgs, Gate Threshold Voltage | Gate Charge, Input Capacitance, Power Dissipation |
| Transistors | BJTs | Polarity (NPN/PNP), Transistor Type (general/digital/RF), Collector-Emitter Voltage, Collector Current, hFE @ Ic, Power Dissipation | Built-in Resistors (R1/R2), Transition Frequency |
| Transistors | IGBTs | Collector-Emitter Voltage, Collector Current, Vce Sat, Power Dissipation | Built-in Diode, Short-Circuit Withstand Time |
| LED | Indicator | Colour, Wavelength, Forward Voltage @ If, Forward Current, Luminous Intensity | Viewing Angle |
| LED | RGB & Addressable | Colours, Protocol (e.g. WS2812), Supply Voltage, Current per Channel | Refresh Rate |
| LED | Lighting | Colour or CCT, Luminous Flux, Forward Voltage @ If, Forward Current, CRI | Viewing Angle, Thermal Resistance |
| Optoelectronics | Optocouplers | Output Type, Channels, Isolation Voltage, Current Transfer Ratio, Collector-Emitter Voltage | Data Rate, Rise and Fall Time |
| Optoelectronics | IR Emitters & Receivers | Function, Wavelength, Carrier Frequency (receivers), Supply Voltage or Forward Current | Viewing Angle, Radiant Intensity |
| Optoelectronics | Photodetectors | Detector Type, Peak Wavelength, Spectral Range, Dark Current | Active Area |
| Crystals & Oscillators | Crystals | Frequency, Load Capacitance, Frequency Tolerance, Frequency Stability, ESR | Drive Level |
| Crystals & Oscillators | Oscillators | Frequency, Supply Voltage, Output Type (CMOS/LVDS…), Frequency Stability, Supply Current | Enable Function |
| Crystals & Oscillators | Resonators | Frequency, Frequency Tolerance, Built-in Capacitors | Frequency Stability |
| Integrated Circuits | Microcontrollers | Core, Max Clock Frequency, Flash, RAM, Supply Voltage Range, GPIO Count | Peripherals, ADC Resolution |
| Integrated Circuits | Processors, SoC & FPGA | Core or Logic Elements, Max Clock Frequency, Core Voltage, I/O Voltage | Memory Interface, Embedded RAM |
| Integrated Circuits | Memory | Memory Type, Capacity, Interface, Supply Voltage Range, Clock Frequency | Endurance, Data Retention |
| Integrated Circuits | Amplifiers & Comparators | Function (op-amp/comparator/instrumentation/audio), Channels, Supply Voltage Range, Gain Bandwidth, Slew Rate, Input Offset Voltage, Output Type (rail-to-rail/open-drain/push-pull) | Quiescent Current, Noise Density, Output Power (audio) |
| Integrated Circuits | Data Converters | Function (ADC/DAC/digital pot), Resolution, Channels, Sample Rate, Interface, Supply Voltage Range | Reference Type, INL |
| Integrated Circuits | Interface | Protocol, Function (transceiver/bridge/PHY), Channels, Data Rate, Supply Voltage Range | ESD Rating, Isolation |
| Integrated Circuits | Logic & Level Shifters | Logic Function, Logic Family, Bits, Supply Voltage Range, Output Type | Propagation Delay |
| Integrated Circuits | Analog Switches & Mux | Configuration (e.g. SPDT, 8:1), Channels, On-Resistance, Supply Voltage Range | Bandwidth |
| Integrated Circuits | Drivers | Driver Type (motor/gate/LED/display), Channels, Output Current, Supply Voltage Range, Interface | Rds On, Protection Features |
| Integrated Circuits | Clock & Timing | Function (RTC/timer/PLL/buffer), Frequency, Supply Voltage Range, Interface | Accuracy, Battery Backup |
| Integrated Circuits | Sensor Interface & Audio Codecs | Function, Resolution, Channels, Interface, Supply Voltage Range | Sample Rate |
| Integrated Circuits | Supervisors & Isolators | Function, Threshold Voltage or Isolation Voltage, Channels, Supply Voltage Range | Reset Timeout, Data Rate |
| Power | Linear Regulators (LDO) | Output Type (fixed/adjustable), Output Voltage, Output Current, Input Voltage Max, Dropout Voltage @ Iout, Quiescent Current | PSRR, Enable Pin |
| Power | Switching Regulators | Topology (buck/boost/buck-boost), Input Voltage Range, Output Voltage, Output Current, Switching Frequency, Integrated Switch | Efficiency, Quiescent Current |
| Power | Battery Chargers & Management | Function, Battery Chemistry, Cells, Charge Current, Charge Voltage, Input Voltage Range | Interface, Protection Features |
| Power | Power Switches & Ideal Diodes | Function, Channels, Input Voltage Range, Output Current or Current Limit, Rds On | Quick Discharge |
| Power | Voltage References | Reference Type (series/shunt), Output Voltage, Initial Accuracy, Temperature Coefficient, Output Current | Noise |
| Power | Power Modules | Conversion (AC-DC/DC-DC), Input Voltage Range, Output Voltage, Output Power, Isolation Voltage | Efficiency |
| Power | PMICs | Outputs, Input Voltage Range, Output Voltages, Output Currents, Interface | Charger Included |
| Sensors | Temperature & Humidity | Sensor Type, Measured Quantity, Range, Accuracy, Interface or Output, Supply Voltage Range | Resistance @ 25°C and B Value (NTC) |
| Sensors | Motion & IMU | Axes, Acceleration Range, Gyro Range, Resolution, Interface, Supply Voltage Range | Output Data Rate |
| Sensors | Current & Power | Sensing Method (shunt/Hall), Current Range, Accuracy, Interface or Output, Supply Voltage Range | Isolation Voltage |
| Sensors | Pressure & Gas | Measured Quantity, Range, Accuracy, Interface, Supply Voltage Range | Response Time |
| Sensors | Optical & Biometric | Measured Quantity, Wavelengths, Interface, Supply Voltage Range | Range |
| RF & Wireless | Wireless Modules | Protocol, Frequency Band, Output Power, Sensitivity, Interface, Supply Voltage Range, Antenna (integrated/external), Certifications | Core Chip, Flash |
| RF & Wireless | Transceiver ICs | Protocol or Modulation, Frequency Band, Output Power, Sensitivity, Interface, Supply Voltage Range | Data Rate |
| RF & Wireless | Antennas | Antenna Type, Frequency Band, Gain, Impedance | VSWR |
| RF & Wireless | RF Components | Function, Frequency Range, Impedance, Insertion Loss | Gain, Isolation |
| Connectors | Pin Headers | Pitch, Positions, Rows, Orientation, Current Rating | Contact Plating, Mating Length |
| Connectors | Female Headers & Sockets | Pitch, Positions, Rows, Orientation, Current Rating | Contact Plating |
| Connectors | Wire-to-Board | Series, Pitch, Positions, Gender, Orientation, Current Rating | Wire Gauge Range |
| Connectors | Terminal Blocks | Pitch, Positions, Current Rating, Voltage Rating, Wire Gauge Range | Pluggable |
| Connectors | USB | USB Type, Gender, Orientation, Positions, Current Rating | USB Version |
| Connectors | Power & Audio Jacks | Jack Type, Positions or Pin Diameter, Current Rating, Voltage Rating, Orientation | Switched Contacts |
| Connectors | FFC / FPC | Pitch, Positions, Contact Side, Locking Type, Orientation | Current Rating |
| Connectors | RF Coaxial | Connector Type, Impedance, Max Frequency, Gender, Orientation | Mated Height |
| Connectors | Board-to-Board & Card Edge | Pitch, Positions, Gender, Mated Height, Current Rating | Rows |
| Connectors | Card Sockets | Card Type, Ejection Type, Card Detect | Orientation |
| Connectors | Modular Jacks | Jack Type, Positions, Magnetics, Speed, Orientation | LEDs |
| Switches | Tactile & Pushbutton | Circuit, Contact Rating, Operating Force, Actuator Height | Illumination |
| Switches | Slide, DIP & Rocker | Circuit (e.g. SPDT), Positions, Contact Rating | Actuator Type |
| Switches | Other Switches | Switch Type, Contact Rating, Pulses per Revolution (encoders), Detents | Integrated Push Switch |
| Electromechanical | Relays | Relay Type (signal/power/solid-state), Coil Voltage, Coil Current, Contact Form, Contact Rating | Isolation Voltage |
| Electromechanical | Audio Transducers | Transducer Type, Drive (active/passive), Rated Voltage, Frequency, Sound Pressure Level | Impedance |
| Electromechanical | Motors & Fans | Rated Voltage, Rated Current, Speed | Airflow or Torque |
| Protection | Fuses & PTC | Fuse Type (fast/slow/PTC), Current Rating or Hold Current, Trip Current (PTC), Voltage Rating, Breaking Capacity | Resistance |
| Protection | Fuse Holders | Fuse Size, Current Rating, Voltage Rating | Cover |
| Protection | Varistors & GDT | Varistor or Breakdown Voltage, Max AC Voltage, Max DC Voltage, Surge Current, Energy Rating | Capacitance |
| Displays | Display Modules | Display Type, Size, Resolution, Interface, Controller, Supply Voltage Range | Colour |
| Mechanical | Hardware | Hardware Type, Size or Thread, Dimensions | Material |
| Mechanical | Batteries & Holders | Battery Size, Chemistry, Nominal Voltage, Cells | Capacity |
| Board Features | Test Points & Jumpers | Feature Type, Pad Size, Positions | Default State (jumpers) |
| Board Features | Fiducials & Logos | Feature Type, Pad Size, Mask Opening | — |
| Modules | Development & Breakout Modules | Main Chip, Function, Supply Voltage Range, Interface, Header Pitch | Dimensions |
| Miscellaneous | Unclassified (Review) | Common parameters only | — |

### Sources

Altium parameter names and import behaviour were checked against Altium's own documentation; electrical parameter names follow distributor parametric search wording.

- [Importing Existing Libraries to Your Connected Workspace](https://www.altium.com/documentation/altium-designer/components-libraries/importing-existing-libraries-workspace): Part Choice Mapping, `Supplier 1` / `Supplier Part Number 1` as the primary reference, unit-aware parameter types, reserved system parameter names, validation checks.
- [Linking to Supply Chain Data for Database and File-based Component Libraries](https://www.altium.com/documentation/altium-designer/components-libraries/linking-supply-chain-data-database-file-based): supplier links and the numbered `… 1` parameters.
- [Component Types](https://www.altium.com/documentation/altium-designer/components-libraries/component-types): types, templates and default folders.
- [Celestial Altium Library](https://github.com/issus/altium-library): category structure and per-category parametric data.

Industry references used by name, not linked here: IPC-7351B (land pattern density levels), JEDEC J-STD-020 (moisture sensitivity levels).

## Part 3. Symbols, Footprints and 3D Rules

Every symbol, footprint and 3D body is built from one fixed set of rules so all parts of a kind are correct and look identical; the datasheet wins on correctness, IPC on geometry, and Celestial only on look. Version 1.1 resolves the 2026-11-02 review: polarity, footprint naming, paste, ERC pin types, MCU pin names, origins, 3D naming and a defined verification process.

Rules have IDs (`SYM-`, `FP-`, `3D-`) so reviewers and AI agents can cite them: "fails FP-07".

### Priority order

When sources disagree, the higher one wins and the deviation is written in the component's revision notes.

1. **Manufacturer documents**: pinout, dimensions, recommended land pattern. If the product datasheet and a separate package drawing disagree, the newer revision wins; if the dates are equal, the package drawing wins. The revision and page used are recorded (`Datasheet Revision`, `Package Drawing`).
2. **This document's rules.**
3. **IPC-7351B, Nominal density**, for every geometry question the manufacturer leaves open (land pattern, courtyard, orientation).
4. **Celestial Altium Library**, only for look and layout (symbol style, text positions, layer use). Celestial's licence allows commercial use but requires attribution: our library notes credit it, and no Celestial file is copied without that credit.

**Defect or style fault**

- **Defect** (wrong pin, pad, polarity, dimension, pin type): blocks release. No waiver.
- **Style fault** (looks different from its class template): blocks release by default. The library owner may release with a logged waiver and a fix-by date of at most 30 days, only when a design is waiting on the part.

### Schematic symbol rules

A symbol is accepted only when every pin matches the datasheet by number and name, every pin type follows the table below, and its look matches the class template.

**Pin names and numbers**

| ID | Rule |
|---|---|
| SYM-01 | Pin names copy the datasheet's primary name exactly (`PA9`, `VIN`, `EN`). One transformation only: active-low markers (`/RESET`, `RESET_N`, `nRESET`, `RESET#`) become an Altium overbar (`R\E\S\E\T\`). Pin names are ASCII only: `D-`, never a Unicode minus. |
| SYM-02 | Pin numbers equal the package's pin numbers. Every datasheet pin is present, including NC pins (named `NC`, type Passive; the reference design puts a No ERC marker on them). |
| SYM-03 | Exposed and extra pads: use the datasheet number; if it gives none, the exposed pad is pin count + 1, named `EP` (`EP1`, `EP2` when several). Shield and mounting tabs are named `SH` or `MP` and numbered after the EP. All are visible pins. |
| SYM-04 | Alternate functions never go in the pin name. They go in the pin's Description field; design-specific roles are shown with net labels on the schematic. |
| SYM-05 | No hidden pins. Same-named power and ground pins (an MCU's several VSS) are all drawn as separate pins, grouped together; pins are never stacked, so the pin table maps 1:1 to the package. |

**Pin electrical types** (Altium types; the connection matrix is frozen in the project template)

| Pin | Type |
|---|---|
| Supply inputs, grounds, exposed pads tied to ground | Power |
| Regulator, reference and PMIC outputs that supply other parts | Power |
| Digital inputs, enables, resets driven by others | Input |
| Push-pull outputs | Output |
| GPIO and bidirectional pins | I/O |
| Open-drain and open-collector outputs (PG, INT, I2C) | Open Collector |
| Tri-state outputs | HiZ |
| Passives, analog pins, crystal pins, NC pins, connector pins | Passive |

The project template's ERC connection matrix is set once, tested on a fixed reference design that contains every pin type, and not changed per project.

**Layout**

| ID | Rule |
|---|---|
| SYM-10 | Pin ends sit on the 100 mil grid; graphics on a 10 mil grid. |
| SYM-11 | One symbol per function: all resistors share one symbol, all non-polarised capacitors one, and so on. Parts with the same pinout share one IC symbol. Before a shared symbol gets a new revision, a where-used check lists every component using it, and each is re-verified. |
| SYM-12 | Every 2-pin passive and diode spans 400 mil between pin ends (drawing below). |
| SYM-13 | Single-part ICs (not MCUs), up to 64 pins: left side power inputs at the top, control inputs (EN, RESET, MODE) in the middle, ground and EP at the bottom; right side outputs, top to bottom in signal-flow order. |
| SYM-14 | MCUs up to 64 pins, one part: left side power at the top, then reset, boot, clock and debug pins, then ground and EP at the bottom; right side GPIO ports in numeric order (PA0, PA1… PB0…). If the right side would run longer than 1.5× the left, the last whole port moves to the left side under the debug pins. |
| SYM-15 | Bus pins keep a fixed order using the datasheet's own names: SPI = clock, data out, data in, chip select; I2C = SCL, SDA; UART = TX, RX, RTS, CTS; USB = D+, D-. No renaming. |
| SYM-16 | Pin pitch 100 mil; a 200 mil gap separates function groups. |
| SYM-17 | ICs over 64 pins are multi-part: part A = power, ground, EP, reset, boot, clock and debug; then one part per GPIO port; other peripherals keep their pins in one part. |
| SYM-18 | Small multi-unit parts (dual op-amp, quad gate): one part per unit plus a separate power part holding V+ and V- (no hidden or part-zero power pins). The "unused sub-part" ERC check is on, so a forgotten unit is reported. |
| SYM-19 | Every non-rectangular class has one template drawn once: op-amp and comparator triangle; BJT, MOSFET and IGBT (IEEE 315 style); diode, Zener, Schottky, TVS, LED; crystal and resonator; switch; relay; transformer; connector (rectangle, pins in numeric order on one side, 100 mil pitch). |

**Text on the schematic**

| ID | Rule |
|---|---|
| SYM-20 | Positions are fixed by the template (values in the style table): passives use the 2-pin positions; ICs show the Designator 100 mil above the body's top-left corner and the Comment 100 mil below the body's bottom-left corner. |
| SYM-21 | Comment is linked to a parameter, never typed: resistors, inductors and ferrite beads show their main value (Resistance, Inductance, Impedance @ 100MHz); ICs show the Manufacturer Part Number 1. |
| SYM-22 | Capacitors show two lines: Comment = Capacitance, and the Voltage Rating parameter visible 100 mil below it (`10uF` / `25V`). |

### Symbol style values

These values live in one shared symbol template and are never changed per part; the Celestial column shows what was measured in its symbol files (capacitor, resistor, inductor, ferrite, diode, LED, op-amp, LDO, STM32 MCU).

| Item | Value | Celestial measured |
|---|---|---|
| Pin-end grid | 100 mil | 100 mil |
| Pin length, R, C, L, FB | 100 mil, body 200 mil | Same |
| Pin length, diodes and LEDs | 160 mil, body 80 mil | Same |
| Pin-end span, every 2-pin passive and diode | 400 mil | 400 mil |
| Pin length and pitch, ICs | 300 mil, 100 mil pitch | Same |
| IC body | Rectangle, width = smallest that fits pin names, in 100 mil steps | Same |
| Passive and diode graphics | Blue #0000FF, Small line | Same |
| IC body colours | Line #800000, fill #FFFFB0 | Same |
| Designator and Comment colour | Navy #000080 | Same |
| Font | Times New Roman 10 for all text, set as the document font (decided: matches Altium defaults and every Celestial part) | Same |
| Passive Designator | (−50, +50) mil | Same |
| Passive Comment | (−50, −150) mil | Same |
| Capacitor Voltage Rating line | (−50, −250) mil | Not shown |
| IC Designator | 100 mil above the body's top-left corner | Varies |
| IC Comment | 100 mil below the body's bottom-left corner | Hidden |
| Micro prefix in values | `u` (ASCII), e.g. `10uF` | — |

**Designator prefixes**

| Prefix | Parts |
|---|---|
| R / RN / RV | Resistor / resistor array / varistor |
| C, L, FB | Capacitor, inductor, ferrite bead |
| D, Q, U | Diode and LED, transistor, IC and module |
| J | Every connector, plug or receptacle (no P) |
| SW, K, T | Switch, relay, transformer |
| Y, F, BT | Crystal or oscillator, fuse, battery |
| BZ, LS, M | Buzzer, speaker, motor or fan |
| PS, JP | Power module, solder jumper |
| TP, MH, FID | Test point, mounting hole, fiducial |

**Where we differ from Celestial, deliberately**

- **Pin types:** Celestial sets every pin to Passive (all sampled symbols, even the MCU); we use the type table above so ERC finds real faults.
- **IC prefix U** instead of IC.
- **MCU pin names:** Celestial writes every alternate function into the pin name; we use the primary name only (SYM-01, SYM-04).

### Two-pin symbol template

All 2-pin passives and diodes share this geometry, so any of them can replace another on a schematic without moving a wire.

_(diagram in the original document)_

Positions are in mil from the symbol centre; the pin-end dots are the electrical connection points on the 100 mil grid.

### PCB footprint rules

A footprint is approved only after every pad's size and position, read from Altium's Properties panel, matches the manufacturer's drawing in a filled checklist.

**Standard and source**

| ID | Rule |
|---|---|
| FP-01 | The manufacturer's recommended land pattern is used whenever one is given (Celestial follows the same order). |
| FP-02 | Otherwise the pattern is calculated to IPC-7351B, Nominal density, with Altium's IPC Compliant Footprint Wizard. |
| FP-03 | Density names: IPC-7351 A/B/C became M/N/L (Most, Nominal, Least) in IPC-7351B; our "IPC B" = N. Density levels are not IPC product Classes 1 to 3. |
| FP-04 | Any deviation from the manufacturer pattern is written in the footprint description and revision notes. |
| FP-05 | IPC-7352, the newer land-pattern guideline, is reviewed before the first library import; any change it causes is logged in Governance. |

**Geometry**

| ID | Rule |
|---|---|
| FP-10 | Pad size and position, pitch and row spacing are read from the Properties panel and entered in the verification checklist next to the datasheet value, with pass/fail per pad group. |
| FP-11 | Body outline (assembly, component outline, 3D) uses the datasheet's maximum dimensions. |
| FP-12 | Origin = centre of the package body's maximum outline (moulded body, not leads or tabs) for SMD, through-hole and asymmetric packages (SOT-223, DPAK). Connectors and modules use the manufacturer's stated pick-up point when given, else body centre. The assembler receives the component reference point (origin) as the placement coordinate. |
| FP-13 | Zero orientation per IPC-7351B: pin 1 top-left for ICs, pin 1 on the left for 2-pin parts. Polarity follows the table below, and the symbol-to-footprint check compares pin names as well as numbers. |
| FP-14 | Through-hole: finished hole = maximum lead diameter + 0.2 mm (round leads) or lead diagonal + 0.2 mm (square leads), rounded up to the fab's 0.05 mm drill step; pad diameter = hole + 0.6 mm; pin 1 pad square, others round; flat leads get plated slots = lead width and thickness + 0.2 mm; non-plated pegs use the datasheet's hole, else peg diameter + 0.1 mm; inner-layer pads equal outer pads (unused ones removed by board rules); thermal relief comes from board rules. |
| FP-15 | Exposed pads: copper per datasheet. The EP pad itself gets no paste; paste is drawn as Top Paste regions: the datasheet's stencil pattern, or if none, a grid of square windows with 0.2 mm gaps covering 60% of the pad. Thermal vias are part of the footprint only when the datasheet shows them: plated holes numbered as the EP, 0.3 mm finished drill, paste windows kept 0.15 mm clear of them. |
| FP-16 | Solder mask expansion and paste reduction come from the board design rules. Only two exceptions exist: exposed-pad paste (FP-15) and openings the datasheet specifies; each exception is written in the footprint description. |
| FP-17 | BGA: pads per datasheet; if none, non-solder-mask-defined round pads at 80% of the nominal ball diameter, mask opening pad + 0.1 mm. |

**Polarity and pin 1**

| Part | Pin 1 | Pin names |
|---|---|---|
| Diode, Schottky, Zener, unidirectional TVS | Cathode | 1 = K, 2 = A |
| Bidirectional TVS | Either | 1, 2 |
| LED | As the datasheet numbers it; cathode = 1 when it gives no numbers | A, K |
| Polarised capacitor (aluminium, polymer, tantalum) | Positive | 1 = +, 2 = - |
| Transistors, ICs, connectors | As the datasheet | As the datasheet |

**Marking, naming and board features**

| ID | Rule |
|---|---|
| FP-20 | One marking style per kind, on silkscreen and assembly: ICs and connectors = filled dot outside the body next to pin 1 (silk) and a chamfered corner (assembly); diodes and LEDs = cathode bar; polarised capacitors = "+" beside the positive pad. |
| FP-21 | Silkscreen line 0.15 mm, kept 0.2 mm from every solder mask opening (not from the copper). The outline runs 0.1 mm outside the body; any segment that would break the clearance is left out. Chip parts smaller than 0603 get no silkscreen; their polarity is shown on the assembly layer only. The silkscreen designator is set in the board template: 1.0 mm text height, 0.15 mm stroke. |
| FP-22 | Names: IPC-calculated patterns use the IPC name exactly as Altium's IPC wizard generates it (no home-made suffixes). Manufacturer patterns use the IPC body name without the density letter plus the manufacturer's package code: `SOT95P280X145-5_TI-DBV`. Parts with no IPC name (connectors, modules, switches, odd crystals): `<Mfr>_<Series or MPN base>`, e.g. `JST_B2B-XH-A`, `Espressif_ESP32-WROOM-32E`. A name is never reused for different pad geometry; the release check compares the pad table of a new footprint against any existing footprint of the same name. |
| FP-23 | Footprint name = library item name. 3D models are named after the body, not the footprint (3D-05). |
| FP-24 | Every footprint carries Millable = Yes/No against the FabLab limits. A part needed on milled prototypes whose production pattern fails gets a separate `_M` variant (wider pads and holes); production boards never use `_M`. |
| FP-25 | Board features: fiducial = 1.0 mm round copper, 2.0 mm mask opening, 3.0 mm keepout; test point = 1.0 mm round top pad; mounting holes sized to the screw (M3 = 3.2 mm hole, 6.0 mm pad) with a copper keepout of head diameter + 1.0 mm; module antenna keepouts are copied from the module datasheet onto the Keepout layer; net ties use Altium's net-tie component type. |
| FP-26 | The PCB board template defines the same mechanical layer names, types and pairs as the layer map, so parts flipped to the bottom land on the right layers. |

### Layer map and line widths

Every footprint uses the same mechanical layers with the same layer types; the map below is Celestial's own footprint template (`Templates/Footprint Defaults.PCBLIB`), read from the file, and is adopted unchanged.

| Layer | Layer type (Altium) | Content | Line width |
|---|---|---|---|
| Top Layer | Signal | Pads | — |
| Top Solder / Top Paste | Mask, paste | Openings from design rules (FP-16) | — |
| Top Overlay | Silkscreen | Outline outside the body, pin 1 dot | 0.15 mm |
| Mechanical 1 / 2 | 3D Body Top / Bottom | 3D body (STEP) | — |
| Mechanical 3 / 4 | Component Center Top / Bottom | Centre cross at origin | 0.05 mm |
| Mechanical 5 / 6 | Component Outline Top / Bottom | Body outline at maximum size | 0.05 mm |
| Mechanical 13 / 14 | Assembly Top / Bottom | Body outline, pin 1 chamfer, `.Designator` text | 0.1 mm |
| Mechanical 15 / 16 | Courtyard Top / Bottom | Courtyard rectangle | 0.05 mm |

Mechanical 7 to 12 stay unused in footprints (free for board-level use). Layer pairs are 1/2, 3/4, 5/6, 13/14, 15/16 so parts flip correctly to the bottom side.

**Measured in Celestial footprints:** silkscreen 0.15 mm (0603 MLCC) and 0.2 mm (SOT-23-5), assembly 0.1 mm, courtyard layer 0.05 mm and 0.1 mm lines. The sampled footprints draw only on Mechanical 1, 13 and 15; Mechanical 3 to 6 are defined in the template, and their content and widths above are our choice. We fix silkscreen at 0.15 mm for every part, because one value is the point of the standard.

**Courtyard clearance** (added around the envelope of all pads and the body)

| Part kind | Clearance |
|---|---|
| Default (Nominal density) | 0.25 mm |
| Chip parts smaller than 0603 | 0.15 mm |
| Connectors (plus mating space), crystals in metal cans, electrolytic cans | 0.5 mm |
| BGA | 1.0 mm |

The 0.25 mm default is IPC-7351B's courtyard excess for Nominal density; the other tiers follow the KiCad library convention. Courtyard lines sit on a 0.01 mm grid.

### 3D body rules

Every 3D body matches the datasheet's maximum dimensions, is a STEP file stored as its own Workspace 3D model item, and looks like every other body of its class.

| ID | Rule |
|---|---|
| 3D-01 | Source order: (1) the manufacturer's STEP, checked against the datasheet; (2) our own model built in a CAD tool from the class template; (3) a third-party model only after checking its dimensions and that its licence allows our use. Celestial models are used only with the attribution its licence requires. |
| 3D-02 | STEP only (AP214, which keeps colours). Altium's extruded or generated bodies are not used in released parts. |
| 3D-03 | Passives, diodes, LEDs and standard IC packages are built from one parametric template per class, so size and colour are identical across the library. Connectors, modules and odd shapes use the manufacturer's STEP. |
| 3D-04 | Body = datasheet maximum length, width and height; leads, standoff and lead shape modelled; through-hole leads modelled to the datasheet lead length below the seating plane; polarity marked on polarised parts only. |
| 3D-05 | A 3D model is its own Workspace item, named after the body without pad or density suffix (`SOT95P280X145-5`), and shared by every footprint of that body. It sits on Mechanical 1 (3D Body Top), origin at body centre, seated on the board, pins on their pads, pin 1 on pin 1. |
| 3D-06 | Size limit 2 MB per model; larger manufacturer models are simplified (internal features and engraved text removed) before release. |
| 3D-07 | Our own models use the class colours below. Manufacturer STEP files keep their own colours; Altium's colour override is never used, because it paints the whole model one colour. |

**Class colours for our own models** (decided)

| Class | Body | Terminals / leads |
|---|---|---|
| Ceramic capacitor (MLCC) | Tan #C8A27A | Silver #C0C0C0 |
| Chip resistor | Black #1E1E1E top, white #F0F0F0 substrate | Silver #C0C0C0 |
| Electrolytic capacitor | Can #C8C8C8, sleeve #1E1E1E | Silver #C0C0C0 |
| Tantalum capacitor | Yellow #E0B000 | Silver #C0C0C0 |
| Power inductor | Dark grey #404040 | Silver #C0C0C0 |
| IC and diode body (plastic) | Black #1E1E1E | Silver #C0C0C0 |
| LED | Clear lens tinted to the LED colour | Silver #C0C0C0 |
| Polarity mark | Light grey #A0A0A0 | — |

### Verification and release

No part is released by the person who built it: a second person verifies it against a filled checklist, and only then sets the lifecycle to Released.

**Roles**

- **Author** builds the symbol, footprint, 3D model and parameters.
- **Verifier** (never the author) checks and releases; only the verifier fills `Verified By` and `Verified Date`.
- **Library owner** approves new categories, style-fault waivers and new revisions of shared items.

**Checklist per component** (kept with the component as its verification record)

1. **Source recorded:** datasheet URL, `Datasheet Revision`, and the package drawing document and page used.
2. **Pin table diff:** export the component's pin list (number, name, type) to CSV and diff it against the datasheet pin table, names and numbers both. Any mismatch is a defect.
3. **Pin types** match the pin electrical type table, and NC, EP and power pins follow SYM-02, SYM-03 and SYM-05.
4. **Footprint dimensions:** a table per pad group with datasheet value, value read from Properties, pass/fail; plus body outline and courtyard.
5. **Polarity:** pin 1 and polarity names match the polarity table on symbol, footprint, silkscreen, assembly and 3D.
6. **3D:** top and side view checked against the outline and height; model is the shared body item.
7. **Automated checks clean:** schematic library Component Rule Check, PCB library Component Rule Check, ERC on the reference design, DRC on a placement test board with the part on the top and the bottom side.
8. **1:1 print test** for every first-time package and every connector: print the footprint at 1:1 and lay the real part on it.
9. **Shared items:** if a shared symbol, footprint or 3D model changed, the where-used list is attached and every affected component is re-verified before the new revision is released.

### Open decisions

Version 1.1 decides every style and rule choice; five items remain because they need outside data, not a preference.

- **FabLab milling limits** (FP-24): minimum track, clearance, pad pitch and drill sizes of the mill.
- **PCB fab capability** (FP-14, FP-21): confirm the 0.05 mm drill step, the hole + 0.6 mm pad, 0.15 mm silkscreen line and 1.0 mm silkscreen text.
- **Assembler confirmation** (FP-12, FP-15): placement coordinate format and the 60% exposed-pad paste default.
- **IPC text check** with a copy of the standards: IPC-7351B courtyard tiers (is 0.15 mm below 0603 IPC's own value?), IPC-2222 hole allowance, and the IPC wizard's thermal-pad naming.
- **IPC-7352 review** (FP-05): owner and date, before the first import.

### Sources

- [Celestial Altium Library](https://github.com/issus/altium-library): symbol and footprint files measured for this tab (`symbols/Passives`, `symbols/Diodes`, `symbols/Opamp`, `symbols/Power - Linear VReg`, `symbols/MCU - STM32`, `footprints/Capacitor - MLCC`, `footprints/Leaded - SOT-23`, `Templates/Footprint Defaults.PCBLIB`) and its README (manufacturer land patterns first, pick-and-place centre, standardised pin placement, equal passive lead span).
- [KiCad Library Convention F5.3, courtyard](https://klc.kicad.org/footprint/f5/f5.3/): 0.05 mm courtyard lines, 0.01 mm grid, clearance tiers.
- [KiCad Library Convention F5.1, silkscreen](https://klc.kicad.org/footprint/f5/f5.1/): silkscreen kept 0.2 mm off exposed copper.
- [PCB Libraries forum: courtyard excess](https://www.pcblibraries.com/Forum/topic3372.html): 0.25 mm Nominal courtyard excess (IPC-7351B) and the IPC-7352 tables.

Standards used by name: IPC-7351B (land patterns, density levels M/N/L, zero orientation, naming), IPC-7352 (newer land-pattern guideline).
