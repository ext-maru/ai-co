#!/usr/bin/env python3
"""
Elder Council Management Command
エルダー会議管理コマンド - 自動召集と進化支援システム
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from libs.elder_council_summoner import ElderCouncilSummoner, UrgencyLevel, TriggerCategory

console = Console()
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Elder Council Auto-Summoning System - エルダー会議自動召集システム"""
    pass

@cli.command()
@click.option('--daemon', is_flag=True, help='Run as daemon process')
@click.option('--interval', default=300, help='Monitoring interval in seconds')
def start(daemon, interval):
    """Start the Elder Council monitoring system"""
    console.print("[bold blue]🏛️ Starting Elder Council Auto-Summoning System[/bold blue]")
    
    summoner = ElderCouncilSummoner()
    summoner.monitoring_interval = interval
    
    if daemon:
        import daemon
        with daemon.DaemonContext():
            summoner.start_monitoring()
            while True:
                time.sleep(60)
    else:
        summoner.start_monitoring()
        console.print(f"[yellow]Monitoring system evolution every {interval} seconds...[/yellow]")
        console.print("[dim]Press Ctrl+C to stop[/dim]")
        
        try:
            while True:
                time.sleep(10)
                status = summoner.get_system_status()
                
                # Display status update
                if status.get('pending_councils', 0) > 0:
                    console.print(f"[red]⚠️  {status['pending_councils']} Elder Council(s) pending[/red]")
                
                if status.get('total_triggers', 0) > 0:
                    console.print(f"[yellow]📊 {status['total_triggers']} active trigger(s)[/yellow]")
                
        except KeyboardInterrupt:
            console.print("\n[red]Stopping monitoring...[/red]")
            summoner.stop_monitoring()

@cli.command()
def status():
    """Show current system evolution status"""
    summoner = ElderCouncilSummoner()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing system evolution status...", total=None)
        
        # Force evaluation
        status = summoner.force_trigger_evaluation()
        
        progress.remove_task(task)
    
    # Create status overview
    status_table = Table(title="Elder Council System Status", box=box.ROUNDED)
    status_table.add_column("Metric", style="cyan")
    status_table.add_column("Value", style="green")
    status_table.add_column("Status", style="yellow")
    
    # System metrics
    status_table.add_row("Monitoring Active", str(status['monitoring_active']), "✅" if status['monitoring_active'] else "❌")
    status_table.add_row("Active Triggers", str(status['total_triggers']), get_trigger_status_emoji(status['total_triggers']))
    status_table.add_row("Pending Councils", str(status['pending_councils']), get_council_status_emoji(status['pending_councils']))
    status_table.add_row("4 Sages Integration", str(status['four_sages_enabled']), "✅" if status['four_sages_enabled'] else "❌")
    
    console.print(status_table)
    
    # Urgency distribution
    if status.get('urgency_distribution'):
        urgency_table = Table(title="Trigger Urgency Distribution", box=box.ROUNDED)
        urgency_table.add_column("Urgency Level", style="cyan")
        urgency_table.add_column("Count", style="yellow")
        urgency_table.add_column("Description", style="dim")
        
        urgency_descriptions = {
            'critical': '24 hours - Immediate attention required',
            'high': '1 week - Strategic decision needed',
            'medium': '1 month - Evolution opportunity',
            'low': '3 months - Long-term planning'
        }
        
        for level, count in status['urgency_distribution'].items():
            if count > 0:
                urgency_table.add_row(
                    level.upper(),
                    str(count),
                    urgency_descriptions.get(level, 'Unknown')
                )
        
        console.print(urgency_table)
    
    # Recent metrics
    if status.get('recent_metrics'):
        metrics = status['recent_metrics']
        metrics_panel = create_metrics_panel(metrics)
        console.print(metrics_panel)

@cli.command()
def triggers():
    """Show active triggers and their details"""
    summoner = ElderCouncilSummoner()
    
    # Load triggers from file
    triggers_file = PROJECT_ROOT / 'data' / 'council_triggers.json'
    
    if not triggers_file.exists():
        console.print("[yellow]No triggers found[/yellow]")
        return
    
    try:
        with open(triggers_file, 'r') as f:
            triggers_data = json.load(f)
        
        if not triggers_data:
            console.print("[yellow]No triggers found[/yellow]")
            return
        
        # Create triggers table
        triggers_table = Table(title="Elder Council Triggers", box=box.ROUNDED)
        triggers_table.add_column("Triggered", style="cyan")
        triggers_table.add_column("Urgency", style="yellow")
        triggers_table.add_column("Category", style="blue")
        triggers_table.add_column("Title", style="white")
        triggers_table.add_column("Affected Systems", style="dim")
        
        # Show last 20 triggers
        for trigger in triggers_data[-20:]:
            urgency = trigger.get('urgency', 'unknown')
            urgency_style = get_urgency_style(urgency)
            
            affected_systems = ', '.join(trigger.get('affected_systems', []))
            if len(affected_systems) > 30:
                affected_systems = affected_systems[:30] + "..."
            
            triggers_table.add_row(
                trigger.get('triggered_at', '')[:19],
                f"[{urgency_style}]{urgency.upper()}[/{urgency_style}]",
                trigger.get('category', 'unknown').replace('_', ' ').title(),
                trigger.get('title', 'Unknown'),
                affected_systems
            )
        
        console.print(triggers_table)
        
    except Exception as e:
        console.print(f"[red]Error reading triggers: {e}[/red]")

