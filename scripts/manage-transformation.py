# manage_transformations.py
#!/usr/bin/env python3
import argparse
from job_executor import TransformationJobExecutor
from utils import TransformationUtils


def list_journeys():
    """List all transformation journeys"""
    utils = TransformationUtils()
    journeys = utils.list_journeys()

    if not journeys:
        print('No journeys found.')
        return

    print('\n📋 Transformation Journeys:')
    print('-' * 80)
    for journey in journeys:
        status_emoji = {
            'pending': '⏳',
            'running': '🏃',
            'completed': '✅',
            'failed': '❌',
            'paused': '⏸️',
        }.get(journey['status'], '❓')

        print(f'{status_emoji} {journey["journeyId"]}')
        print(f'   Name: {journey["name"]}')
        print(f'   Status: {journey["status"]} ({journey["progress"]}%)')
        print(f'   Current Stage: {journey.get("currentStage", "N/A")}')
        print(f'   Created: {journey.get("createdAt", "N/A")}')
        print()


def show_journey_status(journey_id: str):
    """Show detailed journey status"""
    utils = TransformationUtils()
    journey = utils.get_journey_status(journey_id)

    if not journey:
        print(f'Journey {journey_id} not found.')
        return

    print(f'\n📊 Journey Status: {journey_id}')
    print('-' * 60)
    print(f'Name: {journey["name"]}')
    print(f'Status: {journey["status"]}')
    print(f'Progress: {journey.get("overallProgress", 0)}%')
    print(f'Current Stage: {journey.get("currentStageId", "N/A")}')
    print(f'Created: {journey.get("createdAt")}')

    print('\n🎯 Current Jobs:')
    for stage_id, job_info in journey.get('currentJobs', {}).items():
        print(f'  {stage_id}: {job_info["jobId"]} ({job_info["status"]})')

    print('\n📈 Aggregates:')
    aggregates = journey.get('aggregates', {})
    print(f'  Total Jobs: {aggregates.get("totalJobs", 0)}')
    print(f'  Completed: {aggregates.get("completedJobs", 0)}')
    print(f'  Failed: {aggregates.get("failedJobs", 0)}')


def list_stage_jobs(journey_id: str, stage_id: str):
    """List job executions for a stage"""
    utils = TransformationUtils()
    jobs = utils.get_stage_jobs(journey_id, stage_id)

    if not jobs:
        print(f'No jobs found for stage {stage_id}.')
        return

    print(f'\n🔧 Jobs for Stage: {stage_id}')
    print('-' * 60)
    for job in jobs:
        status_emoji = {
            'pending': '⏳',
            'in_progress': '🏃',
            'completed': '✅',
            'failed': '❌',
        }.get(job['status'], '❓')

        print(f'{status_emoji} Execution #{job["executionNumber"]}: {job["jobId"]}')
        print(f'   Status: {job["status"]} ({job["progress"]}%)')
        print(f'   Started: {job["startTime"]}')
        if job.get('endTime'):
            print(f'   Completed: {job["endTime"]} (Duration: {job.get("duration")})')
        print()


def run_stage(journey_id: str, stage_id: str, triggered_by: str = 'cli'):
    """Run a stage execution"""
    executor = TransformationJobExecutor()

    try:
        print(f'🚀 Starting execution for stage: {stage_id}')

        job_id = executor.start_job_execution(
            journey_id=journey_id,
            stage_id=stage_id,
            triggered_by=triggered_by,
            reason='Manual execution via CLI',
        )

        print(f'✅ Job started: {job_id}')

        executor.execute_job(journey_id, job_id)

        print(f'🎉 Job {job_id} completed successfully!')

    except Exception as e:
        print(f'❌ Job execution failed: {str(e)}')


def download_files(journey_id: str, stage_id: str, job_id: str, step_id: str, file_type: str):
    """Download logs or reports"""
    utils = TransformationUtils()

    if file_type == 'logs':
        output_file = f'{job_id}_{step_id}_logs.json'
        utils.download_logs(journey_id, stage_id, job_id, step_id, output_file)
    elif file_type == 'reports':
        output_file = f'{job_id}_{step_id}_report.json'
        utils.download_report(journey_id, stage_id, job_id, step_id, output_file)
    else:
        print("Invalid file type. Use 'logs' or 'reports'.")


def main():
    parser = argparse.ArgumentParser(description='Manage Transformation System')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List journeys
    subparsers.add_parser('list', help='List all journeys')

    # Show journey status
    status_parser = subparsers.add_parser('status', help='Show journey status')
    status_parser.add_argument('journey_id', help='Journey ID')

    # List stage jobs
    jobs_parser = subparsers.add_parser('jobs', help='List jobs for a stage')
    jobs_parser.add_argument('journey_id', help='Journey ID')
    jobs_parser.add_argument('stage_id', help='Stage ID')

    # Run stage
    run_parser = subparsers.add_parser('run', help='Run a stage')
    run_parser.add_argument('journey_id', help='Journey ID')
    run_parser.add_argument('stage_id', help='Stage ID')
    run_parser.add_argument('--triggered-by', default='cli', help='Who triggered the execution')

    # Download files
    download_parser = subparsers.add_parser('download', help='Download logs or reports')
    download_parser.add_argument('journey_id', help='Journey ID')
    download_parser.add_argument('stage_id', help='Stage ID')
    download_parser.add_argument('job_id', help='Job ID')
    download_parser.add_argument('step_id', help='Step ID')
    download_parser.add_argument(
        'file_type', choices=['logs', 'reports'], help='File type to download'
    )

    args = parser.parse_args()

    if args.command == 'list':
        list_journeys()
    elif args.command == 'status':
        show_journey_status(args.journey_id)
    elif args.command == 'jobs':
        list_stage_jobs(args.journey_id, args.stage_id)
    elif args.command == 'run':
        run_stage(args.journey_id, args.stage_id, args.triggered_by)
    elif args.command == 'download':
        download_files(args.journey_id, args.stage_id, args.job_id, args.step_id, args.file_type)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
