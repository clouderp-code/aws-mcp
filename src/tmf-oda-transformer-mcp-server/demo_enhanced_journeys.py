#!/usr/bin/env python3
"""
Comprehensive Demo of Enhanced TMF ODA Journey Lifecycle Management

This demo showcases all the enhanced capabilities of the journeys MCP tool
that now provides comprehensive lifecycle management similar to manage_journey.py:

Features Demonstrated:
1. Journey CRUD Operations
2. Stage Management (add, update, delete, list)
3. Second Brain Rules Management
4. Job Lifecycle Management
5. Logs and Reports Management
6. Interactive Dashboards
7. Performance Analysis
8. Error Analysis and Insights
9. Import/Export Functionality

Usage:
    python3 demo_enhanced_journeys.py
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, Any

# Mock MCP context for demonstration
class MockContext:
    def __init__(self):
        self.errors = []
    
    async def error(self, message: str):
        self.errors.append(message)
        print(f"❌ Error: {message}")

async def demo_journey_crud():
    """Demo basic journey CRUD operations."""
    print("\n" + "=" * 80)
    print("🏗️ DEMO: JOURNEY CRUD OPERATIONS")
    print("=" * 80)
    
    # Import the enhanced journeys tool
    from awslabs.tmf_oda_transformer_mcp_server.tools.management_tools import journeys_tool
    
    ctx = MockContext()
    
    # 1. Create a new journey
    print("\n1️⃣ Creating a new journey...")
    journey_data = {
        "name": "Demo Customer Management Transformation",
        "description": "Comprehensive demo of customer database transformation to TMF ODA",
        "oda_component_type": "customer-management",
        "priority": "high",
        "source_type": "database"
    }
    
    result = await journeys_tool(
        ctx=ctx,
        action="create",
        journey_data=journey_data
    )
    
    if result['status'] == 'success':
        journey_id = result['journey_id']
        print(f"✅ Journey created: {journey_id}")
        print(f"   Name: {journey_data['name']}")
        print(f"   Component: {journey_data['oda_component_type']}")
    else:
        print(f"❌ Failed to create journey: {result.get('message', 'Unknown error')}")
        return None
    
    # 2. List all journeys
    print("\n2️⃣ Listing all journeys...")
    result = await journeys_tool(
        ctx=ctx,
        action="list"
    )
    
    if result['status'] == 'success':
        journeys = result.get('journeys', [])
        print(f"✅ Found {len(journeys)} journeys:")
        for journey in journeys[:3]:  # Show first 3
            print(f"   📋 {journey.get('journeyId', 'N/A')}: {journey.get('name', 'N/A')}")
    
    # 3. Get journey details
    print("\n3️⃣ Getting journey details...")
    result = await journeys_tool(
        ctx=ctx,
        action="read",
        journey_id=journey_id,
        include_stages=True,
        include_job_history=True
    )
    
    if result['status'] == 'success':
        print(f"✅ Journey details retrieved:")
        print(f"   📊 Status: {result.get('status', 'N/A')}")
        print(f"   📈 Progress: {result.get('overall_progress', 0)}%")
        print(f"   📋 Current Stage: {result.get('current_stage', 'N/A')}")
    
    # 4. Update journey
    print("\n4️⃣ Updating journey...")
    update_data = {
        "description": "Updated demo description with enhanced capabilities",
        "status": "running",
        "overall_progress": 25
    }
    
    result = await journeys_tool(
        ctx=ctx,
        action="update",
        journey_id=journey_id,
        journey_data=update_data
    )
    
    if result['status'] == 'success':
        print(f"✅ Journey updated successfully")
        print(f"   📝 New description: {update_data['description']}")
        print(f"   📊 New status: {update_data['status']}")
    
    return journey_id


async def demo_stage_management(journey_id: str):
    """Demo stage management operations."""
    print("\n" + "=" * 80)
    print("📋 DEMO: STAGE MANAGEMENT OPERATIONS")
    print("=" * 80)
    
    from awslabs.tmf_oda_transformer_mcp_server.tools.management_tools import journeys_tool
    ctx = MockContext()
    
    # 1. Add default stages
    print("\n1️⃣ Adding default transformation stages...")
    result = await journeys_tool(
        ctx=ctx,
        action="add_default_stages",
        journey_id=journey_id
    )
    
    if result['status'] == 'success':
        stages_added = result.get('stages_added', [])
        print(f"✅ Added {len(stages_added)} default stages:")
        for stage in stages_added:
            print(f"   📋 {stage}")
    
    # 2. List stages
    print("\n2️⃣ Listing all stages...")
    result = await journeys_tool(
        ctx=ctx,
        action="list_stages",
        journey_id=journey_id
    )
    
    if result['status'] == 'success':
        stages = result.get('stages', [])
        print(f"✅ Found {len(stages)} stages:")
        for stage in stages:
            ai_indicator = "🤖" if stage.get('second_brain_enabled') else "🔧"
            print(f"   {ai_indicator} {stage.get('name', 'N/A')} ({stage.get('estimated_duration', 'N/A')})")
    
    # 3. Add custom stage
    print("\n3️⃣ Adding custom stage...")
    custom_stage = {
        "stage_id": "custom_demo_stage",
        "name": "Custom Demo Stage",
        "description": "A custom stage for demonstration purposes",
        "order": 99,
        "estimated_duration": "5m",
        "can_skip": True,
        "second_brain_enabled": True,
        "rule_types": ["contextual_recommendations", "data_interpretation"],
        "steps": [
            {
                "id": "demo_step_1",
                "name": "Demo Step 1",
                "description": "First demo step",
                "order": 0,
                "estimated_duration": "2m",
                "ai_assisted": True,
                "applicable_rules": ["contextual_recommendations"]
            },
            {
                "id": "demo_step_2", 
                "name": "Demo Step 2",
                "description": "Second demo step",
                "order": 1,
                "estimated_duration": "3m",
                "ai_assisted": True,
                "applicable_rules": ["data_interpretation"]
            }
        ]
    }
    
    result = await journeys_tool(
        ctx=ctx,
        action="add_stage",
        journey_id=journey_id,
        stage_data=custom_stage
    )
    
    if result['status'] == 'success':
        print(f"✅ Custom stage added: {custom_stage['stage_id']}")
        print(f"   📋 Name: {custom_stage['name']}")
        print(f"   🔧 Steps: {len(custom_stage['steps'])}")
    
    # 4. Update stage
    print("\n4️⃣ Updating custom stage...")
    stage_update = {
        "description": "Updated demo stage with enhanced functionality",
        "estimated_duration": "8m"
    }
    
    result = await journeys_tool(
        ctx=ctx,
        action="update_stage",
        journey_id=journey_id,
        stage_id="custom_demo_stage",
        stage_data=stage_update
    )
    
    if result['status'] == 'success':
        print(f"✅ Stage updated successfully")


async def demo_rules_management(journey_id: str):
    """Demo Second Brain rules management."""
    print("\n" + "=" * 80)
    print("🧠 DEMO: SECOND BRAIN RULES MANAGEMENT")
    print("=" * 80)
    
    from awslabs.tmf_oda_transformer_mcp_server.tools.management_tools import journeys_tool
    ctx = MockContext()
    
    # 1. List existing rules
    print("\n1️⃣ Listing existing rules...")
    result = await journeys_tool(
        ctx=ctx,
        action="list_rules",
        journey_id=journey_id
    )
    
    if result['status'] == 'success':
        rules = result.get('rules', [])
        print(f"✅ Found {len(rules)} existing rules:")
        for rule in rules:
            print(f"   🧠 {rule.get('title', 'N/A')} ({rule.get('type', 'N/A')}, {rule.get('priority', 'N/A')})")
    
    # 2. Add custom rule
    print("\n2️⃣ Adding custom Second Brain rule...")
    custom_rule = {
        "title": "Customer ID Field Mapping Demo Rule",
        "description": "Demo rule for mapping customer ID fields to TMF Party.id",
        "type": "field_mapping",
        "priority": "high",
        "scope": "global",
        "context": {
            "applies_to": ["customer", "party", "account"],
            "conditions": [
                {"field_name_contains": "customer_id"},
                {"field_name_contains": "cust_id"}
            ],
            "prerequisites": []
        },
        "content": {
            "natural_language": "Map any field containing 'customer_id' or 'cust_id' to TMF Party.id field",
            "json_rule": {
                "field_mapping": {
                    "source_patterns": ["*customer_id*", "*cust_id*"],
                    "target_field": "Party.id",
                    "transformation": "direct_mapping"
                }
            },
            "examples": [
                "customer_id -> Party.id",
                "cust_id -> Party.id",
                "customer_identifier -> Party.id"
            ]
        },
        "created_by": "demo-user",
        "version": "1.0",
        "tags": ["customer", "mapping", "demo"]
    }
    
    result = await journeys_tool(
        ctx=ctx,
        action="add_rule",
        journey_id=journey_id,
        stage_id="raw_analysis",
        rule_data=custom_rule
    )
    
    if result['status'] == 'success':
        rule_id = result.get('rule_id', 'N/A')
        print(f"✅ Custom rule added: {rule_id}")
        print(f"   🧠 Title: {custom_rule['title']}")
        print(f"   📋 Type: {custom_rule['type']}")
        print(f"   ⚡ Priority: {custom_rule['priority']}")
    
    # 3. Update rule
    print("\n3️⃣ Updating rule...")
    rule_update = {
        "description": "Enhanced demo rule with additional mapping patterns",
        "priority": "critical"
    }
    
    result = await journeys_tool(
        ctx=ctx,
        action="update_rule",
        journey_id=journey_id,
        stage_id="raw_analysis",
        rule_id=rule_id,
        rule_data=rule_update
    )
    
    if result['status'] == 'success':
        print(f"✅ Rule updated successfully")
        print(f"   📝 New priority: {rule_update['priority']}")


async def demo_job_management(journey_id: str):
    """Demo job lifecycle management."""
    print("\n" + "=" * 80)
    print("🚀 DEMO: JOB LIFECYCLE MANAGEMENT")
    print("=" * 80)
    
    from awslabs.tmf_oda_transformer_mcp_server.tools.management_tools import journeys_tool
    ctx = MockContext()
    
    # 1. List existing jobs
    print("\n1️⃣ Listing existing jobs...")
    result = await journeys_tool(
        ctx=ctx,
        action="list_jobs",
        journey_id=journey_id,
        limit=10
    )
    
    if result['status'] == 'success':
        jobs = result.get('jobs', [])
        print(f"✅ Found {len(jobs)} existing jobs:")
        for job in jobs:
            print(f"   🚀 {job.get('job_id', 'N/A')}: {job.get('stage_id', 'N/A')} ({job.get('status', 'N/A')})")
    
    # 2. Run a new job
    print("\n2️⃣ Starting new job for raw_analysis stage...")
    result = await journeys_tool(
        ctx=ctx,
        action="run_job",
        journey_id=journey_id,
        stage_id="raw_analysis",
        triggered_by="demo-user",
        reason="Demonstration of enhanced job management capabilities"
    )
    
    if result['status'] == 'success':
        job_id = result.get('job_id', 'N/A')
        print(f"✅ Job started: {job_id}")
        print(f"   📋 Stage: {result.get('stage_id', 'N/A')}")
        print(f"   👤 Triggered by: {result.get('triggered_by', 'N/A')}")
        print(f"   📝 Reason: {result.get('reason', 'N/A')}")
    else:
        # Use a mock job ID for demo purposes
        job_id = "JOB-DEMO-001"
        print(f"ℹ️ Using mock job ID for demo: {job_id}")
    
    # 3. Get job details
    print("\n3️⃣ Getting job details...")
    result = await journeys_tool(
        ctx=ctx,
        action="get_job",
        journey_id=journey_id,
        job_id=job_id,
        include_all=True
    )
    
    if result['status'] == 'success':
        print(f"✅ Job details retrieved:")
        print(f"   📊 Status: {result.get('status', 'N/A')}")
        print(f"   📈 Progress: {result.get('progress', 0)}%")
        print(f"   🔧 Current Step: {result.get('current_step', 'N/A')}")
        print(f"   📋 Total Steps: {result.get('total_steps', 'N/A')}")
    
    # 4. Update job status
    print("\n4️⃣ Updating job status...")
    result = await journeys_tool(
        ctx=ctx,
        action="update_job_status",
        journey_id=journey_id,
        job_id=job_id,
        job_status="running",
        progress=50,
        current_step="relationship_discovery"
    )
    
    if result['status'] == 'success':
        print(f"✅ Job status updated:")
        update_data = result.get('update_data', {})
        print(f"   📊 Status: {update_data.get('status', 'N/A')}")
        print(f"   📈 Progress: {update_data.get('progress', 'N/A')}%")
        print(f"   🔧 Current Step: {update_data.get('current_step', 'N/A')}")
    
    # 5. Get job metrics
    print("\n5️⃣ Getting job performance metrics...")
    result = await journeys_tool(
        ctx=ctx,
        action="get_job_metrics",
        journey_id=journey_id,
        job_id=job_id
    )
    
    if result['status'] == 'success':
        metrics = result.get('metrics', {})
        print(f"✅ Job metrics retrieved:")
        perf_metrics = metrics.get('performance_metrics', {})
        if perf_metrics.get('slowest_step'):
            slowest = perf_metrics['slowest_step']
            print(f"   🐌 Slowest Step: {slowest.get('step', 'N/A')} ({slowest.get('duration', 'N/A')}s)")
        if perf_metrics.get('fastest_step'):
            fastest = perf_metrics['fastest_step']
            print(f"   ⚡ Fastest Step: {fastest.get('step', 'N/A')} ({fastest.get('duration', 'N/A')}s)")
        print(f"   🎯 Error Rate: {perf_metrics.get('error_rate', 0)*100:.1f}%")
    
    # 6. Get job timeline
    print("\n6️⃣ Getting job execution timeline...")
    result = await journeys_tool(
        ctx=ctx,
        action="get_job_timeline",
        journey_id=journey_id,
        job_id=job_id
    )
    
    if result['status'] == 'success':
        timeline = result.get('timeline', {})
        events = timeline.get('timeline', [])
        print(f"✅ Job timeline retrieved ({len(events)} events):")
        for event in events[-3:]:  # Show last 3 events
            event_type = event.get('type', 'unknown')
            description = event.get('description', 'N/A')
            timestamp = event.get('timestamp', 'N/A')[:19]
            type_symbol = {'job_started': '🚀', 'job_completed': '🏁', 'log_entry': '📝'}.get(event_type, '📝')
            print(f"   {type_symbol} {timestamp}: {description}")
    
    return job_id


async def demo_logs_and_reports(journey_id: str, job_id: str):
    """Demo logs and reports management."""
    print("\n" + "=" * 80)
    print("📋📊 DEMO: LOGS AND REPORTS MANAGEMENT")
    print("=" * 80)
    
    from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool
    ctx = MockContext()
    
    # 1. Get job logs
    print("\n1️⃣ Retrieving job logs...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="get_job_logs",
        journey_id=journey_id,
        job_id=job_id,
        limit=20
    )
    
    if result['status'] == 'success':
        total_logs = result.get('total_logs', 0)
        logs = result.get('logs', [])
        print(f"✅ Retrieved {total_logs} log entries:")
        for log in logs[-3:]:  # Show last 3 logs
            level = log.get('level', 'info').upper()
            step = log.get('step', 'N/A')
            message = log.get('message', 'N/A')[:60]
            level_symbol = {'ERROR': '❌', 'WARNING': '⚠️', 'INFO': 'ℹ️', 'DEBUG': '🔍'}.get(level, 'ℹ️')
            print(f"   {level_symbol} [{step}] {message}...")
    
    # 2. Search logs
    print("\n2️⃣ Searching logs...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="search_logs",
        journey_id=journey_id,
        search_query="schema",
        job_id=job_id
    )
    
    if result['status'] == 'success':
        total_matches = result.get('total_matches', 0)
        print(f"✅ Search found {total_matches} matching log entries")
    
    # 3. Get logs by level
    print("\n3️⃣ Getting warning logs...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="get_logs_by_level",
        journey_id=journey_id,
        log_level="warning",
        job_id=job_id
    )
    
    if result['status'] == 'success':
        warning_logs = result.get('logs', [])
        print(f"✅ Found {len(warning_logs)} warning log entries:")
        for log in warning_logs:
            step = log.get('step', 'N/A')
            message = log.get('message', 'N/A')[:60]
            print(f"   ⚠️ [{step}] {message}...")
    
    # 4. Get error summary
    print("\n4️⃣ Getting error summary...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="get_error_summary",
        journey_id=journey_id,
        job_id=job_id
    )
    
    if result['status'] == 'success':
        error_summary = result.get('error_summary', {})
        summary = error_summary.get('summary', {})
        print(f"✅ Error summary retrieved:")
        print(f"   ❌ Total Errors: {summary.get('total_errors', 0)}")
        print(f"   ⚠️ Total Warnings: {summary.get('total_warnings', 0)}")
    
    # 5. Generate summary report
    print("\n5️⃣ Generating job summary report...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="generate_summary_report",
        journey_id=journey_id,
        job_id=job_id
    )
    
    if result['status'] == 'success':
        report = result.get('report', {})
        job_summary = report.get('job_summary', {})
        execution_metrics = report.get('execution_metrics', {})
        recommendations = report.get('recommendations', [])
        
        print(f"✅ Summary report generated:")
        print(f"   📋 Stage: {job_summary.get('stage_name', 'N/A')}")
        print(f"   📊 Status: {job_summary.get('status', 'N/A')}")
        print(f"   ⏱️ Execution Time: {job_summary.get('execution_time', 'N/A')}s")
        print(f"   📈 Total Steps: {execution_metrics.get('total_steps', 'N/A')}")
        print(f"   💡 Recommendations: {len(recommendations)}")
    
    # 6. Generate performance report
    print("\n6️⃣ Generating performance report...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="generate_performance_report",
        journey_id=journey_id,
        job_id=job_id
    )
    
    if result['status'] == 'success':
        report = result.get('report', {})
        performance_metrics = report.get('performance_metrics', {})
        recommendations = report.get('recommendations', [])
        
        print(f"✅ Performance report generated:")
        print(f"   ⏱️ Execution Time: {performance_metrics.get('execution_time', 'N/A')}s")
        print(f"   📊 Avg Step Duration: {performance_metrics.get('avg_step_duration', 'N/A')}s")
        print(f"   🎯 Error Rate: {performance_metrics.get('error_rate', 0)*100:.1f}%")
        print(f"   💡 Recommendations: {len(recommendations)}")
    
    # 7. Analyze job performance
    print("\n7️⃣ Analyzing job performance...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="analyze_job_performance",
        journey_id=journey_id,
        job_id=job_id,
        include_recommendations=True
    )
    
    if result['status'] == 'success':
        analysis = result.get('analysis', {})
        overall_performance = analysis.get('overall_performance', {})
        recommendations = analysis.get('recommendations', [])
        
        print(f"✅ Performance analysis completed:")
        print(f"   🏆 Rating: {overall_performance.get('rating', 'N/A')}")
        print(f"   📊 Score: {overall_performance.get('score', 'N/A')}/100")
        print(f"   ⚡ Efficiency: {overall_performance.get('execution_efficiency', 'N/A')}%")
        print(f"   💡 Recommendations: {len(recommendations)}")


async def demo_interactive_features(journey_id: str):
    """Demo interactive dashboard and summary features."""
    print("\n" + "=" * 80)
    print("📊 DEMO: INTERACTIVE FEATURES & DASHBOARDS")
    print("=" * 80)
    
    from awslabs.tmf_oda_transformer_mcp_server.tools.management_tools import journeys_tool
    ctx = MockContext()
    
    # 1. Get journey dashboard
    print("\n1️⃣ Getting journey dashboard...")
    result = await journeys_tool(
        ctx=ctx,
        action="dashboard",
        journey_id=journey_id
    )
    
    if result['status'] == 'success':
        dashboard = result.get('dashboard', {})
        summary = dashboard.get('summary', {})
        health_status = dashboard.get('health_status', {})
        recent_activity = dashboard.get('recent_activity', [])
        
        print(f"✅ Journey dashboard retrieved:")
        print(f"   📋 Journey: {dashboard.get('journey_name', 'N/A')}")
        print(f"   📊 Status: {dashboard.get('status', 'N/A')}")
        print(f"   📈 Progress: {dashboard.get('overall_progress', 0)}%")
        print(f"   🏃 Running Jobs: {summary.get('running_jobs', 0)}")
        print(f"   ✅ Completed Jobs: {summary.get('completed_jobs', 0)}")
        print(f"   💚 Health: {health_status.get('overall', 'N/A')}")
        print(f"   📝 Recent Activity: {len(recent_activity)} events")
    
    # 2. Get comprehensive journey summary
    print("\n2️⃣ Getting comprehensive journey summary...")
    result = await journeys_tool(
        ctx=ctx,
        action="get_journey_summary",
        journey_id=journey_id
    )
    
    if result['status'] == 'success':
        summary = result.get('summary', {})
        basic_info = summary.get('basic_info', {})
        progress_summary = summary.get('progress_summary', {})
        execution_summary = summary.get('execution_summary', {})
        second_brain_summary = summary.get('second_brain_summary', {})
        recommendations = summary.get('recommendations', [])
        
        print(f"✅ Comprehensive summary retrieved:")
        print(f"   📋 Name: {basic_info.get('name', 'N/A')}")
        print(f"   🏗️ Component: {basic_info.get('oda_component_type', 'N/A')}")
        print(f"   📈 Overall Progress: {progress_summary.get('overall_progress', 0)}%")
        print(f"   🔧 Current Stage: {progress_summary.get('current_stage', 'N/A')}")
        print(f"   📋 Total Stages: {execution_summary.get('total_stages', 0)}")
        print(f"   ✅ Completed Stages: {execution_summary.get('completed_stages', 0)}")
        print(f"   🚀 Total Jobs: {execution_summary.get('total_jobs', 0)}")
        print(f"   🧠 Active Rules: {second_brain_summary.get('active_rules', 0)}")
        print(f"   💡 Recommendations: {len(recommendations)}")


async def demo_analysis_and_insights(journey_id: str):
    """Demo advanced analysis and insights generation."""
    print("\n" + "=" * 80)
    print("🔍💡 DEMO: ANALYSIS & INSIGHTS GENERATION")
    print("=" * 80)
    
    from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool
    ctx = MockContext()
    
    # 1. Analyze error patterns
    print("\n1️⃣ Analyzing error patterns...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="analyze_error_patterns",
        journey_id=journey_id,
        analysis_period="24h"
    )
    
    if result['status'] == 'success':
        analysis = result.get('analysis', {})
        pattern_summary = analysis.get('pattern_summary', {})
        identified_patterns = analysis.get('identified_patterns', [])
        recommendations = analysis.get('recommendations', [])
        
        print(f"✅ Error pattern analysis completed:")
        print(f"   🔍 Patterns Identified: {pattern_summary.get('total_patterns_identified', 0)}")
        print(f"   🔴 Critical Patterns: {pattern_summary.get('critical_patterns', 0)}")
        print(f"   ⚠️ Warning Patterns: {pattern_summary.get('warning_patterns', 0)}")
        print(f"   🔄 Recurring Patterns: {pattern_summary.get('recurring_patterns', 0)}")
        print(f"   💡 Recommendations: {len(recommendations)}")
    
    # 2. Generate insights
    print("\n2️⃣ Generating AI-powered insights...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="generate_insights",
        journey_id=journey_id,
        analysis_period="24h"
    )
    
    if result['status'] == 'success':
        insights = result.get('insights', {})
        key_insights = insights.get('key_insights', [])
        trend_predictions = insights.get('trend_predictions', [])
        actionable_recommendations = insights.get('actionable_recommendations', [])
        
        print(f"✅ AI insights generated:")
        print(f"   💡 Key Insights: {len(key_insights)}")
        for insight in key_insights[:2]:  # Show first 2
            print(f"      🔍 {insight.get('title', 'N/A')} (confidence: {insight.get('confidence', 0)}%)")
        print(f"   📈 Trend Predictions: {len(trend_predictions)}")
        print(f"   🎯 Actionable Recommendations: {len(actionable_recommendations)}")
    
    # 3. Get recommendations
    print("\n3️⃣ Getting improvement recommendations...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="get_recommendations",
        journey_id=journey_id
    )
    
    if result['status'] == 'success':
        recommendations_data = result.get('recommendations', {})
        recommendations = recommendations_data.get('recommendations', [])
        summary = recommendations_data.get('summary', {})
        
        print(f"✅ Recommendations generated:")
        print(f"   💡 Total Recommendations: {summary.get('total_recommendations', 0)}")
        print(f"   🔴 High Priority: {summary.get('high_priority', 0)}")
        print(f"   🟡 Medium Priority: {summary.get('medium_priority', 0)}")
        print(f"   🟢 Low Priority: {summary.get('low_priority', 0)}")
        print(f"   📊 Avg Confidence: {summary.get('avg_confidence', 0):.1f}%")
        
        for rec in recommendations[:2]:  # Show first 2
            priority_symbol = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(rec.get('priority', 'low'), '🟢')
            print(f"   {priority_symbol} {rec.get('title', 'N/A')} (confidence: {rec.get('confidence', 0)}%)")


async def demo_not_implemented_features(journey_id: str):
    """Demo features that are planned but not yet implemented."""
    print("\n" + "=" * 80)
    print("🚧 DEMO: PLANNED FEATURES (NOT YET IMPLEMENTED)")
    print("=" * 80)
    
    from awslabs.tmf_oda_transformer_mcp_server.tools.management_tools import journeys_tool
    from awslabs.tmf_oda_transformer_mcp_server.tools.utility_tools import logs_and_reports_tool
    ctx = MockContext()
    
    print("\nThese features are planned and will return 'not_implemented' status:")
    
    # 1. Import/Export operations
    print("\n1️⃣ Testing import/export operations...")
    result = await journeys_tool(
        ctx=ctx,
        action="export_complete",
        journey_id=journey_id,
        output_file="journey_backup.json"
    )
    
    if result['status'] == 'not_implemented':
        print(f"✅ Export operation properly returns not_implemented status")
        print(f"   📝 Note: {result.get('note', 'N/A')}")
    
    # 2. Advanced log operations
    print("\n2️⃣ Testing advanced log operations...")
    result = await logs_and_reports_tool(
        ctx=ctx,
        action="export_reports",
        journey_id=journey_id,
        output_file="reports.json"
    )
    
    if result['status'] == 'not_implemented':
        print(f"✅ Export reports operation properly returns not_implemented status")
        print(f"   📝 Note: This action will be implemented in future versions")
    
    print(f"\n📋 Available Actions in Current Implementation:")
    implemented_actions = [
        "Journey CRUD: create, read, update, delete, list",
        "Stage Management: list_stages, add_stage, update_stage, delete_stage, add_default_stages",
        "Rules Management: list_rules, add_rule, update_rule, delete_rule",
        "Job Management: list_jobs, get_job, run_job, cancel_job, update_job_status, retry_job, get_job_metrics, get_job_timeline, batch_cancel_jobs",
        "Interactive: dashboard, get_journey_summary",
        "Logs Analysis: get_job_logs, search_logs, get_logs_by_level, get_error_summary, generate_summary_report, generate_performance_report",
        "AI Insights: analyze_job_performance, analyze_error_patterns, generate_insights, get_recommendations"
    ]
    
    for action in implemented_actions:
        print(f"   ✅ {action}")


async def main():
    """Main demo function that showcases all enhanced capabilities."""
    print("🚀 COMPREHENSIVE TMF ODA JOURNEY LIFECYCLE MANAGEMENT DEMO")
    print("=" * 80)
    print("This demo showcases the enhanced MCP journeys tool that now provides")
    print("comprehensive lifecycle management capabilities similar to manage_journey.py")
    print("=" * 80)
    
    try:
        # 1. Journey CRUD Operations
        journey_id = await demo_journey_crud()
        if not journey_id:
            print("❌ Failed to create journey for demo")
            return
        
        # 2. Stage Management
        await demo_stage_management(journey_id)
        
        # 3. Rules Management
        await demo_rules_management(journey_id)
        
        # 4. Job Management
        job_id = await demo_job_management(journey_id)
        
        # 5. Logs and Reports
        await demo_logs_and_reports(journey_id, job_id)
        
        # 6. Interactive Features
        await demo_interactive_features(journey_id)
        
        # 7. Analysis and Insights
        await demo_analysis_and_insights(journey_id)
        
        # 8. Not Yet Implemented Features
        await demo_not_implemented_features(journey_id)
        
        # Final Summary
        print("\n" + "=" * 80)
        print("🎉 DEMO COMPLETE - ENHANCED JOURNEY MANAGEMENT CAPABILITIES")
        print("=" * 80)
        print("✅ Successfully demonstrated all enhanced capabilities:")
        print("   🏗️ Journey CRUD Operations")
        print("   📋 Stage Management") 
        print("   🧠 Second Brain Rules Management")
        print("   🚀 Job Lifecycle Management")
        print("   📊 Logs and Reports Management")
        print("   📈 Interactive Dashboards")
        print("   🔍 Performance Analysis")
        print("   💡 AI-Powered Insights")
        print("   🎯 Improvement Recommendations")
        print("\n🚀 The MCP journeys tool now provides comprehensive lifecycle management")
        print("   capabilities that mirror the functionality of manage_journey.py!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting Enhanced TMF ODA Journey Management Demo...")
    asyncio.run(main()) 