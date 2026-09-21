import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / 'skills/platform/scripts/tier0_auth.py'
spec = importlib.util.spec_from_file_location('tier0_auth', path)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)
SECRET = 'test-secret-must-never-appear'


def response(data, code=0, stderr=''):
    return subprocess.CompletedProcess([], code, json.dumps(data), stderr)


def options(action, **kwargs):
    defaults = dict(action=action, base_url='https://tier0.dev', setup_code='ABCDEFGH', name='test', save='test', broker=None, dry_run=False)
    return SimpleNamespace(**(defaults | kwargs))


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(auth.os.environ, {'TIER0_API_KEY': '', 'TIER0_BASE_URL': ''})
        self.env.start()
        self.binary = patch.object(auth, 'executable', return_value='/test/tier0')
        self.binary.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.binary.stop)

    def call(self, args, outputs):
        with patch.object(auth.subprocess, 'run', side_effect=outputs) as mock:
            value, code = auth.run(args)
        self.assertNotIn(SECRET, json.dumps(value))
        return value, code, mock

    def test_missing_cli(self):
        with patch.object(auth, 'executable', return_value=None):
            self.assertEqual(auth.run(options('status'))[0]['error']['reason'], 'cli_not_installed')

    def test_missing_auth_does_not_call_api(self):
        value, code, mock = self.call(options('status'), [response({'apiKeyConfigured': False})])
        self.assertEqual(code, 3)
        self.assertEqual(mock.call_count, 1)

    def test_instance_mismatch_does_not_call_api(self):
        value, code, mock = self.call(options('status'), [response({'apiKeyConfigured': True, 'baseURL': 'https://other.example'})])
        self.assertEqual(value['error']['reason'], 'different_instance_login_required')
        self.assertEqual(mock.call_count, 1)

    def test_status_identity_allowlist(self):
        v, c, _ = self.call(options('status'), [response({'apiKeyConfigured': True, 'baseURL': 'https://tier0.dev'}), response({'code': 200, 'data': {'userID': 1, 'workspaceID': 2, 'apiKey': SECRET, 'permissions': ['read_only'], 'other': {'password': SECRET}}})])
        self.assertEqual(c, 0)
        self.assertEqual(v['identity']['workspaceID'], 2)

    def test_begin_keeps_original_url(self):
        url = 'https://tier0.dev/cli-auth?setup=ABCDEFGH'
        v, c, _ = self.call(options('begin'), [response({'status': 'authorization_required', 'verification_url': url, 'setup_code': 'ABCDEFGH', 'api_key': SECRET})])
        self.assertEqual(v['verification_url'], url)
        self.assertEqual(c, 0)

    def test_begin_rejects_unexpected_url(self):
        v, c, _ = self.call(options('begin'), [response({'status': 'authorization_required', 'verification_url': 'https://other.example', 'setup_code': 'ABCDEFGH'})])
        self.assertNotEqual(c, 0)

    def test_finish_never_returns_key_and_verifies_identity(self):
        v, c, mock = self.call(options('finish'), [response({'event': 'authorization_complete', 'api_key': SECRET}), response({'code': 200, 'data': {'userID': 1, 'workspaceID': 2}})])
        self.assertEqual(c, 0)
        self.assertEqual(mock.call_count, 2)
        self.assertEqual(mock.call_args_list[0].kwargs['timeout'], 45)

    def test_finish_does_not_claim_success_if_whoami_fails(self):
        v, c, _ = self.call(options('finish'), [response({'event': 'authorization_complete', 'api_key': SECRET}), response({}, 3, json.dumps({'error': {'type': 'authorization', 'message': SECRET}}))])
        self.assertEqual(c, 3)
        self.assertFalse(v['ok'])

    def test_timeout_not_success_and_drops_partial_output(self):
        v, c, _ = self.call(options('finish'), [subprocess.TimeoutExpired('tier0', 45, output=SECRET, stderr=SECRET)])
        self.assertEqual(c, 4)
        self.assertFalse(v['ok'])

    def test_error_does_not_echo_raw_stderr(self):
        v, c, _ = self.call(options('begin'), [response({}, 3, json.dumps({'error': {'type': 'authentication', 'message': SECRET, 'hint': SECRET}}))])
        self.assertEqual(v['error']['type'], 'authentication')

    def test_malformed_output_is_not_echoed(self):
        v, c, _ = self.call(options('finish'), [subprocess.CompletedProcess([], 0, SECRET, SECRET)])
        self.assertNotEqual(c, 0)

    def test_business_error_even_if_exit_zero(self):
        v, c, _ = self.call(options('finish'), [response({'code': 403, 'msg': SECRET})])
        self.assertNotEqual(c, 0)

    def test_environment_override_prevents_wrong_instance(self):
        with patch.dict(auth.os.environ, {'TIER0_API_KEY': SECRET}), patch.object(auth.subprocess, 'run') as mock:
            v, c = auth.run(options('begin'))
        self.assertEqual(c, 3)
        mock.assert_not_called()
        self.assertNotIn(SECRET, json.dumps(v))

    def test_mqtt_secret_is_removed_and_profile_required(self):
        v, c, mock = self.call(options('mqtt-create'), [response({'code': 200, 'data': {'id': 7, 'password': SECRET, 'username': SECRET}})])
        self.assertEqual(v['credential_id'], 7)
        self.assertIn('--save', mock.call_args.args[0])

    def test_mqtt_failure_does_not_invite_retry(self):
        v, c, _ = self.call(options('mqtt-create'), [response({}, 4, json.dumps({'error': {'type': 'network', 'message': SECRET}}))])
        self.assertEqual(v['error']['mutation_result'], 'unknown_check_remote_before_retry')

    def test_invalid_identity_is_not_authenticated(self):
        v, c, _ = self.call(options('finish'), [response({'event': 'authorization_complete', 'api_key': SECRET}), response({'code': 200, 'data': {}})])
        self.assertNotEqual(c, 0)


if __name__ == '__main__':
    unittest.main()
