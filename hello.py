import random
import time

import sentry_sdk
from sentry_sdk import capture_exception, capture_message
from sentry_sdk.tracing import Span

sentry_sdk.init(
    # https://daily-habits-ben-coe-test-orga.sentry.io/profiling/?project=4508264924315648
    dsn="https://99f7769e482e93064d3d51feac4e2093@o4506956365430784.ingest.us.sentry.io/4508264924315648",
    # dsn=(
    #     "https://3a076cacc3dd1cdc233d62f06f484acd@"
    #     "o4507289866010624.ingest.us.sentry.io/4508264505606144"
    # ),
    # https://testorg-am3launch-am3-team.sentry.io/settings/projects/alberto-rust/keys/
    # dsn="https://b52904e72a72c0ed8d3996cafe40d4af@o4507289623330816.ingest.us.sentry.io/4507352301240320",
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
