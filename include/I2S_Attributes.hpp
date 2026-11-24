// I2S_Attributes.hpp: typed I2S values, their DICOM text, and an adapter to and
// from IFE's attribute pairs.
//
// I2S defines a vocabulary; IFE's attribute block is the container. This header
// converts between typed C++ values and the (key name, value text) pairs that
// block stores under METADATA_I2S, and nothing else: no byte layout, no
// separator between pairs, no file representation.
//
//   I2S::Attributes attributes;
//   attributes[I2S::Manufacturer] = "Leica";
//   attributes[I2S::ScanTime]     = std::chrono::system_clock::now();
//
// Each key constant (I2S_Keys.hpp) is a TypedKey<Key::...>, so the value a key
// accepts is checked at compile time: a value of the wrong type has no viable
// operator=, and the compiler's note names the concept it failed (TextValue,
// DateTimeValue, IntegerValue, DecimalValue, BooleanValue).
//
// Errors follow the style guide: the codec throws detail::CodecError inside;
// every public function is noexcept and returns a Result naming the key, the
// offending text and the rule it broke. Nothing here recurses.
// RTM TypedKeys_01, Encoding_01, Adapter_01, Iteration_01, PhiFlag_02
#ifndef I2S_ATTRIBUTES_HPP
#define I2S_ATTRIBUTES_HPP

#include "I2S_Keys.hpp"

#include <array>
#include <charconv>
#include <chrono>
#include <cmath>
#include <concepts>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <initializer_list>
#include <iterator>
#include <limits>
#include <new>
#include <optional>
#include <ranges>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <system_error>
#include <type_traits>
#include <utility>
#include <variant>
#include <vector>

namespace I2S {

/// A DATE_TIME value: a UTC time, at the microsecond precision a DT holds.
using Time = std::chrono::sys_time<std::chrono::microseconds>;

/// Why a value or a pair was refused: the key (when one is known), the
/// offending text, and the rule it broke.
struct Error {
    std::optional<Key> key;
    std::string text;
    std::string message;
};

/// A value or the Error explaining its absence. value() and error() throw
/// std::logic_error when called on the other state, naming that state.
template <class T>
class [[nodiscard]] Result {
public:
    Result(T value) : _state(std::in_place_index<0>, std::move(value)) {}
    Result(Error error) : _state(std::in_place_index<1>, std::move(error)) {}

    [[nodiscard]] bool has_value() const noexcept { return _state.index() == 0; }

    [[nodiscard]] const T& value() const
    {
        if (!has_value()) {
            throw std::logic_error("I2S::Result::value() on an error: " + std::get<1>(_state).message);
        }
        return std::get<0>(_state);
    }

