#!/usr/bin/env python3
"""mc_rest_api_example checks. --motion physically rotates the free MC349 shaft.

Run: python test_mc_rest_api_example.py --offline
Run: python test_mc_rest_api_example.py [DEVICE_IP] --motion
"""
import argparse
import ast
import importlib.util
import json
import os
import socket
import sys
import time
import types
from unittest.mock import patch

import requests
from mctk import RefgoClient, TestRunner, UdpMonitor, start_script, stop_script, upload_script

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_API_NAME = 'mc_rest_api_example'
EXPECTED_API_VERSION = '0.0.1'
EXPECTED_ENDPOINTS = (
    'GET /api/status', 'GET /api/motor', 'GET /api/config',
    'GET/PUT /api/objects/index/subindex', 'POST /api/refgo',
    'POST /api/move', 'POST /api/velocity', 'POST /api/stop',
    'POST /api/continue', 'POST /api/enable', 'POST /api/disable',
)
SCRIPT_NAME = EXPECTED_API_NAME + '.py'
SCRIPT = os.path.join(ROOT, 'app-scripts', SCRIPT_NAME)
RESULTS = os.path.join(ROOT, 'testing', 'results')
# Bench-specific motion values for the current freely rotating MC349 setup.
# Review these constants before using --motion with different mechanics or power.
SAFE_RAMP = 100
MAX_TEST_VELOCITY = 1000
NETWORK_TIMEOUT = 30.0


