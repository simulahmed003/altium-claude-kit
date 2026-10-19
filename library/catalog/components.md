# Global component catalog

Generated from components.json by the lib scripts; do not edit by hand. Preferred = use first.

## Components

| ID | Cat | Value | MPN | LCSC | Verified | Tier | Footprint | Rev | Preferred | Caveats |
|---|---|---|---|---|---|---|---|---|---|---|
| J_MKDS1.5-2-5.08_1715721 | connectors | MKDS 1,5/2-5,08 | 1715721 | C480516 | yes | Extended (hand-soldered, not in SMT order) | TB_MKDS1.5-2-5.08 | 2 |  | hand-soldered, not in the SMT order |
| TP_PAD | connectors | TP | - | - | NO | - (copper pad, no part) | TP_PAD_D1.5 | 1 | yes | copper pad, no part; symbol pin length 70 mil (accepted exception, LIB-03) |
| Q_AO4407C | discretes | AO4407C | AO4407C | C469397 | yes | Extended | SOIC8_MS012 | 1 |  | AO4407C datasheet is marked Preliminary; alternative AO4407A C16072 (not in library) |
| U_LMR33630ADDAR | ics | LMR33630ADDAR | LMR33630ADDAR | C841384 | yes | Extended | LMR33630_HSOIC8_DDA | 2 | yes | EP = AGND, tie to GND copper with vias (footprint has tented vias) |
| C_100n_50V_X7R_0603_CC0603KRX7R9BB104 | passives | 100n 50V X7R | CC0603KRX7R9BB104 | C14663 | yes | Basic | CAPC1608_0603 | 2 | yes | symbol pin length 80 mil (accepted exception, LIB-03) |
| C_10u_50V_X7R_1206_1206B106K500NT | passives | 10u 50V X7R | 1206B106K500NT | C303950 | yes | Extended | CAPC3216_1206 | 2 |  | symbol pin length 80 mil (accepted exception, LIB-03) |
| C_1u_50V_X5R_0603_CL10A105KB8NNNC | passives | 1u 50V X5R | CL10A105KB8NNNC | C15849 | yes | Basic | CAPC1608_0603 | 2 | yes | symbol pin length 80 mil (accepted exception, LIB-03) |
| C_220n_50V_X7R_0603_CC0603KRX7R9BB224 | passives | 220n 50V X7R | CC0603KRX7R9BB224 | C107083 | yes | Extended | CAPC1608_0603 | 2 |  | symbol pin length 80 mil (accepted exception, LIB-03) |
| C_22u_25V_X5R_1206_CL31A226KAHNNNE | passives | 22u 25V X5R | CL31A226KAHNNNE | C12891 | yes | Basic | CAPC3216_1206 | 2 | yes | symbol pin length 80 mil (accepted exception, LIB-03); DC-bias derating at 5 V assumed 0.72 in buck calcs |
| C_DNP_0603 | passives | DNP | - | - | NO | - | CAPC1608_0603 | 1 |  | footprint-only placeholder, value DNP, no part; symbol pin length 80 mil (accepted exception, LIB-03) |
| L_10u_CDRH10D60_CDRH10D60BT150NP-100MC | passives | 10u 6.2A | CDRH10D60BT150NP-100MC | C2594362 | yes | Extended | IND_CDRH10D60 | 2 |  | buck deviation accepted at G1: DCR max 22.1 mOhm > 20 mOhm target, body 10.3 mm > 10 mm limit - re-check per project |
| R_100k_1%_0603_0603WAF1003T5E | passives | 100k | 0603WAF1003T5E | C25803 | yes | Basic | RESC1608_0603 | 2 | yes |  |
| R_10k_1%_0603_0603WAF1002T5E | passives | 10k | 0603WAF1002T5E | C25804 | yes | Basic | RESC1608_0603 | 2 | yes |  |
| R_20k0_0.1%_0603_PTFR0603B20K0P9 | passives | 20.0k 0.1% | PTFR0603B20K0P9 | C328424 | yes | Extended | RESC1608_0603 | 2 |  |  |
| R_4k99_0.1%_0603_PTFR0603B4K99P9 | passives | 4.99k 0.1% | PTFR0603B4K99P9 | C5382597 | yes | Extended | RESC1608_0603 | 2 |  |  |
| R_51k_1%_0603_0603WAF5102T5E | passives | 51k | 0603WAF5102T5E | C23196 | yes | Basic | RESC1608_0603 | 2 | yes |  |

## Footprints

| Name | Cat | Status | Source of status | Rev | Courtyard mm | 3D | Caveats |
|---|---|---|---|---|---|---|---|
| TB_MKDS1.5-2-5.08 | connectors | datasheet-verified | Phoenix 1715721 datasheet p1-2 (pitch 5.08, hole 1.3); G1 user 2026-10-13 | 1 | TODO | - | body outline position relative to the pins assumed centred - check with a real part |
| TP_PAD_D1.5 | connectors | derived | test pad sized for the user's probes; G1 user 2026-10-13 | 1 | TODO | - | no datasheet (copper pad) |
| SOIC8_MS012 | discretes | unverified-accepted | user at G1 2026-10-13 | 1 | TODO | - | NOT verified against an AOS package drawing (none in the AO4407C/AO4407A datasheets) |
| LMR33630_HSOIC8_DDA | ics | datasheet-verified | lmr33630.pdf p55/p58 (DDA0008B); G1 user 2026-10-13 | 1 | TODO | - | vias 0.3/0.6 mm in the EP (TI shows 0.2 mm), tented both sides (G1 decision) |
| CAPC1608_0603 | passives | derived | no numeric land in Yageo/Samsung datasheets; G1 user 2026-10-13 | 1 | TODO | - | derived land |
| CAPC3216_1206 | passives | derived | no numeric land in Samsung/FH datasheets; IPC-style land, width per Samsung 2/3W < b < W; G1 user 2026-10-13 | 1 | TODO | - | derived land |
| IND_CDRH10D60 | passives | datasheet-verified | Sumida CDRH10D60 datasheet p1; G1 user 2026-10-13 | 1 | TODO | - |  |
| RESC1608_0603 | passives | derived | no numeric land in UNI-ROYAL/RESI datasheets; G1 user 2026-10-13 | 1 | TODO | models/step/chip/RESC1608_0603.step | derived land |

## Generic symbols (specs, value set per instance)

| ID | Footprint | Spec |
|---|---|---|
| R_GENERIC_0603 | RESC1608_0603 | specs/generic_passives.json |
| C_GENERIC_0603 | CAPC1608_0603 | specs/generic_passives.json |
| C_GENERIC_1206 | CAPC3216_1206 | specs/generic_passives.json |
