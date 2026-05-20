import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential


def _is_retryable_http_error(exc: BaseException) -> bool:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500
    return isinstance(exc, (httpx.TimeoutException, httpx.NetworkError))


network_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, max=4),
    retry=retry_if_exception(_is_retryable_http_error),
    reraise=True,
)


__all__ = ["network_retry"]
