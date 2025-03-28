# ----------------------- CONFIGURATION OPTIONS -----------------------

# Dictionary of available DSNs - add new ones here
AVAILABLE_DSNS = {
    "profile-hours-am2-business": "https://b700116ce3eadd661071ad84ed45028b@o4508486249218048.ingest.us.sentry.io/4508486249938944",
    "profile-hours-am3-business": "https://e3be3e9fd4c48a23b3a65ec2e62743d1@o4508486299942912.ingest.de.sentry.io/4508486300729424",
}

# The DSN to use for this run - can be overridden by presets
SELECTED_DSN = "profile-hours-am3-business"  # Default to AM3 plan

# Define which platforms are considered UI platforms
# These platforms get categorized as UI profile hours rather than backend profile hours
# See relay-profiling/src/lib.rs:ProfileChunk::profile_type() for the canonical Relay source
UI_PLATFORMS = ("javascript", "android", "cocoa")

# === PROFILE HOUR TESTING PRESETS ===
#
# Set the PRESET variable to quickly switch between different testing configurations.
# Each preset configures PROFILE_TYPE, PLATFORM, DIRECT_CHUNK_GENERATION, and DSN for you.
# 
# Available presets (AM2 plans):
# - "AM2_TRANSACTION_BACKEND": Transaction profiling with Python platform (AM2 transaction billing)
# - "AM2_TRANSACTION_UI": Transaction profiling with JavaScript platform (AM2 transaction billing)
# - "AM2_CONTINUOUS_BACKEND": Continuous profiling with Python platform (AM2 backend profile hours)
# - "AM2_CONTINUOUS_UI": Continuous profiling with JavaScript platform (AM2 UI profile hours)
#
# Available presets (AM3 plans):
# - "AM3_TRANSACTION_BACKEND": Transaction converted to backend profile hours (AM3 plans)
# - "AM3_TRANSACTION_UI": Transaction converted to UI profile hours (AM3 plans)
# - "AM3_CONTINUOUS_BACKEND": Continuous backend profile hours (AM3 plans)
# - "AM3_CONTINUOUS_UI": Continuous UI profile hours (AM3 plans)
#
# Fast Direct Generation (AM2 plans):
# - "DIRECT_AM2_TRANSACTION_BACKEND": Fast transaction profiling with Python platform (AM2)
# - "DIRECT_AM2_TRANSACTION_UI": Fast transaction profiling with JavaScript platform (AM2)
# - "DIRECT_AM2_CONTINUOUS_BACKEND": Fast continuous profiling with Python platform (AM2)
# - "DIRECT_AM2_CONTINUOUS_UI": Fast continuous profiling with JavaScript platform (AM2)
#
# Fast Direct Generation (AM3 plans):
# - "DIRECT_AM3_TRANSACTION_BACKEND": Fast transaction profiling with Python platform (AM3)
# - "DIRECT_AM3_TRANSACTION_UI": Fast transaction profiling with JavaScript platform (AM3)
# - "DIRECT_AM3_CONTINUOUS_BACKEND": Fast continuous profiling with Python platform (AM3)
# - "DIRECT_AM3_CONTINUOUS_UI": Fast continuous profiling with JavaScript platform (AM3)
#
# Special Modes:
# - "CUSTOM": Use the custom settings defined below
# - "DISABLED": Don't use any preset (uses the manual settings below)
#
# How to use:
# 1. Set PRESET to your desired configuration
# 2. Set MOCK_DURATION_HOURS to control how many hours of data to generate
# 3. Run the script - it will configure and run based on your preset
#
# Plan information:
# - AM2 plans: Have separate billing for transaction profiling and profile hours
# - AM3 plans: All profiling billed as profile hours (transactions converted automatically)

PRESET = "DISABLED"  # Choose a preset from the list above or "CUSTOM" or "DISABLED"

# === CUSTOM CONFIGURATION ===
# These settings are used when PRESET is set to "CUSTOM" or "DISABLED"
# When using a preset, these settings are overridden by the preset's values

# === PRESET IMPLEMENTATION ===
# This code applies the settings based on the selected preset
# It runs before the rest of the script and overrides relevant settings

def apply_preset():
    global PROFILE_TYPE, PLATFORM, DIRECT_CHUNK_GENERATION, SELECTED_DSN
    
    # Don't modify settings if no preset is selected
    if PRESET == "DISABLED":
        print(f"No preset selected. Using manual configuration.")
        return
        
    # Set up the preset configurations with their values
    presets = {
        # AM2 Plan Presets - Standard Mode
        "AM2_TRANSACTION_BACKEND": {
            "profile_type": "transaction",
            "platform": "python",
            "direct_generation": False,
            "dsn": "profile-hours-am2-business", 
            "description": "Transaction profiling with backend platform (AM2 transaction billing)"
        },
        "AM2_TRANSACTION_UI": {
            "profile_type": "transaction",
            "platform": "javascript",
            "direct_generation": False,
            "dsn": "profile-hours-am2-business",
            "description": "Transaction profiling with UI platform (AM2 transaction billing)"
        },
        "AM2_CONTINUOUS_BACKEND": {
            "profile_type": "continuous",
            "platform": "python",
            "direct_generation": False,
            "dsn": "profile-hours-am2-business",
            "description": "Continuous profiling with backend platform (AM2 backend profile hours)"
        },
        "AM2_CONTINUOUS_UI": {
            "profile_type": "continuous",
            "platform": "javascript",
            "direct_generation": False,
            "dsn": "profile-hours-am2-business",
            "description": "Continuous profiling with UI platform (AM2 UI profile hours)"
        },
        
        # AM3 Plan Presets - Standard Mode
        "AM3_TRANSACTION_BACKEND": {
            "profile_type": "transaction",
            "platform": "python",
            "direct_generation": False,
            "dsn": "profile-hours-am3-business",
            "description": "Transaction profiling converted to backend profile hours (AM3)"
        },
        "AM3_TRANSACTION_UI": {
            "profile_type": "transaction",
            "platform": "javascript",
            "direct_generation": False,
            "dsn": "profile-hours-am3-business",
            "description": "Transaction profiling converted to UI profile hours (AM3)"
        },
        "AM3_CONTINUOUS_BACKEND": {
            "profile_type": "continuous",
            "platform": "python",
            "direct_generation": False,
            "dsn": "profile-hours-am3-business",
            "description": "Continuous backend profile hours (AM3)"
        },
        "AM3_CONTINUOUS_UI": {
            "profile_type": "continuous",
            "platform": "javascript",
            "direct_generation": False,
            "dsn": "profile-hours-am3-business",
            "description": "Continuous UI profile hours (AM3)"
        },
        
        # Direct Generation Presets (Fast mode for AM2)
        "DIRECT_AM2_TRANSACTION_BACKEND": {
            "profile_type": "transaction",
            "platform": "python",
            "direct_generation": True,
            "dsn": "profile-hours-am2-business",
            "description": "Fast direct transaction profiling with backend platform (AM2)"
        },
        "DIRECT_AM2_TRANSACTION_UI": {
            "profile_type": "transaction",
            "platform": "javascript",
            "direct_generation": True,
            "dsn": "profile-hours-am2-business",
            "description": "Fast direct transaction profiling with UI platform (AM2)"
        },
        "DIRECT_AM2_CONTINUOUS_BACKEND": {
            "profile_type": "continuous",
            "platform": "python",
            "direct_generation": True,
            "dsn": "profile-hours-am2-business",
            "description": "Fast direct continuous profiling with backend platform (AM2)"
        },
        "DIRECT_AM2_CONTINUOUS_UI": {
            "profile_type": "continuous",
            "platform": "javascript",
            "direct_generation": True,
            "dsn": "profile-hours-am2-business",
            "description": "Fast direct continuous profiling with UI platform (AM2)"
        },
        
        # Direct Generation Presets (Fast mode for AM3)
        "DIRECT_AM3_TRANSACTION_BACKEND": {
            "profile_type": "transaction",
            "platform": "python",
            "direct_generation": True,
            "dsn": "profile-hours-am3-business",
            "description": "Fast direct transaction profiling with backend platform (AM3)"
        },
        "DIRECT_AM3_TRANSACTION_UI": {
            "profile_type": "transaction",
            "platform": "javascript",
            "direct_generation": True,
            "dsn": "profile-hours-am3-business",
            "description": "Fast direct transaction profiling with UI platform (AM3)"
        },
        "DIRECT_AM3_CONTINUOUS_BACKEND": {
            "profile_type": "continuous",
            "platform": "python",
            "direct_generation": True,
            "dsn": "profile-hours-am3-business",
            "description": "Fast direct continuous profiling with backend platform (AM3)"
        },
        "DIRECT_AM3_CONTINUOUS_UI": {
            "profile_type": "continuous",
            "platform": "javascript",
            "direct_generation": True,
            "dsn": "profile-hours-am3-business",
            "description": "Fast direct continuous profiling with UI platform (AM3)"
        },
        
        # Custom preset - uses the values defined below
        "CUSTOM": {
            "profile_type": PROFILE_TYPE,
            "platform": PLATFORM,
            "direct_generation": DIRECT_CHUNK_GENERATION,
            "dsn": SELECTED_DSN,
            "description": "Custom configuration (using settings defined below)"
        }
    }
    
    # Check if the preset exists
    if PRESET not in presets:
        print(f"WARNING: Unknown preset '{PRESET}'. Using manual configuration.")
        return
    
    # Get the preset configuration
    preset_config = presets[PRESET]
    
    # Apply the preset settings
    PROFILE_TYPE = preset_config["profile_type"]
    PLATFORM = preset_config["platform"]
    DIRECT_CHUNK_GENERATION = preset_config["direct_generation"]
    SELECTED_DSN = preset_config["dsn"]
    
    print(f"Applied preset: {PRESET}")
    print(f"Description: {preset_config['description']}")
    print(f"Settings: PROFILE_TYPE={PROFILE_TYPE}, PLATFORM={PLATFORM}, DIRECT_CHUNK_GENERATION={DIRECT_CHUNK_GENERATION}")
    print(f"DSN: {SELECTED_DSN}")

