# 09 Library standard

The component library standard v1.1 (Simul, 2026-11-02) is in `docs/LIBRARY_STANDARD.md`; these rules make it binding in the kit.
Decisions D1-D12 are at the top of that file. Decided 2026-11-02: D1 (IC pins 200 mil), D2 (2-pin geometry by convenience), D3 (capacitors show capacitance and voltage), D4 (standard parameter names; existing libraries renamed only with permission), D6 (unknown distributor number = blank, ask the user), D5 (standard Description), D7 (3D from the database library first), D8 and D9 (names and folders by the category tree; restructure briefed first), D11 (Datasheet URL from the maker, DigiKey/LCSC only when the maker has none), D12 (the standard is public in the kit). Still open: D10; until it is decided LIB-19 applies.
Parameter set frozen 2026-11-03 (LIB-31, LIB-32): the parameters below are the complete list until the user asks to change or add one.

### LIB-21 The library standard applies to every library component
- MUST: build, copy, classify and check every component (kit global, project local and client libraries) to `docs/LIBRARY_STANDARD.md`; where it is silent, the other LIB rules apply; where a client's rules differ, LIB-20 applies.
- MUST: follow an older kit rule over the standard only for the items still listed open (D1-D12), and name the item in the report.
- Why: one written standard keeps every part of a kind correct and identical, for people and agents alike.
- Check: checklist (report names the standard version and any open item used)
- Source: user 2026-11-02 (draft standard; "integrate these rules with our existing workspace rules")
- Status: CHECKLIST

### LIB-22 One category per part, from the default tree
- MUST: give every component exactly one Type/Subtype from the standard's default tree, by its classification procedure and tie-breaks, copied exactly; never put package, value, rating, polarity, channel count, mounting, pitch or brand into a category.
- MUST: mark a part REVIEW (and ask the user) when two subtypes still fit, tie-break 6 was used, no subtype fits, or no datasheet was found; a new category only as a proposal that passes the five gates, after the user approves it.
- Why: one home per part makes parts findable; a category made to avoid a decision splits the library.
- Check: checklist (planned tool lib_std_check: category exists in the tree)
- Source: user 2026-11-02 (standard: core principles, classification, AI agent instructions)
- Status: CHECKLIST

### LIB-23 Common and electrical parameters, values from the datasheet
- MUST: give every component the 25 common parameters and its subtype's required electrical parameters (tables at the end of this file), named exactly as written, in its value format (SI prefix, no space, ASCII u, decimal point, ranges with "to", one value each); take every value from the component database (RQ-01), unknown = empty.
- MUST NOT: store price, stock, MOQ or lead time values, or a second manufacturer on a component (an alternate brand is its own component); the Price/Stock product links of LIB-31 are links, not values, and are allowed.
- Why: names and formats Altium's importer and ActiveBOM can read; values traceable to a datasheet page.
- Check: checklist (planned tool lib_std_check: names, required values, value format, Description pattern)
- Source: user 2026-11-02 (standard: Parameters tab)
- Status: CHECKLIST

### LIB-24 Legacy component names stay until the user approves a rename
- MUST: keep a component's existing name (for example a Workspace `CMP-xxx` ID) until the user approves the rename batch; meanwhile its manufacturer and MPN parameters must be correct and checked.
- MUST NOT: rename a component, symbol or footprint on the way, even when the standard (Name = MPN) asks for it.
- Why: other designs and the client's Workspace point to those names; the user decides when they change.
- Check: lib_audit.py (lists names that are not the MPN)
- Source: user 2026-11-02 ("right now we did not change any component name")
- Status: CHECKLIST

### LIB-25 Symbol pins: datasheet names, numbers and electrical types
- MUST: name each pin with the datasheet's primary name (ASCII; active-low as an overbar), number it as the package, draw every pin including NC, exposed pad (EP, pin count + 1 when unnumbered), shield and mounting tabs; alternate functions only in the pin Description; no hidden or stacked pins (SYM-01..05).
- MUST: set each pin's electrical type from the standard's pin type table (Power, Input, Output, I/O, Open Collector, HiZ, Passive).
- Why: ERC only finds real faults when pin types are right; a pin table that maps 1:1 to the package can be diffed.
- Check: pin_match.py (pins = pads); checklist (pin type table)
- Source: user 2026-11-02 (standard SYM-01..05, pin electrical types)
- Status: CHECKLIST

