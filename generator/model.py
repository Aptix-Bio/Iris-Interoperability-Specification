"""The specification as typed values, parsed from the two spec documents.

parse() is the one place the JSON's shape is checked: every field is required
(null where it does not apply), unknown fields are refused, and every reference
(a key's value type, its identity class) must name a defined member. The first
problem raises SpecError naming the field and the offending value, so nothing
downstream ever sees a half-valid spec.
"""
# RTM Schema_01, UniqueNames_01, PhiFlag_01
from __future__ import annotations

import re
from dataclasses import dataclass

Json = dict[str, "Json"] | list["Json"] | str | int | float | bool | None

# The identity class whose keys may still be decided: the append-only gate
# lets a key leave it (validate.py), and only then.
UNDER_REVIEW = "UNDER_REVIEW"
# The value type a PHI flag must have.
BOOLEAN = "BOOLEAN"

_KEY_NAME = re.compile(r"[A-Z][A-Za-z0-9]*")
_SHORT_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_MEMBER_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_TAG = re.compile(r"([0-9A-F]{4}),([0-9A-F]{4})")
_MULTIPLICITY = re.compile(r"([1-9][0-9]*)(?:-([1-9][0-9]*|n))?")
_KEY_FIELDS = frozenset(
    {"short_name", "dicom", "value_type", "multiplicity", "identity",
     "identity_note", "phi_flag", "deprecated", "description"}
)


class SpecError(ValueError):
    """A spec document breaks a schema rule; the message names where and what."""


@dataclass(frozen=True)
class Version:
    major: int
    minor: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"


@dataclass(frozen=True)
class Member:
    """A value type or an identity class."""
    name: str
    since: Version
    description: str


@dataclass(frozen=True)
class DicomTag:
    group: int
    element: int

    def __str__(self) -> str:
        return f"({self.group:04X},{self.element:04X})"


@dataclass(frozen=True)
class DicomSequence:
    keyword: str
    tag: DicomTag


@dataclass(frozen=True)
class Dicom:
    keyword: str
    tag: DicomTag
    vr: str
    sequence: DicomSequence | None
    verified: str


@dataclass(frozen=True)
class Multiplicity:
    minimum: int
    maximum: int | None  # None: no upper bound ("n")
    text: str


@dataclass(frozen=True)
class PhiFlag:
    """The BOOLEAN key that states, per file, whether this key's value is
    protected health information, and what a reader assumes when it is absent."""
    key: str
    absent_means_phi: bool


@dataclass(frozen=True)
class Key:
    name: str
    since: Version
    short_name: str | None
    dicom: Dicom | None
    value_type: str
    multiplicity: Multiplicity
    identity: str
    identity_note: str | None
    phi_flag: PhiFlag | None
    deprecated: str | None
    description: str


@dataclass(frozen=True)
class Revision:
    version: str
    status: str
    authors: tuple[str, ...]
    summary: str


@dataclass(frozen=True)
class Spec:
    name: str
    abbreviation: str
    repository: str
    version: Version
    status: str
    revisions: tuple[Revision, ...]
    value_types: tuple[Member, ...]
    identity_classes: tuple[Member, ...]
    keys: tuple[Key, ...]


def _object(value: Json, where: str) -> dict[str, Json]:
    if not isinstance(value, dict):
        raise SpecError(f"{where}: expected an object, found {value!r}")
    return value


def _field(obj: dict[str, Json], name: str, where: str) -> Json:
    if name not in obj:
        raise SpecError(f"{where}: missing field '{name}'")
    return obj[name]


def _text(obj: dict[str, Json], name: str, where: str) -> str:
    value = _field(obj, name, where)
    if not isinstance(value, str) or not value:
        raise SpecError(f"{where}.{name}: expected non-empty text, found {value!r}")
    return value


def _optional_text(obj: dict[str, Json], name: str, where: str) -> str | None:
    return None if _field(obj, name, where) is None else _text(obj, name, where)


def _match(pattern: re.Pattern[str], value: str, where: str, what: str) -> re.Match[str]:
    match = pattern.fullmatch(value)
    if match is None:
        raise SpecError(f"{where}: {value!r} is not {what}")
    return match


def _only(obj: dict[str, Json], allowed: frozenset[str], where: str) -> None:
    # "// MARK: ..." entries are the documents' section comments.
    unknown = sorted(k for k in obj if k not in allowed and not k.startswith("//"))
    if unknown:
        raise SpecError(f"{where}: unknown field(s) {unknown}")


