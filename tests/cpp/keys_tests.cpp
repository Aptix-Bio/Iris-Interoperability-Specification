// The generated header, used as a consumer uses it. Every check that can be a
// static_assert is one: the tables are constexpr, so a wrong table fails the
// build instead of a test run.
// RTM Generated_01, Generated_02, Generated_03, Adoption_03, ScanTimeKeys_01, Enumerated_01
#include "I2S.hpp"

#include <catch2/catch_test_macros.hpp>

#include <cstddef>
#include <cstdint>
#include <optional>
#include <type_traits>

namespace {

constexpr bool every_key_round_trips()
{
    for (const I2S::KeyInfo& entry : I2S::kKeys) {
        if (I2S::key_from_name(I2S::name(entry.key)) != entry.key) {
            return false;
        }
        if (entry.short_name && I2S::key_from_name(*entry.short_name) != entry.key) {
            return false;
        }
    }
    return true;
}

constexpr bool every_key_has_a_defined_type()
{
    for (const I2S::KeyInfo& entry : I2S::kKeys) {
        if (static_cast<std::size_t>(entry.value_type) >= I2S::kValueTypeNames.size()) {
            return false;
        }
        if (static_cast<std::size_t>(entry.identity) >= I2S::kIdentityClassNames.size()) {
            return false;
        }
    }
    return true;
}

} // namespace

TEST_CASE("every key's name and short name look up the key", "[Generated_01]")
{
    STATIC_REQUIRE(every_key_round_trips());
    STATIC_REQUIRE(I2S::key_from_name("Manufacturer") == I2S::Key::Manufacturer);
}

TEST_CASE("a name I2S does not define is an explicit absence", "[Generated_01]")
{
    STATIC_REQUIRE_FALSE(I2S::key_from_name("AccessionNumber").has_value());
    STATIC_REQUIRE_FALSE(I2S::key_from_name("").has_value());
    // Names are case-sensitive, as DICOM keywords are.
    STATIC_REQUIRE_FALSE(I2S::key_from_name("manufacturer").has_value());
}

TEST_CASE("every key has a value type and an identity class", "[Generated_02]")
{
    STATIC_REQUIRE(every_key_has_a_defined_type());
    STATIC_REQUIRE(I2S::name(I2S::info(I2S::Key::SoftwareVersions).value_type) == "TEXT");
    STATIC_REQUIRE_FALSE(I2S::info(I2S::Key::SoftwareVersions).multiplicity.maximum.has_value());
}

TEST_CASE("the Digital Image Identifier is DII and has no DICOM keyword", "[Generated_03]")
{
    constexpr const I2S::KeyInfo& dsi = I2S::info(I2S::Key::DigitalImageIdentifier);
    STATIC_REQUIRE(dsi.short_name == "DII");
    STATIC_REQUIRE(I2S::key_from_name("DII") == I2S::Key::DigitalImageIdentifier);
    STATIC_REQUIRE_FALSE(dsi.dicom.has_value());
    STATIC_REQUIRE(dsi.identity == I2S::IdentityClass::UNDER_REVIEW);
}

TEST_CASE("scanner keys carry their DICOM tags", "[Generated_03]")
{
    STATIC_REQUIRE(I2S::info(I2S::Key::DeviceSerialNumber).dicom->tag == I2S::DicomTag{0x0018, 0x1000});
    constexpr const auto& udi = I2S::info(I2S::Key::UniqueDeviceIdentifier).dicom;
    STATIC_REQUIRE(udi->tag == I2S::DicomTag{0x0018, 0x1009});
    STATIC_REQUIRE(udi->sequence->tag == I2S::DicomTag{0x0018, 0x100A});
}

namespace {

constexpr bool every_phi_flag_is_a_boolean_key()
{
    for (const I2S::KeyInfo& entry : I2S::kKeys) {
        if (entry.phi_flag && I2S::info(entry.phi_flag->key).value_type != I2S::ValueType::BOOLEAN) {
            return false;
        }
    }
    return true;
}

} // namespace

