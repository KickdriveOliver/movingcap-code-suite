#id mc_rest_api_example.py v0.0.2 2026-11-18
# MovingCap CODE REST-API server example
# see mc_rest_api_example_README.md for details

import mcnet
import mcdrive as mc
import refgo
import time
import gc
from collections import namedtuple

API_NAME = 'mc_rest_api_example'
API_VERSION = '0.0.1'
API_ENDPOINTS = (
    'GET /api/status', 'GET /api/motor', 'GET /api/config',
    'GET/PUT /api/objects/index/subindex', 'POST /api/refgo',
    'POST /api/move', 'POST /api/velocity', 'POST /api/stop',
    'POST /api/continue', 'POST /api/enable', 'POST /api/disable',
)
API_DISCOVERY_BODY = ('{"name":"%s","version":"%s","endpoints":["%s"]}'
                      % (API_NAME, API_VERSION, '","'.join(API_ENDPOINTS)))
PORT = 8080
MAX_REQUEST = 2048
REQUEST_TIMEOUT_MS = 1000
SAMPLE_MS = 50
POWER_SAMPLES = 20
MOTION_TIMEOUT_MS = 60000
Request = namedtuple('Request', ('method', 'path', 'body', 'close'))
REASONS = {200: 'OK', 202: 'Accepted', 400: 'Bad Request', 404: 'Not Found',
           405: 'Method Not Allowed', 408: 'Request Timeout', 409: 'Conflict',
           413: 'Payload Too Large', 415: 'Unsupported Media Type',
           422: 'Unprocessable Entity', 500: 'Internal Server Error'}


class ApiError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


class Application:
    def __init__(self):
        self.last_move = None
        self.started = None
        self.stopped = False
        self.motion = 'idle'
        self.errors = []
        self.error_signature = None
        self.samples = [0] * POWER_SAMPLES
        self.sample_count = 0
        self.sample_slot = 0
        self.power_sum = 0
        self.power_instant = None
        self.last_sample = time.ticks_ms()


APP = Application()


def divide_signed(numerator, denominator):
    value = abs(numerator) // denominator
    return -value if numerator < 0 else value