def _version(text: str, where: str) -> Version:
    match = _match(_VERSION, text, where, "a MAJOR.MINOR version")
    return Version(int(match.group(1)), int(match.group(2)))


def _tag(text: str, where: str) -> DicomTag:
    match = _match(_TAG, text, where, "a DICOM tag written GGGG,EEEE in upper-case hexadecimal")
    return DicomTag(int(match.group(1), 16), int(match.group(2), 16))


def _groups(doc: dict[str, Json], group: str, ceiling: Version) -> list[tuple[str, Version, dict[str, Json]]]:
    """(name, since, entry) for every member of a version-grouped section, oldest
    version first and in document order within a version. A name defined in two
    version groups is refused: append-only means a member is defined once."""
    section = _object(_field(doc, group, group), group)
    _only(section, frozenset({"description", "i2s_version"}), group)
    versions = _object(_field(section, "i2s_version", group), f"{group}.i2s_version")
    parsed = sorted(
        ((_version(label, f"{group}.i2s_version"), label) for label in versions),
        key=lambda item: (item[0].major, item[0].minor),
    )
    seen: dict[str, Version] = {}
    out: list[tuple[str, Version, dict[str, Json]]] = []
    for since, label in parsed:
        if (since.major, since.minor) > (ceiling.major, ceiling.minor):
            raise SpecError(f"{group}.i2s_version.{label}: newer than the specification version {ceiling}")
        members = _object(versions[label], f"{group}.i2s_version.{label}")
        for name, entry in members.items():
            if name in seen:
                raise SpecError(f"{group}.{name}: defined in {seen[name]} and {since}")
            seen[name] = since
            out.append((name, since, _object(entry, f"{group}.{name}")))
    return out


def _members(doc: dict[str, Json], group: str, ceiling: Version) -> tuple[Member, ...]:
    out: list[Member] = []
    for name, since, entry in _groups(doc, group, ceiling):
        where = f"{group}.{name}"
        _match(_MEMBER_NAME, name, where, "an UPPER_SNAKE_CASE name")
        _only(entry, frozenset({"description"}), where)
        out.append(Member(name, since, _text(entry, "description", where)))
    return tuple(out)


def _dicom(value: Json, where: str) -> Dicom | None:
    if value is None:
        return None
    obj = _object(value, where)
    _only(obj, frozenset({"keyword", "tag", "vr", "sequence", "verified"}), where)
    sequence: DicomSequence | None = None
    raw_sequence = _field(obj, "sequence", where)
    if raw_sequence is not None:
        seq = _object(raw_sequence, f"{where}.sequence")
        _only(seq, frozenset({"keyword", "tag"}), f"{where}.sequence")
        sequence = DicomSequence(
            _text(seq, "keyword", f"{where}.sequence"),
            _tag(_text(seq, "tag", f"{where}.sequence"), f"{where}.sequence.tag"),
        )
    return Dicom(
        keyword=_text(obj, "keyword", where),
        tag=_tag(_text(obj, "tag", where), f"{where}.tag"),
        vr=_text(obj, "vr", where),
        sequence=sequence,
        verified=_text(obj, "verified", where),
    )


def _phi_flag(value: Json, where: str) -> PhiFlag | None:
    if value is None:
        return None
    obj = _object(value, where)
    _only(obj, frozenset({"key", "absent_means_phi"}), where)
    absent_means_phi = _field(obj, "absent_means_phi", where)
    if not isinstance(absent_means_phi, bool):
        raise SpecError(f"{where}.absent_means_phi: expected true or false, found {absent_means_phi!r}")
    return PhiFlag(_text(obj, "key", where), absent_means_phi)


def _multiplicity(text: str, where: str) -> Multiplicity:
    match = _match(_MULTIPLICITY, text, where, "a multiplicity such as 1, 1-3 or 1-n")
    minimum = int(match.group(1))
    upper = match.group(2)
    maximum = minimum if upper is None else None if upper == "n" else int(upper)
    if maximum is not None and maximum < minimum:
        raise SpecError(f"{where}: {text!r} has its maximum below its minimum")
    return Multiplicity(minimum, maximum, text)


