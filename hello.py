import random
import time
import uuid
from datetime import datetime, timezone

import sentry_sdk
from sentry_sdk import capture_exception, capture_message, set_tag
from sentry_sdk.envelope import Envelope, Item, PayloadRef
from sentry_sdk.profiler.continuous_profiler import ProfileChunk

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
from sentry_sdk.tracing import Span

# Save original methods - we'll patch these to modify the platform
original_profile_to_json = Profile.to_json
original_profile_chunk_to_json = ProfileChunk.to_json
original_add_profile_chunk = Envelope.add_profile_chunk
original_profile_valid = Profile.valid

PLATFORM = "javascript"

# Create patched methods that set platform to PLATFORM
def patched_profile_to_json(self, event_opt, options):
    result = original_profile_to_json(self, event_opt, options)
    orig_platform = result.get("platform")
    if orig_platform == "python":
        print(f"DEBUG: Changing Profile platform from '{orig_platform}' to '{PLATFORM}'")
    # Force platform to PLATFORM (which is in UI_PROFILE_PLATFORMS)
    # This affects regular profiles (not continuous profiling chunks)
    result["platform"] = PLATFORM
    
    # Add debugging tags to help identify these profiles in Sentry
    result["tags"] = result.get("tags", {})
    result["tags"]["profile_spoof"] = "true"
    result["tags"]["original_platform"] = orig_platform
    return result


def patched_profile_chunk_to_json(self, profiler_id, options, sdk_info):
    result = original_profile_chunk_to_json(self, profiler_id, options, sdk_info)
    # Critical: override platform in ProfileChunk payload
    # This is what Sentry uses to categorize as UI_PROFILE_PLATFORMS
    # and track as PROFILE_DURATION_UI
    orig_platform = result.get("platform")
    if orig_platform != PLATFORM:
        print(f"DEBUG: Changing ProfileChunk platform from '{orig_platform}' to '{PLATFORM}'")
    # Must be one of UI_PROFILE_PLATFORMS = {"cocoa", "android", "javascript"}
    # See sentry/profiles/task.py:UI_PROFILE_PLATFORMS
    result["platform"] = PLATFORM
    
    # Add additional debugging fields to the profile chunk
    # These won't affect processing but help with debugging
    result["debug_info"] = {
        "original_platform": orig_platform,
        "spoofed_platform": PLATFORM,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_id": str(uuid.uuid4())[:8]
    }
    
    # Add tags if possible (may not be used in processing)
    if not result.get("tags"):
        result["tags"] = {}
    result["tags"]["profile_debug"] = "true"
    
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


# Patch Profile.valid to bypass the minimum samples check
def patched_profile_valid(self):
    client = sentry_sdk.get_client()
    if not client.is_active():
        print("DEBUG: Profile invalid - client not active")
        return False

    # Check if profiling is enabled in options
    if not sentry_sdk.profiler.transaction_profiler.has_profiling_enabled(client.options):
        print("DEBUG: Profile invalid - profiling not enabled in options")
        return False

    if self.sampled is None or not self.sampled:
        if client.transport:
            client.transport.record_lost_event(
                "sample_rate", data_category="profile"
            )
        print("DEBUG: Profile invalid - not sampled")
        return False
    
    # Check if we have enough samples
    if self.unique_samples < PROFILE_MINIMUM_SAMPLES:
        print(f"DEBUG: Profile has only {self.unique_samples} samples (minimum is {PROFILE_MINIMUM_SAMPLES})")
        
        # Instead of discarding due to insufficient samples, add fake samples
        print("DEBUG: Adding fake samples to reach minimum requirement...")
        
        # Only add fake samples if there's at least one real sample
        if self.unique_samples > 0 and self.samples:
            # Get the last sample as a template for fake samples
            if len(self.samples) > 0:
                last_sample = self.samples[-1]
                
                # Number of fake samples needed
                samples_needed = PROFILE_MINIMUM_SAMPLES - self.unique_samples
                
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
                
                print(f"DEBUG: Added {samples_needed} fake samples, now have {self.unique_samples} samples")
            else:
                print("WARNING: Can't add fake samples - no existing samples to use as template")
        else:
            print("WARNING: Can't add fake samples - no existing samples at all")
    
    print(f"DEBUG: Profile valid with {self.unique_samples} samples")
    return True

