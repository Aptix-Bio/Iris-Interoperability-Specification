"""The specification as typed values, parsed from the two spec documents.

parse() is the one place the JSON's content is checked, and the linter's rules
on names, DICOM mappings, times, versions and consistency live here: every
field is required (null where it does not apply), unknown fields are refused,
every reference must name a defined member, every date and time is ISO 8601,
and the revisions and version groups agree. The first problem raises SpecError
naming the file, the field and the offending value, so nothing downstream ever
sees a half-valid spec.

The *_FIELDS tuples are the schema: the fields each object may hold, in the
order the canonical form writes them (validate.canonical).
"""
# RTM Schema_01, UniqueNames_01, PhiFlag_01, Lint_02, Lint_03, Lint_04, Lint_05, Lint_06
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit

Json = dict[str, "Json"] | list["Json"] | str | int | float | bool | None

HEADER_FILE = "spec/i2s_header.json"
KEYS_FILE = "spec/i2s_keys.json"

# The identity class whose keys may still be decided: the append-only gate
# lets a key leave it (validate.py), and only then.
UNDER_REVIEW = "UNDER_REVIEW"
# The value type a PHI flag must have.
BOOLEAN = "BOOLEAN"
DRAFT = "draft"
RATIFIED = "ratified"

HEADER_FIELDS = ("name", "abbreviation", "repository", "version", "status", "revisions")
VERSION_FIELDS = ("major", "minor")
REVISION_FIELDS = ("version", "status", "date", "authors", "summary")
KEYS_DOCUMENT_FIELDS = ("value_types", "identity_classes", "keys")
SECTION_FIELDS = ("description", "i2s_version")
VALUE_TYPE_FIELDS = ("description", "example")
IDENTITY_CLASS_FIELDS = ("description",)
KEY_FIELDS = ("short_name", "dicom", "value_type", "multiplicity", "identity",
              "identity_note", "phi_flag", "deprecated", "description")
DICOM_FIELDS = ("keyword", "tag", "vr", "sequence", "verified")
SEQUENCE_FIELDS = ("keyword", "tag")
VERIFIED_FIELDS = ("title", "url", "read")
PHI_FLAG_FIELDS = ("key", "absent_means_phi")

# Every name is ASCII: these patterns admit nothing else.
_KEY_NAME = re.compile(r"[A-Z][A-Za-z0-9]*")
_SHORT_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
_MEMBER_NAME = re.compile(r"[A-Z][A-Z0-9_]*")
_VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_TAG = re.compile(r"([0-9A-F]{4}),([0-9A-F]{4})")
_MULTIPLICITY = re.compile(r"([1-9][0-9]*)(?:-([1-9][0-9]*|n))?")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_DATE_TIME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})?")
_DECIMAL = re.compile(r"[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?")
_INTEGER = re.compile(r"[+-]?[0-9]+")

# DICOM PS3.5 2026e, Table 6.2-1, read 2026-11-24 from
# https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_6.2.html
DICOM_VRS = frozenset({
    "AE", "AS", "AT", "CS", "DA", "DS", "DT", "FD", "FL", "IS", "LO", "LT", "OB", "OD", "OF", "OL", "OV",
    "OW", "PN", "SH", "SL", "SQ", "SS", "ST", "SV", "TM", "UC", "UI", "UL", "UN", "UR", "US", "UT", "UV",
})


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
    """A value type (with its example) or an identity class (example None)."""
    name: str
    since: Version
    description: str
    example: str | None


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
class Verified:
    title: str
    url: str
    read: str


@dataclass(frozen=True)
class Dicom:
    keyword: str
    tag: DicomTag
    vr: str
    sequence: DicomSequence | None
    verified: tuple[Verified, ...]


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
    version: Version
    status: str
    date: str
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


# --- Lexical forms ------------------------------------------------------------
# Each value type's rule: the reason a text is not of that type, or None. A
# value type the JSON defines without a rule here is refused, so a new type
# cannot be published without its lexical form being checkable.

def _text_rule(text: str) -> str | None:
    if not text:
        return "it is empty"
    if any(ord(c) < 0x20 or 0x7F <= ord(c) < 0xA0 for c in text):
        return "it contains a control character"
    return None


def _date_time_rule(text: str) -> str | None:
    match = _DATE_TIME.fullmatch(text)
    if match is None:
        return "it is not YYYY-MM-DDThh:mm:ss, with up to six fractional digits, then Z or a ±hh:mm offset"
    if match.group(2) is None:
        return "it has no UTC offset"
    try:
        offset = datetime.fromisoformat(text).utcoffset()
    except ValueError as error:
        return f"it is not a calendar date and time ({error})"
    if offset is None or not timedelta(hours=-12) <= offset <= timedelta(hours=14):
        return f"its UTC offset {match.group(2)} is outside -12:00 to +14:00"
    return None


def _pattern_rule(pattern: re.Pattern[str], form: str) -> Callable[[str], str | None]:
    return lambda text: None if pattern.fullmatch(text) else f"it is not {form}"


