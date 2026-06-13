"""Chart rendering functions for the dashboard."""

from __future__ import annotations

from typing import Any, Optional
import tkinter as tk
import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def create_chart_canvas(parent: tk.Frame, figure: Figure) -> FigureCanvasTkAgg:
    """Create a matplotlib canvas widget parented to a plain tk.Frame."""
    canvas = FigureCanvasTkAgg(figure, master=parent)
    widget = canvas.get_tk_widget()
    widget.configure(borderwidth=0, highlightthickness=0)
    widget.pack(fill="both", expand=True)
    return canvas


def setup_figure(bg_color: str, figsize=(8, 4), dpi=100) -> Figure:
    """Create a matplotlib figure with appropriate background color."""
    return Figure(figsize=figsize, dpi=dpi, facecolor=bg_color)


def configure_axes(ax, fg_color: str, bg_color: str) -> None:
    """Configure matplotlib axes with theme colors."""
    ax.set_facecolor(bg_color)
    ax.tick_params(colors=fg_color, labelsize=8)
    for sp in ax.spines.values():
        sp.set_color(fg_color)
    ax.xaxis.label.set_color(fg_color)
    ax.yaxis.label.set_color(fg_color)
    ax.title.set_color(fg_color)


def draw_line_chart(ax, dates: list, values: list, color: str, 
                    ylabel: str, title: str) -> None:
    """Draw a line chart."""
    if dates:
        ax.plot(range(len(dates)), values, color=color,
                linewidth=2, marker="o", markersize=4)
        step = max(1, len(dates) // 12)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels(
            [dates[i] for i in range(0, len(dates), step)],
            rotation=45, fontsize=7)
    ax.set_ylabel(ylabel)
    ax.set_title(title)


def draw_bar_chart(ax, dates: list, values: list, color: str,
                   ylabel: str, title: str) -> None:
    """Draw a bar chart."""
    if dates:
        ax.bar(range(len(dates)), values, color=color, width=0.7)
        step = max(1, len(dates) // 12)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels(
            [dates[i] for i in range(0, len(dates), step)],
            rotation=45, fontsize=7)
    ax.set_ylabel(ylabel)
    ax.set_title(title)


def draw_pie_chart(ax, labels: list, values: list, colors: list, fg_color: str) -> None:
    """Draw a pie chart."""
    if labels:
        wedges, _, _ = ax.pie(
            values, labels=None, autopct="%1.1f%%",
            colors=colors,
            textprops={"color": fg_color, "fontsize": 8})
        ax.legend(wedges, labels, loc="center left",
                  bbox_to_anchor=(1, 0.5), fontsize=7,
                  frameon=False, labelcolor=fg_color)
    ax.set_title("Earnings by Task")


def draw_rate_distribution(ax, buckets: list, fg_color: str, bg_color: str, 
                           accent_color: str) -> None:
    """Draw a rate distribution histogram."""
    if buckets:
        xs = [b["bucket"] for b in buckets]
        ys = [b["count"] for b in buckets]
        w = buckets[0]["size"] * 0.9
        ax.bar(xs, ys, width=w, color=accent_color,
                edgecolor=bg_color, linewidth=0.5, align="edge")
    ax.set_xlabel("Hourly Rate ($)")
    ax.set_ylabel("Entries")
    ax.set_title("Rate Distribution")