### LIB-26 Symbol layout and style from the class template
- MUST: draw each symbol from its class template and the standard's style values: pin ends on 100 mil, 2-pin parts 400 mil span, IC side layout (SYM-13), MCU and multi-part rules (SYM-14, 17, 18), IC pin length 200 mil (D1, not the standard's 300), bus order (SYM-15), text positions and linked Comment (SYM-20..22), colours and font, designator prefixes.
- Why: identical symbols can be swapped without moving wires and read the same everywhere.
- Check: pin_match.py --style (to be updated to the style values after D1-D3)
- Source: user 2026-11-02 (standard SYM-10..22, symbol style values); decided D1 (IC pins 200 mil, LIB-11), D2 (2-pin geometry where convenient), D3 (capacitors show capacitance and voltage, LIB-02)
- Status: CHECKLIST

### LIB-27 Footprints: maker's land first, IPC-7351B Nominal otherwise
- MUST: use the maker's recommended land pattern, else IPC-7351B Nominal (FP-01..05); build geometry, origin, zero orientation, through-hole holes, exposed-pad paste, mask and BGA pads to FP-10..17; polarity and pin 1 to the polarity table; marking, silkscreen, names and board features to FP-20..26; layers and courtyard to the layer map; record the source in `Package Drawing` and `Footprint Standard`.
- Why: a footprint is only as good as its source and its numbers; one layer map lets parts flip to the bottom correctly.
- Check: checklist (verification step 4 table per pad group); catalog_check.py (status)
- Source: user 2026-11-02 (standard FP-01..26, layer map, courtyard); open D8 against LIB-13, LIB-15
- Status: CHECKLIST

### LIB-28 3D bodies: STEP at datasheet maximum size, one per body
- MUST: give every footprint a STEP body at the datasheet's maximum length, width and height, seated on the board with pin 1 on pin 1, on Mechanical 1, shared by every footprint of that body, at most 2 MB, keeping the maker's colours (3D-02..07).
- Why: a wrong height or pin-1 corner shows up only at assembly or in the enclosure.
- Check: cad_fetch.py (box check against the record)
- Source: user 2026-11-02 (standard 3D-01..07); open D7 (source order) against LIB-13
- Status: CHECKLIST

### LIB-29 Verification checklist per component, author never releases
- MUST: fill the standard's nine-step checklist for every component and keep it with the component: source, pin table diff, pin types, footprint dimension table, polarity, 3D, automated checks, 1:1 print (person only), shared-item where-used.
- MUST: the author (the agent, or whoever built it) never releases its own part: the agent's check makes it "checked" (LIB-18, LIB-19); only the verifier (a person) fills Verified By and Verified Date and marks it "confirmed".
- Why: a second pair of eyes against a fixed checklist catches what the author missed.
- Check: lib_audit.py mark; checklist (verification record per component)
- Source: user 2026-11-02 (standard: verification and release); open D10
- Status: CHECKLIST

### LIB-30 Brief the user and get a yes before each part or step
- MUST: before each library part or work step (copying a symbol or footprint, creating one, filling or renaming parameters, writing a library), tell the user in a few lines what will be done, to which part and from which source, and wait for the user's yes; then do only that.
- MUST: copy symbols and footprints from the user's database library first, made consistent (LIB-17); create one from scratch only when none exists and the user permits it.
- Why: the user follows the library work from the phone and wants to approve each part before it changes.
- Check: checklist (each part's report starts with the brief and the user's yes)
- Source: user 2026-11-02 ("before next part or going to each work brief user what going to do then taking permission do the job"; "part need not be built from scratch, mainly copy symbol and footprint from that database library")
- Status: CHECKLIST

