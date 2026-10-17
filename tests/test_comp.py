"""Smoke tests for tools/comp/comp.py. Run: python -m pytest tests/"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

KIT = Path(__file__).resolve().parents[1]


def run(kit, *args, cwd=None):
    r = subprocess.run([sys.executable, str(kit / "tools/comp/comp.py"), *args],
                       capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout


def make_kit(tmp_path):
    kit = tmp_path / "kit"
    shutil.copytree(KIT, kit, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    d = kit / "components/power/buck/TESTPART"
    shutil.copytree(kit / "components/_template", d)
    rec = yaml.safe_load((d / "part.yaml").read_text())
    rec.update(id="TESTPART", mfr="TestCo", description="test buck",
               selection={"vin": {"min": 3.5, "max": 28, "unit": "V", "ref": "p1"}},
               pins=[{"num": "1", "name": "BOOT", "ref": "p3"}])
    (d / "part.yaml").write_text(yaml.safe_dump(rec, sort_keys=False))
    return kit


def test_validate_index_search_get_pull(tmp_path):
    kit = make_kit(tmp_path)
    assert run(kit, "validate", "--all")[0] == 0
    assert run(kit, "index")[0] == 0
    assert "TESTPART" in run(kit, "search", "buck", "28V")[1]
    assert "BOOT" in run(kit, "get", "TESTPART", "--section", "pins")[1]
    proj = tmp_path / "proj"
    assert run(kit, "new-project", str(proj))[0] == 0
    code, outp = run(kit, "pull", "TESTPART", cwd=proj)
    assert code == 0 and json.loads(outp)["pulled"] == ["TESTPART"]
    assert "TESTPART" in yaml.safe_load((proj / "components.lock.yaml").read_text())["parts"]


def test_missing_unit_is_reported(tmp_path):
    kit = make_kit(tmp_path)
    p = kit / "components/power/buck/TESTPART/part.yaml"
    rec = yaml.safe_load(p.read_text())
    rec["selection"]["iout"] = {"value": 3, "ref": "p1"}
    p.write_text(yaml.safe_dump(rec))
    code, outp = run(kit, "validate", "TESTPART")
    assert code == 1 and "missing unit" in outp
