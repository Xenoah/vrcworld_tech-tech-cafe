"""Reproducible C# syntax gate; Unity/Udon compilation remains separate."""
from pathlib import Path
import json
from tree_sitter import Language,Parser
import tree_sitter_c_sharp
ROOT=Path(__file__).resolve().parents[1]
parser=Parser(Language(tree_sitter_c_sharp.language()))
checks=[{'file':p.name,'syntax_errors':parser.parse(p.read_bytes()).root_node.has_error}
        for p in sorted((ROOT/'Unity/Assets/TheCommons').rglob('*.cs')) if 'Generated' not in p.parts]
report={'checks':checks,'note':'Syntax parsing only. Not Unity or Udon compilation.'}
(ROOT/'Documentation/csharp_syntax_report.json').write_text(json.dumps(report,indent=2)+'\n')
assert checks and not any(c['syntax_errors'] for c in checks),report
print(f'C# syntax: {len(checks)} files passed')
