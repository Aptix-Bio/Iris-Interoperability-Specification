// I2S_Attributes.hpp: a slide's I2S attributes as typed C++ values, held as
// DICOM text, converted to and from IFE's METADATA_I2S attribute pairs.
//
//   I2S::Attributes attributes;
//   attributes[I2S::Attribute::Manufacturer] = "Leica";
//   attributes[I2S::Attribute::ScanTime]     = std::chrono::system_clock::now();
//   const std::vector<I2S::Pair> pairs       = attributes.to_pairs().value();
//
// This file is the public surface, declarations only. The keys are listed at
// the top of I2S_Keys.hpp (namespace I2S::Attribute). The concepts naming the
// C++ types each value type accepts are in detail/I2S_Concepts.hpp; the DICOM
// text codec and every function body are in detail/I2S_Attributes_impl.hpp,
// included at the end of this file.
// RTM TypedKeys_01, Encoding_01, Adapter_01, Iteration_01, PhiFlag_02, ReadableHeaders_01, DicomSource_01
#ifndef I2S_ATTRIBUTES_HPP
#define I2S_ATTRIBUTES_HPP

#include "I2S_Keys.hpp"
#include "detail/I2S_Concepts.hpp" // TextValue, TextListValue, DateTimeValue, IntegerValue, DecimalValue, BooleanValue, DicomLookup

#include <array>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <variant>
#include <vector>

namespace I2S {

/// A DATE_TIME value: a UTC time, at the microsecond precision a DT holds.
using Time = std::chrono::sys_time<std::chrono::microseconds>;

/// A value as its C++ type: one TEXT, several TEXT, DATE_TIME, INTEGER, DECIMAL, BOOLEAN.
using Value = std::variant<std::string, std::vector<std::string>, Time, std::int32_t, double, bool>;

namespace detail {
template <Key K>
struct ValueOfKey;
} // namespace detail

/// The C++ type key K's value reads as: std::string for Manufacturer, Time for ScanTime.
template <Key K>
using ValueOf = typename detail::ValueOfKey<K>::type;

/// Why a value or a pair was refused: the key (when one is known), the
/// offending text, and the rule it broke.
struct Error {
    std::optional<Key> key;
    std::string text;
    std::string message;
};

/// A value, or the Error explaining its absence.
template <class T>
class [[nodiscard]] Result {
public:
    Result(T value);
    Result(Error error);
    /// Whether it holds a value.
    [[nodiscard]] bool has_value() const noexcept;
    /// The value; throws std::logic_error naming the error when it holds one.
    [[nodiscard]] const T& value() const;
    /// The error; throws std::logic_error when it holds a value.
    [[nodiscard]] const Error& error() const;

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

/// One key that holds a value, as iterating an Attributes yields it.
class Element {
public:
    Element(Key key, std::string_view text) noexcept;
    [[nodiscard]] Key key() const noexcept;
    [[nodiscard]] std::string_view name() const noexcept;
    [[nodiscard]] std::optional<std::string_view> short_name() const noexcept;
    [[nodiscard]] Vr vr() const noexcept;
    [[nodiscard]] IdentityClass identity() const noexcept;
    /// The value as DICOM text, exactly as the attribute pair carries it.
    [[nodiscard]] std::string_view text() const noexcept;
    /// The value as its C++ type; the text was checked when it was written or read.
    [[nodiscard]] Value value() const;
    /// Calls visitor with the value as its C++ type.
    template <class Visitor>
    decltype(auto) visit(Visitor&& visitor) const;

private:
    Key _key;
    std::string_view _text;
};

/// What attributes[key] returns: an assignment target that accepts only key
/// K's C++ type, with one operator= per value type.
template <Key K>
class Slot;

/// A slide's I2S attributes: each key's value written and read as its C++
/// type, held as DICOM text, iterated in the specification's key order.
class Attributes {
public:
    /// A forward iterator over the keys that hold a value, yielding Element.
    class Iterator;

    /// attributes[I2S::Attribute::Manufacturer] = "Leica"; a value of the wrong type does not compile.
    template <Key K>
    [[nodiscard]] Slot<K> operator[](TypedKey<K>) noexcept;

    /// Writes key K. A value its VR refuses is not stored: the Error is
    /// returned, kept in errors(), and makes to_pairs() refuse.
    template <Key K, class T>
        requires detail::Assignable<K, T>
    Result<std::monostate> set(TypedKey<K>, T&& value) noexcept;

    /// Key K's value as its C++ type, or std::nullopt when the key holds none.
    template <Key K>
    [[nodiscard]] std::optional<ValueOf<K>> get(TypedKey<K>) const noexcept;

    /// A key's DICOM text, or std::nullopt when it holds none.
    [[nodiscard]] std::optional<std::string_view> text(Key key) const noexcept;

    /// The writes refused since each key was last written successfully.
    [[nodiscard]] const std::vector<Error>& errors() const noexcept;

    /// The (key name, value text) pairs in the spec's key order, or the first
    /// refused write, so a refused value is never silently left out.
    [[nodiscard]] Result<std::vector<Pair>> to_pairs() const noexcept;

    /// Attributes read from IFE's pairs: each key an I2S key's name, once, and
    /// each text a valid value of the key's VR.
    [[nodiscard]] static Result<Attributes> from_pairs(std::span<const Pair> pairs) noexcept;

    /// Attributes read from a DICOM data set: lookup(tag) is called once for
    /// each key with a DICOM attribute (I2S::kKeys) and returns its DICOM text
    /// or std::nullopt; trailing padding spaces are dropped. A value I2S
    /// refuses is kept in errors(), as a refused write is.
    template <DicomLookup Lookup>
    [[nodiscard]] static Attributes from_dicom(Lookup&& lookup) noexcept;

    [[nodiscard]] Iterator begin() const noexcept;
    [[nodiscard]] Iterator end() const noexcept;

private:
    static Result<std::monostate> check_pair(Key key, std::string_view text) noexcept;
    /// Stores key's text, or records its refusal, naming the key, in errors().
    Result<std::monostate> keep(Key key, const Result<std::string>& text) noexcept;

    std::array<std::optional<std::string>, kKeyCount> _texts{};
    std::vector<Error> _errors;
};

/// Whether a de-identifier must treat key K's value as protected health
/// information: its PHI flag's value when present, else the flag's absent
/// default (for the DII: true, scramble it).
template <Key K>
    requires(info(K).phi_flag.has_value())
[[nodiscard]] bool is_phi(const Attributes& attributes, TypedKey<K>) noexcept;

} // namespace I2S

#include "detail/I2S_Attributes_impl.hpp"

#endif // I2S_ATTRIBUTES_HPP
