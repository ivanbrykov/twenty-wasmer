#!/usr/bin/env python3
"""Build the four server workspaces explicitly, matching upstream build commands.

Nx's full-repository graph introduces unrelated UI tasks that the Docker build's
reduced source context never contains. This keeps the server build input explicit.
"""
from pathlib import Path
import os
import argparse
import subprocess
import shutil

root=Path(__file__).resolve().parent.parent
fork=root
env=os.environ.copy()
env['NODE_OPTIONS']='--max-old-space-size=8192'
env['PATH']=str(fork/'node_modules/.bin')+os.pathsep+env['PATH']
env.setdefault('COREPACK_HOME',str(root/'.wasmer/corepack'))
yarn=['node',str(fork/'.yarn/releases/yarn-4.13.0.cjs')]
tasks=[
 ('twenty',['tsx','packages/twenty-shared/scripts/generateBarrels.ts']),
 ('twenty-shared',['vite','build']),
 ('twenty-shared',['tsgo','-p','tsconfig.lib.json','--declaration','--emitDeclarationOnly','--noEmit','false','--outDir','dist','--rootDir','src']),
 ('twenty-shared',['tsc-alias','-p','tsconfig.lib.json','--outDir','dist']),
 ('twenty-client-sdk',['vite','build']),
 ('twenty-client-sdk',['vite','build','-c','vite.metadata.config.ts']),
 ('twenty-client-sdk',['tsgo','-p','tsconfig.lib.json','--declaration','--emitDeclarationOnly','--noEmit','false','--outDir','dist','--rootDir','src']),
 ('twenty-client-sdk',['tsc-alias','-p','tsconfig.lib.json','--outDir','dist']),
 ('twenty-emails',['lingui','extract','--overwrite','--clean']),
 ('twenty-emails',['lingui','compile','--typescript']),
 ('twenty-emails',['vite','build']),
 ('twenty-emails',['tsgo','-p','tsconfig.lib.json','--declaration','--emitDeclarationOnly','--outDir','dist','--rootDir','src','--composite','false']),
 ('twenty-emails',['tsc-alias','-p','tsconfig.lib.json','--outDir','dist']),
 ('twenty-server',['lingui','extract','--overwrite','--clean']),
 ('twenty-server',['lingui','compile','--typescript']),
 ('twenty-server',['nest','build','--path','./tsconfig.build.json']),
]
results=root/'.wasmer/results';results.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--start-at');options=parser.parse_args()
if options.start_at:
    keys=[workspace+' '+' '.join(args) for workspace,args in tasks]
    if options.start_at not in keys:raise SystemExit('Unknown start step')
    tasks=tasks[keys.index(options.start_at):]
with (results/'fork-build.log').open('a' if options.start_at else 'w') as log:
 for workspace,args in tasks:
  print(workspace,' '.join(args),flush=True);log.write('\n'+workspace+' '+' '.join(args)+'\n');log.flush()
  p=subprocess.run(yarn+['workspace',workspace,'exec']+args,cwd=fork,env=env,stdout=log,stderr=subprocess.STDOUT)
  if p.returncode:raise SystemExit(p.returncode)
dest=fork/'packages/twenty-server/dist/assets/twenty-client-sdk';dest.mkdir(parents=True,exist_ok=True)
shutil.copyfile(fork/'packages/twenty-client-sdk/package.json',dest/'package.json')
shutil.copytree(fork/'packages/twenty-client-sdk/dist',dest/'dist',dirs_exist_ok=True)
print('Full server build complete',flush=True)
