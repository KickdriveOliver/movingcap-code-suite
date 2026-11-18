---
applyTo: "app-scripts/**/*.py"
description: "MovingCap CODE (MicroPython) coding rules for drive application scripts in app-scripts/."
---
# MovingCap CODE (MicroPython) Script Rules

Files in `app-scripts/` are **MovingCap CODE MicroPython** scripts that run on a MovingCap
Ethernet ETH servo drive — not desktop Python. Always treat "Python" here as drive-side
MicroPython. (Host-side tooling in `testing/` is ordinary CPython and is NOT covered by
these rules.)

## Allowed APIs only
- Use ONLY modules, functions, and patterns documented in
  [`.github/skills/movingcap-code-python-writer/SKILL.md`](../skills/movingcap-code-python-writer/SKILL.md),
  the `app-scripts/*.pyi` stubs, `movingcap.de` docs, or the explicitly validated
  MicroPython modules and methods listed below.
- Do NOT invent function names, arguments, return values, or side effects.
- Do NOT assume desktop-Python or standard-library modules are available unless the
  MovingCap docs or the validated table below explicitly show them.

## Syntax & style constraints
- Do NOT use f-strings — they are unavailable. Format strings with `%` modulo formatting
  (`'status=0x%04X, pos=%d' % (sw, pos)`) or concatenation (`'pos=' + str(pos)`).
- Do NOT use floating-point literals (`float`) or `math`/`cmath` — use integer or
  fixed-point arithmetic.
- Prefer `time.sleep_ms(ms)` over the legacy `sys.wait(ms)`.
- Keep scripts small, conservative, and matched to the drive's documented capabilities.

## Motion & IO safety
- Wait for motion completion with `mc.ChkReady()` and check `mc.ChkError()` before continuing.
  Prefer a bounded wait (timeout) over an infinite loop so faults are handled.
- Use a clean enable/disable sequence (`mc.EnableDrive()` … `mc.PowerQuit()`).
- Do not assume speed, acceleration, current, or direction settings unless the spec gives them.
- Add a comment whenever a line can move the axis, power the drive, or switch an output.

## MicroPython options enabled / modules available (Firmware v5X.XX.13.00+)

The following features are explicitly configured in the MovingCap CODE MicroPython port
(`mpconfigport.h`) starting with firmware **v5X.XX.13.00** across all MovingCap ETH motor
variants. This is not an exhaustive inventory of core language builtins (`list`, `dict`,
`tuple`, `bytes`, `range`, `int`, etc.), but defines which optional MicroPython features
and modules are enabled vs. disabled.

```c
// MovingCap CODE - mpconfigport.h excerpt (firmware v5X.XX.13.00 or higher)
#define MICROPY_ENABLE_GC                   (1)
#define MICROPY_ENABLE_SOURCE_LINE          (1)
#define MICROPY_PY_GC                       (1)
#define MICROPY_PY_MICROPYTHON_MEM_INFO     (1)
#define MICROPY_PY_ARRAY                    (1)
#define MICROPY_PY_COLLECTIONS              (1)
#define MICROPY_PY_STRUCT                   (1)
#define MICROPY_CPYTHON_COMPAT              (1)
#define MICROPY_LONGINT_IMPL                (MICROPY_LONGINT_IMPL_MPZ)

// Explicitly guarantee string modulo formatting ('... %d' % value) stays enabled
#define MICROPY_PY_BUILTINS_STR_OP_MODULO   (1)
// Explicitly guarantee string substring counting (.count() method)
#define MICROPY_PY_BUILTINS_STR_COUNT       (1)
// uses modsys.c features now
#define FULLMO_MPY_SYS_EXTENSIONS           (1)
// added UTIME implementation
#define MICROPY_PY_UTIME_MP_HAL             (1)
// for mcnet protocol applications, support
#define MICROPY_PY_UBINASCII                (1)

// extra string & sequence processing capabilities
#define MICROPY_PY_BUILTINS_STR_SPLITLINES  (1)
#define MICROPY_PY_BUILTINS_STR_PARTITION   (1)
#define MICROPY_PY_BUILTINS_SLICE           (1)
```

