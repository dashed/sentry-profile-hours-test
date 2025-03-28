# JavaScript and Node Platform Investigation

This document provides an analysis of how the "javascript" and "node" platforms are handled in the Sentry JavaScript SDK and Relay's profiling system.

## Overview

The Sentry JavaScript SDK has different platform handling based on the JavaScript environment:

1. **Browser Environment**: Uses "javascript" as the platform value
2. **Node.js Environment**: Uses "node" as the platform value

This distinction is important for profile hour billing because Relay classifies only certain platforms as UI platforms, which impacts billing categories.

## Platform Values in the JavaScript SDK

### Browser JavaScript

In the browser environment, the JavaScript SDK explicitly sets the platform value to "javascript":

```typescript
// File: /external/sentry-javascript/packages/browser/src/profiling/utils.ts
export function createProfilingEvent(
  // ...
): ProfilingEvent {
  return {
    // ...
    platform: 'javascript',
    // ...
  };
}
```

### Node.js

In the Node.js environment, the SDK explicitly sets the platform value to "node":

```typescript
// File: /external/sentry-javascript/packages/profiling-node/src/utils.ts
export function createProfilingEvent(
  // ...
): ProfilingEvent {
  return {
    // ...
    platform: 'node',
    // ...
  };
}

// Also for profile chunks:
export function createProfileChunk(
  // ...
): ProfileChunk {
  return {
    // ...
    platform: 'node',
    // ...
  };
}
```

## Platform Classification in Relay

In Relay, profiles are classified as either UI or Backend based on their platform value:

```rust
// File: /external/relay/relay-profiling/src/lib.rs
pub fn profile_type(&self) -> ProfileType {
    match self.profile.platform.as_str() {
        "cocoa" | "android" | "javascript" => ProfileType::Ui,
        _ => ProfileType::Backend,
    }
}
```

This classification has significant implications:

1. **UI Platforms** (javascript, android, cocoa):
   - Classified as UI profile hours
   - Typically higher cost in billing

2. **Backend Platforms** (including node):
   - Classified as backend profile hours
   - Typically lower cost in billing

## Impact on Testing

For our profile hours testing tool, this means:

1. Using "javascript" as the platform value will result in UI profile hours
2. Using "node" as the platform value will result in backend profile hours

This distinction is important when testing different billing scenarios:

- If testing UI profile hours in a JavaScript context, use "javascript" platform
- If testing backend profile hours in a JavaScript context, use "node" platform

## Comparison with Other Platforms

Platform | Classification | Used By
---------|---------------|--------
javascript | UI | Browser JavaScript SDK
node | Backend | Node.js JavaScript SDK
cocoa | UI | Cocoa SDK (iOS, macOS)
android | UI | Android SDK
python | Backend | Python SDK

## Conclusion

The JavaScript SDK is unique in that it uses different platform values depending on the execution environment:

1. **Browser JavaScript**: Uses "javascript" platform → Categorized as UI profile hours
2. **Node.js**: Uses "node" platform → Categorized as backend profile hours

For our testing tool, we should clearly distinguish between these two when setting the PLATFORM value to ensure we're testing the correct billing category. The current implementation already supports this by allowing PLATFORM to be set to either "javascript" or "node" as needed.