### LIB-31 The parameter set is frozen until the user changes it
- MUST: give each component exactly the parameters in the tables below and nothing new: the stored common ones, its subtype's electrical ones and the links `Mouser Price/Stock`, `DigiKey Price/Stock`, `LCSC Price/Stock`; names without the hint in brackets (`Dielectric`, not `Dielectric (X7R, X5R, C0G)`); `Supplier 1` and `Supplier Part Number 1` present but empty.
- MUST: Description in the component field and as a hidden `Description` parameter; Comment = the value (`100nF`, `10k`, `10R`, `4.7uH`) or the short part name for ICs; resistance below 1k as `10R`, `49.9R`, from 1k as `1k`; other ohm values as `22mOhm`; manufacturer short name as on the datasheet cover.
- MUST NOT: add price/stock parameters or remove existing ones; keep an old-name duplicate of a standard parameter (`Manufacturer_Name`, `MP`, `Datasheet Link`, `Pins`, `Case/Package`...) once the standard one has its value: remove it and log the old value.
- Why: one fixed parameter list, decided with the user, keeps every library and BOM export identical; duplicates disagree sooner or later.
- Check: checklist (change log per component: added, updated, removed, kept); planned tool lib_std_check
- Source: user 2026-11-03 (answers on the SpeakerSystemV1 parameter update: "do not kept duplicate", "follow the standard", "use 10R", "do not add like supplier 1 ... leave blank", "lets fixed the parameter rules ... until i asked to change it")
- Status: CHECKLIST

### LIB-32 Parameter values: datasheet wins, distributor numbers from the official APIs
- MUST: values from the datasheet: maker's PDF first, DigiKey second, LCSC third; Height = the datasheet's maximum seated height (nominal + tolerance); on a conflict with the library write the datasheet value only when confirmed on the page, else keep the old value and list it for the user.
- MUST: Mouser and DigiKey numbers and product links from the official APIs (Mouser Search API, DigiKey Product Information V4; Nexar optional) by exact MPN and manufacturer; list every packaging variation, store DigiKey Cut Tape (else the only listing), keep an existing link.
- MUST NOT: type API keys or secrets: they stay in the user's own key file (`%USERPROFILE%\.distributor_keys.json`) or environment variables.
- Why: distributor sites block scripts; the APIs give the real purchasing number and URL for the exact part.
- Check: distributor_lookup.py (all listings with exact-MPN and manufacturer flags); checklist
- Source: user 2026-11-03 ("datasheet first priority mfn second digikey third lcsc", "take height from datasheet", "where conflict keep data sheet", "as your script is blocked by digikey use their api", "add those partnumber and links as parameter")
- Status: CHECKLIST

