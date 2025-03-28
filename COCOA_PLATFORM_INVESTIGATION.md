# Cocoa Platform Investigation

This document provides an analysis of how the "cocoa" platform is handled in Relay's profiling system and its compatibility with the synthetic profile generation in the testing tool.

## Overview

The `cocoa` platform in Sentry refers to profiles generated from Apple's iOS, macOS, watchOS, and tvOS applications using the Sentry Cocoa SDK. Cocoa profiles, like Android and JavaScript profiles, are categorized as UI platforms for billing purposes.

## Cocoa Platform in Relay

### UI/Backend Classification

In Relay, the `cocoa` platform is explicitly classified as a UI platform in the profiling code:

```rust
// File: /external/relay/relay-profiling/src/lib.rs
pub fn profile_type(&self) -> ProfileType {
    match self.profile.platform.as_str() {
        "cocoa" | "android" | "javascript" => ProfileType::Ui,
        _ => ProfileType::Backend,
    }
}
```

This classification ensures that profiles with the `cocoa` platform are counted as UI profile hours rather than backend profile hours.

### Validation Requirements

Cocoa profiles have additional validation requirements that other platforms don't have:

```rust
// File: /external/relay/relay-profiling/src/sample/v1.rs
fn valid(&self) -> bool {
    match self.metadata.platform.as_str() {
        "cocoa" => {
            self.metadata.os.build_number.is_some()
                && self.metadata.device.is_emulator.is_some()
                && self.metadata.device.locale.is_some()
                && self.metadata.device.manufacturer.is_some()
                && self.metadata.device.model.is_some()
        }
        _ => true,
    }
}
```

These validation requirements check for specific metadata about the device:
- OS build number
- Whether the device is an emulator
- Device locale
- Device manufacturer
- Device model

However, it's important to note that for synthetic profile generation, we can provide these values in the profile payload when needed, unlike Android which requires a special format.

### Pointer Authentication Code Handling

Cocoa profiles have special handling for Pointer Authentication Codes (PACs) on ARM64/ARM64e platforms:

```rust
// File: /external/relay/relay-profiling/src/sample/v1.rs
fn strip_pointer_authentication_code(&mut self, platform: &str, architecture: &str) {
    let addr = match (platform, architecture) {
        ("cocoa", "arm64") | ("cocoa", "arm64e") => 0x0000000FFFFFFFFF,
        _ => return,
    };
    for frame in &mut self.frames {
        frame.strip_pointer_authentication_code(addr);
    }
}
```

This feature prevents pointer authentication bits from interfering with symbolication. For synthetic profile generation, this doesn't affect our testing since we're not dealing with real memory addresses or symbolication.

### Queue-Related Data Structures

Cocoa profiles can include queue-related metadata not present in other platform profiles:

```rust
// File: /external/relay/relay-profiling/src/sample/v1.rs
struct Sample {
    // ...other fields...
    // cocoa only
    #[serde(default, skip_serializing_if = "Option::is_none")]
    queue_address: Option<String>,
}

struct SampleProfile {
    // ...other fields...
    // cocoa only
    #[serde(default, skip_serializing_if = "Option::is_none")]
    queue_metadata: Option<HashMap<String, QueueMetadata>>,
}
```

These fields are optional and not required for minimal valid profiles, so we can either include them or omit them in our synthetic profiles.

### Default SDK Identification

Relay identifies cocoa profiles with a specific SDK name:

```rust
// File: /external/relay/relay-profiling/src/utils.rs
pub fn default_client_sdk(platform: &str) -> Option<ClientSdk> {
    let sdk_name = match platform {
        // ...other platforms...
        "cocoa" => "sentry.cocoa",
        // ...other platforms...
        _ => return None,
    };
    Some(ClientSdk {
        name: sdk_name.into(),
        version: "".into(),
    })
}
```

This is mostly for informational purposes and doesn't affect profile processing for our tests.

## Compatibility with Synthetic Profiles

Unlike Android profiles that require a specific base64-encoded format that our testing tool can't easily generate, cocoa profiles follow a more standard JSON structure similar to other platforms. The main differences are the additional metadata validation requirements and queue-related structures, which can be added to our synthetic profiles if needed.

When using the `cocoa` platform in our testing tool:

1. Relay will appropriately classify the profiles as UI profiles
2. The validation requirements can be met by adding the required metadata fields
3. The special handling for PACs doesn't affect our synthetic samples
4. The queue-related data structures are optional and not required for testing

## Comparison with Other Platforms

Platform | Classification | Special Requirements | Compatible with Test Tool
---------|---------------|----------------------|--------------------
javascript | UI | None | Yes
android | UI | Base64-encoded sampled_profile<br>AndroidTraceLog structure | No (complex format)
cocoa | UI | Additional metadata validation | Yes (with minor additions)
python | Backend | None | Yes

## Conclusion

The `cocoa` platform is a good alternative to `javascript` for testing UI profile hours in our synthetic profile generation tool. 

Unlike `android`, which has complex format requirements, `cocoa` only needs a few additional metadata fields to pass validation. The special handling for PACs and queue data doesn't affect our ability to generate synthetic profiles.

To use `cocoa` effectively, we should add the required metadata fields to our synthetic profiles:
- os.build_number
- device.is_emulator
- device.locale
- device.manufacturer
- device.model

With these additions, the `cocoa` platform should work seamlessly in our testing tool for generating UI profile hours.