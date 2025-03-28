# Development Guidelines

## Build & Run Commands
- Run app: `uv run hello.py`
- Install dependencies: `uv add <package>` or `uv pip install -r requirements.txt`
- Update dependencies: `uv pip compile pyproject.toml -o requirements.txt`
- Create virtual environment: `uv venv`
- Run commands in virtual env: `uv run -- <command>`
- Upgrade a package: `uv lock --upgrade-package <package>`

## Testing Commands
- Run Python tests: `python -m pytest tests/`
- Run single test: `python -m pytest tests/test_file.py::test_function`
- Run JS tests: `CI=true yarn test path/to/file.spec.tsx`

## Code Style
- Python: Follow Black formatting (100 char line length)
- Type hints: Use mypy type annotations for all functions
- Imports: Group standard library, third-party, and local imports
- Error handling: Use explicit exception types, avoid bare except
- Variable naming: snake_case for variables, CamelCase for classes
- JavaScript: Follow ESLint rules and React component guidelines

## Project Structure
- `external/` directory contains cloned GitHub repositories for reference:
  - `sentry/`: Main Sentry backend/frontend codebase
  - `sentry-python/`: Python SDK for Sentry
  - `relay/`: Proxy service that validates and processes events
  - `sentry-docs/`: Documentation for Sentry platform and SDKs

## Relay - Sentry's Ingestion Proxy

Relay is Sentry's data ingestion proxy and processing service. It acts as the first layer handling all incoming data before it reaches the Sentry processing pipeline.

### Relay's Role in Profiling

Relay performs several critical functions for profiling:

1. **Profile Validation:**
   - Ensures profiles conform to expected formats
   - Validates duration (maximum 30s for transaction profiles)
   - Validates continuous profile chunk duration (maximum 66s)
   - Checks for sufficient samples
   - Verifies platform compatibility

2. **Profile Classification:**
   - Determines if a profile is UI or Backend based on platform:
   ```rust
   pub fn profile_type(&self) -> ProfileType {
       match self.profile.platform.as_str() {
           "cocoa" | "android" | "javascript" => ProfileType::Ui,
           _ => ProfileType::Backend,
       }
   }
   ```
   - This classification affects data category selection for quotas and billing

3. **Profile Envelope Processing:**
   - Transaction-based profiles use item type `"profile"` 
   - Continuous profiles use item type `"profile_chunk"`
   - Each type has different validation and processing rules

4. **Feature Flag Enforcement:**
   - Enforces feature flags for continuous profiling:
   ```rust
   project_info.has_feature(Feature::ContinuousProfiling)
   ```
   - Controls transaction profiling with:
   ```rust
   project_info.has_feature(Feature::Profiling)
   ```

5. **Profile Filtering:**
   - Applies project-specific filters to profiles
   - Drops profiles if the feature is not enabled
   - Drops standalone profiles without a transaction
   - Prevents duplicates by dropping excessive profiles

6. **Profile Expansion:**
   - Extracts transaction metadata and tags
   - Processes profile data based on version and platform
   - Enforces maximum profile size limits
   - Sets metadata in the envelope for downstream processing

### Key Relay Components for Profiling

1. **`relay-profiling/src/lib.rs`**:
   - Core profile processing functionality
   - Defines validation constants:
   ```rust
   const MAX_PROFILE_DURATION: Duration = Duration::from_secs(30);
   const MAX_PROFILE_CHUNK_DURATION: Duration = Duration::from_secs(66);
   ```
   - Contains platform classification logic

2. **`relay-server/src/services/processor/profile.rs`**:
   - Handles transaction profiles
   - Enforces feature flag checks
   - Ensures proper transaction-profile pairing
   - Discards profiles with validation errors

3. **`relay-server/src/services/processor/profile_chunk.rs`**:
   - Processes continuous profile chunks
   - Controls feature flag enforcement
   - Validates and expands profile chunks
   - Sets profile type for proper billing categorization

4. **`relay-profiling/src/outcomes.rs`**:
   - Defines discard reasons for invalid profiles:
   ```rust
   pub fn discard_reason(err: ProfileError) -> &'static str {
       match err {
           ProfileError::NotEnoughSamples => "profiling_not_enough_samples",
           ProfileError::DurationIsTooLong => "profiling_duration_is_too_long",
           ProfileError::PlatformNotSupported => "profiling_platform_not_supported",
           // More reasons...
       }
   }
   ```