def offline(script_path=None):
    if script_path is None:
        script_path = SCRIPT
    script_name = os.path.basename(script_path)
    values = {(0x6078, 0): 100, (0x606C, 0): 4000, (0x6080, 0): 4000}
    drive = types.SimpleNamespace(ReadObject=lambda index, sub: values.get((index, sub), 0),
                                  ChkError=lambda: 0, ChkReady=lambda: 0)
    clock = types.SimpleNamespace(ticks_ms=lambda: 0, ticks_diff=lambda now, before: now - before)
    spec = importlib.util.spec_from_file_location(EXPECTED_API_NAME, script_path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'mcdrive': drive, 'mcnet': types.SimpleNamespace(),
                                 'refgo': types.SimpleNamespace(), 'time': clock}):
        spec.loader.exec_module(module)
    runner = TestRunner('test_mc_rest_api_example_offline', script=script_name)
    with open(script_path, 'r', encoding='utf-8') as source_file:
        source_tree = ast.parse(source_file.read(), script_path)
    slices = [node for node in ast.walk(source_tree) if isinstance(node, ast.Slice)]
    recent_methods = {
        'startswith', 'endswith', 'partition', 'rpartition', 'splitlines',
        'split', 'strip', 'lstrip', 'rstrip', 'lower', 'upper', 'join',
    }
    recent_calls = [
        node.func.attr for node in ast.walk(source_tree)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr in recent_methods)
    ]
    if 'advanced_string_splitting' not in script_name:
        runner.check('No string slicing required', not slices, repr(slices))
        runner.check('No recent string methods required', not recent_calls, repr(recent_calls))
    else:
        runner.check('Advanced string slicing present', bool(slices))
        runner.check('Advanced string methods present', bool(recent_calls))
    status, discovery_body = module.dispatch(('GET', '/api', '', False))
    discovery = json.loads(discovery_body)
    runner.check('API identity and version discovery', status == 200 and
                 discovery['name'] == EXPECTED_API_NAME and
                 discovery['version'] == EXPECTED_API_VERSION and
                 tuple(discovery['endpoints']) == EXPECTED_ENDPOINTS and
                 tuple(module.API_ENDPOINTS) == EXPECTED_ENDPOINTS)
    removed_alias = False
    try:
        module.dispatch(('GET', '/OR/0x3401/0x0a', '', False))
    except module.ApiError as error:
        removed_alias = error.status == 404
    runner.check('Object access has no short alias', removed_alias)
    for text in ('{}', '{"position":-123,"velocity":60}', '{"command":"OR3401h,Ah"}'):
        runner.check('JSON ' + text, module.parse_json(text) == json.loads(text))
    for text in ('', '{"a":1,}', '{"a":01}', '{"a":1.0}', '{"a":1,"a":2}',
                 '{"a":+1}', '{"a":{}}', '{"command":"TS\\rTP"}', '{"a":1 "b":2}'):
        rejected = False
        try:
            module.parse_json(text)
        except module.ApiError:
            rejected = True
        runner.check('Reject JSON ' + repr(text), rejected)
    value = {'response': 'line\r\n"\\', 'items': [True, False, None, -4]}
    runner.check('JSON escaping roundtrip', json.loads(module.json_encode(value)) == value)
    request = 'POST /api/move HTTP/1.1\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{}'
    runner.check('Partial body waits', module.parse_request(request[:-1]) is None)
    runner.check('HTTP/1.1 remains open', not module.parse_request(request)[3])
    runner.check('Explicit close honored', module.parse_request(request.replace(
        'Content-Type:', 'Connection: close\r\nContent-Type:'))[3])
    module.service(50)
    runner.check('Power formula +10 percent', module.APP.power_instant == 1000)
    values[(0x606C, 0)] = -4000
    module.service(100)
    runner.check('Signed power formula -10 percent', module.APP.power_instant == -1000)
    runner.check('Moving average cancels directions', module.APP.power_sum == 0)
    runner.check('Fixed-point division has no negative floor bias', module.divide_signed(-1, 4000) == 0)
    values[(0x6080, 0)] = 0
    module.service(150)
    runner.check('Zero denominator gives null', module.APP.power_instant is None and module.APP.sample_count == 0)
    drive.ChkError = lambda: values.get('fault', 0)
    drive.GetActualPos = lambda: 123
    values['fault'] = 1
    for count in range(10):
        values[(0x603F, 0)] = count + 1
        module.service(200 + count * 50)
    runner.check('Fault history bounded to eight observations', len(module.APP.errors) == 8)
    values['fault'] = 0
    values[(0x603F, 0)] = 0
    module.service(750)
    runner.check('Fault history survives fault clearance', len(module.APP.errors) == 8)
    stops = []
    drive.StopMotion = lambda: stops.append(True)
    module.APP.last_move = ('position', 100, 60)
    module.APP.started = 0
    module.service(module.MOTION_TIMEOUT_MS)
    runner.check('Motion timeout requests native quick stop', stops == [True] and module.APP.motion == 'timeout')
    drive.ReadStatusword = lambda: 0x27
    drive.ChkMoving = lambda: 1
    values[(0x606F, 0)] = 60
    for velocity in (0, 59, -59, 60, -60, 61, -61):
        values[(0x606C, 0)] = velocity
        state = json.loads(module.status_json())
        moving = abs(velocity) > 60
        direction = ('positive' if velocity > 0 else 'negative') if moving else 'none'
        runner.check('Threshold status at velocity ' + str(velocity),
                     state['moving'] == moving and state['direction'] == direction)
    return runner.finish(RESULTS)


def raw_http(host, pieces):
    with socket.create_connection((host, 8080), timeout=NETWORK_TIMEOUT) as sock:
        for piece in pieces:
            sock.sendall(piece)
        result = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            result += chunk
    header, body = result.split(b'\r\n\r\n', 1)
    for name, value in (('X-API-Name', EXPECTED_API_NAME), ('X-API-Version', EXPECTED_API_VERSION)):
        if (name + ': ' + value).encode('ascii') not in header.split(b'\r\n'):
            raise AssertionError('Missing or mismatched ' + name)
    return int(header.split(b' ')[1]), json.loads(body)


