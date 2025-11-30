#!/usr/bin/env python3
"""
Profile synthesis timing to identify if it's LLM API latency or code overhead
"""
import sys
import os
import time
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.agent_processor import agent_query
import uuid

def profile_synthesis():
    """Run quick test to profile synthesis timing"""
    print("=" * 70)
    print("🔍 Profiling Synthesis Timing")
    print("=" * 70)

    # Test with simple query
    query = "What is my EPS pension benefit?"
    user_id = "IN003"
    country = "IN"
    session_id = str(uuid.uuid4())[:8]

    print(f"\n📝 Query: {query}")
    print(f"👤 User: {user_id}")
    print(f"🌍 Country: {country}")
    print(f"\n⏱️  Starting test...\n")

    start_time = time.time()

    try:
        result = agent_query(
            user_id=user_id,
            session_id=session_id,
            country=country,
            query_string=query,
            validation_mode='llm_judge',
            enable_observability=True
        )

        elapsed = time.time() - start_time

        print(f"\n" + "=" * 70)
        print(f"⏱️  TOTAL TIME: {elapsed:.2f}s")
        print("=" * 70)

        # Extract synthesis timing
        synthesis_results = result.get('synthesis_results', [])
        if synthesis_results:
            total_synthesis_duration = sum(s.get('duration', 0) for s in synthesis_results)
            print(f"\n💡 Synthesis Details:")
            print(f"   Attempts: {len(synthesis_results)}")
            print(f"   Total Duration: {total_synthesis_duration:.2f}s")
            for i, s in enumerate(synthesis_results, 1):
                print(f"   Attempt {i}: {s.get('duration', 0):.2f}s ({s.get('output_tokens', 0)} tokens)")

        # Check if @mlflow.trace is adding overhead
        print(f"\n📊 Overhead Analysis:")
        print(f"   Total time: {elapsed:.2f}s")
        print(f"   Synthesis time: {total_synthesis_duration:.2f}s")
        print(f"   Other phases: {elapsed - total_synthesis_duration:.2f}s")

        # Check tracing overhead
        import inspect
        from src.agent_processor import agent_query as aq
        source = inspect.getsource(aq)
        if '@mlflow.trace' in source:
            print(f"\n⚠️  @mlflow.trace is ENABLED")
            print(f"   Expected overhead: 1-3 seconds")
            print(f"\n💡 To test without tracing:")
            print(f"   1. Comment out @mlflow.trace decorator in src/agent_processor.py:236")
            print(f"   2. Re-run this test")
            print(f"   3. Compare timings")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    profile_synthesis()