# Apply the preset now (at import time)
if PRESET != "DISABLED":
    apply_preset()

# === PROFILING MODE CONFIGURATION ===
#
# PROFILE_TYPE determines which of Sentry's two profiling modes to use:
#
# 1. "transaction" - Transaction-based profiling:
#    - Profiles only code executed during transactions (between startTransaction and transaction.finish)
#    - Limited to 30 seconds maximum duration per profile
#    - Lower overhead as profiling only runs during transactions
#    - Timestamps are represented as nanosecond offsets from transaction start
#    - Configured via profiles_sample_rate in the SDK
#    - In AM3 plans, these still contribute to profile hours based on platform
#
# 2. "continuous" - Continuous profiling:
#    - Profiles your entire application continuously 
#    - No duration limits - can profile for hours/days
#    - Higher overhead since profiler is always running
#    - Timestamps are absolute Unix timestamps (seconds since epoch)
#    - Configured via profile_session_sample_rate in the SDK
#    - Explicitly controlled with start_profiler() and stop_profiler()
#    - Sends regular "profile chunks" approximately every 60 seconds
#
# NOTE: These profiling modes cannot be used simultaneously in the same SDK initialization.
PROFILE_TYPE = "continuous"  # Options: "continuous" or "transaction"

# PLATFORM determines how Relay and Sentry categorize profiles for billing purposes:
#
# - UI Platforms ("javascript", "android", "cocoa"): 
#   Counted as UI profile hours (typically higher cost in billing)
#
# - Backend Platforms ("python", "java", "node", etc.): 
#   Counted as backend profile hours
#
# This script forces the platform to the value specified here, regardless of
# the actual platform the code runs on (Python).
# Options: "javascript", "android", "cocoa" (for UI profiles)
PLATFORM = "javascript"  

# === TIMESTAMP MOCKING CONFIGURATION ===
#
# MOCK_TIMESTAMPS enables simulating longer profiling durations in standard profiling mode.
# This option only affects standard SDK profiling (when DIRECT_CHUNK_GENERATION is False):
#
# - When enabled: Profile timestamps are manipulated to appear spread across MOCK_DURATION_HOURS
#   without needing to run the process for that entire time.
#
# - When disabled: Real timestamps from actual execution are used, meaning you'd need to
#   run the process for the entire duration you want to test.
#
# When using DIRECT_CHUNK_GENERATION, timestamps are always mocked based on MOCK_DURATION_HOURS,
# and this setting is ignored.
#
# For transaction profiling: This extends the relative_end_ns of transactions
# For continuous profiling: This spreads samples across multiple 60-second windows
MOCK_TIMESTAMPS = False  # Set to True to mock longer profiles in standard profiling mode

# MOCK_DURATION_HOURS sets how many hours of profiling data to simulate.
# This controls:
# - How many chunks are generated in direct generation mode (approximately 60 per hour)
# - The effective duration of profiles when using timestamp mocking
# - The total billable profile hours that will be generated
#
# This setting is used by both direct generation and standard profiling with MOCK_TIMESTAMPS.
# 
# NOTE: In AM3 plans, this directly correlates to the number of profile hours
# that will be counted for billing purposes.
MOCK_DURATION_HOURS = 1.0  # How many hours to simulate for each profile session

# MOCK_SAMPLES_PER_HOUR controls the density of samples when MOCK_TIMESTAMPS is enabled.
# Higher values create more detailed profiles but increase payload size.
# For most testing purposes, the default is sufficient.
MOCK_SAMPLES_PER_HOUR = 3600  # How many samples per hour to generate (if mocking)

# === ADVANCED PROFILE GENERATION OPTIONS ===
#
# DIRECT_CHUNK_GENERATION enables the ultra-fast profile generation mode:
# 
# - When enabled: 
#   * Completely bypasses the SDK's normal profiling mechanisms
#   * Creates and sends profile chunks directly to Sentry
#   * Achieves extremely high generation rates (60+ hours of data per second)
#   * Use this for generating large amounts of profile data quickly
#
# - When disabled:
#   * Uses the standard SDK profiling mechanisms with patches
#   * More closely simulates real SDK behavior
#   * Much slower generation rate
#
# The direct chunk generation will automatically use MOCK_DURATION_HOURS to 
# determine how much profile data to generate and will create timestamps 
# spread across that duration.
#
# For billing tests where you need to generate many profile hours quickly, enable this option.
DIRECT_CHUNK_GENERATION = True  # Set to True to generate chunks directly (bypasses profiler)