    [[nodiscard]] const Error& error() const
    {
        if (has_value()) {
            throw std::logic_error("I2S::Result::error() on a value");
        }
        return std::get<1>(_state);
    }

private:
    std::variant<T, Error> _state;
};

/// One attribute as IFE's attribute block stores it under METADATA_I2S: the
/// key's name (ASCII) and the value's text (UTF-8).
struct Pair {
    std::string key;
    std::string value;
    friend bool operator==(const Pair&, const Pair&) = default;
};

namespace detail {

struct CodecError : std::runtime_error {
    using std::runtime_error::runtime_error;
};

[[noreturn]] inline void refuse(std::string message)
{
    throw CodecError(std::move(message));
}

inline std::string quoted(std::string_view text)
{
    return "'" + std::string(text) + "'";
}

/// Unicode characters in valid UTF-8; refuses a malformed sequence.
inline std::size_t characters(std::string_view text)
{
    std::size_t count = 0;
    std::size_t index = 0;
    while (index < text.size()) {
        const auto lead = static_cast<unsigned char>(text[index]);
        const std::size_t width = lead < 0x80 ? 1 : (lead >> 5) == 0x6 ? 2 : (lead >> 4) == 0xE ? 3 : (lead >> 3) == 0x1E ? 4 : 0;
        if (width == 0 || index + width > text.size()) {
            refuse("it is not valid UTF-8 at byte " + std::to_string(index));
        }
        for (std::size_t next = 1; next < width; ++next) {
            if ((static_cast<unsigned char>(text[index + next]) >> 6) != 0x2) {
                refuse("it is not valid UTF-8 at byte " + std::to_string(index + next));
            }
        }
        index += width;
        ++count;
    }
    return count;
}

/// Spaces DICOM allows as padding around a number, a code or a date-time.
inline std::string_view trimmed(std::string_view text) noexcept
{
    const std::size_t first = text.find_first_not_of(' ');
    if (first == std::string_view::npos) {
        return {};
    }
    return text.substr(first, text.find_last_not_of(' ') - first + 1);
}

inline bool digits(std::string_view text) noexcept
{
    if (text.empty()) {
        return false;
    }
    for (const char c : text) {
        if (c < '0' || c > '9') {
            return false;
        }
    }
    return true;
}

inline int number(std::string_view two_or_four_digits) noexcept
{
    int value = 0;
    for (const char c : two_or_four_digits) {
        value = value * 10 + (c - '0');
    }
    return value;
}

/// One value's length, characters and repertoire, by its VR's row in kVrs: a
/// VR that may hold several values refuses the backslash that separates them
/// and every control character; a single-valued text VR allows TAB, LF, FF, CR.
inline void check_string(Vr vr, std::string_view value)
{
    const VrInfo& row = info(vr);
    const std::size_t length = row.counts_characters ? characters(value) : value.size();
    if (!row.counts_characters) {
        characters(value);
    }
    if (length > row.max_length) {
        refuse(std::string(row.name) + " allows " + std::to_string(row.max_length) +
               (row.counts_characters ? " characters" : " bytes") + "; this value has " + std::to_string(length));
    }
    for (const char c : value) {
        const auto code = static_cast<unsigned char>(c);
        if (row.multiple_values && c == '\\') {
            refuse("it contains a backslash, which separates " + std::string(row.name) + " values");
        }
        const bool paragraph = !row.multiple_values && (c == '\t' || c == '\n' || c == '\f' || c == '\r');
        if ((code < 0x20 || code == 0x7F) && !paragraph) {
            refuse("it contains the control character " + std::to_string(code));
        }
    }
}

inline Time parse_dt(std::string_view raw)
{
    using namespace std::chrono;
    const std::string_view text = trimmed(raw);
    if (text.size() < 14 || !digits(text.substr(0, 14))) {
        refuse("it is not a DT: YYYYMMDDHHMMSS, an optional fraction, then a +ZZXX or -ZZXX offset");
    }
    std::size_t position = 14;
    std::int64_t micro = 0;
    if (position < text.size() && text[position] == '.') {
        const std::size_t start = ++position;
        while (position < text.size() && position - start < 6 && text[position] >= '0' && text[position] <= '9') {
            micro = micro * 10 + (text[position] - '0');
            ++position;
        }
        if (position == start) {
            refuse("its fraction has no digits");
        }
        for (std::size_t scale = position - start; scale < 6; ++scale) {
            micro *= 10;
        }
    }
    if (position == text.size()) {
        refuse("it has no UTC offset, which I2S requires");
    }
    const std::string_view offset = text.substr(position);
    if (offset.size() != 5 || (offset[0] != '+' && offset[0] != '-') || !digits(offset.substr(1))) {
        refuse("its offset " + quoted(offset) + " is not +ZZXX or -ZZXX");
    }
    const year_month_day date{year{number(text.substr(0, 4))}, month{static_cast<unsigned>(number(text.substr(4, 2)))},
                              day{static_cast<unsigned>(number(text.substr(6, 2)))}};
    if (!date.ok() || date.year() < year{1}) {
        refuse("its date is not a calendar date");
    }
    const int hour = number(text.substr(8, 2));
    const int minute = number(text.substr(10, 2));
    const int second = number(text.substr(12, 2));
    if (second == 60) {
        refuse("its second is 60, a leap second, which a UTC time point cannot hold");
    }
    if (hour > 23 || minute > 59 || second > 59) {
        refuse("its time is not from 000000 to 235959");
    }
    const int offset_minutes = (offset[0] == '-' ? -1 : 1) * (number(offset.substr(1, 2)) * 60 + number(offset.substr(3, 2)));
    if (number(offset.substr(3, 2)) > 59 || offset_minutes < -12 * 60 || offset_minutes > 14 * 60) {
        refuse("its UTC offset " + std::string(offset) + " is outside -1200 to +1400");
    }
    return Time{sys_days{date}} + hours{hour} + minutes{minute} + seconds{second} + microseconds{micro} -
           minutes{offset_minutes};
}

inline std::int32_t parse_is(std::string_view raw)
{
    if (raw.size() > info(Vr::IS).max_length) {
        refuse("an IS allows " + std::to_string(info(Vr::IS).max_length) + " bytes; this value has " + std::to_string(raw.size()));
    }
    std::string_view text = trimmed(raw);
    if (!text.empty() && text.front() == '+') {
        text.remove_prefix(1);
    }
    std::int64_t value = 0;
    const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), value);
    if (text.empty() || error != std::errc{} || end != text.data() + text.size() || !digits(text.substr(text.front() == '-' ? 1 : 0))) {
        refuse("it is not an IS: a base-10 integer");
    }
    if (!std::in_range<std::int32_t>(value)) {
        refuse("it is outside an IS's range, -2147483648 to 2147483647");
    }
    return static_cast<std::int32_t>(value);
}

