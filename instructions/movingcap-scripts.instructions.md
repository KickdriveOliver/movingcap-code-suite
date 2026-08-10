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
  [`skills/movingcap-code-python-writer/SKILL.md`](../skills/movingcap-code-python-writer/SKILL.md)
  and the `app-scripts/*.pyi` stubs, `movingcap.de` docs, or the explicitly validated
  MicroPython modules and methods listed below.
- Do NOT invent function names, arguments, return values, or side effects.
- Do NOT assume desktop-Python or standard-library modules are available unless the
  MovingCap docs explicitly show them.

## Syntax & style constraints
- Do NOT use f-strings — they are unavailable. Build strings with concatenation:
  `'pos=' + str(pos)`.
- Prefer `time.sleep_ms(ms)` over the legacy `sys.wait(ms)`.
- Keep scripts small, conservative, and matched to the drive's documented capabilities.

## Motion & IO safety
- Wait for motion completion with `mc.ChkReady()` and check `mc.ChkError()` before continuing.
  Prefer a bounded wait (timeout) over an infinite loop so faults are handled.
- Use a clean enable/disable sequence (`mc.EnableDrive()` … `mc.PowerQuit()`).
- Do not assume speed, acceleration, current, or direction settings unless the spec gives them.
- Add a comment whenever a line can move the axis, power the drive, or switch an output.

## Common references
- `mc.GoPosAbs(x)` / `mc.GoPosRel(x)` — absolute / relative move.
- `mc.GoHome(method, vel, acc, offset)` — homing; method 35/37 sets current pos as zero.
- `mc.ChkIn(x)` — read digital input x; `mc.SetOut(x)` / `mc.ClearOut(x)` — set/reset output x.
- `mc.GetActualPos()` — current position; `mc.ReadObject(i, s)` / `mc.WriteObject(i, s, v)` —
  numeric CANopen objects. Free user objects live at 340Bh–3410h (sub 01h–0Ah).

## Micropython options enabled / modules available

The following non-default features are explicitly enabled in the MovingCap CODE
MicroPython build. This is not an exhaustive inventory of core language builtins such as
`list`, `dict`, `tuple`, `bytes`, and `range`. Do not assume other optional standard-library
modules are available unless the MovingCap docs or stubs explicitly list them.

```C
// MovingCap CODE - Micropython options enabled
// MovingCap firmware v50.00.12.00 (MC349) or higher
#define MICROPY_ENABLE_GC           (1)
#define MICROPY_ENABLE_SOURCE_LINE  (1)
#define MICROPY_PY_BUILTINS_SLICE   (1)
#define MICROPY_PY_MICROPYTHON_MEM_INFO (1)
#define MICROPY_PY_GC               (1)
#define MICROPY_PY_COLLECTIONS      (1)
#define MICROPY_PY_STRUCT           (1)
#define MICROPY_PY_ARRAY            (1)
#define MICROPY_CPYTHON_COMPAT      (1)
#define MICROPY_PY_BUILTINS_STR_OP_MODULO   (1)
#define MICROPY_PY_BUILTINS_STR_COUNT       (1)
#define MICROPY_PY_UTIME_MP_HAL (1)
#define MICROPY_PY_UBINASCII (1)
#define MICROPY_PY_BUILTINS_STR_SPLITLINES (1)
#define MICROPY_PY_BUILTINS_STR_PARTITION (1)
```

### Validated import names and operations

| Import | Alternative | Validated capabilities |
|---|---|---|
| `array` | — | `array.array()`, indexing, assignment, iteration, `append()`, buffer-to-buffer `extend()`, readable/writable buffer use |
| `ustruct` | `struct` | `calcsize()`, `pack()`, `pack_into()`, `unpack()`, `unpack_from()` |
| `utime` | `time` | MovingCap timing functions, including `sleep_ms()` and `ticks_ms()` |
| `ubinascii` | `binascii` | Binary/ASCII conversion functions supplied by the firmware module |
| `ucollections` | `collections` | `namedtuple()` creation, attribute access, and tuple indexing |
| `gc` | — | Explicit garbage-collector control |
| `micropython` | — | Runtime helpers including `mem_info()` and `qstr_info()` |
| `sys` | — | MovingCap-specific `sys` extensions documented by the supplied stub |
| `mcdrive` | `drive` | MovingCap drive API documented by `mcdrive.pyi` |
| `mcnet` | — | MovingCap network API documented by `mcnet.pyi` |
| `refgo` | — | MovingCap RefGo API documented by `refgo.pyi` |

The following string methods are explicitly available for both the port's 8-bit `str`
configuration and `bytes` where supported by MicroPython 1.9.4:

- `str.count()` and `%` formatting
- `str.splitlines(keepends=False)`
- `str.partition(separator)` and `str.rpartition(separator)`

`array` supplies writable storage for `struct.pack_into()` even though `bytearray` and
`memoryview` are disabled. In this MicroPython 1.9.4 implementation, `array.extend()`
requires an object that provides the buffer protocol; use another compatible `array`, not
a plain list.

### Important restrictions

```C
#define MICROPY_PY_BUILTINS_STR_UNICODE (0)
#define MICROPY_LONGINT_IMPL        (MICROPY_LONGINT_IMPL_MPZ)
#define MICROPY_FLOAT_IMPL          (MICROPY_FLOAT_IMPL_NONE)
#define MICROPY_PY_MATH             (0)
#define MICROPY_PY_CMATH            (0)
#define MICROPY_PY_BUILTINS_COMPLEX (0)
#define MICROPY_PY_BUILTINS_BYTEARRAY (0)
#define MICROPY_PY_BUILTINS_MEMORYVIEW (0)
#define MICROPY_PY_BUILTINS_SET     (0)
#define MICROPY_PY_BUILTINS_FROZENSET (0)
#define MICROPY_PY_BUILTINS_PROPERTY (0)
#define MICROPY_PY_ASYNC_AWAIT      (0)
#define MICROPY_PY_IO               (0)
#define MICROPY_PY___FILE__         (0)
```

Consequences:

- Strings are 8-bit strings, not full Unicode strings. Treat protocol/binary data as
  `bytes` where practical.
- Floating-point literals and the `math`/`cmath` modules are unavailable; use integer or
  fixed-point calculations.
- Do not generate examples using `bytearray`, `memoryview`, sets, properties, async/await,
  `io`, or `__file__`.