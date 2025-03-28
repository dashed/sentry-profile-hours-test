import random
import time

import sentry_sdk
from sentry_sdk import capture_exception, capture_message
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
from sentry_sdk.profiler.transaction_profiler import Profile
from sentry_sdk.tracing import Span

# Save original methods - we'll patch these to modify the platform
original_profile_to_json = Profile.to_json
original_profile_chunk_to_json = ProfileChunk.to_json
original_add_profile_chunk = Envelope.add_profile_chunk

PLATFORM = "javascript"

# Create patched methods that set platform to PLATFORM
def patched_profile_to_json(self, event_opt, options):
    result = original_profile_to_json(self, event_opt, options)
    if result.get("platform") == "python":
        print(f"DEBUG: Changing Profile platform from 'python' to '{PLATFORM}'")
    # Force platform to PLATFORM (which is in UI_PROFILE_PLATFORMS)
    # This affects regular profiles (not continuous profiling chunks)
    result["platform"] = PLATFORM
    return result


def patched_profile_chunk_to_json(self, profiler_id, options, sdk_info):
    result = original_profile_chunk_to_json(self, profiler_id, options, sdk_info)
    # Critical: override platform in ProfileChunk payload
    # This is what Sentry uses to categorize as UI_PROFILE_PLATFORMS
    # and track as PROFILE_DURATION_UI
    if result.get("platform") != PLATFORM:
        print(f"DEBUG: Changing ProfileChunk platform from '{result.get('platform')}' to '{PLATFORM}'")
    # Must be one of UI_PROFILE_PLATFORMS = {"cocoa", "android", "javascript"}
    # See sentry/profiles/task.py:UI_PROFILE_PLATFORMS
    result["platform"] = PLATFORM
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


# Apply the patches
Profile.to_json = patched_profile_to_json
ProfileChunk.to_json = patched_profile_chunk_to_json
Envelope.add_profile_chunk = patched_add_profile_chunk

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
def cpu_intensive_task():
    result = 0
    for i in range(1000000):
        result += i
    return result


# Start the profiler
sentry_sdk.profiler.start_profiler()


def verify_profile_platform(profile):
    """
    Verify the platform in a profile chunk is correctly set to '{PLATFORM}'.
    This is a helper function to validate our monkey patching is working correctly.
    """
    if isinstance(profile, dict):
        platform = profile.get("platform")
        if platform != PLATFORM:
            print(f"WARNING: Profile platform is '{platform}', not '{PLATFORM}'")
        else:
            print(f"SUCCESS: Profile platform correctly set to '{platform}'")
    return profile

def main():
    try:
        # Verify our patches are working by checking the platform in ProfileChunk
        # Patch the to_json method to include our verification
        original_chunk_to_json = ProfileChunk.to_json
        
        def verified_to_json(self, profiler_id, options, sdk_info):
            result = original_chunk_to_json(self, profiler_id, options, sdk_info)
            return verify_profile_platform(result)
            
        ProfileChunk.to_json = verified_to_json
        
        print("=" * 50)
        print("PROFILE HOURS TEST SCRIPT")
        print("This script tests UI profile hours (PROFILE_DURATION_UI) by spoofing")
        print(f"the platform to '{PLATFORM}' (one of UI_PROFILE_PLATFORMS)")
        print("=" * 50)
        
        while True:  # Infinite loop
            # Start the profiler
            sentry_sdk.profiler.start_profiler()

            with sentry_sdk.start_transaction(name="test-transaction"):

                print("\nStarting test events...")

                with Span(op="child-operation", description="test-child-span"):
                    # Send test error
                    simulate_error()

                # Create and send test transaction
                create_test_transaction()

                # Run CPU intensive task multiple times or for longer duration
                for _ in range(50):  # Run multiple iterations
                    cpu_intensive_task()
                    time.sleep(
                        0.05 + random.uniform(0, 0.05)
                    )  # Add small delays with jitter between iterations

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
