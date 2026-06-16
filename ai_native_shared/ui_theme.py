"""Shared Streamlit UI helpers for the AI native after-sales demos."""

from __future__ import annotations

from html import escape
from typing import Iterable

import streamlit as st


def inject_demo_ui() -> None:
    """Inject a consistent dashboard-style visual layer across demo apps."""
    st.markdown(
        """
        <style>
        :root {
            --as-bg: #f6f8fb;
            --as-panel: #ffffff;
            --as-ink: #111827;
            --as-muted: #64748b;
            --as-line: #dbe3ef;
            --as-primary: #0c5cab;
            --as-primary-dark: #084a8e;
            --as-success: #10b981;
            --as-warning: #f59e0b;
            --as-danger: #ef4444;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(12, 92, 171, 0.11), transparent 30rem),
                linear-gradient(180deg, #f8fafc 0%, var(--as-bg) 100%);
            color: var(--as-ink);
        }
        .block-container {
            max-width: 1260px;
            padding-top: 1.2rem;
            padding-bottom: 2.2rem;
        }
        h1, h2, h3, p, li, div, span {
            letter-spacing: 0;
        }
        div[data-testid="stMetric"] {
            border: 1px solid var(--as-line);
            border-radius: 8px;
            background: rgba(255,255,255,0.94);
            padding: 13px 15px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
        }
        div[data-testid="stMetricLabel"] p {
            color: var(--as-muted);
            font-size: 13px;
        }
        div[data-testid="stMetricValue"] {
            color: var(--as-ink);
            font-weight: 760;
        }
        div[data-testid="stAlert"] {
            border-radius: 8px;
            border: 1px solid var(--as-line);
        }
        .stButton > button,
        .stDownloadButton > button {
            border-radius: 6px;
            min-height: 38px;
            font-weight: 700;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
            border-bottom: 1px solid var(--as-line);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 6px 6px 0 0;
            padding: 8px 12px;
            color: #475569;
        }
        .stTabs [aria-selected="true"] {
            background: #eff6ff;
            color: var(--as-primary);
            font-weight: 800;
        }
        .as-hero {
            border: 1px solid rgba(255,255,255,0.18);
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(17, 24, 39, 0.98), rgba(12, 92, 171, 0.92)),
                #111827;
            color: #f8fafc;
            padding: 22px 24px;
            margin-bottom: 16px;
            box-shadow: 0 18px 46px rgba(15, 23, 42, 0.16);
        }
        .as-hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.45fr) minmax(260px, 0.72fr);
            gap: 20px;
            align-items: end;
        }
        .as-eyebrow {
            color: #93c5fd;
            font-size: 12px;
            font-weight: 800;
            text-transform: uppercase;
            margin-bottom: 7px;
        }
        .as-hero h1 {
            margin: 0 0 9px 0;
            font-size: 30px;
            line-height: 1.2;
            color: #ffffff;
        }
        .as-hero p {
            margin: 0;
            color: #dbeafe;
            font-size: 14px;
            line-height: 1.72;
        }
        .as-status {
            display: grid;
            gap: 8px;
        }
        .as-status-row {
            display: flex;
            justify-content: space-between;
            gap: 10px;
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 8px;
            padding: 9px 11px;
            background: rgba(255,255,255,0.07);
            color: #e0f2fe;
            font-size: 13px;
        }
        .as-chip {
            display: inline-flex;
            min-height: 24px;
            align-items: center;
            border-radius: 999px;
            padding: 3px 8px;
            border: 1px solid #bfdbfe;
            background: #eff6ff;
            color: var(--as-primary);
            font-size: 12px;
            font-weight: 760;
            margin: 0 6px 6px 0;
        }
        @media (max-width: 900px) {
            .as-hero-grid {
                grid-template-columns: 1fr;
            }
            .as-hero h1 {
                font-size: 25px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_demo_hero(
    title: str,
    subtitle: str,
    chips: Iterable[str],
    status: dict[str, str] | None = None,
) -> None:
    """Render a consistent hero for business demo modules."""
    chips_html = "".join(f'<span class="as-chip">{escape(str(chip))}</span>' for chip in chips)
    status_items = status or {}
    status_html = "".join(
        f'<div class="as-status-row"><span>{escape(str(k))}</span><strong>{escape(str(v))}</strong></div>'
        for k, v in status_items.items()
    )
    if not status_html:
        status_html = '<div class="as-status-row"><span>模块状态</span><strong>Demo 可运行</strong></div>'

    st.markdown(
        f"""
        <div class="as-hero">
            <div class="as-hero-grid">
                <div>
                    <div class="as-eyebrow">AI native after-sales module</div>
                    <h1>{escape(title)}</h1>
                    <p>{escape(subtitle)}</p>
                    <div style="margin-top:12px;">{chips_html}</div>
                </div>
                <div class="as-status">{status_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
