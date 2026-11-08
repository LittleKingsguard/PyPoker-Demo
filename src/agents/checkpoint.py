"""`save`, `load`, the zip container and its metadata (`checkpoint.md` §1-§5).

A checkpoint is a zip with exactly two members, written through an open file handle so
the caller's spelling is honoured byte for byte — `numpy.savez` would append `.npz`,
never `os.makedirs`, never a suffix swap (`checkpoint.md` §2, G11).  `metadata.json`
carries the fields of §2.1 — the rule its learner was trained under among them — and
`parameters.npy` one `float64`, C-order, 1-D array of length `2·P + M`: the online
parameters, the target copy, then each sparse layer's mask as `0.0`/`1.0`.

`format_version` is 2 (`rules.md` §6, D-19).  The repository ships 18 containers of
version 1, written before the catalogue existed, and none is regenerated: a version-1
file carries no `learning_rule` and is read as `masked-q-learning`, the only rule its
writer could have used.  A version-1 file that *carries* the field is refused by name,
because no version-1 writer wrote one (`checkpoint.md` §3).
"""

from __future__ import annotations

import io
import json
import os
import zipfile
from collections.abc import Mapping

import numpy

from . import declarations, learner as _learner, model
from .errors import (
    CheckpointMismatch,
    CheckpointUnreadable,
    CheckpointUnwritable,
    UnknownRule,
)

MAGIC = "pypoker-agents-checkpoint"
FORMAT_VERSION = 2
#: The two versions this module reads: 2's required rule, and 1's absence of one.
SUPPORTED_VERSIONS = (1, FORMAT_VERSION)
DTYPE = "float64"
METADATA = "metadata.json"
PARAMETERS = "parameters.npy"

REQUIRED = (
    "format",
    "format_version",
    "dtype",
    "backend",
    "kind",
    "settings",
    "representation",
    "seed",
    "exploration",
    "target",
    "params",
    "tie_break",
)

#: The four settings `checkpoint.md` §2.1 records, all required and all present in a
#: file this module wrote.  On the way back only `width`, `depth` and the resolved
#: `sparsity` are read: `residual` is the kind's, and the kind decides it (§3).
SETTINGS = ("width", "depth", "sparsity", "residual")


def _shape(value):
    """A tuple of ints, or `None`."""
    return None if value is None else [int(size) for size in value]


def _tensors(layout):
    """`params.tensors`: each tensor's name, shape, offset and count, in order."""
    tensors = []
    offset, count = layout.w_in
    tensors.append(
        {
            "name": "input.weights",
            "shape": [layout.input_dim, layout.width],
            "offset": int(offset),
            "count": int(count),
        }
    )
    if layout.dense:
        tensors.append(
            {
                "name": "input.bias",
                "shape": [layout.width],
                "offset": int(layout.b_in),
                "count": layout.width,
            }
        )
    for layer in range(layout.trunk):
        offset, count = layout.trunk_w[layer]
        tensors.append(
            {
                "name": "trunk.%d.weights" % (layer + 1,),
                "shape": [int(count)],
                "offset": int(offset),
                "count": int(count),
            }
        )
        tensors.append(
            {
                "name": "trunk.%d.bias" % (layer + 1,),
                "shape": [layout.width],
                "offset": int(layout.trunk_b[layer]),
                "count": layout.width,
            }
        )
    offset, count = layout.w_out
    tensors.append(
        {
            "name": "output.weights",
            "shape": [layout.width, 3],
            "offset": int(offset),
            "count": int(count),
        }
    )
    tensors.append(
        {
            "name": "output.bias",
            "shape": [3],
            "offset": int(layout.b_out),
            "count": 3,
        }
    )
    return tensors


def _masks_metadata(layout):
    """`params.masks`: each sparse layer's slots, offset and kept count, in order."""
    entries = []
    for layer in range(layout.trunk if layout.sparse else 0):
        entries.append(
            {
                "layer": layer + 1,
                "slots": int(layout.mask_length),
                "offset": int(2 * layout.count + layer * layout.mask_length),
                "kept": int(layout.block_lengths[layer]),
            }
        )
    return entries


