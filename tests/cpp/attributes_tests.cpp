// I2S::Attributes: typed keys, the DICOM text of each value, the adapter to and
// from IFE's (key name, value text) attribute pairs, and iteration.
// RTM TypedKeys_01, Encoding_01, Adapter_01, Iteration_01, PhiFlag_02
#include "I2S_Attributes.hpp"

#include <catch2/catch_test_macros.hpp>

#include <chrono>
#include <cstdint>
#include <limits>
#include <ranges>
#include <string>
#include <type_traits>
#include <utility>
#include <vector>

namespace {

using namespace std::chrono_literals;
using std::chrono::sys_days;
using std::chrono::year_month_day;
using Pairs = std::vector<I2S::Pair>;

// A UTC time with a fraction, so precision is visible in the text.
constexpr I2S::Time kScan = sys_days{std::chrono::year{2026} / 11 / 24} + 15h + 30min + 0s + 123456us;

std::string text_of(const I2S::Attributes& attributes, I2S::Key key)
{
    const std::optional<std::string_view> text = attributes.text(key);
    REQUIRE(text.has_value());
    return std::string{*text};
}

} // namespace

TEST_CASE("every key and short name is a typed constant in namespace I2S", "[TypedKeys_01]")
{
    STATIC_REQUIRE(std::is_same_v<decltype(I2S::Manufacturer), const I2S::TypedKey<I2S::Key::Manufacturer>>);
    STATIC_REQUIRE(std::is_same_v<decltype(I2S::DII), decltype(I2S::DigitalImageIdentifier)>);
    STATIC_REQUIRE(std::is_same_v<decltype(I2S::DII_is_PHI), decltype(I2S::DigitalImageIdentifierIsPHI)>);
    STATIC_REQUIRE(std::is_same_v<decltype(I2S::ScanTime), decltype(I2S::AcquisitionDateTime)>);
    STATIC_REQUIRE(std::is_same_v<I2S::ValueOf<I2S::Key::AcquisitionDateTime>, I2S::Time>);
    STATIC_REQUIRE(std::is_same_v<I2S::ValueOf<I2S::Key::SoftwareVersions>, std::vector<std::string>>);
    STATIC_REQUIRE(I2S::info(I2S::Key::AcquisitionDateTime).vr == I2S::Vr::DT);
}

TEST_CASE("TEXT round-trips as its key's VR", "[Encoding_01]")
{
    I2S::Attributes attributes;
    attributes[I2S::Manufacturer] = "Leica";
    attributes[I2S::ManufacturerModelName] = std::string{"GT450"};
    CHECK(text_of(attributes, I2S::Key::Manufacturer) == "Leica");
    CHECK(attributes.get(I2S::ManufacturerModelName) == std::optional<std::string>{"GT450"});
    CHECK_FALSE(attributes.get(I2S::DeviceSerialNumber).has_value());
}

TEST_CASE("several TEXT values are joined by the backslash", "[Encoding_01]")
{
    I2S::Attributes attributes;
    attributes[I2S::SoftwareVersions] = {"Console 1.2", "Firmware 3.4"};
    CHECK(text_of(attributes, I2S::Key::SoftwareVersions) == "Console 1.2\\Firmware 3.4");
    CHECK(attributes.get(I2S::SoftwareVersions) == std::optional<std::vector<std::string>>{{"Console 1.2", "Firmware 3.4"}});
}

TEST_CASE("DATE_TIME is a DT in UTC, to the microsecond, with its offset", "[Encoding_01]")
{
    I2S::Attributes attributes;
    attributes[I2S::ScanTime] = kScan;
    CHECK(text_of(attributes, I2S::Key::AcquisitionDateTime) == "20261124153000.123456+0000");
    CHECK(attributes.get(I2S::ScanTime) == std::optional<I2S::Time>{kScan});
    // A nanosecond clock is floored to the microsecond it falls in.
    attributes[I2S::ScanTime] = std::chrono::sys_time<std::chrono::nanoseconds>{kScan} + 999ns;
    CHECK(attributes.get(I2S::ScanTime) == std::optional<I2S::Time>{kScan});
}

TEST_CASE("a DT with another offset or fewer fractional digits reads as UTC", "[Encoding_01]")
{
    CHECK(I2S::decode_date_time("20261124103000.123456-0500").value() == kScan);
    CHECK(I2S::decode_date_time("20261125003000.1+0900").value() == kScan - 23456us);
    CHECK(I2S::decode_date_time("20261124153000+0000").value() == kScan - 123456us);
}

TEST_CASE("a DT is refused without an offset, outside the offsets, or at a leap second", "[Encoding_01]")
{
    CHECK(I2S::decode_date_time("20261124153000").error().message.find("no UTC offset") != std::string::npos);
    CHECK(I2S::decode_date_time("20261124153000+1500").error().message.find("+1500") != std::string::npos);
    CHECK(I2S::decode_date_time("20261124235960+0000").error().message.find("leap second") != std::string::npos);
    CHECK(I2S::decode_date_time("20260230153000+0000").error().message.find("calendar date") != std::string::npos);
}