@cli.command()
def councils():
    """Show pending and recent Elder Council requests"""
    council_files = list((PROJECT_ROOT / 'knowledge_base').glob('*elder_council_request.md'))
    
    if not council_files:
        console.print("[yellow]No Elder Council requests found[/yellow]")
        return
    
    # Create councils table
    councils_table = Table(title="Elder Council Requests", box=box.ROUNDED)
    councils_table.add_column("Council ID", style="cyan")
    councils_table.add_column("Created", style="yellow")
    councils_table.add_column("Urgency", style="red")
    councils_table.add_column("Status", style="green")
    councils_table.add_column("File", style="dim")
    
    for council_file in sorted(council_files, key=lambda x: x.stat().st_mtime, reverse=True)[:10]:
        file_name = council_file.name
        created_time = datetime.fromtimestamp(council_file.stat().st_mtime)
        
        # Extract urgency from filename or content
        urgency = "unknown"
        if "critical" in file_name.lower():
            urgency = "critical"
        elif "high" in file_name.lower():
            urgency = "high"
        elif "medium" in file_name.lower():
            urgency = "medium"
        
        # Determine status based on age
        age = datetime.now() - created_time
        if age < timedelta(hours=24):
            status = "🆕 New"
        elif age < timedelta(days=7):
            status = "⏳ Pending"
        else:
            status = "⏰ Overdue"
        
        councils_table.add_row(
            file_name.replace('_elder_council_request.md', ''),
            created_time.strftime('%Y-%m-%d %H:%M'),
            urgency.upper(),
            status,
            file_name
        )
    
    console.print(councils_table)

@cli.command()
@click.argument('council_id')
def show(council_id):
    """Show detailed information about a specific council request"""
    council_file = PROJECT_ROOT / 'knowledge_base' / f'{council_id}_elder_council_request.md'
    
    if not council_file.exists():
        console.print(f"[red]Council request {council_id} not found[/red]")
        return
    
    try:
        with open(council_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        console.print(Panel(content, title=f"Elder Council Request: {council_id}", border_style="blue"))
        
    except Exception as e:
        console.print(f"[red]Error reading council request: {e}[/red]")

@cli.command()
def metrics():
    """Show system evolution metrics"""
    metrics_file = PROJECT_ROOT / 'data' / 'evolution_metrics.json'
    
    if not metrics_file.exists():
        console.print("[yellow]No evolution metrics found[/yellow]")
        return
    
    try:
        with open(metrics_file, 'r') as f:
            metrics_data = json.load(f)
        
        if not metrics_data:
            console.print("[yellow]No metrics data available[/yellow]")
            return
        
        # Show latest metrics
        latest_metrics = metrics_data[-1]
        
        metrics_table = Table(title="System Evolution Metrics", box=box.ROUNDED)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="green")
        metrics_table.add_column("Status", style="yellow")
        
        metrics_info = [
            ("Test Coverage", f"{latest_metrics.get('test_coverage', 0):.2%}", get_coverage_status(latest_metrics.get('test_coverage', 0))),
            ("Worker Health", f"{latest_metrics.get('worker_health_score', 0):.2%}", get_health_status(latest_metrics.get('worker_health_score', 0))),
            ("Memory Usage", f"{latest_metrics.get('memory_usage', 0):.2%}", get_memory_status(latest_metrics.get('memory_usage', 0))),
            ("CPU Usage", f"{latest_metrics.get('cpu_usage', 0):.2%}", get_cpu_status(latest_metrics.get('cpu_usage', 0))),
            ("Queue Backlog", str(latest_metrics.get('queue_backlog', 0)), get_queue_status(latest_metrics.get('queue_backlog', 0))),
            ("Error Rate", f"{latest_metrics.get('error_rate', 0):.2%}", get_error_status(latest_metrics.get('error_rate', 0))),
            ("4 Sages Consensus", f"{latest_metrics.get('four_sages_consensus_rate', 0):.2%}", get_consensus_status(latest_metrics.get('four_sages_consensus_rate', 0))),
            ("Learning Velocity", f"{latest_metrics.get('learning_velocity', 0):.2f}", get_learning_status(latest_metrics.get('learning_velocity', 0))),
        ]
        
        for metric, value, status in metrics_info:
            metrics_table.add_row(metric, value, status)
        
        console.print(metrics_table)
        
        # Show timestamp
        timestamp = latest_metrics.get('timestamp', '')
        console.print(f"[dim]Last updated: {timestamp}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error reading metrics: {e}[/red]")