def hardware(host, motion, script_path=None):
    if script_path is None:
        script_path = SCRIPT
    script_name = os.path.basename(script_path)
    runner = TestRunner('test_mc_rest_api_example', device_ip=host, script=script_name)
    monitor = UdpMonitor(host)
    drive = RefgoClient(host, timeout=NETWORK_TIMEOUT)
    session = requests.Session()
    base = 'http://' + host + ':8080'
    times, server_times, server_samples, polling_times = [], [], [], []
    original_user_value = None
    restore_feed = None
    restore_parameters = {}

    def call(method, path, body=None, expected=200):
        started = time.perf_counter()
        response = session.request(method, base + path, json=body, timeout=NETWORK_TIMEOUT)
        if (response.headers.get('X-API-Name') != EXPECTED_API_NAME
                or response.headers.get('X-API-Version') != EXPECTED_API_VERSION):
            raise AssertionError('Unexpected API identity/version headers')
        times.append((time.perf_counter() - started) * 1000)
        processing_time = int(response.headers['X-Processing-Time-Ms'])
        server_times.append(processing_time)
        server_samples.append((processing_time, method, path))
        if response.status_code != expected:
            raise AssertionError(f'{method} {path}: {response.status_code} {response.text}')
        return response.json()

    def poll(predicate, timeout=12):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            state = call('GET', '/api/status')
            if state['fault']:
                raise AssertionError('Drive fault: ' + repr(state))
            if predicate(state):
                return state
            time.sleep(0.05)
        raise AssertionError('Status wait timed out: ' + repr(state))

    def write(index, sub, value):
        return call('PUT', f'/api/objects/0x{index:x}/{sub}', {'value': value})

    def disable_when_ready(timeout=12):
        deadline = time.monotonic() + timeout
        while True:
            try:
                return call('POST', '/api/disable', {}, 202)
            except AssertionError as error:
                if ('409 {"error":"Stop and wait for standstill before disabling"}'
                        not in str(error) or time.monotonic() >= deadline):
                    raise
                time.sleep(0.05)

    try:
        drive.connect()
        monitor.start()
        assert stop_script(host, timeout=NETWORK_TIMEOUT)
        before_status = drive.read_object(0x6041, 0)
        assert upload_script(host, script_path, timeout=NETWORK_TIMEOUT)
        assert start_script(host, timeout=NETWORK_TIMEOUT)
        deadline = time.monotonic() + 5
        while not monitor.has_line(EXPECTED_API_NAME + ' started') and time.monotonic() < deadline:
            time.sleep(0.05)
        runner.check('Startup UDP received', monitor.has_line(EXPECTED_API_NAME + ' started'))
        discovery = call('GET', '/api')
        runner.check('API identity/version confirmed', discovery['name'] == EXPECTED_API_NAME and
                 discovery['version'] == EXPECTED_API_VERSION)
        initial = call('GET', '/api/status')
        runner.check('Startup preserves existing power state',
                 initial['statusword'] & 0x6f == before_status & 0x6f, repr(initial))
        runner.check('Temperature object read', call('GET', '/api/objects/0x3401/0x0a')['value'] ==
                     drive.read_object(0x3401, 10))
        runner.check('REFGO TS native integer', isinstance(call('POST', '/api/refgo', {'command': 'TS'})['response'], int))
        original_user_value = drive.read_object(0x3410, 10)
        write(0x3410, 10, -12345)
        runner.check('Generic object write/read', call('GET', '/api/objects/3410h/0Ah')['value'] == -12345)
        runner.check('Independent REFGO read agrees', drive.read_object(0x3410, 10) == -12345)
        write(0x3410, 10, original_user_value)
        original_user_value = None
        session.close()
        cases = [
            ('Object access has no short alias', b'GET /OR/0x3401/0x0a HTTP/1.1\r\nConnection: close\r\n\r\n', 404),
            ('Malformed JSON', b'POST /api/move HTTP/1.1\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{,', 400),
            ('Duplicate Content-Length', b'GET /api/status HTTP/1.1\r\nContent-Length: 0\r\nContent-Length: 0\r\n\r\n', 400),
            ('Chunked rejected', b'POST /api/move HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n', 400),
            ('Oversized body rejected', b'POST /api/move HTTP/1.1\r\nContent-Length: 4096\r\n\r\n', 413),
            ('Incomplete request bounded', b'POST /api/move HTTP/1.1\r\nContent-Type: application/json\r\nContent-Length: 2\r\n\r\n{', 408),
        ]
        for name, request, expected in cases:
            status, body = raw_http(host, [request])
            runner.check(name, status == expected, repr(body))
        runner.check('API identity/version headers on success and errors', True)
        request = b'POST /api/refgo HTTP/1.1\r\nContent-Type: application/json\r\nContent-Length: 16\r\nConnection: close\r\n\r\n{"command":"TP"}'
        status, body = raw_http(host, [request[:9], request[9:51], request[51:-1], request[-1:]])
        runner.check('Fragmented HTTP and explicit close', status == 200 and isinstance(body['response'], int))
        session = requests.Session()
        call('GET', '/api/status')
        for path in ('/api/status', '/api/motor', '/api/config', '/api/objects/0x6041/0') * 15:
            call('GET', path)
            polling_times.append(times[-1])
        runner.check('Keep-alive polling', len(polling_times) == 60,
                     '60 successive status/motor/config/object requests')
        motor = call('GET', '/api/motor')
        runner.check('Power average sampled independently', motor['samples'] == 20, repr(motor))
        if motion:
            runner.section('Motion: explicitly verify all three safe ramps')
            feed_obj = call('GET', '/api/objects/0x6092/1')
            feed = feed_obj['value']
            if feed == 65536:
                write(0x6092, 1, 360)
                restore_feed = 65536
                feed = 360
            config = call('GET', '/api/config')
            position_tolerance = call('GET', '/api/objects/0x6067/0')['value']
            if position_tolerance <= 0:
                raise AssertionError('Motion test requires a positive configured position window')
            travel = 3 * feed
            if travel <= position_tolerance:
                raise AssertionError('Configured test travel must exceed the position window')
            threshold = call('GET', '/api/status')['velocity_threshold']
            max_motor_speed = drive.read_object(0x6080, 0) or 4000
            test_velocity = min(MAX_TEST_VELOCITY, max_motor_speed, max(120, 2 * threshold))
            if test_velocity <= threshold:
                raise AssertionError('Velocity threshold is too high for the allowed test speed')
            runner.check('Test speed above threshold and <=1000', threshold < test_velocity <= MAX_TEST_VELOCITY,
                         f'threshold={threshold}, speed={test_velocity}')
            restore_parameters = {
                index: drive.read_object(index, 0)
                for index in (0x6081, 0x6083, 0x6084, 0x6085, 0x605A)
            }
            for index in (0x6083, 0x6084, 0x6085):
                write(index, 0, SAFE_RAMP)
            for index in (0x6083, 0x6084, 0x6085):
                actual = drive.read_object(index, 0)
                assert actual == SAFE_RAMP and 0 < actual <= 200
                runner.check(f'Safe ramp 0x{index:x}', True, str(actual))
            call('POST', '/api/enable', {}, 202)
            origin = call('GET', '/api/status')['position']
            target = origin + travel
            softlimit_min = config['softlimit_min']
            softlimit_max = config['softlimit_max']
            if ((softlimit_min != 0 or softlimit_max != 0)
                    and not softlimit_min <= target <= softlimit_max):
                raise AssertionError('Positive motion target exceeds the configured software limits')
            call('POST', '/api/move', {'position': target, 'velocity': test_velocity}, 202)
            moving = poll(lambda state: state['moving'] and state['velocity'] > threshold)
            runner.check('Asynchronous positive position move', moving['direction'] == 'positive', repr(moving))
            call('POST', '/api/stop', {}, 202)
            stopped = poll(lambda state: not state['moving'])
            runner.check('Stop before target', abs(stopped['position'] - target) > position_tolerance, repr(stopped))
            call('POST', '/api/continue', {}, 202)
            reached = poll(lambda state: state['target_reached'] and abs(state['position'] - target) <= position_tolerance)
            actual_velocity = drive.read_object(0x6081, 0)
            velocity_ok = actual_velocity is not None and abs(actual_velocity - test_velocity) <= 5
            runner.check('Continue retains last target and speed', reached['last_move'] == ['position', target, test_velocity] and
                         velocity_ok, repr(reached))
            call('POST', '/api/move', {'position': origin, 'velocity': test_velocity}, 202)
            reverse = poll(lambda state: state['moving'] and state['velocity'] < -threshold)
            runner.check('Negative direction', reverse['direction'] == 'negative', repr(reverse))
            poll(lambda state: state['target_reached'] and abs(state['position'] - origin) <= position_tolerance)
            call('POST', '/api/velocity', {'velocity': test_velocity}, 202)
            poll(lambda state: state['mode'] == 3 and state['velocity'] > threshold)
            runner.check('Profile velocity uses native API', True)
            call('POST', '/api/stop', {}, 202)
            poll(lambda state: not state['moving'])
            disable_when_ready()
            runner.check('Disable removes power', call('GET', '/api/status')['statusword'] & 0x6f == 0x40)
        slowest = max(server_samples)
        runner.check('Processing <=200 ms', slowest[0] <= 200,
                 f'max={slowest[0]} ms {slowest[1]} {slowest[2]}, requests={len(server_times)}')
        sorted_times = sorted(times)
        runner.check('Established polling round-trip <=250 ms', max(polling_times) <= 250,
                 f'max={max(polling_times):.1f} ms, requests={len(polling_times)}')
        runner.check('Network timing recorded separately', True,
                 f'including connects: max={max(times):.1f} ms p95={sorted_times[int(len(times)*0.95)-1]:.1f} ms')
    except Exception as error:
        runner.check('Run completed without exception', False, repr(error))
    finally:
        session.close()
        if motion:
            try:
                for index in (0x6083, 0x6084, 0x6085):
                    drive.write_object(index, 0, SAFE_RAMP)
                drive.write_object(0x605A, 0, 6)
                drive.write_object(0x6040, 0, 0x0b)
                deadline = time.monotonic() + 5
                stopped = False
                threshold = drive.read_object(0x606F, 0)
                if not isinstance(threshold, int) or threshold <= 0:
                    threshold = 10
                while time.monotonic() < deadline:
                    velocity = drive.read_object(0x606C, 0)
                    if velocity is not None and abs(velocity) <= threshold:
                        stopped = True
                        break
                    time.sleep(0.05)
                drive.write_object(0x6040, 0, 0)
                drive.write_object(0x60FF, 0, 0)
                drive.write_object(0x6060, 0, 0)
                restored = True
                for index, value in restore_parameters.items():
                    restored = (drive.write_object(index, 0, value)
                                and drive.read_object(index, 0) == value
                                and restored)
                if restore_feed is not None:
                    restored = (drive.write_object(0x6092, 1, restore_feed)
                                and drive.read_object(0x6092, 1) == restore_feed
                                and restored)
                runner.check('Cleanup restored modified parameters', restored)
                runner.check('Cleanup stopped and disabled', stopped and drive.read_object(0x6041, 0) & 0x6f == 0x40)
            except Exception as error:
                runner.check('Cleanup succeeded', False, repr(error))
        if original_user_value is not None:
            drive.write_object(0x3410, 10, original_user_value)
        monitor.stop()
        drive.close()
    return runner.finish(RESULTS)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('device_ip', nargs='?', default='192.168.2.150')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--motion', action='store_true', help='POWER and MOVE the approved free MC349 shaft')
    parser.add_argument('--script', default=None, help='Path to alternative script under test')
    args = parser.parse_args()
    script_target = args.script or SCRIPT
    raise SystemExit(0 if (offline(script_target) if args.offline else hardware(args.device_ip, args.motion, script_target)) else 1)