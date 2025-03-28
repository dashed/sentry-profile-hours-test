# ----------------------- CONFIGURATION OPTIONS -----------------------
# Toggle between different profiling options
PROFILE_TYPE = "continuous"  # Options: "continuous" or "transaction"
PLATFORM = "javascript"  # Options: "javascript", "android", "cocoa" (for UI profiles)

# Timestamp mocking options
MOCK_TIMESTAMPS = True  # Set to True to mock longer profiles without actually running that long
MOCK_DURATION_HOURS = 1.0  # How many hours to simulate for each profile session
MOCK_SAMPLES_PER_HOUR = 3600  # How many samples per hour to generate (if mocking)

# Debug and sampling options
DEBUG_PROFILING = True  # Set to True for verbose debugging info
MINIMUM_SAMPLES = 3  # Minimum number of samples to ensure are collected

# ----------------------- IMPLEMENTATION -----------------------
import random
import time
import uuid
from datetime import datetime, timedelta, timezone

import sentry_sdk
from sentry_sdk import capture_exception, capture_message, set_tag
from sentry_sdk.envelope import Envelope, Item, PayloadRef
from sentry_sdk.profiler.continuous_profiler import ProfileChunk, ProfileBuffer

# Monkey patch to override platform from "python" to "android" for profiles
# This is needed to test UI profile hours (PROFILE_DURATION_UI) with the Python SDK
# The platform value determines how Relay and Sentry categorize profile chunks:
# 1. In the envelope header: Relay relies on the platform header for classification
#    - See relay-profiling/src/lib.rs:ProfileChunk::profile_type() method
# 2. In the profile payload: Sentry checks the platform value within the profile itself
#    - See sentry/profiles/task.py:get_data_category() and _track_duration_outcome() methods
# UI platforms are: "cocoa", "android", "javascript"
from sentry_sdk.profiler.transaction_profiler import Profile, PROFILE_MINIMUM_SAMPLES, _scheduler
from sentry_sdk.profiler.utils import DEFAULT_SAMPLING_FREQUENCY
from sentry_sdk.utils import nanosecond_time, now
from sentry_sdk.tracing import Span

# Save original methods - we'll patch these to modify the platform and timestamps
original_profile_to_json = Profile.to_json
original_profile_chunk_to_json = ProfileChunk.to_json
original_add_profile_chunk = Envelope.add_profile_chunk
original_profile_valid = Profile.valid
original_profile_write = Profile.write
original_profile_chunk_write = ProfileChunk.write
original_profile_buffer_write = ProfileBuffer.write
original_profile_buffer_init = ProfileBuffer.__init__

# Create patched methods that set platform to PLATFORM and mock timestamps if configured
def patched_profile_to_json(self, event_opt, options):
    result = original_profile_to_json(self, event_opt, options)
    orig_platform = result.get("platform")
    
    if DEBUG_PROFILING and orig_platform == "python":
        print(f"DEBUG: Changing Profile platform from '{orig_platform}' to '{PLATFORM}'")
    
    # Force platform to PLATFORM (which is in UI_PROFILE_PLATFORMS)
    # This affects regular profiles (not continuous profiling chunks)
    result["platform"] = PLATFORM
    
    # Add debugging tags to help identify these profiles in Sentry
    result["tags"] = result.get("tags", {})
    result["tags"]["profile_spoof"] = "true"
    result["tags"]["original_platform"] = orig_platform
    
    # Mock timestamps for transaction-based profiles if enabled
    if MOCK_TIMESTAMPS and PROFILE_TYPE == "transaction":
        # Mocking strategy: Extend the relative_end_ns to simulate a longer profile
        for tx in result.get("transactions", []):
            # Get original relative end time
            orig_end_ns = int(tx.get("relative_end_ns", "0"))
            
            # Calculate new end time based on mock duration (convert hours to nanoseconds)
            mock_duration_ns = int(MOCK_DURATION_HOURS * 3600 * 1_000_000_000)
            
            # Set the new end time - IMPORTANT: This must be a string per SDK expectations
            tx["relative_end_ns"] = str(mock_duration_ns)
            
            if DEBUG_PROFILING:
                print(f"DEBUG: Extending profile duration from {orig_end_ns/1_000_000_000:.2f}s to {mock_duration_ns/1_000_000_000:.2f}s ({MOCK_DURATION_HOURS} hours)")
                
            # Add tag to indicate timestamp was mocked
            result["tags"]["mock_duration_hours"] = str(MOCK_DURATION_HOURS)
            result["tags"]["mock_timestamp"] = "true"
            
        # Ensure transaction profiles maintain string representation for timestamps
        # Transaction profiles use string representations of nanosecond offsets
        if "profile" in result and "samples" in result["profile"]:
            for sample in result["profile"]["samples"]:
                if "elapsed_since_start_ns" in sample and not isinstance(sample["elapsed_since_start_ns"], str):
                    sample["elapsed_since_start_ns"] = str(sample["elapsed_since_start_ns"])
    
    return result


