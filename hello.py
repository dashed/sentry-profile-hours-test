import random
import time

import sentry_sdk
from sentry_sdk import capture_exception, capture_message
from sentry_sdk.tracing import Span

# Dictionary of available DSNs - add new ones here
AVAILABLE_DSNS = {
    "profile-hours-am2-business": "https://b700116ce3eadd661071ad84ed45028b@o4508486249218048.ingest.us.sentry.io/4508486249938944",
    "profile-hours-am3-business": "https://e3be3e9fd4c48a23b3a65ec2e62743d1@o4508486299942912.ingest.de.sentry.io/4508486300729424",
}


# Define a before_send hook to modify the platform
def before_send(event, hint):
    # Change the platform to whatever you need for testing
    # See UI_PROFILE_PLATFORMS
    # https://github.com/getsentry/sentry/blob/c3420bc3a670ba88cb37b9a40ceede748cafdf50/src/sentry/profiles/task.py#L47
    #
    # Comment out for profile hours (PROFILE_DURATION)
    event["platform"] = "android"
    return event


def profiles_sampler(sampling_context):
    return 1.0


sentry_sdk.init(
    dsn=AVAILABLE_DSNS["profile-hours-am2-business"],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    profile_session_sample_rate=1.0,
    profiles_sample_rate=1.0,
    debug=True,
    before_send=before_send,  # Add before_send hook to modify the platform
    _experiments={
        "continuous_profiling_auto_start": True,
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


def main():
    try:
        while True:  # Infinite loop
            # Start the profiler
            sentry_sdk.profiler.start_profiler()

            with sentry_sdk.start_transaction(name="test-transaction"):

                print("Starting test events...")

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

    except KeyboardInterrupt:
        print("\nShutting down gracefully...")


if __name__ == "__main__":
    main()
