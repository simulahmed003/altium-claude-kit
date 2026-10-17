# projects\

Your designs live here. This folder is git-ignored by the workspace repo, so designs never reach the public repo.

- Create one: `powershell -NoProfile -ExecutionPolicy Bypass -File tools\newproject.ps1 -Name my-board`
- Give each design its own git repo (`git init` inside it) and keep that repo private if you wish.
- The agent reads the design's `CLAUDE.md`, `PROJECT.md`, `requirements.md`, `constraints.md` and `gates.md` before touching it.