def _metadata(learner):
    """The object `checkpoint.md` §2.1 records for one learner."""
    layout = learner.layout
    schedule = declarations.HYPER["exploration"]
    return {
        "format": MAGIC,
        "format_version": FORMAT_VERSION,
        "dtype": DTYPE,
        "backend": learner.backend_name,
        "kind": learner.kind,
        # The catalogue member the learner was trained under: a version-2 field, and the
        # one a table reads to name a member's population (`rules.md` §6, §7, D-19).
        "learning_rule": learner.rule,
        "settings": {
            "width": int(learner.width),
            "depth": int(learner.depth),
            "sparsity": float(learner.sparsity),
            "residual": bool(learner.residual),
        },
        "representation": {
            "family": learner.family,
            "encoding": learner.encoding,
            "size": int(learner.size),
            "shape": _shape(learner.shape),
            "dtype": learner.dtype,
        },
        "seed": int(learner.seed),
        "exploration": {
            "position": int(learner.position),
            "schedule": {
                "start": float(schedule["start"]),
                "end": float(schedule["end"]),
                "samples": int(schedule["samples"]),
            },
        },
        "target": {
            "counter": int(learner.counter),
            "interval": int(declarations.HYPER["target_update_interval"]),
        },
        "params": {
            "count": int(layout.count),
            "target_offset": int(layout.count),
            "length": int(2 * layout.count + layout.mask_count),
            "tensors": _tensors(layout),
            "masks": _masks_metadata(layout),
        },
        "tie_break": {
            "rule": "smallest-masked-index-within-tolerance",
            "tolerance": 1e-09,
        },
    }


def _writable(path):
    """The caller's path as text, or the refusal naming it (`checkpoint.md` §3)."""
    try:
        text = os.fspath(path)
    except TypeError:
        raise CheckpointUnwritable(
            "save(path): the path %r is not a writable file location" % (path,)
        ) from None
    if isinstance(text, bytes):
        text = text.decode()
    parent = os.path.dirname(text) or "."
    if not text or os.path.isdir(text) or not os.path.isdir(parent):
        raise CheckpointUnwritable(
            "save(path): the path %r is not a writable file location" % (text,)
        )
    return text


def save(learner, path):
    """Write one checkpoint at exactly the caller's path, and return it (`surface.md` §8)."""
    held = _learner._require_learner(learner, "save")
    text = _writable(path)
    metadata = _metadata(held)
    backend = held.backend
    online = backend.parameters(held.state)
    masks = backend.masks(held.state)
    array = numpy.concatenate([online, masks]).astype(numpy.float64, copy=False)
    buffer = io.BytesIO()
    numpy.save(buffer, numpy.ascontiguousarray(array), allow_pickle=False)
    try:
        with open(text, "wb") as handle:
            with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as container:
                container.writestr(
                    METADATA, json.dumps(metadata, sort_keys=False).encode("utf-8")
                )
                container.writestr(PARAMETERS, buffer.getvalue())
    except OSError as error:
        raise CheckpointUnwritable(
            "save(path): the path %r is not a writable file location (%s)"
            % (text, error.strerror or error)
        ) from None
    return str(text)


def _path_text(path, entry):
    """The path a reader opens, or the refusal naming it."""
    try:
        text = os.fspath(path)
    except TypeError:
        raise CheckpointUnreadable(
            "%s(path): %r cannot be read: it is not a path" % (entry, path)
        ) from None
    if isinstance(text, bytes):
        text = text.decode()
    return text


# --------------------------------------------------------------------------
# §2.1's form: every field is validated before it is used
# --------------------------------------------------------------------------
def _wrong(text, label, wanted, value):
    """The refusal of a field whose JSON type is not the one §2.1 records (§3)."""
    return CheckpointUnreadable(
        "load(path): %r records the field %r, which must be %s, got %r"
        % (text, label, wanted, value)
    )