inline double parse_ds(std::string_view raw)
{
    if (raw.size() > info(Vr::DS).max_length) {
        refuse("a DS allows " + std::to_string(info(Vr::DS).max_length) + " bytes; this value has " + std::to_string(raw.size()));
    }
    std::string_view text = trimmed(raw);
    for (const char c : text) {
        if (!((c >= '0' && c <= '9') || c == '+' || c == '-' || c == 'E' || c == 'e' || c == '.')) {
            refuse("it is not a DS: it contains " + quoted(std::string_view{&c, 1}));
        }
    }
    if (!text.empty() && text.front() == '+') {
        text.remove_prefix(1);
    }
    double value = 0.0;
    const auto [end, error] = std::from_chars(text.data(), text.data() + text.size(), value);
    if (text.empty() || error != std::errc{} || end != text.data() + text.size() || !std::isfinite(value)) {
        refuse("it is not a DS: a finite base-10 number");
    }
    return value;
}

inline bool parse_cs_boolean(std::string_view raw)
{
    const std::string_view text = trimmed(raw);
    if (text == "YES") {
        return true;
    }
    if (text == "NO") {
        return false;
    }
    refuse(quoted(raw) + " is not YES or NO");
}

/// The rule of each VR beyond its length and repertoire. The switch is
/// exhaustive over the generated Vr, so a VR added to the spec fails to build
/// until it has a rule here.
inline void check_lexical(Vr vr, std::string_view value)
{
    check_string(vr, value);
    switch (vr) {
    case Vr::CS:
        for (const char c : value) {
            if (!((c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == ' ' || c == '_')) {
                refuse("it is not a CS: upper-case letters, digits, spaces and underscores");
            }
        }
        return;
    case Vr::DS: parse_ds(value); return;
    case Vr::DT: parse_dt(value); return;
    case Vr::IS: parse_is(value); return;
    case Vr::LO:
    case Vr::LT:
    case Vr::SH:
    case Vr::ST:
    case Vr::UT: return;
    }
}

inline std::vector<std::string_view> split(std::string_view text)
{
    std::vector<std::string_view> values;
    std::size_t start = 0;
    for (std::size_t end = text.find('\\'); end != std::string_view::npos; end = text.find('\\', start)) {
        values.push_back(text.substr(start, end - start));
        start = end + 1;
    }
    values.push_back(text.substr(start));
    return values;
}

/// Runs a codec step at a public boundary: a CodecError becomes the Result's
/// Error, with the offending text; nothing else is expected to throw.
template <class F>
auto guarded(std::string_view text, F&& step) noexcept -> Result<decltype(step())>
{
    try {
        return step();
    } catch (const CodecError& error) {
        return Error{std::nullopt, std::string(text), quoted(text) + ": " + error.what()};
    } catch (const std::bad_alloc&) {
        return Error{std::nullopt, {}, "out of memory in the I2S codec"};
    } catch (...) {
        return Error{std::nullopt, {}, "an unexpected exception in the I2S codec"};
    }
}

} // namespace detail