def patched_profile_chunk_to_json(self, profiler_id, options, sdk_info):
    result = original_profile_chunk_to_json(self, profiler_id, options, sdk_info)
    
    # Critical: override platform in ProfileChunk payload
    # This is what Sentry uses to categorize as UI_PROFILE_PLATFORMS
    # and track as PROFILE_DURATION_UI
    orig_platform = result.get("platform")
    if orig_platform != PLATFORM and DEBUG_PROFILING:
        print(f"DEBUG: Changing ProfileChunk platform from '{orig_platform}' to '{PLATFORM}'")
    
    # Must be one of UI_PROFILE_PLATFORMS = {"cocoa", "android", "javascript"}
    # See sentry/profiles/task.py:UI_PROFILE_PLATFORMS
    result["platform"] = PLATFORM
    
    # Add timestamp mocking debug info if enabled
    mock_info = {}
    if MOCK_TIMESTAMPS:
        mock_info = {
            "mock_timestamp": "true",
            "mock_duration_hours": str(MOCK_DURATION_HOURS),
            "samples_per_hour": MOCK_SAMPLES_PER_HOUR,
        }
    
    # Add additional debugging fields to the profile chunk
    result["debug_info"] = {
        "original_platform": orig_platform,
        "spoofed_platform": PLATFORM,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_id": str(uuid.uuid4())[:8],
        **mock_info
    }
    
    # Add tags if possible (may not be used in processing)
    if not result.get("tags"):
        result["tags"] = {}
    result["tags"]["profile_debug"] = "true"
    
    # CRITICAL FIX: Process profile samples for continuous profiles
    if PROFILE_TYPE == "continuous" and "profile" in result:
        if "samples" in result["profile"]:
            samples = result["profile"]["samples"]
            
            if DEBUG_PROFILING:
                sample_count = len(samples)
                print(f"DEBUG: Processing {sample_count} samples for Vroom compatibility")
            
            # 1. Ensure all timestamps are proper floats
            for sample in samples:
                if "timestamp" in sample:
                    if not isinstance(sample["timestamp"], float):
                        sample["timestamp"] = float(sample["timestamp"])
            
            # 2. Sort samples by timestamp (required by Vroom)
            samples.sort(key=lambda s: s["timestamp"])
            
            # 3. Check duration and trim if necessary to stay under the 66-second limit
            if len(samples) >= 2:
                first_ts = samples[0]["timestamp"]
                last_ts = samples[-1]["timestamp"]
                duration = last_ts - first_ts
                
                if DEBUG_PROFILING:
                    print(f"DEBUG: Final chunk duration is {duration:.2f} seconds")
                
                # If duration exceeds safe limit, trim samples to fit
                if duration > 60:  # 60 seconds is safe (below the 66-second limit)
                    # Calculate required reduction
                    reduction_factor = 60 / duration
                    target_count = max(2, int(len(samples) * reduction_factor))
                    
                    # Select evenly distributed samples
                    if target_count < len(samples):
                        step = len(samples) / target_count
                        new_samples = [samples[min(int(i * step), len(samples) - 1)] 
                                      for i in range(target_count)]
                        
                        # Update the samples list
                        result["profile"]["samples"] = new_samples
                        
                        if DEBUG_PROFILING:
                            print(f"DEBUG: Trimmed samples from {len(samples)} to {len(new_samples)} "
                                  f"to reduce duration from {duration:.2f}s to under 60s")
                
                # Verify final duration
                if len(result["profile"]["samples"]) >= 2:
                    first_ts = result["profile"]["samples"][0]["timestamp"]
                    last_ts = result["profile"]["samples"][-1]["timestamp"]
                    final_duration = last_ts - first_ts
                    
                    if DEBUG_PROFILING:
                        print(f"DEBUG: Final chunk contains {len(result['profile']['samples'])} samples "
                              f"spanning {final_duration:.2f} seconds")
    
    return result