def _counted(text, value, label):
    """One JSON integer: never a flag, a float, a string or a `null` (§1)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise _wrong(text, label, "an integer", value)
    return value


def _numbered(text, value, label):
    """One real-valued field: a JSON integer or float, and never a flag."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _wrong(text, label, "a number", value)
    return value


def _named(text, value, label):
    """One JSON string, and nothing else."""
    if not isinstance(value, str):
        raise _wrong(text, label, "a string", value)
    return value


def _flagged(text, value, label):
    """One JSON boolean, and nothing else."""
    if not isinstance(value, bool):
        raise _wrong(text, label, "a bool", value)
    return value


def _recorded(text, value, label):
    """One object of §2.1's form."""
    if not isinstance(value, Mapping):
        raise _wrong(text, label, "an object", value)
    return value


def _listed(text, value, label):
    """One array of §2.1's form."""
    if not isinstance(value, list):
        raise _wrong(text, label, "an array", value)
    return value


def _or_null(check):
    """A validator that also accepts `null`, as §2.1 records an encoder-less build."""

    def _either(text, value, label):
        return None if value is None else check(text, value, label)

    return _either


def _field(text, record, key, label, check):
    """One field of one §2.1 record: present, and of the JSON type §2.1 records.

    A missing key is named, and no `got` clause is invented for it (`errors.md` §3);
    a field that is present but wrong-typed is refused naming the field and the
    offending value.  Nothing is coerced on the way back: a `5.0` or a `"5"` where
    the file's form records an integer is a form this module does not read, because
    `evaluation.policy_from` loads a member from its path alone and the file's own
    fields are then the only authority there is (`surface.md` §1, §9;
    `checkpoint.md` §1, §3; `errors.md` §4).
    """
    if key not in record:
        raise CheckpointUnreadable(
            "load(path): %r has a metadata.json without the field %r" % (text, label)
        )
    return check(text, record[key], label)


#: The JSON type each of §2.1's four settings is recorded as.  `residual` is recorded
#: and never consulted — the kind decides the connection (`architecture.md` §3) — but
#: it is still a field of the form, so a `"true"` is refused like any other field's.
SETTING_TYPES = {
    "width": _counted,
    "depth": _counted,
    "sparsity": _numbered,
    "residual": _flagged,
}


