#!/usr/bin/env python3
"""Scoped Codex lifecycle guard. Requires the user's normal hook trust review.

No network, no transcript reads, no global file scanning, no trust bypass.
Stop only checks jobs explicitly registered for this session. This cannot detect
all possible visual work or retract media already displayed by another tool.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

REMINDER = ('For visual creation/editing, use $golden-ratio-visual-design, including 3D. '
            'Declare a measurable geometric contract before rendering. Distinguish world-space '
            'geometry from perspective projection. Use golden_delivery.py begin/check/export; '
            'a draft or local PASS is not universal conformity. Keep nonvisual work unaffected.')


def state_path(session):
    if not isinstance(session,str) or not session:
        raise ValueError('Session ID required')
    root=Path(os.getenv('GOLDEN_STATE_DIR',str(Path.home()/'.codex/golden-guard')))
    return root/(hashlib.sha256(session.encode()).hexdigest()+'.json')


def read_state(session):
    path=state_path(session)
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'jobs':{}}


def write_state(session,state):
    path=state_path(session); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.'+str(os.getpid())+'.tmp')
    temp.write_text(json.dumps(state,indent=2),encoding='utf-8');os.replace(temp,path)


def register_job(session,job):
    state=read_state(session);state['jobs'][str(Path(job).resolve())]={'receipt':None}
    write_state(session,state)


def register_receipt(session,job,receipt):
    state=read_state(session);key=str(Path(job).resolve())
    # Unit-test and diagnostic jobs that were not registered never arm a hook.
    if key in state['jobs']:
        state['jobs'][key]['receipt']=str(Path(receipt).resolve());write_state(session,state)


def handle(event):
    name=event.get('hook_event_name');session=event.get('session_id')
    if name in ('SessionStart','UserPromptSubmit'):
        return {'hookSpecificOutput':{'hookEventName':name,'additionalContext':REMINDER}}
    if not session:
        return {'systemMessage':'Golden guard: missing session ID; enforcement NOT VERIFIED.'}
    state=read_state(session)
    if name=='PreToolUse':
        tool=str(event.get('tool_name','')).lower()
        if 'imagegen' in tool and not any(v.get('receipt') is None for v in state['jobs'].values()):
            return {'hookSpecificOutput':{'hookEventName':name,'permissionDecision':'deny',
                    'permissionDecisionReason':'Prepare a new visual job with golden_delivery.py begin before generating. Generated images remain drafts until measured.'}}
        return {}
    if name=='Stop':
        from golden_delivery import validate_receipt
        problems=[]
        for job,info in state['jobs'].items():
            try:
                if not info.get('receipt'): raise ValueError('No verified export receipt')
                receipt=validate_receipt(info['receipt'])
                if Path(receipt['job']).resolve()!=Path(job).resolve(): raise ValueError('Wrong job receipt')
            except (ValueError,LookupError,TypeError,OSError,ImportError,OverflowError) as error:
                problems.append(job+': '+str(error))
        if problems:
            reason='Golden visual delivery is NOT VERIFIED. Do not claim completion. '+ '; '.join(problems)
            if event.get('stop_hook_active'):
                state['last_failure']=reason;state['jobs']={};write_state(session,state)
                return {'continue':False,'stopReason':reason,'systemMessage':reason}
            return {'decision':'block','reason':reason+' Correct the evidence/export, or explain the blocker. No automatic retry loop.'}
        if state['jobs']:
            # Completed turns must not turn into permanent locks on unrelated
            # future requests after old evidence files are archived or removed.
            state['jobs']={};write_state(session,state)
    return {}


if __name__=='__main__':
    try:
        event=json.load(sys.stdin);print(json.dumps(handle(event)))
    except Exception as error:
        # Explicit supported block, not an unhandled callback failure that the
        # host might treat as advisory. Never modify Codex's own trust settings.
        print('Golden guard could not verify its state: '+str(error),file=sys.stderr)
        sys.exit(2)
