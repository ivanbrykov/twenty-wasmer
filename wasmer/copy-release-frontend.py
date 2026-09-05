#!/usr/bin/env python3
"""Copy unchanged frontend assets from the pinned official release image.

The image is never started; the patched backend continues to come from this fork.
"""
from pathlib import Path
import json
import subprocess
root=Path(__file__).resolve().parent.parent
image='twentycrm/twenty@sha256:aa605eec185160cc600ead1648dffd95b1a5ae5e939dce4d84e56c1e5a692a38'
subprocess.run(['docker','pull',image],check=True)
metadata=json.loads(subprocess.check_output(['docker','image','inspect',image]))[0]
version=next((e.split('=',1)[1] for e in metadata['Config'].get('Env',[]) if e.startswith('APP_VERSION=')),None)
if version not in ('2.37.0','v2.37.0'):
    raise SystemExit('Unexpected image APP_VERSION: '+str(version))
container=subprocess.check_output(['docker','create','--platform','linux/arm64',image],text=True).strip()
target=root/'packages/twenty-server/dist/front'
try:
    target.mkdir(parents=True,exist_ok=True)
    subprocess.run(['docker','cp',container+':/app/packages/twenty-server/dist/front/.',str(target)],check=True)
finally:
    subprocess.run(['docker','rm',container],check=True,stdout=subprocess.DEVNULL)
if not (target/'index.html').is_file():raise SystemExit('Frontend index missing')
print('Copied official '+version+' frontend; image was not executed.')