// RTM PhiFlag_01, PhiFlag_02
TEST_CASE("the DII is paired with DII_is_PHI, which defaults to PHI when absent", "[PhiFlag_01][PhiFlag_02]")
{
    STATIC_REQUIRE(every_phi_flag_is_a_boolean_key());
    constexpr const auto& flag = I2S::info(I2S::Key::DigitalImageIdentifier).phi_flag;
    STATIC_REQUIRE(flag->key == I2S::Key::DigitalImageIdentifierIsPHI);
    STATIC_REQUIRE(flag->absent_means_phi);
    STATIC_REQUIRE(I2S::key_from_name("DII_is_PHI") == I2S::Key::DigitalImageIdentifierIsPHI);
    STATIC_REQUIRE(I2S::info(I2S::Key::DigitalImageIdentifierIsPHI).identity == I2S::IdentityClass::NONE);
    STATIC_REQUIRE_FALSE(I2S::info(I2S::Key::DigitalImageIdentifierIsPHI).phi_flag.has_value());
}

// RTM Adoption_03
TEST_CASE("the version IFE's attribute block carries is major << 8 | minor", "[Adoption_03]")
{
    STATIC_REQUIRE(I2S::kIfeAttributesVersion == (I2S::kVersionMajor << 8 | I2S::kVersionMinor));
    STATIC_REQUIRE(I2S::kIfeAttributesVersion >> 8 == I2S::kVersionMajor);
    STATIC_REQUIRE((I2S::kIfeAttributesVersion & 0xFF) == I2S::kVersionMinor);
    // Zero is IFE's unversioned claim, read as free text: I2S never writes it.
    STATIC_REQUIRE(I2S::kIfeAttributesVersion != 0);
}

// RTM ScanTimeKeys_01
TEST_CASE("the scan-time keys carry their DICOM tags and identify no one", "[ScanTimeKeys_01]")
{
    constexpr const I2S::KeyInfo& burned = I2S::info(I2S::Key::BurnedInAnnotation);
    STATIC_REQUIRE(burned.dicom->tag == I2S::DicomTag{0x0028, 0x0301});
    STATIC_REQUIRE(burned.value_type == I2S::ValueType::BOOLEAN);
    constexpr const I2S::KeyInfo& aperture = I2S::info(I2S::Key::ObjectiveLensNumericalAperture);
    STATIC_REQUIRE(aperture.dicom->tag == I2S::DicomTag{0x0048, 0x0113});
    STATIC_REQUIRE(aperture.dicom->sequence->tag == I2S::DicomTag{0x0048, 0x0105});
    STATIC_REQUIRE(aperture.vr == I2S::Vr::DS);
    STATIC_REQUIRE(I2S::info(I2S::Key::FocusMethod).dicom->tag == I2S::DicomTag{0x0048, 0x0011});
    STATIC_REQUIRE(I2S::info(I2S::Key::ExtendedDepthOfField).dicom->tag == I2S::DicomTag{0x0048, 0x0012});
    for (const I2S::Key key : {I2S::Key::BurnedInAnnotation, I2S::Key::ObjectiveLensNumericalAperture,
                               I2S::Key::FocusMethod, I2S::Key::ExtendedDepthOfField}) {
        CHECK(I2S::info(key).identity == I2S::IdentityClass::NONE);
        CHECK(I2S::info(key).multiplicity.maximum == std::optional<std::uint16_t>{1});
    }
}

// RTM Enumerated_01
TEST_CASE("an ENUMERATED key lists its values, in the order of its enumeration", "[Enumerated_01]")
{
    constexpr const I2S::KeyInfo& focus = I2S::info(I2S::Key::FocusMethod);
    STATIC_REQUIRE(focus.value_type == I2S::ValueType::ENUMERATED);
    STATIC_REQUIRE(focus.vr == I2S::Vr::CS);
    STATIC_REQUIRE(focus.values.size() == 2);
    STATIC_REQUIRE(focus.values[static_cast<std::size_t>(I2S::FocusMethod::AUTO)] == "AUTO");
    STATIC_REQUIRE(I2S::name(I2S::FocusMethod::MANUAL) == "MANUAL");
    STATIC_REQUIRE(std::is_same_v<I2S::EnumerationOf<I2S::Key::FocusMethod>::type, I2S::FocusMethod>);
    STATIC_REQUIRE(std::is_void_v<I2S::EnumerationOf<I2S::Key::Manufacturer>::type>);
    STATIC_REQUIRE(I2S::info(I2S::Key::Manufacturer).values.empty());
}