// --- Codec: one value's text under its VR --------------------------------------

/// Text written as a string VR (SH, LO, ST, LT, UT), checked against its limits.
[[nodiscard]] inline Result<std::string> encode_text(Vr vr, std::string_view value) noexcept
{
    return detail::guarded(value, [&] {
        detail::check_lexical(vr, value);
        return std::string(value);
    });
}

/// Whether text is one valid value of a VR, by every rule I2S applies to it.
[[nodiscard]] inline Result<std::monostate> check_text(Vr vr, std::string_view value) noexcept
{
    return detail::guarded(value, [&] {
        detail::check_lexical(vr, value);
        return std::monostate{};
    });
}

/// A DT in UTC, to the microsecond: YYYYMMDDHHMMSS.FFFFFF+0000, 26 bytes.
[[nodiscard]] inline Result<std::string> encode_date_time(Time time) noexcept
{
    return detail::guarded({}, [&] {
        using namespace std::chrono;
        const sys_days day = floor<days>(time);
        const year_month_day date{day};
        const hh_mm_ss clock{time - day};
        const int year_number = static_cast<int>(date.year());
        if (year_number < 1 || year_number > 9999) {
            detail::refuse("its year " + std::to_string(year_number) + " is outside a DT's 0001 to 9999");
        }
        std::array<char, 32> text{};
        std::snprintf(text.data(), text.size(), "%04d%02u%02u%02d%02d%02d.%06lld+0000", year_number,
                      static_cast<unsigned>(date.month()), static_cast<unsigned>(date.day()),
                      static_cast<int>(clock.hours().count()), static_cast<int>(clock.minutes().count()),
                      static_cast<int>(clock.seconds().count()), static_cast<long long>(clock.subseconds().count()));
        return std::string(text.data());
    });
}

[[nodiscard]] inline Result<Time> decode_date_time(std::string_view text) noexcept
{
    return detail::guarded(text, [&] { return detail::parse_dt(text); });
}

[[nodiscard]] inline Result<std::string> encode_integer(std::int32_t value) noexcept
{
    return std::to_string(value);
}

[[nodiscard]] inline Result<std::int32_t> decode_integer(std::string_view text) noexcept
{
    return detail::guarded(text, [&] { return detail::parse_is(text); });
}

/// The shortest text that reads back to the same double, refused when it
/// exceeds a DS's 16 bytes.
[[nodiscard]] inline Result<std::string> encode_decimal(double value) noexcept
{
    return detail::guarded({}, [&] {
        if (!std::isfinite(value)) {
            detail::refuse("a DS holds a finite number");
        }
        std::array<char, 32> text{};
        const auto [end, error] = std::to_chars(text.data(), text.data() + text.size(), value);
        if (error != std::errc{}) {
            detail::refuse("std::to_chars could not write it");
        }
        const std::string written(text.data(), end);
        if (written.size() > info(Vr::DS).max_length) {
            detail::refuse("a DS allows " + std::to_string(info(Vr::DS).max_length) + " bytes; " + written + " needs " +
                           std::to_string(written.size()));
        }
        return written;
    });
}

[[nodiscard]] inline Result<double> decode_decimal(std::string_view text) noexcept
{
    return detail::guarded(text, [&] { return detail::parse_ds(text); });
}

/// A BOOLEAN as a CS, YES or NO, as DICOM's Burned In Annotation (0028,0301) writes one.
[[nodiscard]] inline Result<std::string> encode_boolean(bool value) noexcept
{
    return std::string(value ? "YES" : "NO");
}

[[nodiscard]] inline Result<bool> decode_boolean(std::string_view text) noexcept
{
    return detail::guarded(text, [&] { return detail::parse_cs_boolean(text); });
}

// --- Typed values ----------------------------------------------------------------