# Patch Envelope.add_profile_chunk to force platform
def patched_add_profile_chunk(self, profile_chunk):
    # Force platform in the profile_chunk itself
    if isinstance(profile_chunk, dict):
        orig_platform = profile_chunk.get("platform")
        profile_chunk["platform"] = PLATFORM
        print(
            f"DEBUG: Setting profile_chunk platform from '{orig_platform}' to '{PLATFORM}'"
        )

    # CRITICALLY IMPORTANT: Set platform in envelope header
    # Relay uses this header to identify UI profile chunks in the fast path
    # See relay-profiling/src/lib.rs:ProfileChunk::profile_type() method
    # This determines categorization as UI vs backend profile hours
    print(f"DEBUG: Forcing envelope profile_chunk header platform to '{PLATFORM}'")
    self.add_item(
        Item(
            payload=PayloadRef(json=profile_chunk),
            type="profile_chunk",
            headers={"platform": PLATFORM},  # This header is critical for proper categorization
        )
    )


# Add patched methods for timestamp mocking in continuous profiles
def patched_profile_buffer_init(self, options, sdk_info, buffer_size, capture_func):
    original_profile_buffer_init(self, options, sdk_info, buffer_size, capture_func)
    
    # Store the original timestamp for later reference
    # CRITICAL FIX: Ensure timestamp is a proper float (seconds since epoch)
    self.original_start_timestamp = float(self.start_timestamp)
    
    if MOCK_TIMESTAMPS and PROFILE_TYPE == "continuous":
        # Log the override if debugging is enabled
        if DEBUG_PROFILING:
            print(f"DEBUG: Initializing ProfileBuffer with mock timestamps (duration: {MOCK_DURATION_HOURS} hours, start: {self.original_start_timestamp})")

def patched_profile_buffer_write(self, monotonic_time, sample):
    """Override buffer write to modify timestamps for mocking lengthy profiles"""
    # Standard behavior when not mocking
    if not MOCK_TIMESTAMPS or PROFILE_TYPE != "continuous":
        return original_profile_buffer_write(self, monotonic_time, sample)
    
    # CRITICAL FIX: Vroom has a MAX_PROFILE_CHUNK_DURATION of 66 seconds
    # We must create chunks that stay under this limit
    # Strategy: Pretend each buffer collects 60 seconds of data, distributed across the hour
    
    # Calculate how far we are into the buffer (as a fraction)
    elapsed_fraction = (monotonic_time - self.start_monotonic_time) / self.buffer_size
    
    # Don't flush yet, we'll manually flush at specific intervals for mocking
    if elapsed_fraction < 1.0:
        # Generate a buffer-wide timestamp offset that stays within vroom limits
        # Current buffer will represent a 60-second window somewhere within the mocked duration
        
        # Initialize chunk counter if not present
        if not hasattr(self, 'mock_chunk_counter'):
            self.mock_chunk_counter = 0
        
        # Calculate which 60-second window this chunk represents
        hours_in_seconds = MOCK_DURATION_HOURS * 3600
        max_windows = max(1, int(hours_in_seconds / 60))
        
        # Use the counter to determine which 60-second window we're in
        window_index = self.mock_chunk_counter % max_windows
        window_start_time = window_index * 60
        
        # Calculate a timestamp within the 60-second window
        in_window_offset = elapsed_fraction * 60  # 0-60 second offset within window
        mock_elapsed_secs = window_start_time + in_window_offset
        
        # Calculate the absolute timestamp
        base_timestamp = float(self.original_start_timestamp)
        mocked_timestamp = base_timestamp + float(mock_elapsed_secs)
        
        # Write the sample with the properly mocked timestamp
        original_profile_chunk_write(self.chunk, mocked_timestamp, sample)
        
        if DEBUG_PROFILING and random.random() < 0.01:  # Only log occasionally to avoid spam
            print(f"DEBUG: Writing sample at window {window_index+1}/{max_windows}, "
                  f"offset +{in_window_offset:.2f}s, absolute: {mocked_timestamp:.3f}")
    else:
        # Time to flush the buffer and increment counter
        if hasattr(self, 'mock_flush_count'):
            self.mock_flush_count += 1
        else:
            self.mock_flush_count = 1
            
        # Increment the window counter for next chunk
        if hasattr(self, 'mock_chunk_counter'):
            self.mock_chunk_counter += 1
        else:
            self.mock_chunk_counter = 1
            
        # Reset the buffer
        self.flush()
        self.chunk = ProfileChunk()
        self.start_monotonic_time = now()
        
        if DEBUG_PROFILING:
            print(f"DEBUG: Flushed profile chunk {self.mock_flush_count}, moving to window {self.mock_chunk_counter}")