def _form(text, metadata):
    """Refuse a `metadata.json` whose form is not §2.1's (`checkpoint.md` §1-§3).

    Every field a restore reads is validated before it is used, and the fields a
    restore only records — the tensor table, the masks, the schedule, the target's
    interval and the tie-break — with them, so no field of the form can arrive at a
    reader as a value of another type.
    """
    _field(text, metadata, "format", "format", _named)
    _field(text, metadata, "format_version", "format_version", _counted)
    _field(text, metadata, "dtype", "dtype", _named)
    _field(text, metadata, "backend", "backend", _named)
    _field(text, metadata, "kind", "kind", _named)
    # The rule is a field of the form when it is present; whether it must be present is
    # the format version's question and `_declared` answers it (`checkpoint.md` §3).
    if "learning_rule" in metadata:
        _field(text, metadata, "learning_rule", "learning_rule", _named)
    settings = _field(text, metadata, "settings", "settings", _recorded)
    for key in SETTINGS:
        _field(text, settings, key, "settings." + key, SETTING_TYPES[key])
    recorded = _field(text, metadata, "representation", "representation", _recorded)
    _field(text, recorded, "family", "representation.family", _named)
    _field(text, recorded, "encoding", "representation.encoding", _named)
    _field(text, recorded, "size", "representation.size", _counted)
    shape = _field(text, recorded, "shape", "representation.shape", _or_null(_listed))
    for index, entry in enumerate(shape if shape is not None else ()):
        _counted(text, entry, "representation.shape[%d]" % (index,))
    _field(text, recorded, "dtype", "representation.dtype", _or_null(_named))
    _field(text, metadata, "seed", "seed", _counted)
    exploration = _field(text, metadata, "exploration", "exploration", _recorded)
    _field(text, exploration, "position", "exploration.position", _counted)
    schedule = _field(text, exploration, "schedule", "exploration.schedule", _recorded)
    _field(text, schedule, "start", "exploration.schedule.start", _numbered)
    _field(text, schedule, "end", "exploration.schedule.end", _numbered)
    _field(text, schedule, "samples", "exploration.schedule.samples", _counted)
    target = _field(text, metadata, "target", "target", _recorded)
    _field(text, target, "counter", "target.counter", _counted)
    _field(text, target, "interval", "target.interval", _counted)
    params = _field(text, metadata, "params", "params", _recorded)
    _field(text, params, "count", "params.count", _counted)
    _field(text, params, "target_offset", "params.target_offset", _counted)
    _field(text, params, "length", "params.length", _counted)
    tensors = _field(text, params, "tensors", "params.tensors", _listed)
    for index, tensor in enumerate(tensors):
        label = "params.tensors[%d]" % (index,)
        entry = _recorded(text, tensor, label)
        _field(text, entry, "name", label + ".name", _named)
        shape = _field(text, entry, "shape", label + ".shape", _listed)
        for slot, size in enumerate(shape):
            _counted(text, size, "%s.shape[%d]" % (label, slot))
        _field(text, entry, "offset", label + ".offset", _counted)
        _field(text, entry, "count", label + ".count", _counted)
    masks = _field(text, params, "masks", "params.masks", _listed)
    for index, mask in enumerate(masks):
        label = "params.masks[%d]" % (index,)
        entry = _recorded(text, mask, label)
        for key in ("layer", "slots", "offset", "kept"):
            _field(text, entry, key, label + "." + key, _counted)
    tie_break = _field(text, metadata, "tie_break", "tie_break", _recorded)
    _field(text, tie_break, "rule", "tie_break.rule", _named)
    _field(text, tie_break, "tolerance", "tie_break.tolerance", _numbered)


