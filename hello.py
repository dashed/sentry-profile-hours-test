import time

import sentry_sdk
from sentry_sdk import capture_exception, capture_message
from sentry_sdk.tracing import Span, Transaction

sentry_sdk.init(
    dsn="https://3a076cacc3dd1cdc233d62f06f484acd@o4507289866010624.ingest.us.sentry.io/4508264505606144",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    debug=True,
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


def main():
    with sentry_sdk.start_transaction(name="test-transaction"):
        # Start the profiler
        sentry_sdk.profiler.start_profiler()

        print("Starting test events...")

        # Send test error
        simulate_error()

        # Create and send test transaction
        create_test_transaction()

        # Run CPU intensive task multiple times or for longer duration
        for _ in range(50):  # Run multiple iterations
            cpu_intensive_task()
            time.sleep(0.05)  # Add small delays between iterations

        # Stop the profiler
        sentry_sdk.profiler.stop_profiler()

        print("Test events sent!")

        # Add delay before exit to ensure events are sent
        # time.sleep(3)


if __name__ == "__main__":
    main()