def patched_profile_chunk_write(self, ts, sample):
    """Override ProfileChunk.write to add additional mock samples if needed"""
    # Standard behavior - write the real sample
    original_profile_chunk_write(self, ts, sample)
    
    # Only add mock samples when timestamp mocking is enabled
    if not MOCK_TIMESTAMPS:
        return
        
    # For continuous profiling with timestamp mocking, add additional samples
    if PROFILE_TYPE == "continuous" and len(self.samples) > 0:
        # Get the last real sample as a template
        last_sample = self.samples[-1]
        
        # CRITICAL FIX: Ensure we don't exceed MAX_PROFILE_CHUNK_DURATION (66 seconds)
        # Add a few more samples within a narrow time window (< 5 seconds from last)
        if random.random() < 0.15:  # 15% chance per sample
            # Add 1-2 samples with slightly different timestamps
            for i in range(random.randint(1, 2)):
                # Clone the sample with the minimal required structure
                new_sample = {
                    "timestamp": 0.0,  # Will be set below
                    "thread_id": last_sample["thread_id"],
                    "stack_id": last_sample["stack_id"]
                }
                
                # Keep timestamps close (0.1-3 seconds) to avoid exceeding max duration
                time_offset = random.uniform(0.1, 3.0)
                new_timestamp = float(last_sample["timestamp"]) + time_offset
                
                # Ensure timestamp is a proper float
                new_sample["timestamp"] = new_timestamp
                
                # Add to samples list
                self.samples.append(new_sample)
                
                if DEBUG_PROFILING and random.random() < 0.05:
                    print(f"DEBUG: Added mock sample at timestamp {new_timestamp:.3f} (+{time_offset:.2f}s offset)")
        
        # Occasionally (1.5% chance) check and sort samples by timestamp
        # This ensures timestamps are monotonically increasing, which Vroom expects
        if random.random() < 0.015:
            if DEBUG_PROFILING:
                print(f"DEBUG: Sorting {len(self.samples)} samples by timestamp")
                
            # Sort samples by timestamp to ensure proper ordering
            self.samples.sort(key=lambda s: s["timestamp"])
            
            # Check that sample spread doesn't exceed max duration (66 seconds)
            if len(self.samples) >= 2:
                first_ts = float(self.samples[0]["timestamp"])
                last_ts = float(self.samples[-1]["timestamp"])
                duration = last_ts - first_ts
                
                if DEBUG_PROFILING:
                    print(f"DEBUG: Current chunk spans {duration:.2f} seconds")
                
                # If we're close to the limit, trim some older samples
                if duration > 60:  # Leave some margin below the 66-second limit
                    cutoff_index = len(self.samples) // 3  # Remove oldest third
                    if cutoff_index > 0:
                        self.samples = self.samples[cutoff_index:]
                        if DEBUG_PROFILING:
                            print(f"DEBUG: Trimmed oldest {cutoff_index} samples to stay within duration limits")