TEST_CASE("BOOLEAN is the CS YES or NO", "[Encoding_01]")
{
    CHECK(I2S::encode_boolean(true).value() == "YES");
    CHECK(I2S::encode_boolean(false).value() == "NO");
    CHECK(I2S::decode_boolean("NO").value() == false);
    CHECK(I2S::decode_boolean("TRUE").error().message.find("'TRUE'") != std::string::npos);
}

TEST_CASE("INTEGER is an IS across its whole range", "[Encoding_01]")
{
    constexpr std::int32_t low = std::numeric_limits<std::int32_t>::min();
    constexpr std::int32_t high = std::numeric_limits<std::int32_t>::max();
    CHECK(I2S::encode_integer(low).value() == "-2147483648");
    CHECK(I2S::decode_integer("-2147483648").value() == low);
    CHECK(I2S::decode_integer(I2S::encode_integer(high).value()).value() == high);
    CHECK(I2S::decode_integer("+40").value() == 40);
    CHECK(I2S::decode_integer("2147483648").error().message.find("2147483648") != std::string::npos);
    CHECK(I2S::decode_integer("4 0").error().message.find("'4 0'") != std::string::npos);
}

TEST_CASE("DECIMAL is the shortest DS that reads back to the same double", "[Encoding_01]")
{
    CHECK(I2S::encode_decimal(2.5e-4).value() == "0.00025");
    CHECK(I2S::decode_decimal("2.5E-4").value() == 2.5e-4);
    CHECK(I2S::decode_decimal(I2S::encode_decimal(-1234.5678).value()).value() == -1234.5678);
    // 0.30000000000000004 needs 19 bytes; a DS holds 16.
    const I2S::Error error = I2S::encode_decimal(0.1 + 0.2).error();
    CHECK(error.message.find("16") != std::string::npos);
    CHECK(error.message.find("19") != std::string::npos);
    CHECK(I2S::encode_decimal(std::numeric_limits<double>::infinity()).error().message.find("finite") != std::string::npos);
}

TEST_CASE("a string VR is held to its length in characters and refuses a backslash", "[Encoding_01]")
{
    const std::string at_limit(64, 'A');
    CHECK(I2S::encode_text(I2S::Vr::LO, at_limit).value() == at_limit);
    // 64 characters of two UTF-8 bytes each: 128 bytes, still within LO's 64 characters.
    std::string accents;
    for (int i = 0; i < 64; ++i) {
        accents += "\xC3\xA9";
    }
    CHECK(I2S::encode_text(I2S::Vr::LO, accents).has_value());
    const I2S::Error over = I2S::encode_text(I2S::Vr::LO, at_limit + "A").error();
    CHECK(over.message.find("65") != std::string::npos);
    CHECK(over.message.find("64") != std::string::npos);
    CHECK(I2S::encode_text(I2S::Vr::SH, std::string(17, 'A')).error().message.find("16") != std::string::npos);
    CHECK(I2S::encode_text(I2S::Vr::LO, "GT\\450").error().message.find("backslash") != std::string::npos);
    CHECK(I2S::encode_text(I2S::Vr::UT, "(01)0\\1").has_value());
    CHECK(I2S::encode_text(I2S::Vr::LO, "line\nbreak").error().message.find("control") != std::string::npos);
    CHECK(I2S::encode_text(I2S::Vr::LT, "line\nbreak").has_value());
    CHECK(I2S::encode_text(I2S::Vr::LO, "\xC3").error().message.find("UTF-8") != std::string::npos);
}

TEST_CASE("every VR's example in the spec reads through the codec", "[Encoding_01]")
{
    for (const I2S::VrInfo& vr : I2S::kVrs) {
        INFO(vr.name);
        CHECK(I2S::check_text(vr.vr, vr.example).has_value());
    }
}

TEST_CASE("a write the VR refuses is reported by name, and the pairs refuse it", "[Adapter_01]")
{
    I2S::Attributes attributes;
    attributes[I2S::Manufacturer] = std::string(65, 'A');
    CHECK_FALSE(attributes.text(I2S::Key::Manufacturer).has_value());
    REQUIRE(attributes.errors().size() == 1);
    const I2S::Error& error = attributes.errors().front();
    CHECK(error.key == I2S::Key::Manufacturer);
    CHECK(error.message.find("Manufacturer") != std::string::npos);
    CHECK(error.message.find("64") != std::string::npos);
    CHECK(error.message.find("65") != std::string::npos);
    CHECK_FALSE(attributes.to_pairs().has_value());
    CHECK_FALSE(attributes.set(I2S::Manufacturer, std::string(65, 'A')).has_value());
}

