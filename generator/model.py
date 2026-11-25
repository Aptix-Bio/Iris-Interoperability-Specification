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
from datetime import date
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
KEYS_DOCUMENT_FIELDS = ("value_representations", "value_types", "identity_classes", "keys")
SECTION_FIELDS = ("description", "i2s_version")
VR_FIELDS = ("description", "max_length", "length_unit", "multiple_values", "example", "verified")
VALUE_TYPE_FIELDS = ("description", "vrs")
IDENTITY_CLASS_FIELDS = ("description",)
KEY_FIELDS = ("short_name", "dicom", "value_type", "vr", "multiplicity", "identity",
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
_DT = re.compile(r"([0-9]{4})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})(\.[0-9]{1,6})?(([+-])([0-9]{2})([0-9]{2}))?")
_DS = re.compile(r"[+-]?([0-9]+(\.[0-9]*)?|\.[0-9]+)([eE][+-]?[0-9]+)?")
_IS = re.compile(r"[+-]?[0-9]+")
_CS = re.compile(r"[A-Z0-9 _]+")
TEXT = "TEXT"
# Names the generated and hand-written C++ already declare in namespace I2S.
# Every key and short name becomes a constant in I2S::Attribute, whose lines
# name Key and TypedKey unqualified, so a key named like one of these would
# shadow it there; the whole set stays reserved so a key never reads as API.
RESERVED_NAMES = frozenset({
    "Attributes", "DicomAttribute", "DicomSequence", "DicomTag", "Element", "Error", "IdentityClass", "Key",
    "KeyInfo", "Multiplicity", "Pair", "PhiFlag", "Result", "Slot", "Time", "TypedKey", "Value", "ValueOf",
    "ValueType", "Vr", "VrInfo", "decode", "encode", "info", "key_from_name", "name",
})

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
    """A value type (with the VRs it may be written as) or an identity class (no VRs)."""
    name: str
    since: Version
    description: str
    vrs: tuple[str, ...]


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
class ValueRepresentation:
    """A DICOM VR as I2S writes it: one value's text."""
    name: str
    since: Version
    description: str
    max_length: int
    length_unit: str  # "bytes" or "characters"
    multiple_values: bool
    example: str
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
    vr: str
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
    value_representations: tuple[ValueRepresentation, ...]
    value_types: tuple[Member, ...]
    identity_classes: tuple[Member, ...]
    keys: tuple[Key, ...]


# --- Lexical forms ------------------------------------------------------------
# Each VR's rule, as I2S writes it (PS3.5 section 6.2, read 2026-11-24): the
# reason a text is not a value of that VR, or None. A VR the JSON defines
# without a rule here is refused, so its examples are always checkable. The
# C++ codec (include/I2S_Attributes.hpp) implements the same rules at run time;
# its tests read every VR's example through it.

def _controls(allowed: str) -> Callable[[str], str | None]:
    def rule(text: str) -> str | None:
        if any((ord(c) < 0x20 or 0x7F <= ord(c) < 0xA0) and c not in allowed for c in text):
            return "it contains a control character"
        return None
    return rule


def _string_rule(text: str) -> str | None:
    if "\\" in text:
        return "it contains a backslash, which separates values"
    return _controls("")(text)


def _dt_rule(text: str) -> str | None:
    match = _DT.fullmatch(text)
    if match is None:
        return "it is not YYYYMMDDHHMMSS, with up to six fractional digits, then a +ZZXX or -ZZXX offset"
    if match.group(8) is None:
        return "it has no UTC offset"
    year, month, day, hour, minute, second = (int(match.group(i)) for i in range(1, 7))
    try:
        date(year, month, day)
    except ValueError as error:
        return f"it is not a calendar date ({error})"
    if hour > 23 or minute > 59 or second > 59:
        return "its time is not from 000000 to 235959"
    offset = (1 if match.group(9) == "+" else -1) * (int(match.group(10)) * 60 + int(match.group(11)))
    if int(match.group(11)) > 59 or not -12 * 60 <= offset <= 14 * 60:
        return f"its UTC offset {match.group(8)} is outside -1200 to +1400"
    return None


def _is_rule(text: str) -> str | None:
    if _IS.fullmatch(text) is None:
        return "it is not a base-10 integer"
    if not -(2**31) <= int(text) <= 2**31 - 1:
        return "it is outside -2147483648 to 2147483647"
    return None


def _pattern_rule(pattern: re.Pattern[str], form: str) -> Callable[[str], str | None]:
    return lambda text: None if pattern.fullmatch(text) else f"it is not {form}"


LEXICAL_RULES: dict[str, Callable[[str], str | None]] = {
    "CS": _pattern_rule(_CS, "upper-case letters, digits, spaces and underscores"),
    "DS": _pattern_rule(_DS, "a base-10 number"),
    "DT": _dt_rule,
    "IS": _is_rule,
    "LO": _string_rule,
    "LT": _controls("\t\n\f\r"),
    "SH": _string_rule,
    "ST": _controls("\t\n\f\r"),
    "UT": _controls("\t\n\f\r"),
}


def length(text: str, unit: str) -> int:
    """A value's length in its VR's unit: UTF-8 bytes, or Unicode characters."""
    return len(text.encode("utf-8")) if unit == "bytes" else len(text)


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
             revisions: set[Version], vrs: set[str]) -> tuple[Member, ...]:
    out: list[Member] = []
    for name, since, entry in _groups(doc, group, revisions):
        where = f"{group}.{name}"
        _match(_MEMBER_NAME, name, where, "an UPPER_SNAKE_CASE name")
        _only(entry, fields, where)
        listed: tuple[str, ...] = ()
        if "vrs" in fields:
            raw = _field(entry, "vrs", where)
            if not isinstance(raw, list) or not raw or not all(isinstance(v, str) for v in raw):
                raise SpecError(f"{where}.vrs: expected a non-empty list of VR names, found {raw!r}")
            listed = tuple(str(v) for v in raw)
            for vr in listed:
                if vr not in vrs:
                    raise SpecError(f"{where}.vrs: {vr!r} is not a value representation of this specification")
        out.append(Member(name, since, _text(entry, "description", where), listed))
    return tuple(out)


