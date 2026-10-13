# Backlog - candidate guideline topics (names only, no values)

Status: draft list made 2026-10-13 so the topics are not lost. The user decides which topics to take, in which order,
and sets the values. "Automation today" lists what exists now; the `calclib.py` names were checked against its function list
on 2026-10-13. "none yet" = an automation candidate.

| Area | Topic | Parameters (names only) | Automation today |
|---|---|---|---|
| Power stage | Inductor ripple current allowance | ripple ratio k = delta I / IOUT: allowed range | `inductor_ripple`, `inductor_for_ripple` (k is an input; no stored range) |
| Power stage | Inductor saturation and RMS margin | Isat margin over peak or current limit; Irms margin | `inductor_check` (checks Isat >= max(peak, current limit) and Irms rating >= rms; no margin factor) |
| Power stage | Inductor DCR loss budget | DCR share of the total loss | none yet (`loss_from_efficiency` gives the total loss only) |
| Power stage | Output capacitor | output ripple budget; minimum effective C after tolerance and DC bias | `cap_derated` for C_eff; ripple voltage: none yet |
| Power stage | Input capacitor | RMS ripple current rating; input voltage ripple | none yet |
| Power stage | Capacitor voltage margin and dielectric | rating against working voltage; X7R / X5R | rule RQ-06 holds a first version today (see note) |
| Control | Feedback divider accuracy | total VOUT tolerance (reference and resistors) | `divider_worst` |
| Control | Enable and UVLO thresholds | start and stop voltage targets; hysteresis | `en_uvlo` |
| Control | Soft start and start-up | start-up time; inrush current | none yet |
| Efficiency and thermal | Efficiency and loss budget | target efficiency at the load points | `loss_from_efficiency` |
| Efficiency and thermal | Thermal margin | TJ margin to TJmax; ambient assumption | `junction_temp`, `rth_needed`; rule RQ-07 holds a first version (see note) |
| Protection | Input protection | reverse polarity; surge; fuse | none yet |
| Layout and fab | Current-carrying copper | allowed temperature rise; copper weight | `trace_width_ipc2221` |
| Layout and fab | DFM margins against the fab | min trace and space; copper to edge; drill and annular ring | fab profile `_tools\fab_profiles\jlcpcb_2layer.json` (fab limits and workspace defaults) and `place.py` |
| Layout and fab | Switching loop | hot-loop area; switch-node copper | none yet |
| Architecture | Power tree and grounding | rails and their order; ground partition | none yet |

Note: two rules already carry design numbers: RQ-06 (capacitor rating >= 2x working voltage, X7R or X5R) and RQ-07 (thermal target).
They stay in `_rules\` for now. Whether they move here is the user's decision (a rule change needs approval, rule WF-04).