def _declared(text, metadata):
    """Refuse a value §2.1 does not declare, or one outside its range (`checkpoint.md` §3).

    `_form` checks the JSON *type* of every field of the form; this checks each
    recorded *value*: this container's magic name, format version and dtype, the two
    backends, the seven kinds, the kind's own representation row, the settings'
    ranges, the schedule position and the target counter.  A value outside those is a
    form this module does not read — never coerced, never defaulted — and the message
    names the field and the offending value (`surface.md` §1, §9; `errors.md` §3).

    `backend` is checked here, before `_rebuild` and so before any backend module is
    imported, and `learner._backend` refuses an undeclared name itself: a checkpoint
    recording `numpy` imports no `torch`, and one recording an undeclared name imports
    neither (`README.md` §6, `backends.md` §1).
    """
    if metadata["format"] != MAGIC:
        raise _wrong(text, "format", "the magic name %r" % (MAGIC,), metadata["format"])
    version = metadata["format_version"]
    if version not in SUPPORTED_VERSIONS:
        raise _wrong(
            text, "format_version", "%d or %d" % SUPPORTED_VERSIONS, version
        )
    # The rule's presence is the format version's: version 2 requires it and version 1
    # predates the catalogue, so a version-1 container carrying one was edited and is
    # refused by name (`checkpoint.md` §3, `rules.md` §6, D-19).
    if version == FORMAT_VERSION:
        if "learning_rule" not in metadata:
            raise CheckpointUnreadable(
                "load(path): %r has a metadata.json without the field %r"
                % (text, "learning_rule")
            )
        if metadata["learning_rule"] not in declarations.LEARNING_RULES:
            raise UnknownRule(
                "load(path): %r records the field 'learning_rule', which must be one "
                "of %r, got %r"
                % (
                    text,
                    tuple(declarations.LEARNING_RULES),
                    metadata["learning_rule"],
                )
            )
    elif "learning_rule" in metadata:
        raise _wrong(
            text,
            "learning_rule",
            "absent from a format version 1 container",
            metadata["learning_rule"],
        )
    if metadata["dtype"] != DTYPE:
        raise _wrong(text, "dtype", repr(DTYPE), metadata["dtype"])
    if metadata["backend"] not in declarations.BACKENDS:
        raise _wrong(
            text,
            "backend",
            "one of %r" % (declarations.BACKENDS,),
            metadata["backend"],
        )
    kind = metadata["kind"]
    if kind not in declarations.KINDS:
        raise _wrong(text, "kind", "one of %r" % (declarations.KINDS,), kind)
    settings = metadata["settings"]
    for key in ("width", "depth"):
        if int(settings[key]) < 1:
            raise _wrong(text, "settings." + key, "a positive integer", settings[key])
    sparsity = settings["sparsity"]
    if not 0.0 <= float(sparsity) <= 1.0:
        raise _wrong(text, "settings.sparsity", "in [0, 1]", sparsity)
    row = declarations.KIND_ROWS[kind]
    representation = metadata["representation"]
    for key, declared in (
        ("family", row["observation"]),
        ("encoding", row["encoding"]),
        ("size", row["observation_size"]),
    ):
        if representation[key] != declared:
            raise _wrong(
                text,
                "representation." + key,
                "%r, the kind %r's own row" % (declared, kind),
                representation[key],
            )
    position = metadata["exploration"]["position"]
    if int(position) < 0:
        raise _wrong(text, "exploration.position", "a non-negative integer", position)
    target = metadata["target"]
    counter, interval = target["counter"], target["interval"]
    # The counter resets at its interval (`rule.md` §3), so a counter at or past it
    # is not a state this module writes (`checkpoint.md` §3).
    if int(counter) < 0 or int(counter) >= int(interval):
        raise _wrong(
            text,
            "target.counter",
            "a non-negative integer below the target interval %d" % (int(interval),),
            counter,
        )