namespace detail {

template <Key K>
inline constexpr ValueType kType = info(K).value_type;

template <Key K>
inline constexpr bool kMany = info(K).multiplicity.maximum != std::optional<std::uint16_t>{1};

template <ValueType V, bool Many>
struct ValueOfImpl;
template <>
struct ValueOfImpl<ValueType::TEXT, false> {
    using type = std::string;
};
template <>
struct ValueOfImpl<ValueType::TEXT, true> {
    using type = std::vector<std::string>;
};
template <>
struct ValueOfImpl<ValueType::DATE_TIME, false> {
    using type = Time;
};
template <>
struct ValueOfImpl<ValueType::INTEGER, false> {
    using type = std::int32_t;
};
template <>
struct ValueOfImpl<ValueType::DECIMAL, false> {
    using type = double;
};
template <>
struct ValueOfImpl<ValueType::BOOLEAN, false> {
    using type = bool;
};

template <class T>
struct IsSysTime : std::false_type {};
template <class Duration>
struct IsSysTime<std::chrono::sys_time<Duration>> : std::true_type {};

template <class T>
inline constexpr bool kCharacter = std::is_same_v<T, char> || std::is_same_v<T, wchar_t> || std::is_same_v<T, char8_t> ||
                                   std::is_same_v<T, char16_t> || std::is_same_v<T, char32_t>;

} // namespace detail

/// The C++ type a key's value reads as.
template <Key K>
using ValueOf = typename detail::ValueOfImpl<detail::kType<K>, detail::kMany<K>>::type;

/// Text: a string literal, std::string or std::string_view. A number, a bool
/// or a null pointer is refused.
template <class T>
concept TextValue = std::convertible_to<T, std::string_view> && !std::is_arithmetic_v<std::remove_cvref_t<T>> &&
                    !std::is_null_pointer_v<std::remove_cvref_t<T>>;

/// Several texts, for a key that holds several values.
template <class T>
concept TextListValue = std::ranges::input_range<T> && TextValue<std::ranges::range_reference_t<T>> && !TextValue<T>;

/// A UTC time point of any precision, std::chrono::sys_time<Duration>.
template <class T>
concept DateTimeValue = detail::IsSysTime<std::remove_cvref_t<T>>::value;

/// An integer type whose every value is an IS: no bool, no character type,
/// nothing wider than 32 bits, so nothing narrows.
template <class T>
concept IntegerValue = std::integral<std::remove_cvref_t<T>> && !std::same_as<std::remove_cvref_t<T>, bool> &&
                       !detail::kCharacter<std::remove_cvref_t<T>> &&
                       std::in_range<std::int32_t>(std::numeric_limits<std::remove_cvref_t<T>>::min()) &&
                       std::in_range<std::int32_t>(std::numeric_limits<std::remove_cvref_t<T>>::max());

/// A float or a double.
template <class T>
concept DecimalValue = std::same_as<std::remove_cvref_t<T>, double> || std::same_as<std::remove_cvref_t<T>, float>;

/// bool and nothing that converts to it.
template <class T>
concept BooleanValue = std::same_as<std::remove_cvref_t<T>, bool>;

