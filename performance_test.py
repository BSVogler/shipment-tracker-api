#!/usr/bin/env python3
"""Performance test script for shipment API."""

import asyncio
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import requests
import argparse
from typing import List, Tuple
import json


class PerformanceTester:
    """Performance test runner for shipment API."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def get_shipment(self, tracking_number: str, include_weather: bool = True) -> Tuple[float, int, dict]:
        """Get a single shipment and return response time, status code, and data."""
        start_time = time.time()
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/shipments/{tracking_number}",
                params={"include_weather": include_weather}
            )
            response_time = time.time() - start_time
            return response_time, response.status_code, response.json() if response.status_code == 200 else {}
        except Exception as e:
            response_time = time.time() - start_time
            return response_time, 0, {"error": str(e)}
    
    def run_concurrent_requests(self, tracking_numbers: List[str], 
                              num_workers: int = 10, 
                              include_weather: bool = True) -> dict:
        """Run concurrent requests and collect metrics."""
        response_times = []
        successful_requests = 0
        failed_requests = 0
        errors = []
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit all tasks
            futures = []
            for tn in tracking_numbers:
                future = executor.submit(self.get_shipment, tn, include_weather)
                futures.append(future)
            
            # Collect results
            for future in futures:
                response_time, status_code, data = future.result()
                response_times.append(response_time)
                
                if status_code == 200:
                    successful_requests += 1
                else:
                    failed_requests += 1
                    if "error" in data:
                        errors.append(data["error"])
        
        total_time = time.time() - start_time
        
        return {
            "total_requests": len(tracking_numbers),
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "total_time": total_time,
            "requests_per_second": len(tracking_numbers) / total_time,
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "median_response_time": statistics.median(response_times),
            "p95_response_time": statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times),
            "p99_response_time": statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times),
            "errors": errors[:5]  # Show first 5 errors
        }
    
    def run_performance_test(self, duration_seconds: int = 60, 
                           num_workers: int = 50,
                           include_weather: bool = True) -> dict:
        """Run performance test for specified duration."""
        # Get available tracking numbers
        tracking_numbers = [
            "TN12345678", "TN12345679", "TN12345680", 
            "TN12345681", "TN12345682"
        ]
        
        print(f"Running performance test for {duration_seconds} seconds with {num_workers} workers...")
        print(f"Weather API calls: {'Enabled' if include_weather else 'Disabled'}")
        
        all_metrics = []
        requests_sent = 0
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            # Create a larger batch of requests for higher throughput
            batch_size = num_workers * 20  # Increased from 5 to 20
            batch = [tracking_numbers[i % len(tracking_numbers)] for i in range(batch_size)]
            
            # Run batch
            metrics = self.run_concurrent_requests(batch, num_workers, include_weather)
            all_metrics.append(metrics)
            requests_sent += batch_size
            
            # Much shorter pause to maximize throughput
            time.sleep(0.01)  # Reduced from 0.1 to 0.01 seconds
        
        # Calculate overall statistics
        total_successful = sum(m["successful_requests"] for m in all_metrics)
        total_failed = sum(m["failed_requests"] for m in all_metrics)
        all_response_times = []
        for m in all_metrics:
            batch_size = m["total_requests"]
            # Approximate individual response times from batch metrics
            all_response_times.extend([m["avg_response_time"]] * batch_size)
        
        overall_duration = time.time() - start_time
        
        return {
            "test_duration": overall_duration,
            "total_requests": requests_sent,
            "successful_requests": total_successful,
            "failed_requests": total_failed,
            "overall_rps": requests_sent / overall_duration,
            "avg_response_time": statistics.mean(all_response_times) if all_response_times else 0,
            "num_workers": num_workers,
            "weather_enabled": include_weather
        }


def main():
    parser = argparse.ArgumentParser(description="Performance test for shipment API")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--workers", type=int, default=50, help="Number of concurrent workers")
    parser.add_argument("--no-weather", action="store_true", help="Disable weather API calls")
    parser.add_argument("--quick", action="store_true", help="Run a quick test (10 seconds)")
    parser.add_argument("--extreme", action="store_true", help="Run extreme load test (200 workers)")
    
    args = parser.parse_args()
    
    # Adjust parameters for extreme mode
    if args.extreme:
        workers = 200
        print("🔥 EXTREME MODE: Very high concurrency!")
    else:
        workers = args.workers
    
    tester = PerformanceTester(args.url)
    
    # Check if API is available
    try:
        response = requests.get(f"{args.url}/health")
        if response.status_code != 200:
            print(f"Error: API health check failed with status {response.status_code}")
            return
    except Exception as e:
        print(f"Error: Cannot connect to API at {args.url}: {e}")
        return
    
    duration = 10 if args.quick else args.duration
    include_weather = not args.no_weather
    
    # Run performance test
    results = tester.run_performance_test(duration, workers, include_weather)
    
    # Print results
    print("\n" + "="*60)
    print("PERFORMANCE TEST RESULTS")
    print("="*60)
    print(f"Test Duration: {results['test_duration']:.2f} seconds")
    print(f"Total Requests: {results['total_requests']}")
    print(f"Successful Requests: {results['successful_requests']}")
    print(f"Failed Requests: {results['failed_requests']}")
    print(f"Workers: {results['num_workers']}")
    print(f"Weather API: {'Enabled' if results['weather_enabled'] else 'Disabled'}")
    print("-"*60)
    print(f"Requests per Second: {results['overall_rps']:.2f}")
    print(f"Average Response Time: {results['avg_response_time']*1000:.2f} ms")
    print("="*60)
    
    # Run comparison test without weather if it was enabled
    if include_weather:
        print("\nRunning comparison test without weather API...")
        results_no_weather = tester.run_performance_test(duration, workers, False)
        
        print("\n" + "="*60)
        print("COMPARISON RESULTS")
        print("="*60)
        print("Metric                 | With Weather | Without Weather | Difference")
        print("-"*70)
        print(f"Requests per Second    | {results['overall_rps']:>12.2f} | {results_no_weather['overall_rps']:>15.2f} | {(results_no_weather['overall_rps'] - results['overall_rps']) / results['overall_rps'] * 100:>+8.1f}%")
        print(f"Avg Response Time (ms) | {results['avg_response_time']*1000:>12.2f} | {results_no_weather['avg_response_time']*1000:>15.2f} | {(results_no_weather['avg_response_time'] - results['avg_response_time']) / results['avg_response_time'] * -100:>+8.1f}%")
        print("="*60)


if __name__ == "__main__":
    main()