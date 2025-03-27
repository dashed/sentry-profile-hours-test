import random
import time

import sentry_sdk
from sentry_sdk import capture_exception, capture_message
from sentry_sdk.tracing import Span

# Define available DSNs
DSN_DAILY_HABITS = (
    "https://99f7769e482e93064d3d51feac4e2093@"
    "o4506956365430784.ingest.us.sentry.io/4508264924315648"
)  # daily-habits-ben-coe-test-orga

DSN_ALTERNATIVE = (
    "https://3a076cacc3dd1cdc233d62f06f484acd@"
    "o4507289866010624.ingest.us.sentry.io/4508264505606144"
)

DSN_ALBERTO_RUST = (
    "https://b52904e72a72c0ed8d3996cafe40d4af@"
    "o4507289623330816.ingest.us.sentry.io/4507352301240320"
)  # testorg-am3launch-am3-team

# Dictionary of available DSNs - add new ones here
AVAILABLE_DSNS = {
    # Old orgs
    "daily_habits": DSN_DAILY_HABITS,
    "alternative": DSN_ALTERNATIVE,
    "alberto_rust": DSN_ALBERTO_RUST,
    "testorg-am3launch-am2-team": "https://aa95ea1dd9e58651693d3e8055d2cd69@o4507289522733056.ingest.us.sentry.io/4508298575020032",
    # Current orgs
    "profile-hours-am2-team": "https://c9275450b3c73d2e984beee5aab20689@o4508486227722240.ingest.us.sentry.io/4508616529346560",
    "profile-hours-am3-team": "https://c523b2b6fbf35cd224884b8f3538cf13@o4508486283952128.ingest.us.sentry.io/4508486284738560",
}

sentry_sdk.init(
    dsn=AVAILABLE_DSNS["profile-hours-am2-team"],
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    debug=True,
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
