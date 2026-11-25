// detail/I2S_Concepts.hpp: the concepts naming the C++ types each value type
// accepts. I2S_Attributes.hpp includes it ahead of its declarations, which are
// constrained on these concepts; it is not meant to be included on its own. A
// refused value's compiler note names the concept it failed.
// RTM TypedKeys_01, ReadableHeaders_01, DicomSource_01
#ifndef I2S_DETAIL_CONCEPTS_HPP
#define I2S_DETAIL_CONCEPTS_HPP

#include "I2S_Keys.hpp"

#include <chrono>
#include <concepts>
#include <cstdint>
#include <limits>
#include <optional>
#include <ranges>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>

namespace I2S {

namespace detail {

template <Key K>
inline constexpr ValueType kType = info(K).value_type;

template <Key K>
inline constexpr bool kMany = info(K).multiplicity.maximum != std::optional<std::uint16_t>{1};

template <class T>
struct IsSysTime : std::false_type {};
template <class Duration>
struct IsSysTime<std::chrono::sys_time<Duration>> : std::true_type {};

template <class T>
inline constexpr bool kCharacter = std::is_same_v<T, char> || std::is_same_v<T, wchar_t> || std::is_same_v<T, char8_t> ||
                                   std::is_same_v<T, char16_t> || std::is_same_v<T, char32_t>;

} // namespace detail

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

/// A DICOM data set as Attributes::from_dicom reads it: called with a DICOM
/// tag, it returns that attribute's value as DICOM text, or std::nullopt when
/// the data set does not carry it.
template <class F>
concept DicomLookup = std::invocable<F&, DicomTag> &&
                      std::convertible_to<std::invoke_result_t<F&, DicomTag>, std::optional<std::string>>;

namespace detail {

template <Key K, class T>
concept Assignable = (kType<K> == ValueType::TEXT && (TextValue<T> || (kMany<K> && TextListValue<T>))) ||
                     (kType<K> == ValueType::DATE_TIME && DateTimeValue<T>) ||
                     (kType<K> == ValueType::INTEGER && IntegerValue<T>) ||
                     (kType<K> == ValueType::DECIMAL && DecimalValue<T>) ||
                     (kType<K> == ValueType::BOOLEAN && BooleanValue<T>);

} // namespace detail

} // namespace I2S

#endif // I2S_DETAIL_CONCEPTS_HPP
