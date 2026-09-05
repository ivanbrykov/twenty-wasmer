#!/usr/bin/env python3
"""Assemble a standalone Wasmer package from already-built, pinned workspaces."""
from pathlib import Path
import os
import shutil
import subprocess

root=Path(__file__).resolve().parent.parent
package=root/'.wasmer/package'
app=package/'app'
if package.exists():
    raise SystemExit('Package directory exists; preserve/remove that generated output before rebuilding.')
app.mkdir(parents=True)
for filename in ['package.json','yarn.lock','.yarnrc.yml','tsconfig.base.json','nx.json']:
    shutil.copy2(root/filename,app/filename)
for folder in ['.yarn/releases','.yarn/patches']:
    shutil.copytree(root/folder,app/folder)
workspaces=['twenty-server','twenty-shared','twenty-emails','twenty-client-sdk']
for name in workspaces:
    source=root/'packages'/name
    target=app/'packages'/name
    target.mkdir(parents=True)
    shutil.copy2(source/'package.json',target/'package.json')
    if not (source/'dist').is_dir():raise SystemExit('Build missing: '+name)
    shutil.copytree(source/'dist',target/'dist')
    for optional in ['patches','scripts']:
        if (source/optional).exists():shutil.copytree(source/optional,target/optional)
if not (app/'packages/twenty-server/dist/front/index.html').is_file():
    raise SystemExit('Copy/build the matching release frontend before packaging.')
env=os.environ.copy()
env['YARN_ENABLE_GLOBAL_CACHE']='0'
env.setdefault('YARN_CACHE_FOLDER',str(root/'.wasmer/yarn-cache'))
subprocess.run(['node','.yarn/releases/yarn-4.13.0.cjs','workspaces','focus','--production',*workspaces],cwd=app,env=env,check=True)
# Match Anybuild's native-addon pruning: WASI cannot use these host binaries.
for native in (app/'node_modules').rglob('*.node'):
    native.unlink()
for declaration in (app/'packages').rglob('*.d.ts'):
    declaration.unlink()
server='/app/packages/twenty-server'
manifest='''[package]
entrypoint = "server"

[dependencies]
"wasmer/edgejs-quickjs" = "=0.2.0"
"wasmer/bash" = "=1.0.25"

[fs]
"/app" = "app"
'''
commands={
 'server':['--bytecode-cache','dist/main.js'],
 'initialize':['dist/database/scripts/setup-db.js'],
 'migrate':['dist/command/command.js','run-instance-commands','--force','--include-slow'],
 'upgrade':['dist/command/command.js','upgrade'],
 'precompile':['--precompile','/app'],
}
import json
for name,args in commands.items():
    manifest+='\n[[command]]\nname = '+json.dumps(name)+'\nmodule = "wasmer/edgejs-quickjs:edge"\nrunner = "wasi"\n\n[command.annotations.wasi]\ncwd = '+json.dumps(server)+'\nmain-args = '+json.dumps(args)+'\n'
(package/'wasmer.toml').write_text(manifest)
(package/'app.yaml').write_text('kind: wasmer.io/App.v0\npackage: .\n')
print('Standalone package assembled at',package)
print('Configure namespace, database, Redis, URL, and secrets before any hosted deployment.')
