"""Verify packages are complete and exclude private files, even when those exist."""
import importlib.util
from pathlib import Path
import tempfile
import re
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
def module(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/"scripts"/(name+".py"))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class DistributionTests(unittest.TestCase):
    def test_reproducible_and_no_private_files(self):
        builder=module("build")
        with tempfile.TemporaryDirectory() as d:
            outputs=builder.build(Path(d)/"a");other=builder.build(Path(d)/"b")
            for a,b in zip(outputs,other):
                self.assertEqual(a.read_bytes(),b.read_bytes())
                with zipfile.ZipFile(a) as z:
                    self.assertIsNone(z.testzip())
                    names=z.namelist()
                    self.assertTrue(any(n.endswith("SKILL.md") for n in names))
                    for n in names:
                        self.assertNotIn(".venv/",n);self.assertNotIn("__pycache__/",n)
                        self.assertNotIn("local-profile.json",n)
                        self.assertNotIn("tools/xrd_annotation_tool/assets/",n)
                    for n in names:
                        if n.endswith((".py",".md",".json",".yaml",".html")):
                            self.assertIsNone(re.search(rb"/Users/[A-Za-z0-9_-]+/", z.read(n)),n)

if __name__=="__main__":unittest.main()