TEST_CASE("the pairs round-trip, in the spec's key order", "[Adapter_01]")
{
    I2S::Attributes attributes;
    attributes[I2S::ScanTime] = kScan;
    attributes[I2S::Manufacturer] = "Leica";
    attributes[I2S::DII_is_PHI] = false;
    const Pairs pairs = attributes.to_pairs().value();
    CHECK(pairs == Pairs{{"DigitalImageIdentifierIsPHI", "NO"},
                         {"Manufacturer", "Leica"},
                         {"AcquisitionDateTime", "20261124153000.123456+0000"}});
    const I2S::Attributes read = I2S::Attributes::from_pairs(pairs).value();
    CHECK(read.to_pairs().value() == pairs);
    CHECK(read.get(I2S::ScanTime) == std::optional<I2S::Time>{kScan});
}

TEST_CASE("pairs that are not I2S are refused naming the key and the text", "[Adapter_01]")
{
    const I2S::Error unknown = I2S::Attributes::from_pairs(Pairs{{"PatientName", "Doe^Jane"}}).error();
    CHECK(unknown.message.find("PatientName") != std::string::npos);
    const I2S::Error bad = I2S::Attributes::from_pairs(Pairs{{"AcquisitionDateTime", "yesterday"}}).error();
    CHECK(bad.key == I2S::Key::AcquisitionDateTime);
    CHECK(bad.text == "yesterday");
    CHECK(bad.message.find("AcquisitionDateTime") != std::string::npos);
    const Pairs twice{{"Manufacturer", "Leica"}, {"Manufacturer", "Leica"}};
    CHECK(I2S::Attributes::from_pairs(twice).error().message.find("twice") != std::string::npos);
    // A short name is a C++ convenience; the pair carries the key's name.
    CHECK(I2S::Attributes::from_pairs(Pairs{{"DII", "S26-1"}}).error().message.find("DigitalImageIdentifier") != std::string::npos);
}

TEST_CASE("Attributes is a forward range of elements in the spec's key order", "[Iteration_01]")
{
    STATIC_REQUIRE(std::ranges::forward_range<I2S::Attributes>);
    STATIC_REQUIRE(std::ranges::forward_range<const I2S::Attributes>);
    I2S::Attributes attributes;
    attributes[I2S::ScanTime] = kScan;
    attributes[I2S::SoftwareVersions] = {"1.0", "2.0"};
    attributes[I2S::DII] = "S26-1";
    std::vector<I2S::Key> order;
    for (const auto& element : attributes) {
        order.push_back(element.key());
    }
    CHECK(order == std::vector<I2S::Key>{I2S::Key::DigitalImageIdentifier, I2S::Key::SoftwareVersions,
                                        I2S::Key::AcquisitionDateTime});
    const I2S::Element first = *attributes.begin();
    CHECK(first.name() == "DigitalImageIdentifier");
    CHECK(first.short_name() == std::optional<std::string_view>{"DII"});
    CHECK(first.vr() == I2S::Vr::LO);
    CHECK(first.identity() == I2S::IdentityClass::UNDER_REVIEW);
    CHECK(first.text() == "S26-1");
    CHECK(std::get<std::string>(first.value()) == "S26-1");
    const I2S::Element last = *std::ranges::next(attributes.begin(), 2);
    CHECK(std::get<I2S::Time>(last.value()) == kScan);
}

TEST_CASE("attributes read from pairs iterate as the ones written", "[Iteration_01]")
{
    I2S::Attributes written;
    written[I2S::Manufacturer] = "Leica";
    written[I2S::ScanTime] = kScan;
    const I2S::Attributes read = I2S::Attributes::from_pairs(written.to_pairs().value()).value();
    std::vector<std::pair<std::string, std::string>> a;
    std::vector<std::pair<std::string, std::string>> b;
    for (const auto& element : written) {
        a.emplace_back(element.name(), element.text());
    }
    for (const auto& element : read) {
        b.emplace_back(element.name(), element.text());
    }
    CHECK(a == b);
}

TEST_CASE("a DII written without DII_is_PHI is treated as PHI", "[PhiFlag_02]")
{
    I2S::Attributes attributes;
    attributes[I2S::DII] = "S26-1";
    CHECK(I2S::is_phi(attributes, I2S::DII));
    const I2S::Attributes read = I2S::Attributes::from_pairs(attributes.to_pairs().value()).value();
    CHECK(I2S::is_phi(read, I2S::DII));
    attributes[I2S::DII_is_PHI] = false;
    CHECK_FALSE(I2S::is_phi(attributes, I2S::DII));
    attributes[I2S::DII_is_PHI] = true;
    CHECK(I2S::is_phi(attributes, I2S::DII));
}