@cli.command()
def simulate():
    """Simulate a trigger for testing purposes"""
    console.print("[yellow]🧪 Simulating system evolution trigger...[/yellow]")
    
    summoner = ElderCouncilSummoner()
    
    # Create a test trigger
    from libs.elder_council_summoner import CouncilTrigger, TriggerCategory, UrgencyLevel
    
    test_trigger = CouncilTrigger(
        trigger_id="simulation_test",
        category=TriggerCategory.EVOLUTION_OPPORTUNITY,
        urgency=UrgencyLevel.MEDIUM,
        title="Simulated Evolution Opportunity",
        description="This is a test trigger to demonstrate the Elder Council summoning system",
        triggered_at=datetime.now(),
        metrics={},
        affected_systems=["simulation_system"],
        suggested_agenda=["Review simulation results", "Discuss system improvements"],
        auto_analysis={"test": True}
    )
    
    summoner.triggers["simulation_test"] = test_trigger
    summoner._consider_council_summoning(test_trigger)
    
    console.print("[green]✅ Simulation trigger created successfully[/green]")
    console.print(f"[blue]📄 Check knowledge_base/ for council request document[/blue]")

def get_trigger_status_emoji(count):
    """Get status emoji for trigger count"""
    if count == 0:
        return "✅"
    elif count <= 2:
        return "⚠️"
    else:
        return "🚨"

def get_council_status_emoji(count):
    """Get status emoji for council count"""
    if count == 0:
        return "✅"
    elif count == 1:
        return "📋"
    else:
        return "🏛️"

def get_urgency_style(urgency):
    """Get style for urgency level"""
    styles = {
        'critical': 'red bold',
        'high': 'red',
        'medium': 'yellow',
        'low': 'green'
    }
    return styles.get(urgency, 'white')

def create_metrics_panel(metrics):
    """Create metrics display panel"""
    content = f"""
**System Evolution Metrics**

🧠 Test Coverage: {metrics.get('test_coverage', 0):.2%}
👷 Worker Health: {metrics.get('worker_health_score', 0):.2%}
💾 Memory Usage: {metrics.get('memory_usage', 0):.2%}
⚡ CPU Usage: {metrics.get('cpu_usage', 0):.2%}
📊 Queue Backlog: {metrics.get('queue_backlog', 0)}
❌ Error Rate: {metrics.get('error_rate', 0):.2%}
🧙‍♂️ 4 Sages Consensus: {metrics.get('four_sages_consensus_rate', 0):.2%}
📈 Learning Velocity: {metrics.get('learning_velocity', 0):.2f}
🏗️ System Complexity: {metrics.get('system_complexity_score', 0):.2%}

*Updated: {metrics.get('timestamp', 'Unknown')}*
"""
    
    return Panel(content, title="Current System State", border_style="green")

def get_coverage_status(value):
    """Get status for test coverage"""
    if value < 0.05:
        return "🚨 Critical"
    elif value < 0.2:
        return "⚠️ Low"
    elif value < 0.8:
        return "📈 Improving"
    else:
        return "✅ Good"

def get_health_status(value):
    """Get status for worker health"""
    if value < 0.5:
        return "🚨 Critical"
    elif value < 0.8:
        return "⚠️ Warning"
    else:
        return "✅ Healthy"

def get_memory_status(value):
    """Get status for memory usage"""
    if value > 0.9:
        return "🚨 Critical"
    elif value > 0.8:
        return "⚠️ High"
    else:
        return "✅ Normal"

def get_cpu_status(value):
    """Get status for CPU usage"""
    if value > 0.9:
        return "🚨 Critical"
    elif value > 0.8:
        return "⚠️ High"
    else:
        return "✅ Normal"

def get_queue_status(value):
    """Get status for queue backlog"""
    if value > 500:
        return "🚨 Critical"
    elif value > 100:
        return "⚠️ High"
    else:
        return "✅ Normal"

def get_error_status(value):
    """Get status for error rate"""
    if value > 0.1:
        return "🚨 Critical"
    elif value > 0.05:
        return "⚠️ High"
    else:
        return "✅ Low"

def get_consensus_status(value):
    """Get status for 4 Sages consensus"""
    if value < 0.5:
        return "🚨 Failed"
    elif value < 0.75:
        return "⚠️ Low"
    else:
        return "✅ Good"

def get_learning_status(value):
    """Get status for learning velocity"""
    if value < 0.3:
        return "🚨 Slow"
    elif value < 0.7:
        return "⚠️ Moderate"
    else:
        return "✅ Fast"

if __name__ == '__main__':
    cli()