def _value_representations(doc: dict[str, Json], revisions: set[Version]) -> tuple[ValueRepresentation, ...]:
    out: list[ValueRepresentation] = []
    for name, since, entry in _groups(doc, "value_representations", revisions):
        where = f"value_representations.{name}"
        if name not in DICOM_VRS:
            raise SpecError(f"{where}: {name!r} is not a DICOM value representation (PS3.5 Table 6.2-1)")
        _only(entry, VR_FIELDS, where)
        max_length = _field(entry, "max_length", where)
        if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length < 1:
            raise SpecError(f"{where}.max_length: expected a positive integer, found {max_length!r}")
        unit = _text(entry, "length_unit", where)
        if unit not in ("bytes", "characters"):
            raise SpecError(f"{where}.length_unit: expected 'bytes' or 'characters', found {unit!r}")
        multiple = _field(entry, "multiple_values", where)
        if not isinstance(multiple, bool):
            raise SpecError(f"{where}.multiple_values: expected true or false, found {multiple!r}")
        example = _text(entry, "example", where)
        rule = LEXICAL_RULES.get(name)
        if rule is None:
            raise SpecError(f"{where}: no lexical rule for {name} in generator/model.py")
        reason = rule(example)
        if reason is not None:
            raise SpecError(f"{where}.example: {example!r} is not a {name}: {reason}")
        if length(example, unit) > max_length:
            raise SpecError(f"{where}.example: {length(example, unit)} {unit}, over {name}'s {max_length}")
        out.append(ValueRepresentation(name, since, _text(entry, "description", where), max_length, unit,
                                       multiple, example, _verified(_field(entry, "verified", where), f"{where}.verified")))
    return tuple(out)


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