### LIB-34 One parameter set per category: no duplicates, no blank extras
- MUST: give every component of a category (Type/Subtype) the same parameter set: the stored common parameters, the three Price/Stock links, and all Required and Optional electrical parameters of its subtype; a parameter whose value is unknown stays present and empty.
- MUST: remove every component-level parameter that is not in that set, blank or valued (old Altium content, SnapEDA and database leftovers such as `Value`, `Schedule B`, `Lifecycle Status`, `Length`), and log its old value; where it duplicates a standard parameter that is empty, move its value into the standard one first; keep only one parameter per name; when `Value` goes, `Comment` becomes the visible value text in its place and font.
- MUST NOT: touch parameters owned by a model or implementation (`OwnerIndex` set, e.g. SIM fields, `altium.hash`) or the price/stock parameters of LIB-31 (`Arrow Part Number`, `Arrow Price/Stock`, `Price`, `Check_prices`).
- Why: parts of one category compare and export the same way; duplicates disagree sooner or later and blank extras are noise once the full set is there.
- Check: checklist (change log per component; every category's parameter names identical); planned tool lib_std_check
- Source: user 2026-11-03 ("remove the duplicate keep the authentic", "whats the point of those duplicate and blank parameter", "in each category components should have same parameters", "go ahead and do this make all consistent")
- Status: CHECKLIST

## Parameter tables (part of LIB-23)

Machine-readable copy: `rules/library_parameters.json` (for the planned lib_std_check tool). Names exactly as written, without the hint in brackets (LIB-31); values in the format below; unknown = empty.

#### Common parameters (every component; Category is import only)

| Group | Parameter | Need | Format | Example |
|---|---|---|---|---|
| Identity | Description | Required, field and hidden parameter (LIB-31) | Pattern from *Naming conventions*, ≤ 256 characters | RES 10k 1% 0.1W 0603 |
| Identity | Comment | Required | The value, or the short part name for ICs (LIB-31) | 10k, 10R, 100nF |
| Identity | Category | Import only | `Type/Subtype` exactly as the tree | Resistors/Chip |
| Sourcing | Manufacturer 1 | Required | Manufacturer's short official name | Yageo |
| Sourcing | Manufacturer Part Number 1 | Required | Exact orderable MPN, incl. packaging suffix | RC0603FR-0710KL |
| Sourcing | Supplier 1 | Present, left empty (LIB-31) | Production distributor, chosen per company later | *(empty)* |
| Sourcing | Supplier Part Number 1 | Present, left empty (LIB-31) | That distributor's part number | *(empty)* |
| Sourcing | LCSC Part Number | Required if stocked | LCSC/JLCPCB number for this exact MPN | C12345 (illustrative) |
| Sourcing | DigiKey Part Number | Required if stocked | DigiKey's own part number for this exact MPN | 311-10.0KHRCT-ND (illustrative) |
| Sourcing | Mouser Part Number | Required if stocked | Mouser's own part number for this exact MPN | 603-RC0603FR-0710KL (illustrative) |
| Sourcing | Mouser Price/Stock | Required if stocked (LIB-31) | Mouser product page link from the API | https://www.mouser.com/ProductDetail/… |
| Sourcing | DigiKey Price/Stock | Required if stocked (LIB-31) | DigiKey product page link from the API | https://www.digikey.com/en/products/detail/… |
| Sourcing | LCSC Price/Stock | Required if stocked (LIB-31) | `https://www.lcsc.com/product-detail/<LCSC Part Number>.html` | https://www.lcsc.com/product-detail/C1880995.html |
| Sourcing | Local Source | If applicable | Local market shop or note | Shop name, Dhaka |
| Sourcing | Datasheet URL | Required | Manufacturer's PDF link | https://… |
| Sourcing | Datasheet Revision | Required | Revision and date printed on the datasheet | Rev. 2.1, 2025-03 |
| Sourcing | Package Drawing | Required | Document and page the footprint was built from | Datasheet p.42, or package drawing DBV0005A |
| Physical | Package | Required | EIA/JEDEC name | 0603, SOT-23-3, LQFP-48 |
| Physical | Package Metric | Chip passives only | Metric size code | 1608 |
| Physical | Mounting | Required | SMD / THT / Press-fit / Chassis | SMD |
| Physical | Pin Count | Required | Integer, incl. exposed pad | 3 |
| Physical | Height | Required | Max seated height from the datasheet (nominal + tolerance), mm | 0.55mm |
| Physical | Footprint Standard | Required | IPC-7351 density or Manufacturer | IPC-7351B Nominal |
| Compliance | Operating Temperature | Required | Min to max, °C | -55°C to 155°C |
| Compliance | RoHS | Required | Compliant / Non-compliant / Unknown | Compliant |
| Compliance | MSL | SMD ICs and LEDs | JEDEC level 1 to 6 | 3 |
| Verification | Verified By | Required after check | Initials | SA |
| Verification | Verified Date | Required after check | YYYY-MM-DD | 2026-11-02 |

#### Value format

| Rule | Write | Never |
|---|---|---|
| SI prefix, no space, unit symbol | `10k`, `100nF`, `4.7``u``H`, `50V` | `10 K`, `0.1uF `, `100 nano` |
| u for micro, ASCII only | `4.7``u``F` | `4.7``µF, 4.7``mfd` |
| Decimal point, no trailing zeros | `2.2``u``F` | `2,2``u``F`, `2.20``u``F` |
| Ranges with "to" | `-40°C to 85°C`, `2.7V to 5.5V` | `-40~85` |
| Tolerance as ± percent | `1%` | `F`, `±1 %` |
| Resistance below 1k with R, from 1k with k | `10R`, `49.9R`, `1k`, `4.7k` | `10`, `10Ω`, `1000R` |
| Ohm in other values as Ohm | `22mOhm`, `50Ohm` | `22mΩ`, `22m` |
| One value per parameter | `Channels` = `2` | `2 (dual)` |
| Unknown = empty | *(blank)* | `N/A`, `-`, `TBD` |

#### Electrical parameters by subtype (89 subtypes)

Required = must have a value before the part is used; Optional = filled when the datasheet gives it and it matters for selection; both are present on every part of the subtype, empty when unknown (LIB-34). One name per meaning across all Types (always `Voltage Rating`, `Current Rating`, `Supply Voltage Range`).

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