def _read_container(path):
    """`(metadata, parameters, path text)` from one checkpoint, or `CheckpointUnreadable`.

    The path's own text rides back with the file's fields so every later refusal can
    name the path it is about (`errors.md` §3).
    """
    text = _path_text(path, "load")
    try:
        handle = open(text, "rb")
    except OSError as error:
        raise CheckpointUnreadable(
            "load(path): %r cannot be read: %s" % (text, error.strerror or error)
        ) from None
    with handle:
        try:
            container = zipfile.ZipFile(handle)
        except (zipfile.BadZipFile, OSError) as error:
            raise CheckpointUnreadable(
                "load(path): %r is not a pypoker-agents-checkpoint of format version "
                "1 or 2 (%s)" % (text, error)
            ) from None
        with container:
            names = container.namelist()
            for member in (METADATA, PARAMETERS):
                if member not in names:
                    raise CheckpointUnreadable(
                        "load(path): %r carries no %s member" % (text, member)
                    )
            raw_metadata = container.read(METADATA)
            raw_parameters = container.read(PARAMETERS)
    try:
        metadata = json.loads(raw_metadata.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise CheckpointUnreadable(
            "load(path): %r has a metadata.json that does not parse" % (text,)
        ) from None
    if not isinstance(metadata, dict):
        raise CheckpointUnreadable(
            "load(path): %r is not a pypoker-agents-checkpoint of format version 1 or 2"
            % (text,)
        )
    for field in REQUIRED:
        if field not in metadata:
            raise CheckpointUnreadable(
                "load(path): %r has a metadata.json without the field %r"
                % (text, field)
            )
    # §2.1's form is checked before anything reads a field, and before a spec is
    # compared: a wrong-typed field is the file's form (§3), never a spec's mismatch.
    _form(text, metadata)
    # §3's value checks follow, and before `_rebuild` imports a backend or scatters a
    # value into a learner: an undeclared or out-of-range value is refused here.
    _declared(text, metadata)
    # A version-1 container carries no `learning_rule` and is read as the only rule its
    # writer could have used; the reading happens once, here, so `_compare` and
    # `_rebuild` both see the rule the file is read as (`rules.md` §6, `checkpoint.md`
    # §3, D-19).
    if metadata["format_version"] == 1:
        metadata["learning_rule"] = declarations.DEFAULT_LEARNING_RULE
    try:
        array = numpy.load(io.BytesIO(raw_parameters), allow_pickle=False)
    except (ValueError, OSError):
        raise CheckpointUnreadable(
            "load(path): %r carries no readable parameters.npy member" % (text,)
        ) from None
    if array.ndim != 1 or numpy.dtype(array.dtype) != numpy.dtype(DTYPE):
        raise CheckpointUnreadable(
            "load(path): %r carries a parameters.npy that is not one 1-D float64 array"
            % (text,)
        )
    return metadata, array, text


def _read_metadata(path):
    """`checkpoint.md` §2.1's object read from `path`'s `metadata.json`."""
    return _read_container(path)[0]


def _compare(spec, metadata):
    """Refuse a spec that disagrees with the file on a key the spec carries (§3).

    A compared key is **validated before it is compared** (`checkpoint.md` §3): a
    `seed` that is not an integer — a `bool` included, and never `int("1")` — is
    refused naming `load(spec)` and the offending value, so no `TypeError` from
    `int()` escapes and nothing is coerced (`surface.md` §1, `errors.md` §4).  A
    `learning_rule` is validated against the catalogue before it is compared, and a
    disagreement names both values as a `seed`'s does (`rules.md` §6, D-19).
    """
    if spec is None:
        return
    if not isinstance(spec, Mapping):
        raise CheckpointMismatch(
            "load(spec): the spec must be a mapping, got %s" % type(spec).__name__
        )
    if "backend" in spec and spec["backend"] != metadata["backend"]:
        raise CheckpointMismatch(
            "load(spec): the spec's backend %r is not the checkpoint's backend %r"
            % (spec["backend"], metadata["backend"])
        )
    architecture = spec.get("architecture")
    kind = None
    if isinstance(architecture, str):
        kind = architecture
    elif isinstance(architecture, Mapping):
        kind = architecture.get("kind")
    if kind is not None and kind != metadata["kind"]:
        raise CheckpointMismatch(
            "load(spec): the spec's kind %r is not the checkpoint's kind %r"
            % (kind, metadata["kind"])
        )
    if "seed" in spec:
        seed = spec["seed"]
        if not _learner.is_count(seed):
            raise CheckpointMismatch(
                "load(spec): the seed must be an integer, got %r" % (seed,)
            )
        if int(seed) != metadata["seed"]:
            raise CheckpointMismatch(
                "load(spec): the spec's seed %r is not the checkpoint's seed %r"
                % (seed, metadata["seed"])
            )
    if "learning_rule" in spec:
        named_rule = _learner.learning_rule(spec["learning_rule"], "load")
        if named_rule != metadata["learning_rule"]:
            raise CheckpointMismatch(
                "load(spec): the spec's learning_rule %r is not the checkpoint's "
                "learning_rule %r" % (named_rule, metadata["learning_rule"])
            )
    if "encoder" in spec:
        encoded = _learner.encoder_spec(spec["encoder"], "load", "spec", "encoder")
        recorded = metadata["representation"]
        declared_size = _learner.encoder_size(encoded)
        if encoded["kind"] != recorded["family"] or declared_size != recorded["size"]:
            raise CheckpointMismatch(
                "load(spec): the encoder is %s and the checkpoint is %s at %d"
                % (
                    _learner.encoder_side(encoded),
                    recorded["family"],
                    recorded["size"],
                )
            )


def _rebuild(text, metadata, array):
    """One learner at the state the file records, or `CheckpointUnreadable`.

    Every field used here has been validated by `_form` before it arrives, so the
    values below are the file's own and no reader coerces one (`surface.md` §1).  A
    recorded `params` value that disagrees with the geometry it implies or with the
    array it rides with is refused naming that field and both values, as §2.1 spells
    it: `params.count`, `params.length`, `params.masks[i].kept` (`checkpoint.md` §2.1,
    §3; `errors.md` §3).
    """
    kind = metadata["kind"]
    settings = metadata["settings"]
    recorded = metadata["representation"]
    size = recorded["size"]
    try:
        # `settings.residual` is validated as a field of the form and is read for
        # nothing else: the restored connection is the reconstructed kind's own, so a
        # file whose `residual` contradicts its `kind` still restores the kind's stack
        # (`architecture.md` §3).
        layout = model.layout_for(
            kind,
            settings["width"],
            settings["depth"],
            settings["sparsity"],
            size,
            recorded["family"],
        )
    except (KeyError, TypeError, ValueError):
        raise CheckpointUnreadable(
            "load(path): the checkpoint's kind %r and its settings do not describe one "
            "of the seven architectures" % (kind,)
        ) from None
    count = metadata["params"]["count"]
    if count != layout.count:
        raise CheckpointUnreadable(
            "load(path): %r records the field 'params.count', which must be the count "
            "its own geometry gives, got %d (the geometry gives %d)"
            % (text, count, layout.count)
        )
    length = metadata["params"]["length"]
    if length != 2 * count + layout.mask_count or int(array.shape[0]) != length:
        raise CheckpointUnreadable(
            "load(path): %r records the field 'params.length', which must be the length "
            "of the array it carries and the length its own geometry gives, got %d "
            "(the array carries %d values, the geometry needs %d)"
            % (text, length, int(array.shape[0]), 2 * count + layout.mask_count)
        )
    parameters = array[: 2 * count]
    masks = array[2 * count :]
    if layout.sparse:
        recorded_masks = metadata["params"]["masks"]
        for layer in range(layout.trunk):
            label = "params.masks[%d].kept" % (layer,)
            start = layer * layout.mask_length
            kept = int(numpy.count_nonzero(masks[start : start + layout.mask_length]))
            wanted = layout.block_lengths[layer]
            # The recorded kept count is the field at fault when it disagrees with the
            # mask the array carries, or when that mask disagrees with the sparsity
            # (`checkpoint.md` §2.1, §3).
            recorded_kept = (
                int(recorded_masks[layer]["kept"])
                if layer < len(recorded_masks)
                else kept
            )
            if kept != wanted or recorded_kept != kept:
                raise CheckpointUnreadable(
                    "load(path): %r records the field %r, which must be the number of "
                    "slots its mask keeps in the array and its sparsity keeps, got %d "
                    "(the array keeps %d, the sparsity keeps %d)"
                    % (text, label, recorded_kept, kept, wanted)
                )
    backend = _learner._backend(metadata["backend"])
    state = backend.load_state(layout, parameters, masks)
    shape = recorded["shape"]
    return _learner.Learner(
        metadata["backend"],
        layout,
        state,
        metadata["seed"],
        kind,
        settings["width"],
        settings["depth"],
        # The resolved values in force, derived from the reconstructed kind — the
        # file's flag cannot override the kind (`architecture.md` §3, checkpoint.md §2.1).
        layout.sparsity,
        layout.residual,
        recorded["family"],
        recorded["encoding"],
        size,
        None if shape is None else tuple(shape),
        recorded["dtype"],
        # The rule the file records, or the one a version-1 file is read as: the
        # restored learner learns under the rule its container names (`rules.md` §6).
        metadata["learning_rule"],
        metadata["exploration"]["position"],
        metadata["target"]["counter"],
    )


def load(spec, path):
    """Restore one learner from one checkpoint, or refuse naming the key (§9, §3)."""
    metadata, array, text = _read_container(path)
    _compare(spec, metadata)
    return _rebuild(text, metadata, array)
