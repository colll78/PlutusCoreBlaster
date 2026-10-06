#!/usr/bin/env python3
"""Verify freshly compiled Data/native parameter examples and reject swapped wire types.
Usage: lake env python3 Tests/BlueprintVerify/run_parameters.py GENERATOR OUTPUT
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from runtime import lean_command
lean_args = lean_command()

repo=Path(__file__).resolve().parents[2]
generator=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True)
def run(source,name):
    path=out/name;path.write_text(source)
    result=subprocess.run(lean_args + [str(path)],cwd=repo,text=True,capture_output=True,timeout=300)
    log=result.stdout+result.stderr;(out/(name+'.log')).write_text(log)
    return result.returncode,log
code,log=run('import PlutusCore.UPLC.BlueprintEncoding.Assurance\n'+f'#write_checking_environment {json.dumps(str(out/"environment.json"))}\n','Environment.lean')
if code: raise RuntimeError(log)
subprocess.run([str(generator),'environment.json'],cwd=out,check=True,timeout=120)
code,log=run('import PlutusCore.UPLC.BlueprintEncoding.Assurance\n'+f'#verify_blueprint Parameters {json.dumps(str(out/"assurance.json"))}\n','Check.lean')
print(log,end='')
if code or set(re.findall(r"Property '([^']+)': verified",log)) != {'native_seven','data_seven'}:
    raise RuntimeError('parameter verification did not verify both claims')
# Keep the exact compiled program, change only its declared parameter wire type.
# This must produce a false proposition, demonstrating that encodings affect execution.
bp=json.loads((out/'plutus.json').read_text());doc=json.loads((out/'assurance.json').read_text())
for v in bp['validators']:
    if v['id']=='nativeParameter': v['parameters'][0]['schema']={'dataType':'integer'}
(out/'wrong-wire.json').write_text(json.dumps(bp))
doc['blueprint']={'uri':'wrong-wire.json','hash':{'alg':'sha256','digest':hashlib.sha256((out/'wrong-wire.json').read_bytes()).hexdigest()}}
doc['properties']=[p for p in doc['properties'] if p['id']=='native_seven']
(out/'wrong-wire-assurance.json').write_text(json.dumps(doc))
code,log=run('import PlutusCore.UPLC.BlueprintEncoding.Assurance\n'+f'#verify_blueprint Wrong {json.dumps(str(out/"wrong-wire-assurance.json"))}\n','WrongWire.lean')
if code == 0 or "Property 'native_seven': falsified" not in log: raise RuntimeError(log)
print('PASS swapped native/Data schema falsifies the claim over the same compiled bytes')
