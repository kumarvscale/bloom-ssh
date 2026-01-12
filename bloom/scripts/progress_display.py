#!/usr/bin/env python3
"""
Rich-based progress display for SSH Behaviors evaluation.

Provides clean, informative progress tracking with:
- Overall progress bar (all tests)
- Behavior-level progress bar
- Current behavior and stage display
- ETA calculation based on average stage times
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text


@dataclass
class StageTimings:
    """Track timing for each pipeline stage."""
    understanding: list[float] = field(default_factory=list)
    ideation: list[float] = field(default_factory=list)
    rollout: list[float] = field(default_factory=list)
    judgment: list[float] = field(default_factory=list)
    
    def add_timing(self, stage: str, duration: float) -> None:
        """Add a timing measurement for a stage."""
        if hasattr(self, stage):
            getattr(self, stage).append(duration)
    
    def get_average(self, stage: str) -> float:
        """Get average time for a stage (returns 60s default if no data)."""
        timings = getattr(self, stage, [])
        if timings:
            return sum(timings) / len(timings)
        # Default estimates per stage
        defaults = {
            "understanding": 30,
            "ideation": 60,
            "rollout": 120,
            "judgment": 90,
        }
        return defaults.get(stage, 60)
    
    def get_total_average(self) -> float:
        """Get average total time for one complete test."""
        return (
            self.get_average("understanding") +
            self.get_average("ideation") +
            self.get_average("rollout") +
            self.get_average("judgment")
        )


class ProgressDisplay:
    """
    Rich-based progress display for SSH Behaviors evaluation.
    
    Usage:
        display = ProgressDisplay(total_tests=225, total_behaviors=45)
        display.start()
        
        for behavior in behaviors:
            display.set_current_behavior(behavior, turns)
            
            display.set_stage("understanding")
            # ... run understanding ...
            display.complete_stage("understanding", duration)
            
            # ... repeat for other stages ...
            
            display.complete_test()
        
        display.stop()
    """
    
    STAGES = ["understanding", "ideation", "rollout", "judgment"]
    STAGE_ICONS = {
        "understanding": "🔍",
        "ideation": "💡",
        "rollout": "🎭",
        "judgment": "⚖️",
    }
    
    def __init__(
        self,
        total_tests: int,
        total_behaviors: int,
        turn_counts: list[int],
    ):
        self.total_tests = total_tests
        self.total_behaviors = total_behaviors
        self.turn_counts = turn_counts
        
        self.completed_tests = 0
        self.completed_behaviors = 0
        self.current_behavior = ""
        self.current_turns = 0
        self.current_stage = ""
        self.stage_completed = {s: False for s in self.STAGES}
        
        self.timings = StageTimings()
        self.stage_start_time: Optional[float] = None
        self.test_start_time: Optional[float] = None
        self.run_start_time: Optional[float] = None
        
        self.console = Console()
        self.live: Optional[Live] = None
        
        # Track behaviors completed
        self.behaviors_completed_set: set[str] = set()
    
    def _create_display(self) -> Table:
        """Create the progress display table."""
        # Calculate ETA
        avg_time = self.timings.get_total_average()
        remaining_tests = self.total_tests - self.completed_tests
        eta_seconds = remaining_tests * avg_time
        
        if eta_seconds > 3600:
            eta_str = f"{eta_seconds / 3600:.1f}h"
        elif eta_seconds > 60:
            eta_str = f"{eta_seconds / 60:.0f}m"
        else:
            eta_str = f"{eta_seconds:.0f}s"
        
        # Calculate elapsed time
        elapsed = time.time() - self.run_start_time if self.run_start_time else 0
        if elapsed > 3600:
            elapsed_str = f"{elapsed / 3600:.1f}h"
        elif elapsed > 60:
            elapsed_str = f"{elapsed / 60:.0f}m"
        else:
            elapsed_str = f"{elapsed:.0f}s"
        
        # Overall progress
        overall_pct = (self.completed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        overall_bar = self._make_progress_bar(overall_pct)
        
        # Behavior progress
        behavior_pct = (self.completed_behaviors / self.total_behaviors * 100) if self.total_behaviors > 0 else 0
        behavior_bar = self._make_progress_bar(behavior_pct)
        
        # Stage indicators
        stage_text = self._make_stage_indicators()
        
        # Build display
        table = Table.grid(padding=(0, 1))
        table.add_column(justify="left", width=60)
        
        # Header
        table.add_row(Text("SSH Behaviors Evaluation", style="bold cyan"))
        table.add_row(Text("━" * 55, style="dim"))
        
        # Overall progress
        table.add_row(
            Text(f"Overall:    {overall_bar} {overall_pct:5.1f}% | {self.completed_tests}/{self.total_tests} | ETA: {eta_str} | Elapsed: {elapsed_str}")
        )
        
        # Behavior progress
        table.add_row(
            Text(f"Behaviors:  {behavior_bar} {behavior_pct:5.1f}% | {self.completed_behaviors}/{self.total_behaviors}")
        )
        
        table.add_row(Text("━" * 55, style="dim"))
        
        # Current behavior
        if self.current_behavior:
            table.add_row(
                Text(f"Current: {self.current_behavior} ({self.current_turns} turns)", style="yellow")
            )
        else:
            table.add_row(Text("Current: Waiting...", style="dim"))
        
        # Stage progress
        table.add_row(Text(f"Stage:   {stage_text}"))
        
        table.add_row(Text("━" * 55, style="dim"))
        
        return table
    
    def _make_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Create a text-based progress bar."""
        filled = int(width * percentage / 100)
        empty = width - filled
        return f"[green]{'█' * filled}[/green][dim]{'░' * empty}[/dim]"
    
    def _make_stage_indicators(self) -> str:
        """Create stage indicators showing completion status."""
        parts = []
        for stage in self.STAGES:
            icon = self.STAGE_ICONS[stage]
            name = stage.capitalize()[:4]
            
            if self.stage_completed[stage]:
                parts.append(f"[green][✓] {name}[/green]")
            elif stage == self.current_stage:
                parts.append(f"[yellow][▶] {name}[/yellow]")
            else:
                parts.append(f"[dim][ ] {name}[/dim]")
        
        return " ".join(parts)
    
    def start(self) -> None:
        """Start the progress display."""
        self.run_start_time = time.time()
        self.live = Live(
            self._create_display(),
            console=self.console,
            refresh_per_second=2,
            transient=False,
        )
        self.live.start()
    
    def stop(self) -> None:
        """Stop the progress display."""
        if self.live:
            self.live.stop()
    
    def update(self) -> None:
        """Update the display."""
        if self.live:
            self.live.update(self._create_display())
    
    def set_current_behavior(self, behavior: str, turns: int) -> None:
        """Set the current behavior being evaluated."""
        self.current_behavior = behavior
        self.current_turns = turns
        self.stage_completed = {s: False for s in self.STAGES}
        self.current_stage = ""
        self.test_start_time = time.time()
        self.update()
    
    def set_stage(self, stage: str) -> None:
        """Set the current stage."""
        self.current_stage = stage
        self.stage_start_time = time.time()
        self.update()
    
    def complete_stage(self, stage: str, duration: Optional[float] = None) -> None:
        """Mark a stage as completed."""
        if duration is None and self.stage_start_time:
            duration = time.time() - self.stage_start_time
        
        if duration:
            self.timings.add_timing(stage, duration)
        
        self.stage_completed[stage] = True
        self.current_stage = ""
        self.update()
    
    def complete_test(self) -> None:
        """Mark current test as completed."""
        self.completed_tests += 1
        
        # Track unique behaviors
        if self.current_behavior and self.current_behavior not in self.behaviors_completed_set:
            # Check if all turn variants are complete for this behavior
            # For simplicity, we increment when a test completes
            pass
        
        self.update()
    
    def complete_behavior(self, behavior: str) -> None:
        """Mark a behavior as fully completed (all turn variants done)."""
        if behavior not in self.behaviors_completed_set:
            self.behaviors_completed_set.add(behavior)
            self.completed_behaviors = len(self.behaviors_completed_set)
            self.update()
    
    def set_failed(self, error: str) -> None:
        """Mark current test as failed."""
        self.console.print(f"[red]✗ Failed: {self.current_behavior} - {error[:50]}...[/red]")
    
    def print_summary(self) -> None:
        """Print final summary."""
        elapsed = time.time() - self.run_start_time if self.run_start_time else 0
        
        self.console.print()
        self.console.print(Panel(
            f"[green]✓ Completed:[/green] {self.completed_tests}/{self.total_tests} tests\n"
            f"[green]✓ Behaviors:[/green] {self.completed_behaviors}/{self.total_behaviors}\n"
            f"[blue]⏱ Total time:[/blue] {elapsed/60:.1f} minutes",
            title="[bold]Evaluation Complete[/bold]",
            border_style="green",
        ))