# Apply the patches
Profile.to_json = patched_profile_to_json
ProfileChunk.to_json = patched_profile_chunk_to_json
Envelope.add_profile_chunk = patched_add_profile_chunk
Profile.valid = patched_profile_valid

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


sentry_sdk.init(
    dsn=AVAILABLE_DSNS["profile-hours-am3-business"],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profiles_sample_rate=1.0,
    debug=True,
    before_send=before_send,  # Add before_send hook to modify the platform
    _experiments={
        "continuous_profiling_auto_start": True,
        "continuous_profiling_debug": True,  # Enable debug for more verbose output
    },
)


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
        # Verify our patches are working by checking the platform in ProfileChunk
        # Patch the to_json method to include our verification
        original_chunk_to_json = ProfileChunk.to_json
        
        def verified_to_json(self, profiler_id, options, sdk_info):
            result = original_chunk_to_json(self, profiler_id, options, sdk_info)
            return verify_profile_platform(result)
            
        ProfileChunk.to_json = verified_to_json
        
        # Add a write hook to monitor samples as they're being collected
        original_profile_write = Profile.write
        
        def monitored_write(self, ts, sample):
            # Call original method
            original_profile_write(self, ts, sample)
            # Print sample count after each sample
            if self.unique_samples > 0 and self.unique_samples % 5 == 0:
                print(f"DEBUG: Profile now has {self.unique_samples} samples")
        
        # Apply the monitored write patch
        Profile.write = monitored_write
        
        # Increase sampling frequency to get more profile samples
        increase_sampling_frequency()
        
        print("=" * 50)
        print("PROFILE HOURS TEST SCRIPT")
        print("This script tests UI profile hours (PROFILE_DURATION_UI) by spoofing")
        print(f"the platform to '{PLATFORM}' (one of UI_PROFILE_PLATFORMS)")
        print("=" * 50)
        
        while True:  # Infinite loop
            # Start the profiler
            sentry_sdk.profiler.start_profiler()

            with sentry_sdk.start_transaction(name="test-transaction") as transaction:
                # Add test tags to the transaction
                transaction.set_tag("ui_profile_test", "true")
                transaction.set_tag("platform_override", PLATFORM)
                
                print("\nStarting test events...")

                with Span(op="child-operation", description="test-child-span") as span:
                    # Add tags to span too
                    span.set_tag("ui_profile_test", "true")
                    # Send test error
                    simulate_error()

                # Create and send test transaction
                create_test_transaction()

                # Run CPU intensive task to generate sufficient profile samples
                print("Running CPU intensive tasks to generate profile samples...")
                
                # Run fewer iterations but each one runs longer
                for i in range(3):  # Run 3 iterations of increasingly long durations
                    # Set measurement to show in profile
                    transaction.set_measurement(f"ui_test_{i}", i * 10, "millisecond")
                    
                    # Increase duration for each iteration to ensure we get samples
                    # Start with 500ms and increase each time
                    duration_ms = 500 * (i + 1)
                    print(f"Starting CPU intensive task {i+1}/3 (duration: {duration_ms}ms)...")
                    
                    # Run the CPU intensive task with a specific duration
                    cpu_intensive_task(duration_ms=duration_ms)
                    
                    # Add delay between iterations for pacing
                    time.sleep(0.2)  # Short delay between iterations
                    
                # Check if the current transaction's profile has enough samples
                scope = sentry_sdk.get_isolation_scope()
                if hasattr(scope, "profile") and scope.profile:
                    current_profile = scope.profile
                    print(f"DEBUG: Current profile has {current_profile.unique_samples} samples")
                    
                    # If not enough samples, force add some
                    if current_profile.unique_samples < PROFILE_MINIMUM_SAMPLES:
                        print(f"DEBUG: Adding more samples to ensure minimum of {PROFILE_MINIMUM_SAMPLES}")
                        add_extra_profile_samples(current_profile)
                else:
                    print("WARNING: Could not find active profile in current scope")

                print("Test events sent!")

            # Stop the profiler
            sentry_sdk.profiler.stop_profiler()
            
            # Delay between iterations
            print("\nWaiting 5 seconds before next iteration...\n")
            time.sleep(5)

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")


if __name__ == "__main__":
    main()
