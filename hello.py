import sentry_sdk
from sentry_sdk import capture_exception, capture_message
from sentry_sdk.tracing import Span, Transaction

sentry_sdk.init(
    dsn=(
        "https://3a076cacc3dd1cdc233d62f06f484acd@"
        "o4507289866010624.ingest.us.sentry.io/4508264505606144"
    ),
    traces_sample_rate=1.0,
    enable_tracing=True,
    # To set a uniform sample rate
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production,
    profiles_sample_rate=1.0,
)


def simulate_error():
    try:
        # Simulate a division by zero error
        1 / 0
    except Exception as e:
        capture_exception(e)


def create_test_transaction():
    # Start a new transaction
    transaction = Transaction(name="test-transaction", op="test")
    with transaction:
        # Create a child span
        with Span(op="child-operation", description="test-child-span"):
            print("Performing operation in span...")

        # Capture a message within the transaction
        capture_message("This is a test message within transaction")


def main():
    # Start the profiler
    sentry_sdk.profiler.start_profiler()

    print("Starting test events...")

    # Send test error
    simulate_error()

    # Create and send test transaction
    create_test_transaction()

    # Stop the profiler
    sentry_sdk.profiler.stop_profiler()

    print("Test events sent!")


if __name__ == "__main__":
    main()