class SimpleProgressDisplay:
    """
    Simpler fallback progress display without live updates.
    Used when rich's Live display isn't available.
    """
    
    def __init__(self, total_tests: int, total_behaviors: int, turn_counts: list[int]):
        self.total_tests = total_tests
        self.total_behaviors = total_behaviors
        self.completed_tests = 0
        self.completed_behaviors = 0
        self.current_behavior = ""
        self.current_stage = ""
        self.run_start_time = time.time()
    
    def start(self) -> None:
        print("=" * 60)
        print("SSH Behaviors Evaluation")
        print("=" * 60)
    
    def stop(self) -> None:
        pass
    
    def update(self) -> None:
        pass
    
    def set_current_behavior(self, behavior: str, turns: int) -> None:
        self.current_behavior = behavior
        print(f"\n▶ {behavior} ({turns} turns)")
    
    def set_stage(self, stage: str) -> None:
        self.current_stage = stage
        print(f"  → {stage}...", end=" ", flush=True)
    
    def complete_stage(self, stage: str, duration: Optional[float] = None) -> None:
        print("✓")
    
    def complete_test(self) -> None:
        self.completed_tests += 1
        pct = self.completed_tests / self.total_tests * 100
        print(f"  [Progress: {self.completed_tests}/{self.total_tests} ({pct:.1f}%)]")
    
    def complete_behavior(self, behavior: str) -> None:
        self.completed_behaviors += 1
    
    def set_failed(self, error: str) -> None:
        print(f"✗ FAILED: {error[:50]}")
    
    def print_summary(self) -> None:
        elapsed = time.time() - self.run_start_time
        print(f"\n{'=' * 60}")
        print(f"Complete: {self.completed_tests}/{self.total_tests} tests")
        print(f"Time: {elapsed/60:.1f} minutes")
        print("=" * 60)


def create_progress_display(
    total_tests: int,
    total_behaviors: int,
    turn_counts: list[int],
    use_rich: bool = True,
) -> ProgressDisplay | SimpleProgressDisplay:
    """Create appropriate progress display based on environment."""
    if use_rich:
        try:
            return ProgressDisplay(total_tests, total_behaviors, turn_counts)
        except Exception:
            pass
    return SimpleProgressDisplay(total_tests, total_behaviors, turn_counts)

