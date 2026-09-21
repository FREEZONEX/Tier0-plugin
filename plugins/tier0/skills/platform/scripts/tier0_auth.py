#!/usr/bin/env python3
"""Safe output adapter for existing Tier0 CLI auth and MQTT credential creation.

No API implementation or credential store: Tier0 CLI owns both. Only allowlisted
fields cross stdout; raw child output and exception text are never forwarded.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

CATEGORIES = {'validation', 'authentication', 'authorization', 'config', 'network', 'api', 'internal', 'confirmation'}


def fail(kind, reason, code=1):
    return {'ok': False, 'error': {'type': kind, 'reason': reason}}, code


def executable():
    found = shutil.which('tier0')
    fallback = Path.home() / '.tier0/bin' / ('tier0.exe' if os.name == 'nt' else 'tier0')
    return found or (str(fallback) if fallback.is_file() else None)


def parse_object(raw):
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else {}
    except (ValueError, TypeError):
        return {}


def invoke(binary, args, timeout=40):
    try:
        result = subprocess.run([binary, *args], capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return fail('network', 'wait_timed_out_check_status_before_retry', 4)
    except (OSError, UnicodeError):
        return fail('internal', 'cli_execution_failed', 5)
    if result.returncode:
        error = parse_object(result.stderr).get('error', {})
        kind = error.get('type') if isinstance(error, dict) else None
        if kind not in CATEGORIES:
            kind = 'internal'
        # Do not echo message/hint: upstream may include response bodies or secrets.
        return fail(kind, 'cli_failed', result.returncode if result.returncode > 0 else 1)
    value = parse_object(result.stdout)
    if not value:
        return fail('internal', 'unexpected_cli_output', 5)
    if value.get('ok') is False or ('code' in value and value['code'] not in (0, 200)):
        return fail('api', 'business_request_failed', 1)
    return value, 0


def base_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('invalid platform URL')
    return value.rstrip('/')


def identity(binary):
    value, code = invoke(binary, ['auth', 'whoami', '--json'])
    if code:
        return value, code
    data = value.get('data', value)
    if not isinstance(data, dict) or not data.get('workspaceID') or not data.get('userID'):
        return fail('internal', 'identity_or_workspace_missing', 5)
    safe = {}
    for field in ('userID', 'userName', 'workspaceID', 'workspaceName', 'keyType'):
        if isinstance(data.get(field), (str, int)):
            safe[field] = data[field]
    for field in ('roles', 'permissions'):
        if isinstance(data.get(field), list):
            safe[field] = [item for item in data[field] if isinstance(item, str)]
    return {'ok': True, 'status': 'authenticated', 'identity': safe}, 0


def run(args):
    binary = executable()
    if not binary:
        return fail('config', 'cli_not_installed', 3)
    # Current upstream inconsistently applies these overrides across command families.
    # Refuse rather than checking one identity and operating with another instance/key.
    if os.environ.get('TIER0_API_KEY') or os.environ.get('TIER0_BASE_URL'):
        return fail('config', 'environment_override_present_use_consistent_cli_profile', 3)
    if args.action == 'begin':
        value, code = invoke(binary, ['login', '--no-wait', '--base-url', args.base_url, '--json'])
        if code:
            return value, code
        setup = value.get('setup_code', '')
        url = value.get('verification_url', '')
        expected = args.base_url
        if '/api/' in expected:
            expected = expected[:expected.rfind('/api/')]
        if value.get('status') != 'authorization_required' or not re.fullmatch(r'[A-Z0-9]{8}', setup) or url != expected + '/cli-auth?setup=' + setup:
            return fail('internal', 'unexpected_authorization_response', 5)
        return {'ok': True, 'status': 'authorization_required', 'base_url': args.base_url,
                'verification_url': url, 'setup_code': setup, 'expires_in': 600}, 0
    if args.action == 'finish':
        value, code = invoke(binary, ['login', '--setup-code', args.setup_code, '--base-url', args.base_url, '--json'], timeout=45)
        if code:
            return value, code
        if value.get('event') != 'authorization_complete':
            return fail('internal', 'unexpected_login_completion', 5)
        # The API key in value is deliberately discarded; CLI has saved its profile.
        return identity(binary)
    if args.action == 'status':
        value, code = invoke(binary, ['config', '--json'])
        if code:
            return value, code
        if not value.get('apiKeyConfigured'):
            return fail('authentication', 'login_required', 3)
        if args.base_url and value.get('baseURL', '').rstrip('/') != args.base_url:
            return fail('config', 'different_instance_login_required', 3)
        return identity(binary)
    if args.action == 'mqtt-create':
        cmd = ['mqtt', 'auth', 'create', '--name', args.name, '--save', args.save, '--random-suffix=true', '--json']
        if args.broker:
            cmd += ['--broker', args.broker]
        if args.dry_run:
            cmd += ['--dry-run']
        value, code = invoke(binary, cmd)
        if code:
            value['error']['mutation_result'] = 'unknown_check_remote_before_retry'
            return value, code
        if args.dry_run:
            return {'ok': True, 'dry_run': True, 'name': args.name, 'profile': args.save,
                    'action': 'mqtt auth create', 'random_suffix': True, 'broker_override': args.broker}, 0
        data = value.get('data', {})
        if not isinstance(data, dict) or not isinstance(data.get('id'), int) or data['id'] <= 0:
            return fail('internal', 'unexpected_creation_response_do_not_retry', 5)
        return {'ok': True, 'credential_id': data['id'], 'profile': args.save,
                'credentials_saved_by_cli': True}, 0
    return fail('validation', 'unsupported_action', 2)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    for name in ('status', 'begin', 'finish'):
        s = sub.add_parser(name)
        s.add_argument('--base-url', type=base_url, required=name != 'status')
        if name == 'finish':
            s.add_argument('--setup-code', required=True)
    s = sub.add_parser('mqtt-create')
    s.add_argument('--name', required=True)
    s.add_argument('--save', required=True)
    s.add_argument('--broker')
    s.add_argument('--dry-run', action='store_true')
    args = p.parse_args()
    if args.action == 'finish' and not re.fullmatch(r'[A-Z0-9]{8}', args.setup_code):
        result, code = fail('validation', 'invalid_setup_code', 2)
    else:
        result, code = run(args)
    print(json.dumps(result, ensure_ascii=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