LEXICAL_RULES: dict[str, Callable[[str], str | None]] = {
    "TEXT": _text_rule,
    "DATE_TIME": _date_time_rule,
    "DECIMAL": _pattern_rule(_DECIMAL, "a base-10 number"),
    "INTEGER": _pattern_rule(_INTEGER, "a base-10 integer"),
    BOOLEAN: _pattern_rule(re.compile("true|false"), "true or false"),
}


# --- Readers ------------------------------------------------------------------

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


def _only(obj: dict[str, Json], allowed: tuple[str, ...], where: str) -> None:
    # "// MARK: ..." entries are the documents' section comments.
    unknown = sorted(k for k in obj if k not in allowed and not k.startswith("//"))
    if unknown:
        raise SpecError(f"{where}: unknown field(s) {unknown}")


def _version(text: str, where: str) -> Version:
    match = _match(_VERSION, text, where, "a MAJOR.MINOR version")
    return Version(int(match.group(1)), int(match.group(2)))


def _date(obj: dict[str, Json], name: str, where: str) -> str:
    text = _text(obj, name, where)
    try:
        _match(_DATE, text, f"{where}.{name}", "an ISO 8601 date")
        date.fromisoformat(text)
    except (SpecError, ValueError) as error:
        raise SpecError(f"{where}.{name}: {text!r} is not an ISO 8601 date (YYYY-MM-DD)") from error
    return text


def _tag(text: str, where: str) -> DicomTag:
    match = _match(_TAG, text, where, "a DICOM tag written GGGG,EEEE in upper-case hexadecimal")
    return DicomTag(int(match.group(1), 16), int(match.group(2), 16))


def _groups(doc: dict[str, Json], group: str, revisions: set[Version]) -> list[tuple[str, Version, dict[str, Json]]]:
    """(name, since, entry) for every member of a version-grouped section, oldest
    version first and in document order within a version. Each version group
    must be a revision, and a name defined in two version groups is refused:
    append-only means a member is defined once."""
    section = _object(_field(doc, group, group), group)
    _only(section, SECTION_FIELDS, group)
    versions = _object(_field(section, "i2s_version", group), f"{group}.i2s_version")
    parsed = sorted(
        ((_version(label, f"{group}.i2s_version"), label) for label in versions),
        key=lambda item: (item[0].major, item[0].minor),
    )
    seen: dict[str, Version] = {}
    out: list[tuple[str, Version, dict[str, Json]]] = []
    for since, label in parsed:
        if since not in revisions:
            raise SpecError(f"{group}.i2s_version.{label}: no revision {label} in {HEADER_FILE}")
        members = _object(versions[label], f"{group}.i2s_version.{label}")
        for name, entry in members.items():
            if name in seen:
                raise SpecError(f"{group}.{name}: defined in {seen[name]} and {since}")
            seen[name] = since
            out.append((name, since, _object(entry, f"{group}.{name}")))
    return out


def _members(doc: dict[str, Json], group: str, fields: tuple[str, ...],
             revisions: set[Version]) -> tuple[Member, ...]:
    out: list[Member] = []
    for name, since, entry in _groups(doc, group, revisions):
        where = f"{group}.{name}"
        _match(_MEMBER_NAME, name, where, "an UPPER_SNAKE_CASE name")
        _only(entry, fields, where)
        example = _text(entry, "example", where) if "example" in fields else None
        out.append(Member(name, since, _text(entry, "description", where), example))
    return tuple(out)


def _check_examples(value_types: tuple[Member, ...]) -> None:
    for member in value_types:
        where = f"value_types.{member.name}.example"
        rule = LEXICAL_RULES.get(member.name)
        if rule is None:
            raise SpecError(f"value_types.{member.name}: no lexical rule for {member.name} in generator/model.py")
        reason = rule(member.example or "")
        if reason is not None:
            raise SpecError(f"{where}: {member.example!r} is not a {member.name}: {reason}")


def _verified(value: Json, where: str) -> tuple[Verified, ...]:
    if not isinstance(value, list) or not value:
        raise SpecError(f"{where}: expected a non-empty list of sources, found {value!r}")
    out: list[Verified] = []
    for index, raw in enumerate(value):
        entry_where = f"{where}[{index}]"
        entry = _object(raw, entry_where)
        _only(entry, VERIFIED_FIELDS, entry_where)
        url = _text(entry, "url", entry_where)
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.netloc:
            raise SpecError(f"{entry_where}.url: {url!r} is not an https URL")
        out.append(Verified(_text(entry, "title", entry_where), url, _date(entry, "read", entry_where)))
    return tuple(out)