# SAMPLES_PER_CHUNK controls how many stack samples are included in each profile chunk
# when using DIRECT_CHUNK_GENERATION mode.
# 
# - Higher values: More detailed profiles but larger payload sizes
# - Lower values: Smaller, more efficient payloads but less detailed
#
# For billing testing purposes, the default is adequate. Higher values might be 
# needed if you're testing visualization or specific profile data structures.
SAMPLES_PER_CHUNK = 20  # How many samples to include in each chunk for direct generation

# === DEBUGGING OPTIONS ===
#
# DEBUG_PROFILING controls the verbosity of output during profiling:
#
# - When enabled: 
#   * Prints detailed information about the profiling process
#   * Shows sample counts, chunk generation progress, and platform details
#   * Reports window coverage for continuous profiling
#   * Reports profiling mode initialization details
#
# - When disabled:
#   * Minimal output, reporting only critical errors
#   * Useful for production-like testing scenarios
#
# For initial testing and troubleshooting, enable this option.
# For generating large volumes of profile data, consider disabling to reduce console spam.
DEBUG_PROFILING = True  # Set to True for verbose debugging info

# MINIMUM_SAMPLES defines the minimum number of stack samples a profile must contain to be considered valid.
# Each sample is a snapshot of what functions were being executed at a specific moment.
#
# By default, the Sentry SDK discards profiles with fewer than PROFILE_MINIMUM_SAMPLES
# (typically 2-5 depending on SDK version).
#
# This script overrides the normal behavior by:
# 1. Checking for profiles with fewer than MINIMUM_SAMPLES
# 2. Automatically adding synthetic samples to ensure profiles meet this threshold
# 3. Ensuring no profiles are discarded due to insufficient samples
#
# Setting a higher value means more detailed profiles, but potentially more overhead.
# Setting a lower value ensures almost all profiles are sent, but might include less useful profiles.
# The default (3) is a good balance that ensures profiles have enough data to be meaningful
# while not requiring excessive CPU work in the mock-timestamp mode.
MINIMUM_SAMPLES = 3  # Minimum number of samples to ensure are collected

# ----------------------- IMPLEMENTATION -----------------------
try:
    import platform  # Import the standard platform module for system info
except ImportError:
    # Fall back to a minimal platform implementation if the standard one isn't available
    class PlatformFallback:
        @staticmethod
        def machine():
            return "unknown"
        
        @staticmethod
        def system():
            return "unknown"
        
        @staticmethod
        def release():
            return "unknown"
        
        @staticmethod
        def python_implementation():
            return "python"
        
        @staticmethod
        def python_version():
            return "3.x"
    
    platform = PlatformFallback()