def _or(names: tuple[str, ...]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def _key(name: str, since: Version, entry: dict[str, Json],
         value_types: dict[str, Member], identity_classes: set[str],
         vrs: dict[str, ValueRepresentation]) -> Key:
    where = f"keys.{name}"
    _match(_KEY_NAME, name, where, "a PascalCase name")
    if name in RESERVED_NAMES:
        raise SpecError(f"{where}: {name!r} is a name the generated C++ already uses")
    _only(entry, KEY_FIELDS, where)
    short_name = _optional_text(entry, "short_name", where)
    if short_name is not None:
        _match(_SHORT_NAME, short_name, f"{where}.short_name", "a short name of letters, digits and underscores")
        if short_name in RESERVED_NAMES:
            raise SpecError(f"{where}.short_name: {short_name!r} is a name the generated C++ already uses")
    value_type = _text(entry, "value_type", where)
    if value_type not in value_types:
        raise SpecError(f"{where}.value_type: unknown value type {value_type!r}")
    vr = _text(entry, "vr", where)
    allowed = value_types[value_type].vrs
    if vr not in allowed:
        raise SpecError(f"{where}.vr: {value_type} is written as {_or(allowed)}, not {vr}")
    dicom = _dicom(_field(entry, "dicom", where), f"{where}.dicom")
    if dicom is not None and dicom.vr != vr:
        raise SpecError(f"{where}.vr: {vr} differs from the DICOM attribute's {dicom.vr}")
    multiplicity = _multiplicity(_text(entry, "multiplicity", where), f"{where}.multiplicity")
    if multiplicity.maximum != 1:
        if not vrs[vr].multiple_values:
            raise SpecError(f"{where}.multiplicity: {vr} holds a single value, so {multiplicity.text!r} is not possible")
        if value_type != TEXT:
            raise SpecError(f"{where}.multiplicity: only {TEXT} keys may hold several values in this version")
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
        dicom=dicom,
        value_type=value_type,
        vr=vr,
        multiplicity=multiplicity,
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


def _parse_keys(keys_doc: Json, revisions: set[Version]) -> tuple[
        tuple[ValueRepresentation, ...], tuple[Member, ...], tuple[Member, ...], tuple[Key, ...]]:
    doc = _object(keys_doc, "keys document")
    _only(doc, KEYS_DOCUMENT_FIELDS, "keys document")
    vrs = _value_representations(doc, revisions)
    by_vr = {v.name: v for v in vrs}
    value_types = _members(doc, "value_types", VALUE_TYPE_FIELDS, revisions, set(by_vr))
    identity_classes = _members(doc, "identity_classes", IDENTITY_CLASS_FIELDS, revisions, set())
    keys = tuple(
        _key(name, since, entry, {m.name: m for m in value_types}, {m.name for m in identity_classes}, by_vr)
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
    return vrs, value_types, identity_classes, keys


def parse(header_doc: Json, keys_doc: Json) -> Spec:
    """The specification, or SpecError naming the file and the first broken rule."""
    try:
        header, version, status, revisions = _parse_header(header_doc)
    except SpecError as error:
        raise SpecError(f"{HEADER_FILE}: {error}") from error
    try:
        vrs, value_types, identity_classes, keys = _parse_keys(keys_doc, {r.version for r in revisions})
    except SpecError as error:
        raise SpecError(f"{KEYS_FILE}: {error}") from error
    try:
        name = _text(header, "name", "header")
        abbreviation = _text(header, "abbreviation", "header")
        repository = _text(header, "repository", "header")
    except SpecError as error:
        raise SpecError(f"{HEADER_FILE}: {error}") from error
    return Spec(name, abbreviation, repository, version, status, revisions, vrs, value_types, identity_classes, keys)
