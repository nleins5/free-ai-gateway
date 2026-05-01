import argparse
import asyncio
import json
import statistics
import time
from collections import Counter
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import httpx


@dataclass
class CallResult:
    ok: bool
    latency_ms: float
    provider: str
    model: str
    status_code: Optional[int]
    error: str


def percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * pct))
    return ordered[index]


def compact_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500]
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("error") or payload
        return json.dumps(detail, ensure_ascii=False)[:500]
    return json.dumps(payload, ensure_ascii=False)[:500]


async def one_call(
    client: httpx.AsyncClient,
    url: str,
    model: str,
    prompt: str,
    timeout_s: float,
) -> CallResult:
    started = time.perf_counter()
    try:
        response = await client.post(
            url,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
            timeout=timeout_s,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        error = "" if response.is_success else compact_error(response)
        return CallResult(
            ok=response.is_success,
            latency_ms=elapsed_ms,
            provider=response.headers.get("x-ai-provider", "unknown"),
            model=response.headers.get("x-ai-model", "unknown"),
            status_code=response.status_code,
            error=error,
        )
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return CallResult(
            ok=False,
            latency_ms=elapsed_ms,
            provider="error",
            model="unknown",
            status_code=None,
            error=f"{type(exc).__name__}: {exc}",
        )


async def fetch_router_state(base_url: str, timeout_s: float) -> Dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            response = await client.get(f"{base_url.rstrip('/')}/router/state")
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, dict) else {"value": payload}
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def summarize(
    results: List[CallResult],
    elapsed_s: float,
    router_state: Optional[Dict[str, Any]],
    show_errors: int,
) -> Dict[str, Any]:
    ok_latencies = [result.latency_ms for result in results if result.ok]
    failed = len(results) - len(ok_latencies)
    error_samples = [
        {
            "status_code": result.status_code,
            "provider": result.provider,
            "model": result.model,
            "error": result.error,
        }
        for result in results
        if not result.ok
    ][:show_errors]

    latency: Dict[str, Optional[float]] = {
        "min_ms": round(min(ok_latencies), 2) if ok_latencies else None,
        "avg_ms": round(statistics.mean(ok_latencies), 2) if ok_latencies else None,
        "p50_ms": round(percentile(ok_latencies, 0.50), 2) if ok_latencies else None,
        "p95_ms": round(percentile(ok_latencies, 0.95), 2) if ok_latencies else None,
        "p99_ms": round(percentile(ok_latencies, 0.99), 2) if ok_latencies else None,
        "max_ms": round(max(ok_latencies), 2) if ok_latencies else None,
    }

    summary: Dict[str, Any] = {
        "total_requests": len(results),
        "successful": len(ok_latencies),
        "failed": failed,
        "success_rate": round((len(ok_latencies) / len(results)) * 100.0, 2) if results else 0.0,
        "elapsed_s": round(elapsed_s, 2),
        "throughput_rps": round((len(results) / elapsed_s), 2) if elapsed_s > 0 else 0.0,
        "latency": latency,
        "providers": dict(Counter(result.provider for result in results if result.ok)),
        "models": dict(Counter(result.model for result in results if result.ok)),
        "status_codes": dict(Counter(str(result.status_code or "error") for result in results)),
        "error_samples": error_samples,
    }
    if router_state is not None:
        summary["router_state"] = router_state
    return summary


def print_summary(summary: Dict[str, Any]) -> None:
    print(f"Total requests: {summary['total_requests']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success rate: {summary['success_rate']:.2f}%")
    print(f"Elapsed seconds: {summary['elapsed_s']:.2f}")
    print(f"Throughput req/s: {summary['throughput_rps']:.2f}")

    latency = summary["latency"]
    if latency["avg_ms"] is not None:
        print("Latency ms:")
        print(f"  min: {latency['min_ms']:.2f}")
        print(f"  avg: {latency['avg_ms']:.2f}")
        print(f"  p50: {latency['p50_ms']:.2f}")
        print(f"  p95: {latency['p95_ms']:.2f}")
        print(f"  p99: {latency['p99_ms']:.2f}")
        print(f"  max: {latency['max_ms']:.2f}")
    else:
        print("Latency ms: no successful requests")

    print("Status codes:")
    for status, count in sorted(summary["status_codes"].items()):
        print(f"  - {status}: {count}")

    print("Provider distribution:")
    if summary["providers"]:
        for provider, count in sorted(summary["providers"].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {provider}: {count}")
    else:
        print("  - none")

    print("Model distribution:")
    if summary["models"]:
        for model, count in sorted(summary["models"].items(), key=lambda x: x[1], reverse=True):
            print(f"  - {model}: {count}")
    else:
        print("  - none")

    if summary["error_samples"]:
        print("Error samples:")
        for item in summary["error_samples"]:
            print(f"  - status={item['status_code'] or 'error'} provider={item['provider']} model={item['model']}: {item['error']}")

    router_state = summary.get("router_state")
    if router_state is not None:
        print("Router state:")
        if "error" in router_state:
            print(f"  unavailable: {router_state['error']}")
        else:
            state = router_state.get("state", {})
            print(f"  routing_mode: {router_state.get('routing_mode', 'unknown')}")
            print(f"  adaptive_routing: {router_state.get('adaptive_routing', 'unknown')}")
            print(f"  tracked_providers: {len(state) if isinstance(state, dict) else 0}")


async def run_benchmark(
    base_url: str,
    model: str,
    prompt: str,
    requests: int,
    concurrency: int,
    timeout_s: float,
    include_router_state: bool,
    show_errors: int,
) -> Dict[str, Any]:
    endpoint = f"{base_url.rstrip('/')}/v1/chat/completions"
    semaphore = asyncio.Semaphore(concurrency)
    results: List[CallResult] = []

    started = time.perf_counter()
    async with httpx.AsyncClient() as client:
        async def wrapped() -> None:
            async with semaphore:
                result = await one_call(client, endpoint, model, prompt, timeout_s)
                results.append(result)

        await asyncio.gather(*[wrapped() for _ in range(requests)])

    elapsed_s = time.perf_counter() - started
    router_state = await fetch_router_state(base_url, timeout_s) if include_router_state else None
    return summarize(results, elapsed_s, router_state, show_errors)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load test Free AI Gateway routing behavior.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--model", default="smart-chat")
    parser.add_argument("--prompt", default="Explain CAP theorem in one paragraph.")
    parser.add_argument("--requests", type=int, default=40)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    parser.add_argument("--show-errors", type=int, default=5, help="Number of representative failures to include.")
    parser.add_argument("--router-state", action="store_true", help="Fetch /router/state after the benchmark.")
    args = parser.parse_args()

    summary = asyncio.run(
        run_benchmark(
            base_url=args.base_url,
            model=args.model,
            prompt=args.prompt,
            requests=max(args.requests, 0),
            concurrency=max(args.concurrency, 1),
            timeout_s=args.timeout,
            include_router_state=args.router_state,
            show_errors=max(args.show_errors, 0),
        )
    )
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_summary(summary)


if __name__ == "__main__":
    main()