### Validated import names and operations

| Import | Alternative | Validated capabilities |
|---|---|---|
| `array` | — | `array.array()`, indexing, assignment, iteration, `append()`, buffer-to-buffer `extend()`, readable/writable buffer use |
| `ustruct` | `struct` | `calcsize()`, `pack()`, `pack_into()`, `unpack()`, `unpack_from()` |
| `utime` | `time` | MovingCap timing functions, including `sleep_ms()`, `ticks_ms()`, `ticks_diff()` |
| `ubinascii` | `binascii` | `hexlify()`, `unhexlify()`, `b2a_base64()`, `a2b_base64()` |
| `ucollections` | `collections` | `namedtuple()` creation, attribute access, and tuple indexing |
| `gc` | — | Explicit garbage-collector control (`gc.collect()`, etc.) |
| `micropython` | — | Runtime helpers including `mem_info()` and `qstr_info()` |
| `sys` | — | MovingCap-specific `sys` extensions documented by `app-scripts/sys.pyi` |
| `mcdrive` | `drive` | MovingCap drive API documented by `app-scripts/mcdrive.pyi` |
| `mcnet` | — | MovingCap network API documented by `app-scripts/mcnet.pyi` |
| `refgo` | — | MovingCap RefGo API documented by `app-scripts/refgo.pyi` |

The following string, bytes, and sequence features are explicitly available:

- `%` modulo formatting (`"%d" % val`) and `str.count()`
- `str.splitlines(keepends=False)`
- `str.partition(separator)` and `str.rpartition(separator)`
- `str.encode()` and `bytes.decode()` (via `MICROPY_CPYTHON_COMPAT`, plus `delattr()`)
- Slice syntax (`[2:6]`, `[::2]`, `[:-2]`), including in-place list slice assignment/deletion and `str`/`bytes` slicing

`array` supplies writable storage for `struct.pack_into()` even though `bytearray` and
`memoryview` are disabled. In this MicroPython 1.9.4 implementation, `array.extend()`
requires an object that provides the buffer protocol; use another compatible `array`, not
a plain list.

### Important restrictions

```c
/* Floating-point and math library (disabled) */
#define MICROPY_FLOAT_IMPL                  (MICROPY_FLOAT_IMPL_NONE)
#define MICROPY_PY_MATH                     (0)
#define MICROPY_PY_MATH_SPECIAL_FUNCTIONS   (0)
#define MICROPY_PY_BUILTINS_COMPLEX         (0)
#define MICROPY_PY_CMATH                    (0)

/* Disabled optional builtins / modules */
#define MICROPY_PY_BUILTINS_STR_UNICODE     (0)
#define MICROPY_PY_BUILTINS_BYTEARRAY       (0)
#define MICROPY_PY_BUILTINS_MEMORYVIEW      (0)
#define MICROPY_PY_BUILTINS_SET             (0)
#define MICROPY_PY_BUILTINS_FROZENSET       (0)
#define MICROPY_PY_BUILTINS_PROPERTY        (0)
#define MICROPY_PY_ASYNC_AWAIT              (0)
#define MICROPY_PY_IO                       (0)
#define MICROPY_PY___FILE__                 (0)
```

Consequences:

- **No floating-point (`float`) or `math`/`cmath`:** Use integer or fixed-point arithmetic (arbitrary-precision integers are available via `MPZ`).
- **8-bit strings:** Strings are 8-bit ASCII/byte strings, not Unicode. Treat binary protocol frames as `bytes` where practical.
- **Unavailable builtins/modules:** Do not use f-strings, `bytearray`, `memoryview`, `set`/`frozenset`, `@property`, `async`/`await`, `io`, `__file__`, or desktop stdlib modules (`json`, `re`, `socket`, etc.).