### Implications for Profile Hours Testing

When testing profile hours with the Python SDK:

1. **Platform Setting is Critical:**
   - Relay classifies UI vs Backend profiles based strictly on platform string
   - Consistent platform values must be set in both envelope headers and profile payload

2. **Feature Flag Check:**
   - Your project must have appropriate feature flags enabled
   - Transaction profiling requires the "profiling" feature
   - Continuous profiling requires the "continuous-profiling" feature

3. **Validation Constraints:**
   - Transaction profiles must comply with 30-second maximum duration
   - Profile chunks must stay within 66-second window limits
   - Proper timestamp formatting is essential (nanosecond offsets for transaction profiles, Unix timestamps for continuous profiles)
   - Profiles must contain enough samples (minimum sample check)

4. **Synthetic Profile Generation Strategy:**
   - Mock data must adhere to Relay's validation constraints
   - The 66-second chunk limit is why we generate multiple chunks for continuous profiling
   - Duration mocking happens before the validation to simulate longer duration profiles

### Relay's Profile Test Fixtures

Relay's test suite includes valuable examples of valid profile formats that can be referenced when creating synthetic profiles:

1. **Transaction Profile Examples:**
   - `relay-profiling/tests/fixtures/sample/v1/valid.json` - Valid transaction profile
   - `relay-profiling/tests/fixtures/sample/v1/segment_id.json` - Profile with segment ID

2. **Continuous Profile Examples:**
   - `relay-profiling/tests/fixtures/sample/v2/valid.json` - Valid continuous profile chunk
   - `relay-profiling/tests/fixtures/android/chunk/valid.json` - Valid Android profile chunk

3. **Integration Testing:**
   The `tests/integration/test_profile_chunks.py` file demonstrates:
   - How profile data flows through the Relay processing pipeline
   - Feature flag requirements for continuous profiling:
   ```python
   project_config.setdefault("features", []).append(
       "organizations:continuous-profiling"
   )
   ```
   - Proper envelope structure for profile chunks:
   ```python
   envelope = Envelope()
   envelope.add_item(Item(payload=PayloadRef(bytes=profile), type="profile_chunk"))
   ```
   - Validation and outcome reporting for invalid profiles:
   ```python
   assert outcomes == [
       {
           "category": DataCategory.PROFILE_CHUNK.value,
           "outcome": 3,  # Invalid
           "reason": "profiling_platform_not_supported",
           # ...other fields
       },
   ]
   ```
   - Rate limiting behavior for profiles:
   ```python
   project_config["quotas"] = [
       {
           "id": f"test_rate_limiting_{uuid.uuid4().hex}",
           "categories": ["profile_chunk_ui"],  # Target profile chunks specifically
           "limit": 0,  # Block all profile chunks
           "reasonCode": "profile_chunks_exceeded",
       }
   ]
   ```

These test fixtures and integration tests provide valuable insights into how Relay processes profiles and the validation rules it enforces, which is essential knowledge when implementing profile mocking strategies.

### Recent Relay Profiling Enhancements

Relay has recently improved its profile chunk handling with important changes that affect profile categorization and rate limiting:

1. **UI Profile Chunk Category (PR #4593)**
   - Added dedicated data category for UI profile chunks: `PROFILE_CHUNK_UI`
   - Separates UI profile chunks from backend profile chunks for better categorization
   - Added to `relay-base-schema/src/data_category.rs`:
   ```rust
   /// A continuous profiling profile chunk for UI platforms (mobile, javascript)
   PROFILE_CHUNK_UI = 23,
   ```
   - This enables separate quotas and rate limiting for UI vs backend profile chunks

2. **Platform-Based Chunk Classification (PR #4595)**
   - Enhanced profile chunk handling to determine UI vs Backend based on platform
   - Implemented `profile_type()` function to classify chunks:
   ```rust
   pub fn profile_type(&self) -> ProfileType {
       match self.profile.platform.as_str() {
           "cocoa" | "android" | "javascript" => ProfileType::Ui,
           _ => ProfileType::Backend,
       }
   }
   ```
   - Modified rate limiting and outcome reporting to use the appropriate category
   - Profile chunks without a platform header are processed but may not be correctly categorized
   - Improves accuracy in billing and quota enforcement

3. **Implications for Profile Hours Testing**
   - The platform value is now even more critical for proper categorization
   - Rate limits can be set separately for UI vs backend profile chunks
   - Testing should verify proper platform setting in all profile chunks
   - Future Relay versions may use platform headers (not just payload inspection)

These changes ensure that UI profile chunks (from JavaScript, Android, and iOS) are properly categorized and can be subject to different quotas than backend profile chunks. This is particularly important for profile hours testing, as it ensures accurate platform-based billing.

## Available Tools
- `gh` (GitHub CLI) is available for GitHub operations

## React Testing
- Use exports from 'sentry-test/reactTestingLibrary' instead of directly from '@testing-library/react'

## Sentry Profiling Types: Transaction-Based vs Continuous

Sentry supports two distinct profiling modes, each with different characteristics and use cases:

### Transaction-Based Profiling

Transaction-based profiling was Sentry's first profiling mode. It profiles code executed between `Sentry.startTransaction` and `transaction.finish` calls.

**Key Characteristics:**
- **Scope:** Limited to instrumented transactions
- **Duration Limit:** Max 30 seconds per profile (prevents large payloads)
- **Data Structure:** Uses string-represented nanosecond offsets from transaction start
- **Implementation:**
  - Time measurements use `elapsed_since_start_ns` (nanoseconds since start)
  - Profiles are attached to transactions and sent in the same envelope
  - Uses `Profile` class from `transaction_profiler.py`

**Advantages:**
- Automatically profiles only specifically instrumented parts of your application
- Zero additional configuration if you're already using transactions
- Lower overhead since profiling isn't always running

**Limitations:**
- Cannot profile long-running tasks (>30 seconds)
- Only profiles instrumented code sections
- Misses issues in non-instrumented portions of your application

**Configuration:**
```python
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,  # Enable transaction profiling
)

# Profiling happens automatically with transactions
with sentry_sdk.start_transaction(name="my-transaction"):
    # Code here is automatically profiled
    pass
```

### Continuous Profiling

Continuous profiling mode runs the profiler continuously and regularly flushes "profile chunks" to the server.

**Key Characteristics:**
- **Scope:** Entire application runtime (not just transactions)
- **Duration:** Unlimited - can profile for hours or days
- **Data Structure:** Uses floating-point Unix timestamps (seconds since epoch)
- **Implementation:**
  - Uses absolute timestamps for each sample
  - Regularly sends chunks (~60 seconds worth of data each)
  - Uses `ProfileChunk` class from `continuous_profiler.py`
  - Exposes explicit start/stop controls via SDK

**Advantages:**
- Provides visibility into your entire application, even non-instrumented parts
- Can profile long-running workflows without limitations
- Better overview of system-wide performance issues

**Limitations:**
- Higher overhead as profiler is always running
- May capture idle time, resulting in less targeted data
- Requires explicit start/stop calls (or configuration for auto-start)

**Configuration:**
```python
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,  # Enable continuous profiling
)

# Explicit start/stop control
sentry_sdk.profiler.start_profiler()
# ... code executed will be profiled until ...
sentry_sdk.profiler.stop_profiler()
```

### Key Implementation Differences

1. **Sampling Control:**
   - Transaction profiling: Controlled by `profiles_sample_rate` or `profiles_sampler`
   - Continuous profiling: Controlled by `profile_session_sample_rate`

2. **Timestamp Format:**
   - Transaction profiles: String-represented nanosecond offsets (e.g., `"elapsed_since_start_ns": "1000000000"`)
   - Continuous profiles: Floating-point Unix timestamps (e.g., `"timestamp": 1710805788.500`)

3. **Profile Structure:**
   - Transaction profiles: Single profile with transaction context
   - Continuous profiles: Series of profile chunks sent independently

4. **Duration Handling:**
   - Transaction profiles: Validate with `relative_end_ns` from transactions
   - Continuous profiles: Validate with timestamp differences between profile samples

5. **UI Differences in Sentry:**
   - Transaction-based: View profiles attached to specific transactions
   - Continuous: View aggregated flamegraphs across your entire application

### Choosing Between Modes

- Use transaction-based profiling when you want to focus on specific, instrumented parts of your application with lower overhead
- Use continuous profiling when you need full visibility into your entire application or for long-running processes

**Important Note:** These modes are mutually exclusive - you can't use both simultaneously in the same SDK initialization.

## Vroom - Sentry's Profiling Service

Vroom is Sentry's dedicated profiling service, responsible for processing and deriving data from profiles. It's written in Go and serves as the backend processing engine for all profile data sent to Sentry.

### Core Components

1. **Main Service (`cmd/vroom/`):**
   - Provides HTTP endpoints for receiving profiles
   - Processes incoming profile data
   - Generates derived data (flame graphs, etc.)
   - Handles storage and retrieval of profiles

2. **Utilities:**
   - **Downloader (`cmd/downloader/`):** Tool for downloading profiles
   - **Issue Detection (`cmd/issuedetection/`):** Identifies issues in profiles

3. **Key Packages:**
   - **`internal/profile/`:** Core profile data structures and processing
   - **`internal/platform/`:** Platform-specific handling (Android, JavaScript, etc.)
   - **`internal/flamegraph/`:** Flame graph generation
   - **`internal/occurrence/`:** Issue detection and occurrence tracking
   - **`internal/chunk/`:** Handling profile chunks from continuous profiling

### Platform Support

Vroom supports multiple platforms for profiling:

```go
const (
    Android    Platform = "android"    // Android apps (UI)
    Cocoa      Platform = "cocoa"      // iOS/macOS apps (UI)
    Java       Platform = "java"       // JVM-based apps (backend)
    JavaScript Platform = "javascript" // Web/browser apps (UI)
    Node       Platform = "node"       // NodeJS apps (backend) 
    PHP        Platform = "php"        // PHP apps (backend)
    Python     Platform = "python"     // Python apps (backend)
    Rust       Platform = "rust"       // Rust apps (backend)
)
```

The platform determination is critical for profile classification. UI profiles (Android, Cocoa, JavaScript) are categorized differently than backend profiles for billing and analysis purposes.

### How Vroom Fits in the Profiling Flow

1. **Data Ingestion:**
   - SDKs (like sentry-python) collect profiling data
   - Data is sent to Sentry via Relay
   - Relay categorizes profiles by platform and forwards them

2. **Profile Processing:**
   - Vroom receives profiles via HTTP endpoints
   - Processes the raw profile data
   - Normalizes formats across different platforms
   - Generates derived data (flame graphs, statistics, etc.)

3. **Storage and Retrieval:**
   - Processed profiles are stored in cloud storage
   - Metadata is stored in databases for querying
   - Used for visualization and analysis in the Sentry UI

### Timestamp Validation in Vroom

Vroom enforces strict validation on profile timestamps that must be considered when mocking lengthy profiles:

1. **Maximum Duration Limit:**
   - `MAX_PROFILE_CHUNK_DURATION = 66 seconds` - defined in `relay-profiling/src/lib.rs`
   - Any profile chunk with samples spanning more than 66 seconds will be rejected
   - This is slightly higher than the standard 60-second chunk size to account for high CPU load scenarios

2. **Timestamp Format:**
   - Continuous profile timestamps must be valid Unix timestamps (seconds since epoch)
   - They must be floating-point numbers with millisecond precision
   - Example: `1710805788.500`

3. **Timestamp Ordering:**
   - Samples are sorted by timestamp during processing
   - Timestamps must be monotonically increasing 
   - Widely varying timestamps in a single chunk will cause validation failures

4. **Validation Process:**
   ```rust
   fn is_above_max_duration(&self) -> bool {
       if self.samples.is_empty() {
           return false;
       }
       let mut min = self.samples[0].timestamp;
       let mut max = self.samples[0].timestamp;
       
       for sample in self.samples.iter().skip(1) {
           if sample.timestamp < min {
               min = sample.timestamp
           } else if sample.timestamp > max {
               max = sample.timestamp
           }
       }
       
       let duration = max.saturating_sub(min);
       duration.to_f64() > MAX_PROFILE_CHUNK_DURATION_SECS
   }
   ```

5. **Sample Structure:**
   ```json
   {
     "timestamp": 1710805788.500,
     "thread_id": "main",
     "stack_id": 0
   }
   ```

### Relevance to Profile Hours Testing

When testing UI profile hours with the Python SDK:

1. Our profile spoofing in the SDK sets the platform to a UI platform (javascript, android, cocoa)
2. Relay categorizes the profile based on this platform header
3. Vroom processes the profile according to the specified platform
4. The profile contributes to UI profile hours in Sentry's billing system

Understanding this flow is important because it explains why platform spoofing needs to happen at multiple levels in the SDK to ensure proper categorization throughout the entire pipeline.

### Strategies for Mocking Lengthy Profiles

To effectively mock lengthy profiles while respecting Vroom's validation:

1. **Window-Based Approach:**
   - Divide the mocked duration (e.g., 1 hour) into multiple 60-second windows
   - Each profile chunk represents one 60-second window
   - Rotate through windows as the profiler flushes chunks

2. **Timestamp Management:**
   - Ensure timestamps within each chunk span less than 66 seconds
   - Maintain proper floating-point format for timestamps
   - Sort samples chronologically within each chunk
   - Trim samples when necessary to maintain valid duration

3. **Consistent Types:**
   - Continuous profiles: Use floating-point Unix timestamps
   - Transaction profiles: Use string-represented nanosecond offsets from start

### Synthetic Profile Generation

For efficient mocking of extended profile durations, we can entirely replace real profiling with synthetic data generation:

1. **Synthetic Sample Creation:**
   - Generate complete synthetic profile samples instead of capturing real CPU activity
   - Create artificial stack frames with realistic function names, filenames, and line numbers
   - Construct samples with the correct structure expected by the SDK

2. **Profile Buffer Injection:**
   - Replace the profiler's sampler with a custom synthetic sampler
   - Directly inject synthetic samples into the profile buffer
   - Control the timing and distribution of samples to create realistic profiles

3. **Full Coverage Generation:**
   - For continuous profiling, generate ~60 chunks per hour (one per minute)
   - Track window coverage to ensure the full mocked duration is represented
   - Force buffer flushes to accelerate the generation of chunks

4. **Transaction Profile Mocking:**
   - For transaction profiles, inject samples distributed across the mocked duration
   - Directly modify the relative_end_ns to represent the full duration
   - Create enough samples to ensure the profile is valid without actual CPU tasks

### Ultra-Fast Direct Chunk Generation

For generating massive amounts of profile data in seconds (e.g., hours of data in seconds), we can bypass the SDK's buffer and scheduling mechanisms completely:

1. **Direct Envelope Construction:**
   - Create profile chunks manually without using the SDK's buffers
   - Construct each chunk to represent a discrete 60-second window of the mocked duration
   - Ensure each chunk adheres to Vroom's validation rules (< 66 seconds duration)

2. **Complete Pipeline Bypass:**
   - Directly create and format the JSON payload for each chunk
   - Set the proper envelope headers and payload structure
   - Send envelopes directly to the SDK's transport

3. **Parallelized Generation:**
   - Generate multiple chunks in parallel
   - Each chunk contains synthetic samples with precise timestamps
   - Spread timestamps evenly across the 60-second window

4. **Massive Scale Generation:**
   - Generate 1 hour of profile data (~60 chunks) in under a second
   - Scale to days or weeks of data in seconds
   - Maintain proper structure and timestamp sequencing throughout

This direct generation approach achieves extreme efficiency, enabling the creation of weeks or months of profile data in a matter of seconds. By bypassing the SDK's internal mechanisms and directly using the transport layer, we eliminate all the bottlenecks of normal profile collection.

## Sentry Python SDK Blueprint

### Core Components

The Sentry Python SDK (`external/sentry-python/`) has several key components:

#### Main Module Structure
- **`sentry_sdk/__init__.py`** - Main entry point, exports the public API
- **`sentry_sdk/_init_implementation.py`** - Actual init and core SDK implementation
- **`sentry_sdk/client.py`** - Client class, handles event capturing and processing
- **`sentry_sdk/hub.py`** - Hub implementation, manages scopes and clients
- **`sentry_sdk/scope.py`** - Scope management, handles contextual data
- **`sentry_sdk/transport.py`** - Handles sending data to Sentry
- **`sentry_sdk/envelope.py`** - Envelope implementation for encapsulating data
- **`sentry_sdk/tracing.py`** - Tracing implementation for performance monitoring

#### Profiling Components 
- **`sentry_sdk/profiler/transaction_profiler.py`** - Transaction-based profiling implementation
  - Contains `Profile` class, sampling logic and the `PROFILE_MINIMUM_SAMPLES` constant
  - Implements `Profile.valid()` method which determines if profiles are valid for sending
  - Methods for turning profiles into JSON format
- **`sentry_sdk/profiler/continuous_profiler.py`** - Continuous profiling implementation
  - Contains `ProfileChunk` class for creating profile chunks
  - Contains `ProfileBuffer` for managing profile data
  - Implements timestamping for profiling data
- **`sentry_sdk/profiler/utils.py`** - Utilities for profiling
  - Contains `DEFAULT_SAMPLING_FREQUENCY` and extraction utilities

#### Data Processing
- **`sentry_sdk/serializer.py`** - Serializes Python objects for sending to Sentry
- **`sentry_sdk/utils.py`** - Various utilities used throughout the SDK
- **`sentry_sdk/scrubber.py`** - Data scrubbing utilities for PII removal

#### Integration Points
- **`sentry_sdk/integrations/`** - Contains integrations for various frameworks and libraries

### Important Paths for Profiling
When working with profiles and particularly UI profile hours, these are the key files:

1. **Sentry Platform Profile Classification:**
   - `external/sentry/src/sentry/profiles/task.py` - Contains `UI_PROFILE_PLATFORMS` and categorization logic
   - Sets which platforms are considered UI platforms: "cocoa", "android", "javascript"

2. **Relay Profile Processing:**
   - `external/relay/relay-profiling/src/lib.rs` - Contains logic for profile type determination
   - Classifies profiles as UI vs backend based on platform header

3. **Python SDK Profiling:**
   - `external/sentry-python/sentry_sdk/profiler/transaction_profiler.py` - Transaction-based profiling
   - `external/sentry-python/sentry_sdk/profiler/continuous_profiler.py` - Continuous profiling

### Key Concepts for SDK Monkey Patching

1. **Platform Spoofing:**
   - Platform needs to be set in:
     - Envelope headers for fast classification by Relay
     - Profile payload itself for processing by Sentry
     - Event data for proper association

2. **Transaction vs Continuous Profiling:**
   - **Transaction profiling:** Tied to a single transaction's duration
     - Uses `Profile` class from `transaction_profiler.py`
     - Time measurements use `elapsed_since_start_ns` (nanoseconds since start)
   - **Continuous profiling:** Ongoing profiling across multiple transactions
     - Uses `ProfileChunk` class from `continuous_profiler.py`
     - Time measurements use absolute timestamps

3. **Sample Requirements:**
   - Profiles require a minimum number of samples (`PROFILE_MINIMUM_SAMPLES`) 
   - Insufficient samples lead to profile discarding

4. **Timestamp Manipulation:**
   - For transaction profiles: Modify `relative_end_ns` in transactions
   - For continuous profiles: Manipulate timestamps in `ProfileChunk.samples`

## Managing Profile Hours in the Sentry UI

Once profile data is collected and processed, Sentry provides various UI views for analysis:

1. **Performance Page:** Transactions with profiles show a link in the "Profile" column
2. **Profile Summary Page:** Shows aggregated information from profiles collected under a specific transaction
3. **Transactions Tab:** Lists transactions in descending order of execution time
4. **Flamegraph Tab:** Shows aggregate flamegraph across transaction boundaries

The UI distinguishes between transaction-based and continuous profiling:
- Transaction-based profiling: Focus on individual transaction profiles
- Continuous profiling: System-wide overview with aggregate flamegraphs 

## Mocking Profile Hours

The `hello.py` file contains a comprehensive example of mocking profile hours, with these capabilities:

1. **Configuration Options:**
   - Toggle between continuous and transaction profiling
   - Select UI platform for testing ("javascript", "android", "cocoa")
   - Enable/disable timestamp mocking
   - Set mock duration in hours
   - Control sample generation rates

2. **Monkey Patching Approach:**
   - Patches `Profile.to_json` and `ProfileChunk.to_json` to modify platform
   - Patches `Envelope.add_profile_chunk` to modify envelope headers
   - Patches `Profile.valid` to ensure profiles aren't discarded
   - Patches write methods to inject additional samples
   - Patches buffer processing to spread samples across mocked timespan

3. **Ultra-Fast Direct Generation:**
   - **Continuous Profiling Mode:**
     - Bypasses SDK buffers and scheduling for ultra-fast generation
     - Creates and sends profile chunks directly to transport
     - Generates ~60 chunks per hour of simulated duration
     - Ensures proper 60-second window distribution for Vroom compatibility
   
   - **Transaction Profiling Mode:**
     - Generates synthetic transaction + profile pairs
     - Directly manipulates `relative_end_ns` to simulate lengthy profiles
     - Creates proper envelope structure with both transaction and profile
     - Distributes transactions evenly across mocked duration

## Profile Hours Billing in Different Plan Types

Sentry offers different plan types (AM2 and AM3) with different billing models for profiling:

### AM2 Plans
- **Transaction-based profiling:** Billed as a separate category
- **Continuous profiling:** Billed as profile hours (UI and non-UI separately)

### AM3 Plans
- **No separate transaction profiling billing**
- **All profiling is billed as profile hours**
- Transaction profiles are automatically converted to profile hours
- Categorization is based on platform (UI vs non-UI)

### Implications for Testing

1. **Platform Setting is Critical:**
   - In both plans, the `PLATFORM` setting determines UI vs non-UI categorization
   - UI platforms (javascript, android, cocoa) are billed differently than backend platforms

2. **Testing AM3 Plans:**
   - Both transaction and continuous profiling can be used to generate profile hours
   - Platform spoofing ensures correct UI/non-UI categorization
   - Direct generation works for both modes

3. **Testing AM2 Plans:**
   - Need to test transaction profiling and continuous profiling separately
   - Direct generation supports both for ultra-fast testing

## Useful Code Snippets

### Initializing Sentry with Profiling Enabled

```python
# For transaction-based profiling:
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,  # Enable transaction profiling
)

# For continuous profiling:
sentry_sdk.init(
    dsn="...",
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,  # Enable continuous profiling
    _experiments={
        "continuous_profiling_auto_start": True,
    }
)
```

### Accessing the Current Profile

```python
# Get the current profile from scope
scope = sentry_sdk.get_isolation_scope()
if hasattr(scope, "profile") and scope.profile:
    current_profile = scope.profile
    # Now you can work with the profile
```

### Starting and Stopping Profilers

```python
# Start/stop continuous profiling
sentry_sdk.profiler.start_profiler()
# ... do work
sentry_sdk.profiler.stop_profiler()

# Transaction profiling happens automatically with transactions when enabled
with sentry_sdk.start_transaction(name="my-transaction"):
    # Transaction is automatically profiled if profiles_sample_rate > 0
    pass
```

## Direct Transaction Profile Generation

The transaction profile generation function (`generate_direct_transaction_profiles()`) is similar to the continuous profile chunk generation function, but with key differences to account for the unique structure of transaction profiling:

### Key Components

1. **Profile-Transaction Pairing:**
   - Transaction profiles must be attached to a transaction event
   - Both are sent in the same envelope
   - They share the same `trace_id` and other metadata for proper linking

2. **Timestamp Format Differences:**
   - Transaction profiles use string-represented nanosecond offsets from start
   - Uses `elapsed_since_start_ns` instead of absolute timestamps
   - Sample format example: `{"elapsed_since_start_ns": "1000000000", "thread_id": "123", "stack_id": 0}`

3. **Mocking Duration:**
   - The critical field for duration mocking is `relative_end_ns` in the transaction object
   - Setting this to a large value simulates a longer profile
   - Example: `"relative_end_ns": "3600000000000"` for a 1-hour profile

4. **Envelope Structure:**
   ```python
   envelope = Envelope()
   # Add transaction first
   envelope.add_item(
       Item(
           payload=PayloadRef(json=transaction_event),
           type="transaction",
           headers={"platform": PLATFORM}
       )
   )
   # Add profile second
   envelope.add_item(
       Item(
           payload=PayloadRef(json=profile_payload),
           type="profile",
           headers={"platform": PLATFORM}
       )
   )
   ```

### Key Observations

1. **In AM3 plans**, transaction profiles contribute to profile hours just like continuous profiles
2. **Platform setting** is crucial in both cases for proper UI vs non-UI categorization
3. **Density of transactions** can be adjusted (we use ~10 per hour by default)
4. **Structure differs** but the direct generation approach works for both types