namespace detail {

template <Key K, class T>
concept Assignable = (kType<K> == ValueType::TEXT && (TextValue<T> || (kMany<K> && TextListValue<T>))) ||
                     (kType<K> == ValueType::DATE_TIME && DateTimeValue<T>) ||
                     (kType<K> == ValueType::INTEGER && IntegerValue<T>) ||
                     (kType<K> == ValueType::DECIMAL && DecimalValue<T>) ||
                     (kType<K> == ValueType::BOOLEAN && BooleanValue<T>);

/// The text of a typed value under key K's VR; throws CodecError.
template <Key K, class T>
std::string encode(T&& value)
{
    constexpr Vr vr = info(K).vr;
    if constexpr (kType<K> == ValueType::TEXT && TextValue<T>) {
        const std::string_view text{value};
        check_lexical(vr, text);
        return std::string(text);
    } else if constexpr (kType<K> == ValueType::TEXT) {
        std::string joined;
        std::size_t count = 0;
        for (auto&& item : value) {
            const std::string_view text{item};
            check_lexical(vr, text);
            joined += (count++ == 0 ? "" : "\\");
            joined += text;
        }
        const Multiplicity multiplicity = info(K).multiplicity;
        if (count < multiplicity.minimum || (multiplicity.maximum && count > *multiplicity.maximum)) {
            refuse(std::to_string(count) + " values, outside the key's multiplicity");
        }
        return joined;
    } else if constexpr (kType<K> == ValueType::DATE_TIME) {
        return encode_date_time(std::chrono::floor<std::chrono::microseconds>(value)).value();
    } else if constexpr (kType<K> == ValueType::INTEGER) {
        return encode_integer(static_cast<std::int32_t>(value)).value();
    } else if constexpr (kType<K> == ValueType::DECIMAL) {
        const Result<std::string> text = encode_decimal(static_cast<double>(value));
        if (!text.has_value()) {
            refuse(text.error().message);
        }
        return text.value();
    } else {
        return encode_boolean(value).value();
    }
}

} // namespace detail

/// One element of an Attributes: a key that holds a value.
using Value = std::variant<std::string, std::vector<std::string>, Time, std::int32_t, double, bool>;

class Attributes;

class Element {
public:
    Element(Key key, std::string_view text) noexcept : _key(key), _text(text) {}

    [[nodiscard]] Key key() const noexcept { return _key; }
    [[nodiscard]] std::string_view name() const noexcept { return info(_key).name; }
    [[nodiscard]] std::optional<std::string_view> short_name() const noexcept { return info(_key).short_name; }
    [[nodiscard]] Vr vr() const noexcept { return info(_key).vr; }
    [[nodiscard]] IdentityClass identity() const noexcept { return info(_key).identity; }
    /// The value as DICOM text, exactly as the attribute pair carries it.
    [[nodiscard]] std::string_view text() const noexcept { return _text; }

    /// The value as its C++ type. Text in an Attributes was checked when it was
    /// written or read, so decoding it cannot fail here.
    [[nodiscard]] Value value() const
    {
        const KeyInfo& row = info(_key);
        switch (row.value_type) {
        case ValueType::TEXT:
            if (row.multiplicity.maximum == std::optional<std::uint16_t>{1}) {
                return std::string(_text);
            } else {
                std::vector<std::string> values;
                for (const std::string_view item : detail::split(_text)) {
                    values.emplace_back(item);
                }
                return values;
            }
        case ValueType::DATE_TIME: return decode_date_time(_text).value();
        case ValueType::DECIMAL: return decode_decimal(_text).value();
        case ValueType::INTEGER: return decode_integer(_text).value();
        case ValueType::BOOLEAN: return decode_boolean(_text).value();
        }
        throw std::logic_error("I2S::Element::value(): a ValueType outside the generated enumeration");
    }

    /// Calls visitor with the value as its C++ type.
    template <class Visitor>
    decltype(auto) visit(Visitor&& visitor) const
    {
        return std::visit(std::forward<Visitor>(visitor), value());
    }

private:
    Key _key;
    std::string_view _text;
};

template <Key K>
class Slot;

/// A key's values, written and read as their C++ types and held as DICOM text,
/// in the spec's key order. Converts to and from IFE's attribute pairs.
class Attributes {
public:
    class Iterator {
    public:
        using value_type = Element;
        using difference_type = std::ptrdiff_t;
        using iterator_concept = std::forward_iterator_tag;

        Iterator() noexcept = default;
        Iterator(const Attributes* owner, std::size_t index) noexcept : _owner(owner), _index(index) { settle(); }

        [[nodiscard]] Element operator*() const noexcept
        {
            return Element{kKeys[_index].key, *_owner->_texts[_index]};
        }
        Iterator& operator++() noexcept
        {
            ++_index;
            settle();
            return *this;
        }
        Iterator operator++(int) noexcept
        {
            Iterator before = *this;
            ++*this;
            return before;
        }
        friend bool operator==(const Iterator&, const Iterator&) = default;