def _dicom(value: Json, where: str) -> Dicom | None:
    if value is None:
        return None
    obj = _object(value, where)
    _only(obj, DICOM_FIELDS, where)
    sequence: DicomSequence | None = None
    raw_sequence = _field(obj, "sequence", where)
    if raw_sequence is not None:
        seq = _object(raw_sequence, f"{where}.sequence")
        _only(seq, SEQUENCE_FIELDS, f"{where}.sequence")
        sequence = DicomSequence(
            _text(seq, "keyword", f"{where}.sequence"),
            _tag(_text(seq, "tag", f"{where}.sequence"), f"{where}.sequence.tag"),
        )
    vr = _text(obj, "vr", where)
    if vr not in DICOM_VRS:
        raise SpecError(f"{where}.vr: {vr!r} is not a DICOM value representation (PS3.5 Table 6.2-1)")
    return Dicom(
        keyword=_text(obj, "keyword", where),
        tag=_tag(_text(obj, "tag", where), f"{where}.tag"),
        vr=vr,
        sequence=sequence,
        verified=_verified(_field(obj, "verified", where), f"{where}.verified"),
    )


def _phi_flag(value: Json, where: str) -> PhiFlag | None:
    if value is None:
        return None
    obj = _object(value, where)
    _only(obj, PHI_FLAG_FIELDS, where)
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
    _only(entry, KEY_FIELDS, where)
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
    """The revisions, oldest first: each version follows the one before it
    (the next minor, or the next major at minor 0), and only the newest may be
    a draft."""
    raw = _field(header, "revisions", "header")
    if not isinstance(raw, list) or not raw:
        raise SpecError(f"header.revisions: expected a non-empty list, found {raw!r}")
    out: list[Revision] = []
    for index, value in enumerate(raw):
        where = f"header.revisions[{index}]"
        entry = _object(value, where)
        _only(entry, REVISION_FIELDS, where)
        version = _version(_text(entry, "version", where), f"{where}.version")
        if out:
            last = out[-1].version
            if version not in (Version(last.major, last.minor + 1), Version(last.major + 1, 0)):
                raise SpecError(f"{where}.version: {version} does not follow {last}")
        status = _text(entry, "status", where)
        if status not in (DRAFT, RATIFIED):
            raise SpecError(f"{where}.status: expected '{DRAFT}' or '{RATIFIED}', found {status!r}")
        if status == DRAFT and index != len(raw) - 1:
            raise SpecError(f"{where}.status: only the newest revision may be '{DRAFT}'")
        authors = _field(entry, "authors", where)
        if not isinstance(authors, list) or not authors or not all(isinstance(a, str) and a for a in authors):
            raise SpecError(f"{where}.authors: expected a non-empty list of names, found {authors!r}")
        out.append(Revision(version, status, _date(entry, "date", where),
                            tuple(str(a) for a in authors), _text(entry, "summary", where)))
    return tuple(out)


def _parse_header(header_doc: Json) -> tuple[dict[str, Json], Version, str, tuple[Revision, ...]]:
    header = _object(header_doc, "header")
    _only(header, HEADER_FIELDS, "header")
    raw_version = _object(_field(header, "version", "header"), "header.version")
    _only(raw_version, VERSION_FIELDS, "header.version")
    major, minor = raw_version.get("major"), raw_version.get("minor")
    if not isinstance(major, int) or isinstance(major, bool) or not isinstance(minor, int) or isinstance(minor, bool):
        raise SpecError(f"header.version: expected integer major and minor, found {raw_version!r}")
    version = Version(major, minor)
    revisions = _revisions(header)
    if version != revisions[-1].version:
        raise SpecError(f"header.version: {version} is not the newest revision, {revisions[-1].version}")
    status = _text(header, "status", "header")
    if status != revisions[-1].status:
        raise SpecError(f"header.status: {status!r} is not the newest revision's status, {revisions[-1].status!r}")
    return header, version, status, revisions


def _parse_keys(keys_doc: Json, revisions: set[Version]) -> tuple[tuple[Member, ...], tuple[Member, ...], tuple[Key, ...]]:
    doc = _object(keys_doc, "keys document")
    _only(doc, KEYS_DOCUMENT_FIELDS, "keys document")
    value_types = _members(doc, "value_types", VALUE_TYPE_FIELDS, revisions)
    _check_examples(value_types)
    identity_classes = _members(doc, "identity_classes", IDENTITY_CLASS_FIELDS, revisions)
    keys = tuple(
        _key(name, since, entry, {m.name for m in value_types}, {m.name for m in identity_classes})
        for name, since, entry in _groups(doc, "keys", revisions)
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
    return value_types, identity_classes, keys


def parse(header_doc: Json, keys_doc: Json) -> Spec:
    """The specification, or SpecError naming the file and the first broken rule."""
    try:
        header, version, status, revisions = _parse_header(header_doc)
    except SpecError as error:
        raise SpecError(f"{HEADER_FILE}: {error}") from error
    try:
        value_types, identity_classes, keys = _parse_keys(keys_doc, {r.version for r in revisions})
    except SpecError as error:
        raise SpecError(f"{KEYS_FILE}: {error}") from error
    try:
        name = _text(header, "name", "header")
        abbreviation = _text(header, "abbreviation", "header")
        repository = _text(header, "repository", "header")
    except SpecError as error:
        raise SpecError(f"{HEADER_FILE}: {error}") from error
    return Spec(name, abbreviation, repository, version, status, revisions, value_types, identity_classes, keys)
