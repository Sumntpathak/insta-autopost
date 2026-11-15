"""One shared repository journal, persisted before external mutations."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent


def now(): return datetime.now(timezone.utc)


def config(): return json.loads((ROOT/'config.json').read_text())


def read(): return json.loads((ROOT/'state.json').read_text())


def persist(state):
    path=ROOT/'state.json'
    with tempfile.NamedTemporaryFile('w',dir=ROOT,delete=False) as f:
        json.dump(state,f,indent=2); f.write('\n'); temporary=f.name
    os.replace(temporary,path)
    if os.environ.get('GITHUB_ACTIONS')=='true':
        for cmd in (['git','add','team/state.json'],['git','diff','--cached','--quiet']):
            result=subprocess.run(cmd,check=cmd[1]!='diff')
        if result.returncode==0: return
        if result.returncode!=1: raise RuntimeError('Cannot inspect journal changes')
        subprocess.run(['git','commit','-m','Record ShipStack team journal'],check=True)
        subprocess.run(['git','pull','--rebase'],check=True)
        subprocess.run(['git','push'],check=True)


def save_report(name,data):
    directory=ROOT/'out'; directory.mkdir(exist_ok=True)
    path=directory/name
    path.write_text(json.dumps(data,indent=2)+'\n')
    return path