import random
import threading
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
        # Initialize tracking for window coverage
        self.mock_chunk_counter = 0
        self.mock_flush_count = 0
        self.covered_windows = set()
        self.total_windows = max(1, int(MOCK_DURATION_HOURS * 3600 / 60))
        self.last_coverage_report = 0
        
        # Set to track which chunks we've generated
        self.generated_chunks = {}  # window_index -> count
        
        # Log the override if debugging is enabled
        if DEBUG_PROFILING:
            print(f"DEBUG: Initializing ProfileBuffer with mock timestamps for {MOCK_DURATION_HOURS} hours")
            print(f"DEBUG: Will generate approximately {self.total_windows} chunks to cover the full duration")

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
        # Calculate which 60-second window this chunk represents
        hours_in_seconds = MOCK_DURATION_HOURS * 3600
        
        # IMPORTANT: We need to prioritize uncovered windows to ensure full coverage
        if len(self.covered_windows) < self.total_windows and self.mock_chunk_counter >= self.total_windows:
            # If we've gone through all windows once but still have uncovered windows,
            # find an uncovered window to use next
            uncovered = set(range(self.total_windows)) - self.covered_windows
            if uncovered:
                # Prioritize uncovered windows
                window_index = random.choice(list(uncovered))
            else:
                # Default sequential approach if all are covered (shouldn't happen)
                window_index = self.mock_chunk_counter % self.total_windows
        else:
            # Normal sequential approach for initial coverage
            window_index = self.mock_chunk_counter % self.total_windows
            
        # Mark this window as covered
        self.covered_windows.add(window_index)
        
        # Track which chunks we've generated for each window
        if window_index in self.generated_chunks:
            self.generated_chunks[window_index] += 1
        else:
            self.generated_chunks[window_index] = 1
        
        # Calculate timestamp within the window
        window_start_time = window_index * 60
        in_window_offset = elapsed_fraction * 60  # 0-60 second offset within window
        mock_elapsed_secs = window_start_time + in_window_offset
        
        # Calculate the absolute timestamp
        base_timestamp = float(self.original_start_timestamp)
        mocked_timestamp = base_timestamp + float(mock_elapsed_secs)
        
        # Write the sample with the properly mocked timestamp
        original_profile_chunk_write(self.chunk, mocked_timestamp, sample)
        
        # Log detailed info occasionally to avoid spam
        if DEBUG_PROFILING and random.random() < 0.005:
            coverage_percent = (len(self.covered_windows) / self.total_windows) * 100
            print(f"DEBUG: Writing sample at window {window_index+1}/{self.total_windows} "
                  f"({coverage_percent:.1f}% coverage), offset +{in_window_offset:.2f}s")
    else:
        # Time to flush the buffer and increment counter
        self.mock_flush_count += 1
        
        # Increment window counter for next chunk
        self.mock_chunk_counter += 1
        
        # Reset the buffer
        self.flush()
        self.chunk = ProfileChunk()
        self.start_monotonic_time = now()
        
        # Report coverage progress at regular intervals
        current_time = time.time()
        if DEBUG_PROFILING and (current_time - getattr(self, 'last_coverage_report', 0) > 5):
            self.last_coverage_report = current_time
            coverage_percent = (len(self.covered_windows) / self.total_windows) * 100
            print(f"DEBUG: Flushed chunk {self.mock_flush_count}, window coverage: "
                  f"{len(self.covered_windows)}/{self.total_windows} ({coverage_percent:.1f}%)")
            
            # If we've generated a significant number of chunks but still have uncovered windows,
            # print which ones are missing
            if self.mock_flush_count > self.total_windows * 0.5 and len(self.covered_windows) < self.total_windows:
                uncovered = set(range(self.total_windows)) - self.covered_windows
                if len(uncovered) < 20:
                    print(f"DEBUG: Uncovered windows: {sorted(uncovered)}")
                else:
                    print(f"DEBUG: {len(uncovered)} windows still uncovered")
                    
        # Force another flush immediately if we need more coverage
        # This accelerates coverage of all time windows
        if self.mock_flush_count % 5 == 0 and len(self.covered_windows) < self.total_windows:
            if DEBUG_PROFILING:
                print(f"DEBUG: Accelerating window coverage ({len(self.covered_windows)}/{self.total_windows})")
            # Force immediate start of a new buffer to continue coverage
            self.start_monotonic_time = now() - self.buffer_size * 0.9

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
    
    # Only mark as UI profile test if it's using a UI platform
    is_ui_platform = PLATFORM in UI_PLATFORMS
    event["tags"]["ui_profile_test"] = is_ui_platform
    event["tags"]["is_ui_platform"] = is_ui_platform
    event["tags"]["original_platform"] = original_platform
    event["tags"]["platform_override"] = PLATFORM
    event["tags"]["test_timestamp"] = datetime.now(timezone.utc).isoformat()
    
    # Generate a unique test ID to identify this run
    test_id = str(uuid.uuid4())[:8]
    event["tags"]["test_run_id"] = test_id
    
    # Add this to SDK scope too - will be added to all future events
    set_tag("ui_profile_test", is_ui_platform) 
    set_tag("is_ui_platform", is_ui_platform)
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
    
    # Get the actual DSN value from the selected DSN name
    dsn_value = AVAILABLE_DSNS.get(SELECTED_DSN, AVAILABLE_DSNS["profile-hours-am3-business"])
    
    # Common options for both profile types
    init_options = {
        "dsn": dsn_value,
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
        print(f"Using DSN: {SELECTED_DSN} ({dsn_value})")

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


# Tasks for profiling
def cpu_intensive_task(duration_ms=500):
    """
    CPU intensive task that should generate multiple profile samples.
    If MOCK_TIMESTAMPS is True, this will just sleep instead of actually
    burning CPU cycles, since we'll be generating synthetic profile data.
    
    Args:
        duration_ms: Minimum duration in milliseconds to run the task
    """
    # If we're mocking timestamps, we don't need to actually burn CPU
    # Just sleep a bit to allow the mocking code to run
    if MOCK_TIMESTAMPS:
        sleep_duration = min(duration_ms / 1000, 0.1)  # Sleep for at most 0.1s
        time.sleep(sleep_duration)
        if DEBUG_PROFILING:
            print(f"DEBUG: Skipped CPU task (mocking enabled) - slept for {sleep_duration:.2f}s")
        return 0
    
    # Standard CPU-intensive task for real profiling
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


def generate_synthetic_profile_sample():
    """
    Generate a completely synthetic profile sample for use when MOCK_TIMESTAMPS is True.
    This eliminates the need for actual CPU-intensive tasks.
    """
    # Create a basic synthetic stack (similar to what extract_stack would produce)
    frame_functions = [
        "main",
        "run_app",
        "process_request",
        "handle_data",
        "calculate_result",
        "compute_value",
        "update_cache",
        "format_response",
        "send_result"
    ]
    
    # Randomly select 3-7 functions to create a stack trace
    stack_depth = random.randint(3, 7)
    selected_functions = random.sample(frame_functions, stack_depth)
    
    # Create frame representations
    frames = []
    frame_ids = []
    
    # Create a unique ID for this stack
    stack_id = str(uuid.uuid4())[:8]
    
    # Create synthetic frames
    for i, func_name in enumerate(selected_functions):
        # Create a synthetic frame with typical attributes
        frame = {
            "function": func_name,
            "filename": f"/app/src/{func_name.lower().replace('_', '/')}.py",
            "lineno": random.randint(10, 500),
            "module": f"app.{func_name.lower().replace('_', '.')}",
            "abs_path": f"/app/src/{func_name.lower().replace('_', '/')}.py",
            "in_app": True
        }
        frames.append(frame)
        frame_ids.append(f"frame_{i}_{func_name}")
    
    # Create a synthetic sample with current thread ID and the generated stack
    thread_id = str(threading.get_ident())
    sample = [(thread_id, (stack_id, frame_ids, frames))]
    
    return sample


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
        
        # Increase sampling frequency (only needed for standard profiling mode)
        if not DIRECT_CHUNK_GENERATION:
            increase_sampling_frequency()
        
        print("=" * 50)
        print("PROFILE HOURS TEST SCRIPT")
        if PRESET != "DISABLED":
            print(f"Preset: {PRESET}")
        print(f"Profile type: {PROFILE_TYPE}")
        print(f"Platform: {PLATFORM} {'(UI Platform)' if PLATFORM in UI_PLATFORMS else '(Backend Platform)'}")
        print(f"DSN: {SELECTED_DSN} ({AVAILABLE_DSNS[SELECTED_DSN]})")
        print(f"Plan type: {'AM2' if 'am2' in SELECTED_DSN.lower() else 'AM3'}")
        print(f"Mock timestamps: {'Enabled' if MOCK_TIMESTAMPS else 'Disabled'}")
        print(f"Mock duration: {MOCK_DURATION_HOURS} hours")
        print(f"Direct chunk generation: {'Enabled' if DIRECT_CHUNK_GENERATION else 'Disabled'}")
        print("=" * 50)
        
        # Use direct chunk generation if configured
        if DIRECT_CHUNK_GENERATION:
            print("\nDirect chunk generation mode enabled")
            if PROFILE_TYPE == "continuous":
                print("This will generate hours of continuous profile data in seconds")
                generate_direct_profile_chunks()
            else:
                print("This will generate hours of transaction profile data in seconds")
                generate_direct_transaction_profiles()
        else:
            while True:  # Infinite loop
                run_iteration()
                
                # Delay between iterations
                print("\nWaiting 5 seconds before next iteration...\n")
                time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")

def generate_direct_profile_chunks():
    """
    Generate and send profile chunks directly without using the SDK's buffer.
    This allows generating hours worth of profile data in seconds.
    """
    print(f"\nGenerating {MOCK_DURATION_HOURS} hours of profile chunks directly")
    
    # Calculate how many chunks to generate (approximately 60 per hour)
    hours_in_seconds = MOCK_DURATION_HOURS * 3600
    chunks_to_generate = max(1, int(hours_in_seconds / 60))
    
    # Explain the timestamp approach being used
    current_time = datetime.now(timezone.utc)
    start_time = current_time - timedelta(hours=MOCK_DURATION_HOURS)
    end_time = current_time
    
    print(f"Will generate {chunks_to_generate} profile chunks with {SAMPLES_PER_CHUNK} samples each")
    print(f"Using timestamps from the past: {start_time.isoformat()} to {end_time.isoformat()}")
    
    # Indicate if this is a UI platform test or not
    if PLATFORM in UI_PLATFORMS:
        print(f"Platform: {PLATFORM} (UI platform - will be counted as UI profile hours)")
    else:
        print(f"Platform: {PLATFORM} (Backend platform - will be counted as backend profile hours)")
    
    # Generate a profiler_id - this would normally be created by the SDK
    profiler_id = uuid.uuid4().hex
    
    # Get the client and its options
    client = sentry_sdk.get_client()
    if not client or not client.options:
        print("ERROR: Could not access Sentry client or options")
        return
    
    # Get the SDK info
    sdk_info = {"name": "sentry.python", "version": "2.24.1"}  # Hardcoded version
    
    # Get the capture function - this is what actually sends the envelope to Sentry
    capture_func = None
    if hasattr(client, 'transport') and client.transport:
        if hasattr(client.transport, 'capture_envelope'):
            capture_func = client.transport.capture_envelope
    
    if not capture_func:
        print("ERROR: Could not access capture_envelope function")
        return
    
    # Set up progress tracking
    start_time = time.time()
    last_report_time = start_time
    chunks_generated = 0
    
    print("\nGenerating and sending chunks...")
    
    # Timestamp base - start from the past to avoid clock drift issues
    current_time = datetime.now(timezone.utc).timestamp()
    # Start from X hours in the past, where X is the mock duration
    # This ensures all timestamps are in the past and none exceed current time
    base_timestamp = current_time - (MOCK_DURATION_HOURS * 3600)
    
    # Generate chunks for the entire duration
    for window_index in range(chunks_to_generate):
        # Create a new profile chunk
        chunk = ProfileChunk()
        
        # Calculate the timestamp for this window (each window is 60 seconds)
        window_timestamp = base_timestamp + (window_index * 60)
        
        # Generate samples for this chunk
        for i in range(SAMPLES_PER_CHUNK):
            # Create a synthetic sample
            sample = generate_synthetic_profile_sample()[0]
            
            # Calculate offset within this 60-second window (0-59 seconds)
            # This ensures samples are within a 60-second window to avoid Vroom's validation
            in_window_offset = (i / SAMPLES_PER_CHUNK) * 59  # Spread across 59 seconds
            sample_timestamp = window_timestamp + in_window_offset
            
            # Write the sample to the chunk
            original_profile_chunk_write(chunk, sample_timestamp, [sample])
        
        # Convert the chunk to JSON
        chunk_data = chunk.to_json(profiler_id, client.options, sdk_info)
        
        # Override platform to match the configuration
        chunk_data["platform"] = PLATFORM
        
        # Add tags for searchability in Sentry UI
        chunk_data["tags"] = {
            "profile_type": "continuous", 
            "ui_profile_test": PLATFORM in UI_PLATFORMS,  # Only true for UI platforms
            "is_ui_platform": PLATFORM in UI_PLATFORMS,  # Explicit tag for platform type
            "synthetic": "true",
            "direct_generation": "true",
            "mock_duration_hours": str(MOCK_DURATION_HOURS),
            "platform_override": PLATFORM,
            "original_platform": "python",
            "mock_timestamps": "past",
            "window_index": str(window_index)
        }
        
        # Add debugging info
        chunk_data["debug_info"] = {
            "original_platform": "python",
            "spoofed_platform": PLATFORM,
            "current_timestamp": datetime.now(timezone.utc).isoformat(),
            "mock_timestamp": "past",
            "chunk_timestamp": datetime.fromtimestamp(window_timestamp, tz=timezone.utc).isoformat(),
            "mock_duration_hours": str(MOCK_DURATION_HOURS),
            "window_index": window_index,
            "direct_generation": "true",
            "test_run_id": str(uuid.uuid4())[:8]
        }
        
        # Create an envelope and add the profile chunk
        envelope = Envelope()
        envelope.add_item(
            Item(
                payload=PayloadRef(json=chunk_data),
                type="profile_chunk",
                headers={"platform": PLATFORM},  # Critical for UI profile hours
            )
        )
        
        # Send the envelope directly
        capture_func(envelope)
        
        # Update tracking
        chunks_generated += 1
        
        # Report progress periodically
        current_time = time.time()
        if (current_time - last_report_time) >= 0.5 or chunks_generated == chunks_to_generate:
            last_report_time = current_time
            elapsed = current_time - start_time
            progress = (chunks_generated / chunks_to_generate) * 100
            time_covered = (chunks_generated * 60) / 3600  # Hours of profile data
            
            # Estimate completion time
            if chunks_generated > 0 and elapsed > 0:
                chunks_per_second = chunks_generated / elapsed
                remaining_chunks = chunks_to_generate - chunks_generated
                estimated_remaining_seconds = remaining_chunks / chunks_per_second if chunks_per_second > 0 else 0
                
                print(f"Progress: {chunks_generated}/{chunks_to_generate} chunks "
                      f"({progress:.1f}%, {time_covered:.2f} hours covered), "
                      f"Rate: {chunks_per_second:.1f} chunks/s, "
                      f"ETA: {estimated_remaining_seconds:.1f}s")
    
    # Final report
    total_time = time.time() - start_time
    print(f"\nGeneration complete: {chunks_generated} chunks ({MOCK_DURATION_HOURS} hours) "
          f"generated in {total_time:.2f} seconds")
    print(f"Generation speed: {chunks_generated / total_time:.1f} chunks/second "
          f"({MOCK_DURATION_HOURS / total_time:.2f} hours/second)")
    
    # Offer to run more if needed
    print(f"\nTip: To generate more data, increase MOCK_DURATION_HOURS at the top of the script.")


def generate_direct_transaction_profiles():
    """
    Generate and send transaction profiles directly without using the SDK's transaction mechanism.
    This allows generating hours worth of transaction profile data in seconds.
    
    Unlike continuous profiling which sends chunks regularly, transaction profiling attaches 
    profiles to transactions. This function creates synthetic transactions with attached profiles
    that simulate lengthy durations.
    
    IMPORTANT: Transaction profiles MUST be linked to a transaction event to be visible in Sentry.
    This requires:
    1. Adding the profile to the envelope BEFORE the transaction
    2. Adding a "profile" context to the transaction that references the profile ID
    3. Making sure the transaction ID in profile matches exactly the transaction event ID
    4. Ensuring consistent timestamps between transaction and profile
    
    TIMESTAMP APPROACH:
    - All transactions are generated with timestamps in the past
    - The base timestamp is set to (current_time - mock_duration_hours)
    - Transactions are spread evenly across this past time window
    - This approach avoids clock drift correction that might occur with future timestamps
    - Each transaction has a timestamp in the past with the profile's relative timing preserved
    """
    print(f"\nGenerating {MOCK_DURATION_HOURS} hours of transaction profile data directly")
    
    # Calculate how many transactions/profiles to generate
    # We'll create approximately 10 transactions per hour
    transactions_to_generate = max(1, int(MOCK_DURATION_HOURS * 10))
    
    # Explain the timestamp approach being used
    current_time = datetime.now(timezone.utc)
    start_time = current_time - timedelta(hours=MOCK_DURATION_HOURS)
    end_time = current_time
    
    print(f"Will generate {transactions_to_generate} transactions with profiles")
    print(f"Each profile will have approximately {SAMPLES_PER_CHUNK} samples")
    print(f"Using timestamps from the past: {start_time.isoformat()} to {end_time.isoformat()}")
    
    # Indicate if this is a UI platform test or not
    if PLATFORM in UI_PLATFORMS:
        print(f"Platform: {PLATFORM} (UI platform - will be counted as UI profile hours)")
    else:
        print(f"Platform: {PLATFORM} (Backend platform - will be counted as backend profile hours)")
    
    # Get the client and its options
    client = sentry_sdk.get_client()
    if not client or not client.options:
        print("ERROR: Could not access Sentry client or options")
        return
    
    # Get the capture function - this is what actually sends the envelope to Sentry
    capture_func = None
    if hasattr(client, 'transport') and client.transport:
        if hasattr(client.transport, 'capture_envelope'):
            capture_func = client.transport.capture_envelope
    
    if not capture_func:
        print("ERROR: Could not access capture_envelope function")
        return
    
    # Set up progress tracking
    start_time = time.time()
    last_report_time = start_time
    profiles_generated = 0
    
    print("\nGenerating and sending transaction profiles...")
    
    # Time base for transactions - start from the past to avoid clock drift issues
    current_time = datetime.now(timezone.utc).timestamp()
    # Start from X hours in the past, where X is the mock duration
    # This ensures all timestamps are in the past and none exceed current time
    base_timestamp = current_time - (MOCK_DURATION_HOURS * 3600)
    
    # For transaction profiles, we'll distribute profiles across the mocked duration
    hours_in_seconds = MOCK_DURATION_HOURS * 3600
    
    # Generate each transaction with profile
    for idx in range(transactions_to_generate):
        # Generate unique IDs
        event_id = uuid.uuid4().hex
        trace_id = "".join(["{:02x}".format(random.randint(0, 255)) for _ in range(16)])
        profile_id = uuid.uuid4().hex
        
        # Calculate where in the mocked duration this transaction fits
        # Spread transactions evenly across the mocked duration - all in the past
        relative_position = idx / transactions_to_generate
        transaction_timestamp = base_timestamp + (relative_position * hours_in_seconds)
        
        # Ensure the transaction timestamp doesn't exceed current time
        # (should never happen with our base_timestamp calculation, but double-check)
        current_time = datetime.now(timezone.utc).timestamp()
        if transaction_timestamp > current_time:
            print(f"WARNING: Transaction timestamp {transaction_timestamp} is in the future! Adjusting to past.")
            transaction_timestamp = current_time - 60  # 1 minute in the past
        
        # Create profile start timestamp - use actual transaction timestamp for consistency
        profile_start_ns = int(transaction_timestamp * 1_000_000_000)  # Convert seconds to nanoseconds
        
        # Calculate how long this profile should appear to run
        # For transaction profiles, we can't exceed 30 seconds in reality
        # But we can fake longer durations in the transaction metadata
        # Maximum single-transaction duration should be less than what Relay validates (30 sec)
        tx_duration_sec = min(25.0, hours_in_seconds / transactions_to_generate)
        
        # For transaction profiles, instead of representing absolute timestamps,
        # samples use nanosecond offsets from the start of the profile
        samples = []
        frames = []
        stacks = []
        indexed_frames = {}
        indexed_stacks = {}
        
        # Generate synthetic samples for this profile
        for i in range(SAMPLES_PER_CHUNK):
            # Create a synthetic sample with stack
            tid, stack_data = generate_synthetic_profile_sample()[0]
            stack_id, frame_ids, frame_objects = stack_data
            
            # Calculate offset within the transaction duration (in nanoseconds)
            # We need to spread samples throughout the profile
            relative_offset = (i / SAMPLES_PER_CHUNK) * tx_duration_sec * 1_000_000_000
            
            # Create frame references (just like in Profile.write)
            if stack_id not in indexed_stacks:
                for j, frame_id in enumerate(frame_ids):
                    if frame_id not in indexed_frames:
                        indexed_frames[frame_id] = len(indexed_frames)
                        frames.append(frame_objects[j])
                
                indexed_stacks[stack_id] = len(indexed_stacks)
                stacks.append([indexed_frames[frame_id] for frame_id in frame_ids])
            
            # Transaction profiles require string representation of nanosecond offsets
            # This is different from continuous profiles which use Unix timestamps
            samples.append({
                "elapsed_since_start_ns": str(int(relative_offset)),
                "thread_id": str(tid),
                "stack_id": indexed_stacks[stack_id]
            })
        
        # Get thread metadata
        thread_metadata = {}
        for thread in threading.enumerate():
            thread_metadata[str(thread.ident)] = {
                "name": str(thread.name),
            }
        
        # Create the processed profile
        processed_profile = {
            "frames": frames,
            "stacks": stacks,
            "samples": samples,
            "thread_metadata": thread_metadata,
        }
        
        # Create the full profile payload (like Profile.to_json)
        profile_payload = {
            "environment": client.options.get("environment"),
            "event_id": profile_id,
            "platform": PLATFORM,  # Override to target platform
            "profile": processed_profile,
            "release": client.options.get("release", ""),
            "timestamp": transaction_timestamp,
            "version": "1",
            "device": {
                "architecture": platform.machine(),
            },
            "os": {
                "name": platform.system(),
                "version": platform.release(),
            },
            "runtime": {
                "name": platform.python_implementation(),
                "version": platform.python_version(),
            },
            "transactions": [
                {
                    "id": event_id,
                    "name": f"synthetic-transaction-{idx}",
                    "relative_start_ns": "0",
                    # This is the critical field for mocking long durations
                    # We set it to the entire mocked duration in nanoseconds
                    "relative_end_ns": str(int(MOCK_DURATION_HOURS * 3600 * 1_000_000_000 / transactions_to_generate)),
                    "trace_id": trace_id,
                    # Get the current thread ID (same way the SDK does)
                    "active_thread_id": str(threading.get_ident()),
                }
            ],
            # Add tags for searchability in Sentry UI
            "tags": {
                "profile_type": "transaction",
                "ui_profile_test": PLATFORM in UI_PLATFORMS,  # Only true for UI platforms
                "is_ui_platform": PLATFORM in UI_PLATFORMS,  # Explicit tag for platform type
                "synthetic": "true",
                "direct_generation": "true",
                "mock_duration_hours": str(MOCK_DURATION_HOURS),
                "platform_override": PLATFORM,
                "original_platform": "python",
                "transaction_id": event_id,
                "mock_timestamps": "past",
                "past_timestamp_base": datetime.fromtimestamp(base_timestamp, tz=timezone.utc).isoformat()
            },
            # Add debugging info
            "debug_info": {
                "original_platform": "python",
                "spoofed_platform": PLATFORM,
                "current_timestamp": datetime.now(timezone.utc).isoformat(),
                "mock_timestamp": "past",
                "profile_timestamp": datetime.fromtimestamp(transaction_timestamp, tz=timezone.utc).isoformat(),
                "mock_duration_hours": str(MOCK_DURATION_HOURS),
                "transaction_index": idx,
                "direct_generation": "true",
                "test_run_id": str(uuid.uuid4())[:8]
            }
        }
        
        # Create a matching transaction event
        transaction_duration = tx_duration_sec  # In seconds
        transaction_event = {
            "event_id": event_id,
            "type": "transaction",
            "transaction": f"synthetic-transaction-{idx}",
            "platform": PLATFORM,  # Override to target platform
            "timestamp": datetime.fromtimestamp(transaction_timestamp, tz=timezone.utc).isoformat(),
            "start_timestamp": datetime.fromtimestamp(transaction_timestamp, tz=timezone.utc).isoformat(),
            # Add all the expected transaction fields
            "contexts": {
                "trace": {
                    "trace_id": trace_id,
                    "span_id": uuid.uuid4().hex[:16],
                    "op": "synthetic",
                    "status": "ok"
                },
                # IMPORTANT: Add profile context to link the transaction to its profile
                "profile": {
                    "profile_id": profile_id
                }
            },
            "tags": {
                "transaction": f"synthetic-transaction-{idx}",
                "synthetic": "true",
                "profile_type": "transaction",  # Explicitly mark as transaction profiling
                "mock_duration_hours": str(MOCK_DURATION_HOURS),
                "ui_profile_test": PLATFORM in UI_PLATFORMS,  # Only true for UI platforms
                "is_ui_platform": PLATFORM in UI_PLATFORMS,  # Explicit tag for platform type
                "platform_override": PLATFORM,
                "original_platform": "python",
                "test_run_id": str(uuid.uuid4())[:8],  # Add unique test run ID
                "profile_id": profile_id,  # Add direct reference to profile ID
                "direct_generation": "true",
                "mock_timestamps": "past",  # Indicate we're using past timestamps
                "past_timestamp_base": datetime.fromtimestamp(base_timestamp, tz=timezone.utc).isoformat()
            },
            # Add some spans for realism
            "spans": [
                {
                    "span_id": uuid.uuid4().hex[:16],
                    "parent_span_id": trace_id,
                    "start_timestamp": transaction_timestamp,
                    "timestamp": transaction_timestamp + (transaction_duration * 0.5),
                    "description": "Synthetic child span",
                    "op": "child-operation"
                }
            ],
            "measurements": {
                "synthetic_metric": {
                    "value": random.randint(10, 100),
                    "unit": "millisecond"
                }
            }
        }
        
        # Create an envelope with both the transaction and its profile
        envelope = Envelope()
        
        # IMPORTANT: Add profile FIRST, then transaction
        # This ensures Relay processes them in the correct order
        # Add the profile first
        envelope.add_item(
            Item(
                payload=PayloadRef(json=profile_payload),
                type="profile",
                headers={"platform": PLATFORM}  # Critical for UI profile hours
            )
        )
        
        # Add the transaction second
        envelope.add_item(
            Item(
                payload=PayloadRef(json=transaction_event),
                type="transaction",
                headers={"platform": PLATFORM}  # Set platform in headers
            )
        )
        
        # Send the envelope directly
        capture_func(envelope)
        
        # Update tracking
        profiles_generated += 1
        
        # Report progress periodically
        current_time = time.time()
        if (current_time - last_report_time) >= 0.5 or profiles_generated == transactions_to_generate:
            last_report_time = current_time
            elapsed = current_time - start_time
            progress = (profiles_generated / transactions_to_generate) * 100
            
            # Calculate hours covered based on proportion of profiles generated
            time_covered = (profiles_generated / transactions_to_generate) * MOCK_DURATION_HOURS
            
            # Estimate completion time
            if profiles_generated > 0 and elapsed > 0:
                profiles_per_second = profiles_generated / elapsed
                remaining_profiles = transactions_to_generate - profiles_generated
                estimated_remaining_seconds = remaining_profiles / profiles_per_second if profiles_per_second > 0 else 0
                
                print(f"Progress: {profiles_generated}/{transactions_to_generate} profiles "
                      f"({progress:.1f}%, {time_covered:.2f} hours covered), "
                      f"Rate: {profiles_per_second:.1f} profiles/s, "
                      f"ETA: {estimated_remaining_seconds:.1f}s")
    
    # Final report
    total_time = time.time() - start_time
    print(f"\nGeneration complete: {profiles_generated} transaction profiles ({MOCK_DURATION_HOURS} hours) "
          f"generated in {total_time:.2f} seconds")
    print(f"Generation speed: {profiles_generated / total_time:.1f} profiles/second "
          f"({MOCK_DURATION_HOURS / total_time:.2f} hours/second)")
    
    # Offer to run more if needed
    print(f"\nTip: To generate more data, increase MOCK_DURATION_HOURS at the top of the script.")
        
def run_iteration():
    """Run a single test iteration with the configured profile type"""
    if PROFILE_TYPE == "continuous":
        run_continuous_profile_test()
    else:
        run_transaction_profile_test()
        
def run_continuous_profile_test():
    """Run a test with continuous profiling"""
    print("\nStarting continuous profile test...")
    
    # For MOCK_TIMESTAMPS mode, we can directly inject synthetic profile data
    if MOCK_TIMESTAMPS:
        hours_in_seconds = MOCK_DURATION_HOURS * 3600
        expected_chunks = max(1, int(hours_in_seconds / 60))
        
        print(f"Mock timestamps enabled: Will generate {expected_chunks} synthetic profile chunks")
        print(f"This will simulate {MOCK_DURATION_HOURS} hours of profiling data")
        
        # Get direct access to the scheduler and buffer
        original_sampler = None
        scheduler = None
        buffer = None
        client = sentry_sdk.get_client()
        
        # Start the profiler to initialize the buffer and scheduler
        sentry_sdk.profiler.start_profiler()
        
        # Access the scheduler
        if hasattr(client, '_profiler') and client._profiler:
            scheduler = getattr(client._profiler, '_scheduler', None)
            
            # Get the buffer
            if scheduler and hasattr(scheduler, 'buffer'):
                buffer = scheduler.buffer
                
                # Save the original sampler for restoration later
                if hasattr(scheduler, 'sampler'):
                    original_sampler = scheduler.sampler
        
        if not buffer or not scheduler:
            print("ERROR: Could not access profiler buffer or scheduler. Falling back to standard profiling.")
            return run_standard_profiling()
        
        # Create a custom sampler that injects synthetic samples
        def synthetic_sampler(*args, **kwargs):
            # Generate a synthetic sample
            return generate_synthetic_profile_sample()
        
        # Replace the scheduler's sampler with our synthetic one
        scheduler.sampler = synthetic_sampler
        
        print("\nGenerating synthetic profile chunks...")
        
        # Create initial transactions to set up the profiling context
        with sentry_sdk.start_transaction(name="setup-transaction") as transaction:
            # Only mark as UI profile test if it's using a UI platform
            is_ui_platform = PLATFORM in ("javascript", "android", "cocoa")
            transaction.set_tag("ui_profile_test", is_ui_platform) 
            transaction.set_tag("is_ui_platform", is_ui_platform)
            transaction.set_tag("profile_type", "continuous")
            transaction.set_tag("synthetic_data", "true")
            transaction.set_tag("mock_duration_hours", str(MOCK_DURATION_HOURS))
            
            # Don't need CPU tasks - we're injecting synthetic samples
            time.sleep(0.1)
        
        # Force initial buffer creation if needed
        if not hasattr(scheduler, 'buffer') or not scheduler.buffer:
            scheduler.reset_buffer()
            buffer = scheduler.buffer
        
        # Track progress
        start_time = time.time()
        chunks_generated = 0
        total_samples_generated = 0
        coverage_percent = 0
        
        print(f"Target: {expected_chunks} chunks with coverage across all time windows")
        
        # Loop until we've generated enough chunks or reached a coverage threshold
        while chunks_generated < expected_chunks:
            # Directly inject synthetic samples into the buffer
            for i in range(10):  # Generate multiple samples per iteration
                # Generate a synthetic sample
                sample = generate_synthetic_profile_sample()
                
                # Get current monotonic time (used by buffer to determine flushing)
                monotonic_time = now()
                
                # Directly call buffer.write to process the sample with mocked timestamp
                if buffer:
                    buffer.write(monotonic_time, sample)
                    total_samples_generated += 1
            
            # Check current progress
            if buffer and hasattr(buffer, 'mock_flush_count') and hasattr(buffer, 'covered_windows') and hasattr(buffer, 'total_windows'):
                chunks_generated = buffer.mock_flush_count
                coverage_percent = (len(buffer.covered_windows) / buffer.total_windows) * 100
                
                # Report progress every 10 chunks
                if chunks_generated % 10 == 0 or (chunks_generated == expected_chunks):
                    elapsed = time.time() - start_time
                    print(f"Progress: Generated {chunks_generated}/{expected_chunks} chunks "
                          f"({coverage_percent:.1f}% window coverage), "
                          f"{total_samples_generated} samples, elapsed: {elapsed:.1f}s")
            
            # Force a buffer flush if needed to make progress
            if buffer and hasattr(buffer, 'buffer_size') and hasattr(buffer, 'start_monotonic_time'):
                if random.random() < 0.2:  # 20% chance to force a flush
                    # Simulate buffer full by setting monotonic time past buffer size
                    force_time = buffer.start_monotonic_time + buffer.buffer_size + 1
                    buffer.write(force_time, generate_synthetic_profile_sample())
            
            # Small delay to allow other processing
            time.sleep(0.01)
            
            # Break if we've reached target or timeout
            if (chunks_generated >= expected_chunks or coverage_percent >= 95 or 
                    (time.time() - start_time > 60)):  # 60 second timeout
                break
        
        # Final report
        elapsed = time.time() - start_time
        if buffer and hasattr(buffer, 'covered_windows') and hasattr(buffer, 'total_windows'):
            coverage_percent = (len(buffer.covered_windows) / buffer.total_windows) * 100
            
        print(f"\nSummary: Generated {chunks_generated} profile chunks "
              f"with {coverage_percent:.1f}% window coverage in {elapsed:.1f}s")
        print(f"Total samples generated: {total_samples_generated}")
        
        # Restore original sampler if needed
        if scheduler and original_sampler:
            scheduler.sampler = original_sampler
    
    else:
        # Standard profiling without mocking
        run_standard_profiling()
    
    # Stop the profiler
    print("Stopping profiler...")
    sentry_sdk.profiler.stop_profiler()
    print("Profile test completed")

def run_standard_profiling():
    """Run standard continuous profiling with real CPU tasks"""
    # Start the profiler
    sentry_sdk.profiler.start_profiler()
    
    # Run a series of transactions with errors and CPU-intensive tasks
    for i in range(3):
        with sentry_sdk.start_transaction(name=f"test-transaction-{i}") as transaction:
            # Add test tags
            is_ui_platform = PLATFORM in UI_PLATFORMS
            transaction.set_tag("ui_profile_test", is_ui_platform) 
            transaction.set_tag("is_ui_platform", is_ui_platform)
            transaction.set_tag("profile_type", "continuous")
            transaction.set_tag("platform_override", PLATFORM)
            
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
    
    # Without mocking, we need to run longer to collect meaningful data
    for i in range(10):
        cpu_intensive_task(300)
        if i % 2 == 0:
            print(f"Continuous profiling running... ({i+1}/10)")
        time.sleep(0.2)
    
def run_transaction_profile_test():
    """Run a test with transaction-based profiling"""
    print("\nStarting transaction profile test...")
    
    # When mocking timestamps, we can use synthetic data instead of CPU-intensive tasks
    if MOCK_TIMESTAMPS:
        print(f"Mock timestamps enabled: Will generate synthetic transaction profile")
        print(f"This will simulate a {MOCK_DURATION_HOURS}-hour transaction")
        
        # Create a transaction with synthetic data
        with sentry_sdk.start_transaction(name="synthetic-transaction") as transaction:
            # Add test tags to the transaction
            is_ui_platform = PLATFORM in UI_PLATFORMS
            transaction.set_tag("ui_profile_test", is_ui_platform)
            transaction.set_tag("is_ui_platform", is_ui_platform)
            transaction.set_tag("profile_type", "transaction")
            transaction.set_tag("platform_override", PLATFORM)
            transaction.set_tag("mock_duration_hours", str(MOCK_DURATION_HOURS))
            transaction.set_tag("synthetic_data", "true")
            
            # Add synthetic spans for realism
            for i in range(3):
                with Span(op=f"synthetic-span-{i}", description=f"Synthetic span #{i}"):
                    # No need for CPU tasks - just add synthetic measurements
                    transaction.set_measurement(f"synthetic_metric_{i}", i * 100, "millisecond")
                    time.sleep(0.05)  # Small delay for processing
            
            # Add a synthetic error
            try:
                raise ValueError("Synthetic error for mock profile")
            except Exception as e:
                capture_exception(e)
            
            # Access the profile directly to ensure it will be valid and has the mock duration
            scope = sentry_sdk.get_isolation_scope()
            if hasattr(scope, "profile") and scope.profile:
                current_profile = scope.profile
                
                # For transaction profiles, we need to directly inject synthetic samples
                # instead of using CPU tasks
                if DEBUG_PROFILING:
                    print(f"DEBUG: Injecting synthetic samples into transaction profile")
                
                # Add at least MINIMUM_SAMPLES + 10 synthetic samples
                # This will ensure the profile is valid without needing CPU tasks
                target_samples = max(MINIMUM_SAMPLES + 10, int(MOCK_DURATION_HOURS * 10))
                
                for i in range(target_samples):
                    # Generate offset for this sample (distribute across mock duration)
                    if i < 5:
                        # First few samples close to start
                        offset_ns = i * 1_000_000  # 1ms intervals
                    else:
                        # Distribute rest across mock duration
                        fraction = i / target_samples
                        offset_ns = int(fraction * MOCK_DURATION_HOURS * 3600 * 1_000_000_000)
                    
                    # Generate a synthetic sample
                    synthetic_sample = generate_synthetic_profile_sample()[0]
                    
                    # Extract the stack data
                    stack_data = synthetic_sample[1]
                    
                    # Write the sample to the profile with the calculated offset
                    current_profile.write(current_profile.start_ns + offset_ns, [synthetic_sample])
                
                if DEBUG_PROFILING:
                    print(f"DEBUG: Injected {target_samples} synthetic samples into transaction profile")
                    print(f"DEBUG: Profile now has {current_profile.unique_samples} unique samples")
                
            print(f"Generated synthetic transaction profile simulating {MOCK_DURATION_HOURS} hours")
            
    else:
        # Standard transaction profiling with real CPU tasks
        with sentry_sdk.start_transaction(name="test-transaction") as transaction:
            # Add test tags to the transaction
            transaction.set_tag("ui_profile_test", "true")
            transaction.set_tag("profile_type", "transaction")
            transaction.set_tag("platform_override", PLATFORM)
            
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
                
                duration_ms = 500 * (i + 1)
                
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