    private:
        // Moves to the next key that holds a value: a loop, so a run of empty
        // keys costs no stack.
        void settle() noexcept
        {
            while (_owner != nullptr && _index < kKeyCount && !_owner->_texts[_index].has_value()) {
                ++_index;
            }
        }
        const Attributes* _owner = nullptr;
        std::size_t _index = 0;
    };

    template <Key K>
    [[nodiscard]] Slot<K> operator[](TypedKey<K>) noexcept;

    /// Writes key K. A value its VR refuses is not stored: the Error is
    /// returned, kept in errors(), and makes to_pairs() refuse.
    template <Key K, class T>
        requires detail::Assignable<K, T>
    Result<std::monostate> set(TypedKey<K>, T&& value) noexcept
    {
        constexpr std::size_t index = static_cast<std::size_t>(K);
        std::erase_if(_errors, [](const Error& error) { return error.key == K; });
        Result<std::string> text = detail::guarded({}, [&] { return detail::encode<K>(std::forward<T>(value)); });
        if (!text.has_value()) {
            Error error = text.error();
            error.key = K;
            error.message = std::string(info(K).name) + ": " + error.message;
            _errors.push_back(error);
            return error;
        }
        _texts[index] = text.value();
        return std::monostate{};
    }

    /// Key K's value as its C++ type, or std::nullopt when the key holds none.
    template <Key K>
    [[nodiscard]] std::optional<ValueOf<K>> get(TypedKey<K>) const noexcept
    {
        const std::optional<std::string_view> stored = text(K);
        if (!stored) {
            return std::nullopt;
        }
        return std::get<ValueOf<K>>(Element{K, *stored}.value());
    }

    /// A key's DICOM text, or std::nullopt when it holds none.
    [[nodiscard]] std::optional<std::string_view> text(Key key) const noexcept
    {
        const std::optional<std::string>& stored = _texts[static_cast<std::size_t>(key)];
        return stored ? std::optional<std::string_view>{*stored} : std::nullopt;
    }

    /// The writes refused since each key was last written successfully.
    [[nodiscard]] const std::vector<Error>& errors() const noexcept { return _errors; }

    /// The (key name, value text) pairs in the spec's key order, or the first
    /// refused write, so a refused value is never silently left out.
    [[nodiscard]] Result<std::vector<Pair>> to_pairs() const noexcept
    {
        if (!_errors.empty()) {
            Error first = _errors.front();
            first.message += " (" + std::to_string(_errors.size()) + " write(s) refused)";
            return first;
        }
        return detail::guarded({}, [&] {
            std::vector<Pair> pairs;
            for (const Element& element : *this) {
                pairs.push_back(Pair{std::string(element.name()), std::string(element.text())});
            }
            return pairs;
        });
    }

    /// Attributes read from IFE's pairs. Each key must be an I2S key's name and
    /// appear once, and each text must be a valid value of the key's VR.
    [[nodiscard]] static Result<Attributes> from_pairs(std::span<const Pair> pairs) noexcept
    {
        Attributes read;
        for (const Pair& pair : pairs) {
            const std::optional<Key> key = key_from_name(pair.key);
            if (!key) {
                return Error{std::nullopt, pair.value, detail::quoted(pair.key) + " is not an I2S key"};
            }
            const KeyInfo& row = info(*key);
            if (row.name != pair.key) {
                return Error{key, pair.value,
                             detail::quoted(pair.key) + " is a short name; the pair carries " + std::string(row.name)};
            }
            std::optional<std::string>& slot = read._texts[static_cast<std::size_t>(*key)];
            if (slot) {
                return Error{key, pair.value, std::string(row.name) + " appears twice"};
            }
            Result<std::monostate> valid = check_pair(*key, pair.value);
            if (!valid.has_value()) {
                return Error{key, pair.value, std::string(row.name) + ": " + valid.error().message};
            }
            slot = pair.value;
        }
        return read;
    }