# Patch Profile.valid to bypass the minimum samples check
def patched_profile_valid(self):
    client = sentry_sdk.get_client()
    if not client.is_active():
        if DEBUG_PROFILING:
            print("DEBUG: Profile invalid - client not active")
        return False

    # Check if profiling is enabled in options
    if not sentry_sdk.profiler.transaction_profiler.has_profiling_enabled(client.options):
        if DEBUG_PROFILING:
            print("DEBUG: Profile invalid - profiling not enabled in options")
        return False

    if self.sampled is None or not self.sampled:
        if client.transport:
            client.transport.record_lost_event(
                "sample_rate", data_category="profile"
            )
        if DEBUG_PROFILING:
            print("DEBUG: Profile invalid - not sampled")
        return False
    
    # Check if we have enough samples
    if self.unique_samples < MINIMUM_SAMPLES:
        if DEBUG_PROFILING:
            print(f"DEBUG: Profile has only {self.unique_samples} samples (minimum is {MINIMUM_SAMPLES})")
        
        # Instead of discarding due to insufficient samples, add fake samples
        if DEBUG_PROFILING:
            print("DEBUG: Adding fake samples to reach minimum requirement...")
        
        # Only add fake samples if there's at least one real sample
        if self.unique_samples > 0 and self.samples:
            # Get the last sample as a template for fake samples
            if len(self.samples) > 0:
                last_sample = self.samples[-1]
                
                # Number of fake samples needed
                samples_needed = MINIMUM_SAMPLES - self.unique_samples
                
                # Add fake samples based on the last real sample
                for i in range(samples_needed):
                    # Clone the last sample
                    fake_sample = dict(last_sample)
                    
                    # Modify the elapsed time to make it unique
                    if "elapsed_since_start_ns" in fake_sample:
                        current = int(fake_sample["elapsed_since_start_ns"])
                        fake_sample["elapsed_since_start_ns"] = str(current + (i+1) * 500000)
                    
                    # Add to samples list
                    self.samples.append(fake_sample)
                    
                    # Increment the unique sample counter
                    self.unique_samples += 1
                
                if DEBUG_PROFILING:
                    print(f"DEBUG: Added {samples_needed} fake samples, now have {self.unique_samples} samples")
            else:
                if DEBUG_PROFILING:
                    print("WARNING: Can't add fake samples - no existing samples to use as template")
        else:
            if DEBUG_PROFILING:
                print("WARNING: Can't add fake samples - no existing samples at all")
    
    if DEBUG_PROFILING:
        print(f"DEBUG: Profile valid with {self.unique_samples} samples")
    return True

# Add a patched Profile.write method to handle transaction profile samples when mocking timestamps
def patched_profile_write(self, ts, sample):
    # Call original method to record the sample
    original_profile_write(self, ts, sample)
    
    # Add mock samples for transaction profiles if configured
    if MOCK_TIMESTAMPS and PROFILE_TYPE == "transaction" and self.unique_samples > 0:
        # Only occasionally add additional samples (to avoid too much overhead)
        if random.random() < 0.2:
            # Create 1-3 additional mock samples
            for _ in range(random.randint(1, 3)):
                # Use a new timestamp that's slightly offset from the original
                mock_ts = ts + random.randint(1000000, 10000000)  # 1-10ms offset
                
                # CRITICAL FIX: Ensure mock_ts is an integer for transaction profiles
                if not isinstance(mock_ts, int):
                    mock_ts = int(mock_ts)
                
                # Call original write with new timestamp and same sample
                original_profile_write(self, mock_ts, sample)
                
                if DEBUG_PROFILING and random.random() < 0.01:
                    print(f"DEBUG: Added mock sample to transaction profile at offset +{(mock_ts-ts)/1000000:.2f}ms (now {self.unique_samples} samples)")

# Apply all the patches
Profile.to_json = patched_profile_to_json
ProfileChunk.to_json = patched_profile_chunk_to_json
Envelope.add_profile_chunk = patched_add_profile_chunk
Profile.valid = patched_profile_valid
Profile.write = patched_profile_write
ProfileChunk.write = patched_profile_chunk_write
ProfileBuffer.__init__ = patched_profile_buffer_init
ProfileBuffer.write = patched_profile_buffer_write

# Dictionary of available DSNs - add new ones here
AVAILABLE_DSNS = {
    "profile-hours-am2-business": "https://b700116ce3eadd661071ad84ed45028b@o4508486249218048.ingest.us.sentry.io/4508486249938944",
    "profile-hours-am3-business": "https://e3be3e9fd4c48a23b3a65ec2e62743d1@o4508486299942912.ingest.de.sentry.io/4508486300729424",
}


