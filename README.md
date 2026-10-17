# altium-claude-kit

An open kit that lets Claude design embedded hardware in **Altium Designer** from requirements to fab files,
with as little human back-and-forth and as few tokens as possible.

It has three parts:

| Part | Folder | What it is |
|---|---|---|
| **Skills** | `skills/` | One skill per design phase. Says what the phase must achieve and how to check it. Claude decides how. |
| **Rules** | `rules/` | Engineering standards a PCB designer follows, written once, numbered (`PL-03`), referenced by skills. |
| **Component database + library** | `components/` | One folder per exact MPN: datasheet facts already extracted (with page refs), plus symbol, footprint, 3D and SPICE. |

And the glue:

| Folder | What it is |
|---|---|
| `tools/` | Deterministic scripts. `comp` is the only way Claude reads or writes the component database. |
| `templates/project/` | The skeleton copied into every new Altium project. |
| `examples/` | Reference designs, also used as regression tests (first: a buck converter). |
| `docs/` | Architecture, usage guide, roadmap, guide for AI contributors. |

## Why it saves tokens

- **A datasheet is read once, ever.** After ingest, every project queries `comp get <MPN> --section pins` instead of opening the PDF.
- **Project state lives in files** (`project.yaml`, `decisions.md`), so a new session resumes without replaying chat.
- **Skills are short goal-and-gate files**, and they load only the rules and component fields their phase needs.
- **Calculations and checks are scripts**, which return a 10-line summary and keep the full logs on disk.

## Quick start

```bash
git clone https://github.com/<owner>/altium-claude-kit.git
pip install -r altium-claude-kit/requirements.txt
python altium-claude-kit/tools/comp/comp.py new-project ~/designs/my-board   # copies the template
cd ~/designs/my-board && claude                                              # Claude reads CLAUDE.md and project.yaml
```

Full walkthrough: [docs/USAGE.md](docs/USAGE.md).

## Status

Early skeleton (v0.1-dev). What exists and what is planned: [docs/ROADMAP.md](docs/ROADMAP.md).
Design rationale: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Contributing

Parts, rules, skills and tools are all welcome, and you may use your own AI to write them.
Read [CONTRIBUTING.md](CONTRIBUTING.md); point your AI at [docs/AI-CONTRIBUTOR.md](docs/AI-CONTRIBUTOR.md).

## License

Code and docs: MIT ([LICENSE](LICENSE)). Component CAD files keep their source licence, recorded in each part's `source.yaml`.
Datasheet PDFs are never committed.