def decimal_percent(value):
    if value is None:
        return 'null'
    sign = '-' if value < 0 else ''
    value = abs(value)
    return '%s%d.%02d' % (sign, value // 100, value % 100)


def service(now):
    if time.ticks_diff(now, APP.last_sample) < SAMPLE_MS:
        return
    APP.last_sample = now
    current = mc.ReadObject(0x6078, 0)
    velocity = mc.ReadObject(0x606C, 0)
    maximum = mc.ReadObject(0x6080, 0)
    if maximum > 0:
        sample = divide_signed(abs(current) * velocity * 10, maximum)
        APP.power_instant = sample
        APP.power_sum += sample - APP.samples[APP.sample_slot]
        APP.samples[APP.sample_slot] = sample
        APP.sample_slot = (APP.sample_slot + 1) % POWER_SAMPLES
        APP.sample_count = min(APP.sample_count + 1, POWER_SAMPLES)
    else:
        APP.power_instant = None
        APP.samples = [0] * POWER_SAMPLES
        APP.sample_count, APP.sample_slot, APP.power_sum = 0, 0, 0
    fault = mc.ChkError() != 0
    code = mc.ReadObject(0x603F, 0) & 0xffff
    manufacturer = mc.ReadObject(0x1002, 0) & 0xffffffff
    signature = (fault, code, manufacturer)
    if (fault or code) and signature != APP.error_signature:
        APP.errors.append({'error_code': code, 'manufacturer_status': manufacturer,
                           'position': mc.GetActualPos(), 'time_ms': now})
        if len(APP.errors) > 8:
            APP.errors.pop(0)
    APP.error_signature = signature
    if APP.started is not None:
        if fault:
            APP.motion, APP.started = 'fault', None
        elif APP.last_move[0] == 'position' and mc.ChkReady():
            APP.motion, APP.started = 'reached', None
        elif time.ticks_diff(now, APP.started) >= MOTION_TIMEOUT_MS:
            # Timeout quick-stops the axis using the configured 6085h ramp.
            mc.StopMotion()
            APP.motion, APP.stopped, APP.started = 'timeout', True, None


def status_json():
    status = mc.ReadStatusword()
    position = mc.GetActualPos()
    velocity = mc.ReadObject(0x606C, 0)
    threshold = mc.ReadObject(0x606F, 0) & 0xffffffff
    moving = abs(velocity) > threshold
    direction = 'positive' if velocity > 0 else 'negative'
    if not moving or velocity == 0:
        direction = 'none'
    return ('{"position":%d,"velocity":%d,"velocity_threshold":%d,"moving":%s,"direction":"%s",'
            '"statusword":%d,"mode":%d,"fault":%s,"error_code":%d,'
            '"manufacturer_status":%d,"target_reached":%s,"motion":"%s",'
            '"last_move":%s,"error_history":%s}'
            % (position, velocity, threshold, json_encode(moving), direction, status,
               mc.ReadObject(0x6061, 0), json_encode(bool(status & 8)),
               mc.ReadObject(0x603F, 0) & 0xffff,
               mc.ReadObject(0x1002, 0) & 0xffffffff,
               json_encode(bool(status & 0x400)), APP.motion,
               json_encode(APP.last_move), json_encode(APP.errors)))


def motor_json():
    average = divide_signed(APP.power_sum, APP.sample_count) if APP.sample_count else None
    return ('{"current_actual":%d,"velocity_actual":%d,"max_motor_speed":%d,'
            '"motor_temperature_raw":%d,"mechanical_power_percent":%s,'
            '"mechanical_power_instant_percent":%s,"samples":%d,'
            '"sample_interval_ms":%d,"window_ms":%d}'
            % (mc.ReadObject(0x6078, 0), mc.ReadObject(0x606C, 0),
               mc.ReadObject(0x6080, 0), mc.ReadObject(0x3401, 10),
               decimal_percent(average), decimal_percent(APP.power_instant),
               APP.sample_count, SAMPLE_MS, SAMPLE_MS * POWER_SAMPLES))


def config_json():
    read = mc.ReadObject
    return ('{"profile_velocity":%d,"acceleration":%d,"deceleration":%d,'
            '"softlimit_min":%d,"softlimit_max":%d,"motion_timeout_ms":%d}'
            % (read(0x6081, 0), read(0x6083, 0), read(0x6084, 0),
               read(0x607D, 1), read(0x607D, 2), MOTION_TIMEOUT_MS))


def enabled():
    if mc.ChkError():
        raise ApiError(409, 'Drive fault active; use REFGO or object access to reset')
    if (mc.ReadStatusword() & 0x6f) != 0x27:
        raise ApiError(409, 'Enable the drive before motion')


def move(kind, target, velocity):
    enabled()
    if kind == 'position':
        mc.SetPosVel(velocity)
        # Starts asynchronous absolute position motion.
        mc.GoPosAbs(target)
    else:
        # Starts asynchronous profile velocity motion.
        mc.GoVel(velocity)
    APP.last_move = (kind, target, velocity)
    APP.started, APP.stopped, APP.motion = time.ticks_ms(), False, 'moving'
    return 202, {'accepted': True, 'last_move': APP.last_move}


def json_string(value):
    result = '"'
    for char in value:
        number = ord(char)
        if char == '"' or char == '\\':
            result += '\\' + char
        elif number < 32 or number > 126:
            result += '\\u%04x' % number
        else:
            result += char
    return result + '"'


def json_encode(value):
    if value is None:
        return 'null'
    if type(value) is bool:
        return 'true' if value else 'false'
    if type(value) is int:
        return str(value)
    if type(value) is str:
        return json_string(value)
    if type(value) is dict:
        return '{' + ','.join([json_string(key) + ':' + json_encode(value[key])
                               for key in value]) + '}'
    return '[' + ','.join([json_encode(item) for item in value]) + ']'


def parse_json(text):
    text = text.strip()
    if len(text) < 2 or text[0] != '{' or text[-1] != '}':
        raise ApiError(400, 'Expected a flat JSON object')
    result = {}
    rest = text[1:-1].strip()
    while rest:
        if rest[0] != '"':
            raise ApiError(400, 'Expected a quoted key')
        key, separator, rest = rest[1:].partition('"')
        if not separator or not key or '\\' in key or key in result:
            raise ApiError(400, 'Invalid or duplicate key')
        rest = rest.lstrip()
        if not rest or rest[0] != ':':
            raise ApiError(400, 'Expected colon')
        rest = rest[1:].lstrip()
        if rest.startswith('"'):
            value, separator, rest = rest[1:].partition('"')
            if not separator or '\\' in value:
                raise ApiError(400, 'Escaped strings are not supported')
            for char in value:
                if ord(char) < 32 or ord(char) > 126:
                    raise ApiError(400, 'Strings must be printable ASCII')
        else:
            token, separator, tail = rest.partition(',')
            rest = (',' + tail) if separator else ''
            token = token.strip()
            if token in ('true', 'false', 'null'):
                value = {'true': True, 'false': False, 'null': None}[token]
            else:
                digits = token[1:] if token.startswith('-') else token
                if not digits or any(char not in '0123456789' for char in digits):
                    raise ApiError(400, 'Expected a decimal integer')
                if len(digits) > 10 or (len(digits) > 1 and digits[0] == '0'):
                    raise ApiError(400, 'Invalid integer')
                value = int(token)
        result[key] = value
        rest = rest.strip()
        if rest:
            if rest[0] != ',' or not rest[1:].strip():
                raise ApiError(400, 'Expected another member after comma')
            rest = rest[1:].strip()
    return result


def fields(args, required, optional=()):
    for key in args:
        if key not in required and key not in optional:
            raise ApiError(400, 'Unknown field: ' + key)
    for key in required:
        if key not in args:
            raise ApiError(400, 'Missing field: ' + key)


def integer(value, minimum, maximum):
    if type(value) is not int or value < minimum or value > maximum:
        raise ApiError(422, 'Integer outside permitted range')
    return value


def object_address(path):
    parts = path.split('/')
    if len(parts) != 2:
        raise ApiError(400, 'Expected index/subindex')
    address = []
    for token in parts:
        try:
            if token.lower().startswith('0x'):
                value = int(token, 16)
            elif token.lower().endswith('h'):
                value = int(token[:-1], 16)
            else:
                value = int(token)
        except ValueError:
            raise ApiError(400, 'Invalid object address')
        address.append(value)
    return integer(address[0], 0, 65535), integer(address[1], 0, 255)


def dispatch(request):
    method, path, body = request[:3]
    if path in ('/api', '/api/status', '/api/motor', '/api/config'):
        if method != 'GET':
            raise ApiError(405, 'Use GET; change configuration via numeric object PUT')
        if path == '/api/status':
            return 200, status_json()
        if path == '/api/motor':
            return 200, motor_json()
        if path == '/api/config':
            return 200, config_json()
        return 200, API_DISCOVERY_BODY
    if path in ('/api/move', '/api/velocity', '/api/stop', '/api/continue',
                '/api/enable', '/api/disable'):
        if method != 'POST':
            raise ApiError(405, 'Use POST')
        args = parse_json(body)
        if path == '/api/move':
            fields(args, ('position', 'velocity'))
            target = integer(args['position'], -0x80000000, 0x7fffffff)
            velocity = integer(args['velocity'], 1, 0x7fffffff)
            return move('position', target, velocity)
        if path == '/api/velocity':
            fields(args, ('velocity',))
            velocity = integer(args['velocity'], -0x7fffffff, 0x7fffffff)
            return move('velocity', None, velocity)
        fields(args, ())
        if path == '/api/enable':
            if mc.ChkError():
                raise ApiError(409, 'Drive fault active')
            # Powers the drive, without commanding a move.
            if not mc.EnableDrive():
                raise ApiError(409, 'Drive could not be enabled')
        elif path == '/api/disable':
            if mc.ChkMoving():
                raise ApiError(409, 'Stop and wait for standstill before disabling')
            # Removes power and resets the operation mode.
            mc.PowerQuit()
            APP.started, APP.stopped, APP.motion = None, False, 'disabled'
        elif path == '/api/stop':
            # Quick-stops using the existing 6085h deceleration setting.
            mc.StopMotion()
            APP.started, APP.stopped, APP.motion = None, True, 'stopped'
        elif path == '/api/continue':
            if APP.last_move is None or not APP.stopped:
                raise ApiError(409, 'No stopped API move to continue')
            if mc.ChkError():
                raise ApiError(409, 'Drive fault active')
            if (mc.ReadStatusword() & 0x6f) != 0x07:
                raise ApiError(409, 'Drive is not in quick-stop active state')
            kind, target, velocity = APP.last_move
            if kind == 'position':
                mc.SetPosVel(velocity)
                mc.SetTargetPos(target)
            else:
                # Restores the velocity target that native continuation resumes.
                mc.WriteObject(0x60FF, 0, velocity)
            # Resumes power/motion from quick-stop using the native drive API.
            mc.ContinueMotion()
            # Restores operation-enabled after the firmware's quick-stop resume.
            if not mc.EnableDrive():
                raise ApiError(409, 'Drive could not leave quick-stop state')
            return move(kind, target, velocity)
        return 202, {'accepted': True}
    if path.startswith('/api/objects/'):
        index, subindex = object_address(path[len('/api/objects/'):])
        if method == 'GET':
            return 200, {'index': index, 'subindex': subindex,
                         'value': mc.ReadObject(index, subindex)}
        if method == 'PUT':
            args = parse_json(body)
            fields(args, ('value',))
            value = integer(args['value'], -0x80000000, 0x7fffffff)
            # Generic object writes can POWER/MOVE the axis or SWITCH outputs.
            code = mc.WriteObject(index, subindex, value)
            if code != 0:
                return 422, {'error': 'Object write failed', 'code': code}
            return 200, {'index': index, 'subindex': subindex, 'value': value}
        raise ApiError(405, 'Use GET or PUT for numeric objects')
    if path == '/api/refgo':
        if method != 'POST':
            raise ApiError(405, 'Use POST')
        args = parse_json(body)
        fields(args, ('command',))
        command = args['command']
        if type(command) is not str or not command or len(command) > 128:
            raise ApiError(422, 'Expected one REFGO command, up to 128 characters')
        # REFGO commands can POWER/MOVE the axis or SWITCH outputs.
        result = refgo.cmd(command)
        if result is None:
            raise ApiError(422, 'REFGO returned no response')
        return 200, {'response': result}
    raise ApiError(404, 'Unknown endpoint')


def parse_request(buffer):
    header, separator, remaining = buffer.partition('\r\n\r\n')
    if not separator:
        return None
    lines = header.splitlines()
    parts = lines[0].split(' ')
    if len(parts) != 3 or parts[2] not in ('HTTP/1.0', 'HTTP/1.1'):
        raise ApiError(400, 'Invalid HTTP request line')
    headers = {}
    for line in lines[1:]:
        key, colon, value = line.partition(':')
        key = key.strip().lower()
        if not colon or not key or key in headers:
            raise ApiError(400, 'Invalid or duplicate HTTP header')
        headers[key] = value.strip()
    if 'transfer-encoding' in headers or 'expect' in headers:
        raise ApiError(400, 'Chunked bodies and Expect are not supported')
    length = headers.get('content-length', '0')
    if not length or any(char not in '0123456789' for char in length):
        raise ApiError(400, 'Invalid Content-Length')
    if len(length) > 4:
        raise ApiError(413, 'Request exceeds size limit')
    length = int(length)
    if len(header) + 4 + length > MAX_REQUEST:
        raise ApiError(413, 'Request exceeds size limit')
    if length and headers.get('content-type', '').partition(';')[0].lower() != 'application/json':
        raise ApiError(415, 'Use application/json')
    if len(remaining) < length:
        return None
    if len(remaining) != length:
        raise ApiError(400, 'Only one request per connection is supported')
    close = parts[2] == 'HTTP/1.0' or headers.get('connection', '').lower() == 'close'
    return Request(parts[0], parts[1], remaining[:length], close)


def main():
    server = mcnet.McNet('SERVER:' + str(PORT))
    server.set_line_mode(1, 0, 0, 0, 0, 1)
    buffer, response = '', ''
    connected_at, close_at = None, None
    close_reply = False
    last_gc = time.ticks_ms()
    print(API_NAME + ' started version=' + API_VERSION + ' port=' + str(PORT))
    while True:
        now = time.ticks_ms()
        service(now)
        if close_at is not None:
            if time.ticks_diff(now, close_at) >= 10:
                server.close()
                server.open('SERVER:' + str(PORT))
                server.set_line_mode(1, 0, 0, 0, 0, 1)
                buffer, response, connected_at, close_at = '', '', None, None
            time.sleep_ms(1)
            continue
        if server.is_connected():
            started = None
            status, data = None, None
            try:
                if not response:
                    chunk = server.read(MAX_REQUEST + 1 - len(buffer))
                    if chunk is not None and len(chunk) == 0:
                        buffer, connected_at = '', None
                    if chunk:
                        if connected_at is None:
                            connected_at = now
                        buffer += chunk
                    if len(buffer) > MAX_REQUEST:
                        raise ApiError(413, 'Request exceeds size limit')
                    started = time.ticks_ms()
                    request = parse_request(buffer)
                    if request is not None:
                        close_reply = request.close
                        status, data = dispatch(request)
                if (not response and status is None and connected_at is not None
                        and time.ticks_diff(now, connected_at) >= REQUEST_TIMEOUT_MS):
                    raise ApiError(408, 'Incomplete request timed out')
            except ApiError as error:
                status, data = error.status, {'error': error.message}
                close_reply = True
            except Exception as error:
                print('REST error: ' + str(error))
                status, data = 500, {'error': 'Internal server error'}
                close_reply = True
            if status is not None:
                if started is None:
                    started = time.ticks_ms()
                body = data if type(data) is str else json_encode(data)
                elapsed = time.ticks_diff(time.ticks_ms(), started)
                connection = 'close' if close_reply else 'keep-alive'
                response = ('HTTP/1.1 %d %s\r\nContent-Type: application/json\r\n'
                            'Content-Length: %d\r\nConnection: %s\r\n'
                                     'X-API-Name: %s\r\nX-API-Version: %s\r\n'
                            'Cache-Control: no-store\r\nX-Processing-Time-Ms: %d\r\n\r\n%s'
                                     % (status, REASONS[status], len(body), connection,
                                         API_NAME, API_VERSION, elapsed, body))
            if response:
                written = server.write(response)
                if written > 0:
                    response = response[written:]
                if not response:
                    buffer, connected_at = '', None
                    if close_reply:
                        close_at = time.ticks_ms()
                elif written < 0 or time.ticks_diff(now, connected_at) > REQUEST_TIMEOUT_MS:
                    close_at = time.ticks_ms()
        else:
            buffer, response, connected_at = '', '', None
        if not buffer and not response and time.ticks_diff(now, last_gc) >= 1000:
            gc.collect()
            last_gc = now
        time.sleep_ms(1)


if __name__ == '__main__':
    main()