# Define a before_send hook to modify the platform
def before_send(event, hint):
    # Change the platform to an appropriate UI platform for testing
    # UI_PROFILE_PLATFORMS = {"cocoa", "android", "javascript"}
    # https://github.com/getsentry/sentry/blob/master/src/sentry/profiles/task.py
    # 
    # This is critical for profile hours (UI PROFILE_DURATION)
    original_platform = event.get("platform")
    event["platform"] = PLATFORM
    print(
        f"DEBUG: before_send: Changed event platform from '{original_platform}' to '{PLATFORM}'"
    )

    # Add debugging tags to events
    # These will be visible in Sentry UI and searchable
    if not event.get("tags"):
        event["tags"] = {}
    event["tags"]["ui_profile_test"] = "true"
    event["tags"]["original_platform"] = original_platform
    event["tags"]["platform_override"] = PLATFORM
    event["tags"]["test_timestamp"] = datetime.now(timezone.utc).isoformat()
    # Generate a unique test ID to identify this run
    test_id = str(uuid.uuid4())[:8]
    event["tags"]["test_run_id"] = test_id
    
    # Add this to SDK scope too - will be added to all future events
    set_tag("ui_profile_test", "true") 
    set_tag("test_run_id", test_id)

    # Recursively replace any "python" platform values with PLATFORM
    def replace_platform_recursively(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "platform" and value == "python":
                    obj[key] = PLATFORM
                    print(
                        f"DEBUG: Recursively changed nested platform from 'python' to '{PLATFORM}'"
                    )
                elif isinstance(value, (dict, list)):
                    replace_platform_recursively(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    replace_platform_recursively(item)

    replace_platform_recursively(event)
    return event


def profiles_sampler(sampling_context):
    return 1.0


# Initialize the Sentry SDK with appropriate configuration based on profile type
def initialize_sentry():
    """Initialize Sentry SDK with proper configuration based on profile type"""
    
    # Common options for both profile types
    init_options = {
        "dsn": AVAILABLE_DSNS["profile-hours-am3-business"],
        "traces_sample_rate": 1.0,  # Capture 100% of transactions
        "debug": DEBUG_PROFILING,  # Use the configured debug setting
        "before_send": before_send,  # Add before_send hook to modify the platform
    }
    
    # Add profile-type specific options
    if PROFILE_TYPE == "continuous":
        # For continuous profiling
        init_options.update({
            "profile_session_sample_rate": 1.0,  # Enable continuous profiling
            "_experiments": {
                "continuous_profiling_auto_start": True,
                "continuous_profiling_debug": DEBUG_PROFILING,
            }
        })
    else:
        # For transaction-based profiling
        init_options.update({
            "profiles_sample_rate": 1.0,  # Enable transaction profiling
            "profiler_mode": "thread",    # Use thread mode for better sampling
        })
    
    # Initialize the SDK with the constructed options
    sentry_sdk.init(**init_options)
    
    if DEBUG_PROFILING:
        print(f"Initialized Sentry SDK with {PROFILE_TYPE} profiling")

# Initialize Sentry with the proper configuration
initialize_sentry()


def simulate_error():
    try:
        # Simulate a division by zero error
        1 / 0
    except Exception as e:
        capture_exception(e)


def create_test_transaction():
    # Start a new transaction
    with sentry_sdk.start_transaction(name="test-transaction-2"):
        # Create a child span
        with Span(op="child-operation", description="test-child-span"):
            print("Performing operation in span...")

        # Capture a message within the transaction
        capture_message("This is a test message within transaction")


# Example function to profile
def cpu_intensive_task(duration_ms=500):
    """
    CPU intensive task that should generate multiple profile samples.
    
    Args:
        duration_ms: Minimum duration in milliseconds to run the task
    """
    result = 0
    start_time = time.time()
    iteration = 0
    
    # Run until we've reached at least the specified duration
    while (time.time() - start_time) * 1000 < duration_ms:
        # Make this more intensive to ensure we generate enough profile samples
        for j in range(5):  # Multiple nested loops
            for i in range(100000):  # Small inner loops, repeated
                result += i
                # Add occasional random operations to make the CPU work harder
                if i % 10000 == 0:
                    result = result * 1.01
        
        iteration += 1
        if iteration % 5 == 0:
            elapsed_ms = (time.time() - start_time) * 1000
            print(f"DEBUG: CPU task running for {elapsed_ms:.1f}ms, iteration {iteration}")
    
    elapsed_ms = (time.time() - start_time) * 1000
    print(f"DEBUG: CPU task completed after {elapsed_ms:.1f}ms, {iteration} iterations")
    return result


# Start the profiler
sentry_sdk.profiler.start_profiler()


def verify_profile_platform(profile):
    """
    Verify the platform in a profile chunk is correctly set to PLATFORM.
    This is a helper function to validate our monkey patching is working correctly.
    """
    if isinstance(profile, dict):
        platform = profile.get("platform")
        debug_info = profile.get("debug_info", {})
        
        if platform != PLATFORM:
            print(f"WARNING: Profile platform is '{platform}', not '{PLATFORM}'")
        else:
            print(f"SUCCESS: Profile platform correctly set to '{platform}'")
            print(f"DEBUG INFO: {debug_info}")
            
        # Add more debug info about the profile chunk
        print(f"Profile keys: {list(profile.keys())}")
        if "client_sdk" in profile:
            print(f"SDK: {profile['client_sdk']}")
            
    return profile

# Add a hook to force extra samples into a profile if needed
def add_extra_profile_samples(profile):
    """Helper to add fake samples to a profile to meet the minimum requirement"""
    samples_needed = PROFILE_MINIMUM_SAMPLES - profile.unique_samples
    
    if samples_needed > 0:
        original_sample_count = profile.unique_samples
        print(f"DEBUG: Profile has {original_sample_count} samples, needs {samples_needed} more")
        
        # Add fake sample entries
        if profile.samples and len(profile.samples) > 0:
            # Clone the last sample to create the additional ones needed
            # This will use data from an existing sample
            last_sample = profile.samples[-1]
            
            for i in range(samples_needed):
                if isinstance(last_sample, dict):
                    # Deep copy the sample but modify it slightly for each iteration
                    new_sample = last_sample.copy()
                    # Adjust timestamp or offset slightly
                    if "elapsed_since_start_ns" in new_sample:
                        # For transaction profiles
                        current = int(new_sample["elapsed_since_start_ns"])
                        new_sample["elapsed_since_start_ns"] = str(current + 1000000 * (i + 1))
                    elif "timestamp" in new_sample:
                        # For continuous profiles
                        current = float(new_sample["timestamp"])
                        new_sample["timestamp"] = current + 0.01 * (i + 1)
                    
                    # Add to samples array
                    profile.samples.append(new_sample)
                    
                    # Increment unique samples counter
                    profile.unique_samples += 1
                    print(f"DEBUG: Added fake sample {i+1}, now have {profile.unique_samples} samples")
        else:
            print("WARNING: Can't add fake samples - no existing samples to clone")
    
    return profile

def increase_sampling_frequency():
    """
    Increase the sampling frequency of the profiler to ensure more samples are collected.
    The default sampling frequency is 101, we'll increase it to sample more frequently.
    """
    global _scheduler
    
    if _scheduler is None:
        print("WARNING: Could not increase sampling frequency - scheduler not initialized")
        return
    
    # Original frequency is typically DEFAULT_SAMPLING_FREQUENCY (101 Hz)
    original_interval = _scheduler.interval
    original_frequency = 1.0 / original_interval if original_interval > 0 else DEFAULT_SAMPLING_FREQUENCY
    
    # Increase frequency to 3x the default (300+ Hz)
    new_frequency = original_frequency * 3  
    new_interval = 1.0 / new_frequency
    
    # Update the scheduler interval
    _scheduler.interval = new_interval
    
    print(f"DEBUG: Increased profiler sampling frequency from {original_frequency:.1f}Hz to {new_frequency:.1f}Hz")
    print(f"DEBUG: Decreased sampling interval from {original_interval * 1000:.2f}ms to {new_interval * 1000:.2f}ms")
    
    return new_frequency

def main():
    try:
        # Verify our patches are working 
        original_chunk_to_json = ProfileChunk.to_json
        
        def verified_to_json(self, profiler_id, options, sdk_info):
            result = original_chunk_to_json(self, profiler_id, options, sdk_info)
            return verify_profile_platform(result)
            
        ProfileChunk.to_json = verified_to_json
        
        # Increase sampling frequency (only needed for non-mocked profiles)
        if not MOCK_TIMESTAMPS:
            increase_sampling_frequency()
        
        print("=" * 50)
        print("PROFILE HOURS TEST SCRIPT")
        print(f"Profile type: {PROFILE_TYPE}")
        print(f"Platform: {PLATFORM}")
        print(f"Mock timestamps: {'Enabled' if MOCK_TIMESTAMPS else 'Disabled'}")
        if MOCK_TIMESTAMPS:
            print(f"Mock duration: {MOCK_DURATION_HOURS} hours")
        print("=" * 50)
        
        while True:  # Infinite loop
            run_iteration()
            
            # Delay between iterations
            print("\nWaiting 5 seconds before next iteration...\n")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        
def run_iteration():
    """Run a single test iteration with the configured profile type"""
    if PROFILE_TYPE == "continuous":
        run_continuous_profile_test()
    else:
        run_transaction_profile_test()
        
def run_continuous_profile_test():
    """Run a test with continuous profiling"""
    print("\nStarting continuous profile test...")
    
    # Start the profiler for continuous profiling
    sentry_sdk.profiler.start_profiler()
    
    # Run a series of transactions with errors and CPU-intensive tasks
    for i in range(3):
        with sentry_sdk.start_transaction(name=f"test-transaction-{i}") as transaction:
            # Add test tags
            transaction.set_tag("ui_profile_test", "true") 
            transaction.set_tag("profile_type", "continuous")
            transaction.set_tag("platform_override", PLATFORM)
            transaction.set_tag("mock_timestamps", str(MOCK_TIMESTAMPS))
            
            # Set some measurements
            transaction.set_measurement(f"test_value_{i}", i * 10, "millisecond")
            
            # Run a CPU-intensive task
            duration_ms = 200 * (i + 1)  # Increasing durations
            print(f"Running CPU task {i+1}/3 (duration: {duration_ms}ms)...")
            cpu_intensive_task(duration_ms)
            
            # Send a test error if it's the last iteration
            if i == 2:
                simulate_error()
        
        # Small delay between transactions
        time.sleep(0.5)
        
    # For continuous profiling, let it run longer to collect more data
    print("Running additional CPU tasks to generate more profile samples...")
    
    # If mocking timestamps, we don't need to run as long
    duration = 2 if MOCK_TIMESTAMPS else 10
    for i in range(duration):
        cpu_intensive_task(300)
        if i % 2 == 0:
            print(f"Continuous profiling running... ({i+1}/{duration})")
        time.sleep(0.2)
    
    # Only stop if we want to reset between iterations
    print("Stopping continuous profiler...")
    sentry_sdk.profiler.stop_profiler()
    print("Continuous profile test completed")
    
def run_transaction_profile_test():
    """Run a test with transaction-based profiling"""
    print("\nStarting transaction profile test...")
    
    with sentry_sdk.start_transaction(name="test-transaction") as transaction:
        # Add test tags to the transaction
        transaction.set_tag("ui_profile_test", "true")
        transaction.set_tag("profile_type", "transaction")
        transaction.set_tag("platform_override", PLATFORM)
        transaction.set_tag("mock_timestamps", str(MOCK_TIMESTAMPS))
        
        # Run some spans and errors
        with Span(op="child-operation", description="test-child-span") as span:
            span.set_tag("ui_profile_test", "true")
            simulate_error()

        # Create a nested transaction
        create_test_transaction()

        # Run CPU intensive task to generate sufficient profile samples
        print("Running CPU intensive tasks to generate profile samples...")
        
        # Run CPU-intensive tasks with appropriate durations
        for i in range(3):
            # Set measurement to show in profile
            transaction.set_measurement(f"ui_test_{i}", i * 10, "millisecond")
            
            # Set duration based on whether we're mocking timestamps
            # If mocking, we can use shorter durations
            duration_ms = 200 * (i + 1) if MOCK_TIMESTAMPS else 500 * (i + 1)
            
            print(f"Starting CPU intensive task {i+1}/3 (duration: {duration_ms}ms)...")
            cpu_intensive_task(duration_ms=duration_ms)
            time.sleep(0.1)
                
        # Check if the current transaction's profile has enough samples
        scope = sentry_sdk.get_isolation_scope()
        if hasattr(scope, "profile") and scope.profile:
            current_profile = scope.profile
            if DEBUG_PROFILING:
                print(f"DEBUG: Current profile has {current_profile.unique_samples} samples")
            
            # If not enough samples, force add some
            if current_profile.unique_samples < MINIMUM_SAMPLES:
                if DEBUG_PROFILING:
                    print(f"DEBUG: Adding more samples to ensure minimum of {MINIMUM_SAMPLES}")
                add_extra_profile_samples(current_profile)
        elif DEBUG_PROFILING:
            print("WARNING: Could not find active profile in current scope")

        print("Transaction profile test completed")


if __name__ == "__main__":
    main()