def _key(name: str, since: Version, entry: dict[str, Json],
         value_types: set[str], identity_classes: set[str]) -> Key:
    where = f"keys.{name}"
    _match(_KEY_NAME, name, where, "a PascalCase name")
    _only(entry, _KEY_FIELDS, where)
    short_name = _optional_text(entry, "short_name", where)
    if short_name is not None:
        _match(_SHORT_NAME, short_name, f"{where}.short_name", "a short name of letters, digits and underscores")
    value_type = _text(entry, "value_type", where)
    if value_type not in value_types:
        raise SpecError(f"{where}.value_type: unknown value type {value_type!r}")
    identity = _text(entry, "identity", where)
    if identity not in identity_classes:
        raise SpecError(f"{where}.identity: unknown identity class {identity!r}")
    identity_note = _optional_text(entry, "identity_note", where)
    if (identity == UNDER_REVIEW) != (identity_note is not None):
        raise SpecError(f"{where}.identity_note: required exactly when identity is {UNDER_REVIEW}")
    return Key(
        name=name,
        since=since,
        short_name=short_name,
        dicom=_dicom(_field(entry, "dicom", where), f"{where}.dicom"),
        value_type=value_type,
        multiplicity=_multiplicity(_text(entry, "multiplicity", where), f"{where}.multiplicity"),
        identity=identity,
        identity_note=identity_note,
        phi_flag=_phi_flag(_field(entry, "phi_flag", where), f"{where}.phi_flag"),
        deprecated=_optional_text(entry, "deprecated", where),
        description=_text(entry, "description", where),
    )


def _revisions(header: dict[str, Json]) -> tuple[Revision, ...]:
    raw = _field(header, "revisions", "header")
    if not isinstance(raw, list) or not raw:
        raise SpecError(f"header.revisions: expected a non-empty list, found {raw!r}")
    out: list[Revision] = []
    for index, value in enumerate(raw):
        where = f"header.revisions[{index}]"
        entry = _object(value, where)
        _only(entry, frozenset({"version", "status", "authors", "summary"}), where)
        authors = _field(entry, "authors", where)
        if not isinstance(authors, list) or not all(isinstance(a, str) for a in authors):
            raise SpecError(f"{where}.authors: expected a list of names, found {authors!r}")
        out.append(Revision(
            _text(entry, "version", where), _text(entry, "status", where),
            tuple(str(a) for a in authors), _text(entry, "summary", where),
        ))
    return tuple(out)


def parse(header_doc: Json, keys_doc: Json) -> Spec:
    """The specification, or SpecError naming the first broken rule."""
    header = _object(header_doc, "header")
    _only(header, frozenset({"name", "abbreviation", "repository", "version", "status", "revisions"}), "header")
    raw_version = _object(_field(header, "version", "header"), "header.version")
    major, minor = raw_version.get("major"), raw_version.get("minor")
    if not isinstance(major, int) or not isinstance(minor, int):
        raise SpecError(f"header.version: expected integer major and minor, found {raw_version!r}")
    version = Version(major, minor)
    status = _text(header, "status", "header")
    if status not in ("draft", "ratified"):
        raise SpecError(f"header.status: expected 'draft' or 'ratified', found {status!r}")

    doc = _object(keys_doc, "keys document")
    _only(doc, frozenset({"value_types", "identity_classes", "keys"}), "keys document")
    value_types = _members(doc, "value_types", version)
    identity_classes = _members(doc, "identity_classes", version)
    keys = tuple(
        _key(name, since, entry, {m.name for m in value_types}, {m.name for m in identity_classes})
        for name, since, entry in _groups(doc, "keys", version)
    )
    by_name = {k.name: k for k in keys}
    for key in keys:
        if key.phi_flag is None:
            continue
        flag = by_name.get(key.phi_flag.key)
        if flag is None:
            raise SpecError(f"keys.{key.name}.phi_flag: no key named {key.phi_flag.key!r}")
        if flag.value_type != BOOLEAN:
            raise SpecError(f"keys.{key.name}.phi_flag: {flag.name} is {flag.value_type}, not {BOOLEAN}")
    # A key is found by its name or its short name (I2S::key_from_name), so the
    # two share one namespace.
    owners: dict[str, str] = {k.name: k.name for k in keys}
    for key in keys:
        if key.short_name is None:
            continue
        if key.short_name in owners:
            raise SpecError(
                f"keys.{key.name}.short_name: short name {key.short_name!r} of {key.name} "
                f"is already the name or short name of {owners[key.short_name]}"
            )
        owners[key.short_name] = key.name

    return Spec(
        name=_text(header, "name", "header"),
        abbreviation=_text(header, "abbreviation", "header"),
        repository=_text(header, "repository", "header"),
        version=version,
        status=status,
        revisions=_revisions(header),
        value_types=value_types,
        identity_classes=identity_classes,
        keys=keys,
    )
