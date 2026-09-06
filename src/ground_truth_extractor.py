"""
Ground-truth worker: execute one real notebook's cells in a specified order
and snapshot the final variable state.

Called as a subprocess by tests/run_real_state_groundtruth.py:

    python3 src/ground_truth_extractor.py <notebook.ipynb> <ec|visual>

- `ec`     — cells sorted by execution_count (the order the user really ran)
- `visual` — cells in file order (the order a naive reader simulates)

Executes the SAME set of executed code cells under both orders; the diff of
the two final states is, by construction, the effect of execution order on
real code. Cells that raise are recorded and execution continues (matching
real Jupyter sessions, where a failed cell does not end the kernel).

Global RNGs are seeded identically in both runs so divergence reflects
order, not sampling noise. Per-cell SIGALRM timeout; matplotlib forced to
Agg. Prints a JSON result to stdout (single line, prefixed with GT_JSON:).

DATA SUBSTITUTION (when GT_SYNTH=1): real ML notebooks die at the first
`pd.read_csv('data.csv')` of a file that isn't bundled, and everything
downstream depends on it. To unblock those cells we monkeypatch the common
data loaders (pandas/numpy readers) to return a deterministic,
schema-inferred synthetic frame when the real file is absent. The SAME
synthetic input feeds BOTH execution orders, so the substitution can only
*enable* a cell to run — it can never manufacture an order-divergence.
Divergences therefore remain attributable to execution order, not to the
substituted data. (The divergent value is not the user's original value;
the divergent code path is real.) Column names are inferred from the
notebook's own subscripting (`df['col']`), so downstream `df['col']`
accesses resolve instead of KeyError-ing.
"""
import os
import re
import sys
import json
import signal
import types

CELL_TIMEOUT_S = 10
MAX_REPR = 200
SYNTH = os.environ.get("GT_SYNTH") == "1"
SYNTH_ROWS = 100

os.environ.setdefault("MPLBACKEND", "Agg")


class CellTimeout(Exception):
    pass


def _alarm_handler(signum, frame):
    raise CellTimeout()


def load_cells(path, order):
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    cells = []
    for idx, c in enumerate(nb.get("cells", [])):
        if c.get("cell_type") != "code":
            continue
        ec = c.get("execution_count")
        try:
            ec = int(ec)
        except (TypeError, ValueError):
            continue
        src = c.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        cells.append({"ec": ec, "idx": idx, "code": src})
    if order == "ec":
        cells.sort(key=lambda c: (c["ec"], c["idx"]))
    return cells


# --- Data substitution (GT_SYNTH=1) ---------------------------------------
_SUBSCRIPT_RE = re.compile(r"""\[\s*['"]([A-Za-z_][\w \-./]{0,40})['"]\s*\]""")
_CAT_HINT = re.compile(r"(type|category|categor|label|class|name|sex|gender|"
                       r"target|status|group|color|country|city|region|"
                       r"brand|product|segment)", re.I)
_TARGET_HINT = re.compile(r"(target|label|class|^y$|survived|churn|default|"
                          r"fraud|outcome|is_)", re.I)


def infer_columns(all_source: str):
    """Column names the notebook subscripts out of a DataFrame."""
    cols = []
    seen = set()
    for m in _SUBSCRIPT_RE.finditer(all_source):
        name = m.group(1).strip()
        if name and name not in seen and not name.isdigit():
            seen.add(name)
            cols.append(name)
    return cols[:60]  # cap width


def make_synthetic_df(cols, seed=0):
    import numpy as np
    import pandas as pd
    rng = np.random.RandomState(seed)
    if not cols:
        cols = [f"col{i}" for i in range(6)]
    data = {}
    for c in cols:
        if _TARGET_HINT.search(c):
            data[c] = rng.randint(0, 2, SYNTH_ROWS)          # binary target
        elif _CAT_HINT.search(c):
            data[c] = rng.choice(list("ABCD"), SYNTH_ROWS)   # categorical
        else:
            data[c] = rng.rand(SYNTH_ROWS).astype("float64")  # numeric
    return pd.DataFrame(data)


