#!/usr/bin/env python3
import sys
import traceback


# Test 1: Simple format string
try:
    test1 = f'JOB-{1:03d}-20250709123456'
    print(f'Test 1 passed: {test1}')
except Exception as e:
    print(f'Test 1 failed: {e}')
    traceback.print_exc()

# Test 2: With Decimal
try:
    from decimal import Decimal

    order = Decimal('0')
    test2 = f'JOB#{int(order):02d}#raw_analysis#{1:03d}#20250709123456'
    print(f'Test 2 passed: {test2}')
except Exception as e:
    print(f'Test 2 failed: {e}')
    traceback.print_exc()

# Test 3: Import the class
try:
    sys.path.append('scripts')
    from job_executor import TransformationJobExecutor

    print('Test 3 passed: Import successful')
except Exception as e:
    print(f'Test 3 failed: {e}')
    traceback.print_exc()

# Test 4: Create instance
try:
    executor = TransformationJobExecutor()
    print('Test 4 passed: Instance created')
except Exception as e:
    print(f'Test 4 failed: {e}')
    traceback.print_exc()

# Test 5: Test get_journey
try:
    executor = TransformationJobExecutor()
    journey = executor.get_journey('JRN-SAMPLE-001')
    print(f'Test 5 passed: Journey found: {journey is not None}')
except Exception as e:
    print(f'Test 5 failed: {e}')
    traceback.print_exc()

# Test 6: Start job execution (this might cause the format error)
try:
    job_id = executor.start_job_execution(
        'JRN-SAMPLE-001', 'raw_analysis', 'test', 'format string test'
    )
    print(f'Test 6 passed: Job started: {job_id}')
except Exception as e:
    print(f'Test 6 failed: {e}')
    traceback.print_exc()
