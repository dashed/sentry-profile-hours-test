import sentry_sdk

sentry_sdk.init(
    dsn="https://3a076cacc3dd1cdc233d62f06f484acd@o4507289866010624.ingest.us.sentry.io/4508264505606144",
    traces_sample_rate=1.0,
)

sentry_sdk.profiler.start_profiler()

print("Hello from alberto!")

sentry_sdk.profiler.stop_profiler()

print("bye")