    [[nodiscard]] Iterator begin() const noexcept { return Iterator{this, 0}; }
    [[nodiscard]] Iterator end() const noexcept { return Iterator{this, kKeyCount}; }

private:
    static Result<std::monostate> check_pair(Key key, std::string_view text) noexcept
    {
        return detail::guarded(text, [&] {
            const KeyInfo& row = info(key);
            const bool many = row.multiplicity.maximum != std::optional<std::uint16_t>{1};
            const std::vector<std::string_view> values = many ? detail::split(text) : std::vector<std::string_view>{text};
            for (const std::string_view value : values) {
                detail::check_lexical(row.vr, value);
                if (row.value_type == ValueType::BOOLEAN) {
                    detail::parse_cs_boolean(value);
                }
            }
            if (values.size() < row.multiplicity.minimum || (row.multiplicity.maximum && values.size() > *row.multiplicity.maximum)) {
                detail::refuse(std::to_string(values.size()) + " values, outside the key's multiplicity");
            }
            return std::monostate{};
        });
    }

    std::array<std::optional<std::string>, kKeyCount> _texts{};
    std::vector<Error> _errors;
};

/// What attributes[key] returns: an assignment target that accepts only key
/// K's C++ type. One operator= per value type, so a refused value's diagnostic
/// names the concept the value failed.
template <Key K>
class Slot {
public:
    explicit Slot(Attributes& owner) noexcept : _owner(owner) {}
    Slot(const Slot&) = delete;
    Slot& operator=(const Slot&) = delete;

    template <class T>
        requires(detail::kType<K> == ValueType::TEXT) && TextValue<T>
    void operator=(T&& value) noexcept
    {
        static_cast<void>(_owner.set(TypedKey<K>{}, std::forward<T>(value)));
    }

    template <class T>
        requires(detail::kType<K> == ValueType::TEXT && detail::kMany<K>) && TextListValue<T>
    void operator=(T&& values) noexcept
    {
        static_cast<void>(_owner.set(TypedKey<K>{}, std::forward<T>(values)));
    }

    void operator=(std::initializer_list<std::string_view> values) noexcept
        requires(detail::kType<K> == ValueType::TEXT && detail::kMany<K>)
    {
        static_cast<void>(_owner.set(TypedKey<K>{}, std::span<const std::string_view>{values.begin(), values.size()}));
    }

    template <class T>
        requires(detail::kType<K> == ValueType::DATE_TIME) && DateTimeValue<T>
    void operator=(T&& value) noexcept
    {
        static_cast<void>(_owner.set(TypedKey<K>{}, std::forward<T>(value)));
    }

    template <class T>
        requires(detail::kType<K> == ValueType::INTEGER) && IntegerValue<T>
    void operator=(T&& value) noexcept
    {
        static_cast<void>(_owner.set(TypedKey<K>{}, std::forward<T>(value)));
    }

    template <class T>
        requires(detail::kType<K> == ValueType::DECIMAL) && DecimalValue<T>
    void operator=(T&& value) noexcept
    {
        static_cast<void>(_owner.set(TypedKey<K>{}, std::forward<T>(value)));
    }

    template <class T>
        requires(detail::kType<K> == ValueType::BOOLEAN) && BooleanValue<T>
    void operator=(T&& value) noexcept
    {
        static_cast<void>(_owner.set(TypedKey<K>{}, std::forward<T>(value)));
    }

private:
    Attributes& _owner;
};

template <Key K>
Slot<K> Attributes::operator[](TypedKey<K>) noexcept
{
    return Slot<K>{*this};
}

/// Whether a de-identifier must treat key K's value as protected health
/// information: its PHI flag's value when the flag is present, and the flag's
/// absent default (for the DII: true, scramble it) when it is not.
template <Key K>
    requires(info(K).phi_flag.has_value())
[[nodiscard]] bool is_phi(const Attributes& attributes, TypedKey<K>) noexcept
{
    constexpr PhiFlag flag = *info(K).phi_flag;
    const std::optional<std::string_view> text = attributes.text(flag.key);
    if (!text) {
        return flag.absent_means_phi;
    }
    const Result<bool> value = decode_boolean(*text);
    return value.has_value() ? value.value() : true;
}

static_assert(std::ranges::forward_range<const Attributes>);

} // namespace I2S

#endif // I2S_ATTRIBUTES_HPP