def install_data_substitution(all_source: str):
    """Monkeypatch pandas/numpy readers to return a synthetic frame when the
    real file is missing. Both orders call this with identical seeds → same
    frame → any divergence is order-attributable."""
    cols = infer_columns(all_source)
    try:
        import numpy as np
        import pandas as pd
    except ImportError:
        return

    def _synth_df(*args, **kwargs):
        return make_synthetic_df(cols, seed=0).copy()

    def _guard(orig):
        def wrapper(*args, **kwargs):
            path = args[0] if args else kwargs.get("filepath_or_buffer")
            if isinstance(path, str) and not os.path.exists(path):
                return _synth_df()
            try:
                return orig(*args, **kwargs)
            except (FileNotFoundError, OSError, ValueError):
                return _synth_df()
        return wrapper

    for name in ("read_csv", "read_table", "read_excel", "read_json",
                 "read_parquet", "read_feather"):
        if hasattr(pd, name):
            setattr(pd, name, _guard(getattr(pd, name)))

    def _synth_array(*args, **kwargs):
        return np.random.RandomState(0).rand(SYNTH_ROWS, 8)

    for name in ("load", "loadtxt", "genfromtxt"):
        if hasattr(np, name):
            orig = getattr(np, name)
            def _npguard(o):
                def w(*a, **k):
                    p = a[0] if a else None
                    if isinstance(p, str) and not os.path.exists(p):
                        return _synth_array()
                    try:
                        return o(*a, **k)
                    except (FileNotFoundError, OSError, ValueError):
                        return _synth_array()
                return w
            setattr(np, name, _npguard(orig))


def summarize(value):
    """Compact, deterministic summary of a variable for state comparison."""
    try:
        t = type(value).__name__
        if isinstance(value, (bool, int, float, complex)):
            return f"{t}:{value!r}"
        if isinstance(value, str):
            v = value if len(value) <= MAX_REPR else value[:MAX_REPR] + "..."
            return f"str:{v!r}"
        if isinstance(value, (list, tuple, set, frozenset, dict)):
            r = repr(value)
            if len(r) > MAX_REPR:
                r = r[:MAX_REPR] + "..."
            return f"{t}(len={len(value)}):{r}"
        mod = type(value).__module__
        if mod.startswith("numpy"):
            import numpy as np
            if isinstance(value, np.ndarray):
                head = repr(value.ravel()[:8].tolist()) if value.size else "[]"
                return f"ndarray(shape={value.shape},dtype={value.dtype}):{head}"
            return f"{t}:{value!r}"[:MAX_REPR]
        if mod.startswith("pandas"):
            import pandas as pd
            if isinstance(value, pd.DataFrame):
                cols = list(map(str, value.columns[:10]))
                return f"DataFrame(shape={value.shape},cols={cols})"
            if isinstance(value, pd.Series):
                head = value.head(5).tolist()
                return f"Series(len={len(value)},dtype={value.dtype}):{head}"
        r = repr(value)
        if len(r) > 120:
            r = r[:120] + "..."
        return f"{t}:{r}"
    except Exception as e:  # repr itself can raise on broken objects
        return f"{type(value).__name__}:<unreprable {type(e).__name__}>"


def snapshot(ns):
    out = {}
    for name, value in ns.items():
        if name.startswith("_") or name in ("In", "Out"):
            continue
        if isinstance(value, (types.ModuleType, types.FunctionType,
                              types.BuiltinFunctionType, types.MethodType,
                              types.BuiltinMethodType, type)):
            continue
        out[name] = summarize(value)
    return out


def main():
    path, order = sys.argv[1], sys.argv[2]
    cells = load_cells(path, order)

    # Identical seeds in both runs: divergence must come from order, not RNG
    import random
    random.seed(0)
    try:
        import numpy as np
        np.random.seed(0)
    except ImportError:
        pass

    if SYNTH:
        all_source = "\n".join(c["code"] for c in cells)
        try:
            install_data_substitution(all_source)
        except Exception:
            pass  # substitution is best-effort; never fail the run over it

    ns = {"__name__": "__main__"}
    cell_log = []
    signal.signal(signal.SIGALRM, _alarm_handler)

    for cell in cells:
        status = "ok"
        signal.alarm(CELL_TIMEOUT_S)
        try:
            code = compile(cell["code"], f"<cell ec={cell['ec']}>", "exec")
            exec(code, ns)
        except CellTimeout:
            status = "timeout"
        except SyntaxError:
            status = "syntax_error"  # magics / shell escapes
        except BaseException as e:  # noqa: BLE001 — must survive SystemExit etc.
            status = f"error:{type(e).__name__}"
        finally:
            signal.alarm(0)
        cell_log.append({"ec": cell["ec"], "status": status})

    result = {
        "order": order,
        "synth": SYNTH,
        "n_cells": len(cells),
        "n_ok": sum(1 for c in cell_log if c["status"] == "ok"),
        "cells": cell_log,
        "variables": snapshot(ns),
    }
    print("GT_JSON:" + json.dumps(result))


if __name__ == "__main__":
    main()
