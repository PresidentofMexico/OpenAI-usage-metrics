"""
Frequency Utilities for AI Usage Metrics Dashboard

Provides transforms for unifying weekly and monthly data at query time:
- OpenAI weekly → monthly proration (exact, day-level)
- Blueflame monthly → weekly allocation (estimated, labeled)

No schema changes required - transforms work on DataFrames.
"""
import pandas as pd
import numpy as np

ISO_WEEK_START_DAY = "W-MON"


def _expand_weekly_to_daily(df, date_col="date", value_col="usage_count"):
    """
    Expand weekly records to daily records with equal day weighting.
    
    Args:
        df: DataFrame with weekly records
        date_col: Column containing week start dates
        value_col: Column to distribute across days
        
    Returns:
        DataFrame with daily records
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Create 7 rows for each week (one per day)
    expanded = (
        df.reindex(df.index.repeat(7))
          .assign(_day_offset=np.tile(np.arange(7), len(df)))
    )
    
    # Calculate actual day and distribute value equally
    expanded["day"] = expanded[date_col] + pd.to_timedelta(expanded["_day_offset"], unit="D")
    expanded[value_col] = expanded[value_col] / 7.0
    
    return expanded


def openai_weekly_to_monthly(df, date_col="date", value_col="usage_count"):
    """
    Prorate weekly OpenAI rows into months by equal day weighting.
    
    Weeks spanning two months are split proportionally by days in each month.
    
    Args:
        df: DataFrame with weekly OpenAI data
        date_col: Column with week start dates (default: "date")
        value_col: Column with usage counts (default: "usage_count")
        
    Returns:
        DataFrame with monthly aggregates (period_start = first day of month)
    """
    if df.empty:
        return pd.DataFrame(columns=["period_start", value_col])
    
    # Expand weeks to daily records
    days = _expand_weekly_to_daily(df, date_col=date_col, value_col=value_col)
    
    # Group by month
    days["month"] = days["day"].dt.to_period("M").dt.to_timestamp()
    
    # Aggregate to monthly totals
    out = (days.groupby(["month"], as_index=False)[value_col].sum()
                .rename(columns={"month": "period_start"}))
    
    return out


def _expand_monthly_to_daily(df, date_col="date", value_col="usage_count"):
    """
    Expand monthly records to daily records with equal day weighting.
    
    Args:
        df: DataFrame with monthly records
        date_col: Column containing month start dates
        value_col: Column to distribute across days
        
    Returns:
        DataFrame with daily records
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Calculate days in each month
    month_end = (df[date_col] + pd.offsets.MonthEnd(0))
    days_in_month = (month_end - (df[date_col] - pd.offsets.MonthBegin(0)) + pd.Timedelta(days=1)).dt.days
    
    # Create one row per day in the month
    expanded = (
        df.reindex(df.index.repeat(days_in_month))
          .assign(_day_index=np.hstack([np.arange(n) for n in days_in_month]))
    )
    
    # Calculate actual day and distribute value equally
    expanded["day"] = expanded[date_col] + pd.to_timedelta(expanded["_day_index"], unit="D")
    expanded[value_col] = expanded[value_col] / expanded.groupby(level=0)[value_col].transform("count")
    
    return expanded


def blueflame_monthly_to_weekly_estimated(df, date_col="date", value_col="usage_count",
                                          method="even_by_day", openai_weekly=None):
    """
    Allocate Blueflame monthly totals to ISO weeks (estimated).
    
    Args:
        df: DataFrame with monthly Blueflame data
        date_col: Column with month start dates (default: "date")
        value_col: Column with usage counts (default: "usage_count")
        method: Allocation method:
            - 'even_by_day' (default): equal split across days in the month
            - 'business_days': allocate across Mon–Fri only
            - 'proportional_to_openai': split proportional to OpenAI weekly shares
        openai_weekly: DataFrame with OpenAI weekly data (required for proportional method)
        
    Returns:
        DataFrame with weekly estimates (iso_week_start = Monday of each week)
    """
    if df.empty:
        return pd.DataFrame(columns=["iso_week_start", value_col])
    
    base = df.copy()
    base[date_col] = pd.to_datetime(base[date_col])

    if method == "even_by_day":
        # Expand to daily, then aggregate to weeks
        days = _expand_monthly_to_daily(base, date_col=date_col, value_col=value_col)

    elif method == "business_days":
        # Expand to daily, zero out weekends, renormalize
        days = _expand_monthly_to_daily(base, date_col=date_col, value_col=value_col)
        days["weekday"] = days["day"].dt.weekday
        
        # Zero out Saturdays (5) and Sundays (6)
        mask = days["weekday"] >= 5
        days.loc[mask, value_col] = 0
        
        # Renormalize to preserve monthly total (only across business days)
        month_key = days.groupby(level=0).ngroup()
        month_sums = days.groupby(month_key)[value_col].transform("sum").replace(0, np.nan)
        
        # Scale back up to match original monthly totals
        original_values = base.loc[days.index.get_level_values(0), value_col].values
        days[value_col] = (days[value_col] / month_sums * original_values).fillna(0)

    elif method == "proportional_to_openai" and openai_weekly is not None:
        # Allocate based on OpenAI's weekly proportions within each month
        ow = openai_weekly.copy()
        ow["week_start"] = pd.to_datetime(ow[date_col])
        ow["month"] = ow["week_start"].dt.to_period("M").dt.to_timestamp()
        
        # Calculate OpenAI monthly totals and weekly shares
        weekly_in_month = ow.groupby(["month"], as_index=False)[value_col].sum().rename(
            columns={value_col: "openai_month_total"}
        )
        ow = ow.merge(weekly_in_month, on="month", how="left")
        ow["share"] = np.where(ow["openai_month_total"] > 0, 
                              ow[value_col] / ow["openai_month_total"], 
                              np.nan)
        
        # For each Blueflame month, allocate to weeks based on OpenAI shares
        rows = []
        for _, r in base.iterrows():
            m = r[date_col].to_period("M").to_timestamp()
            candidates = ow[ow["month"] == m]
            
            if not candidates.empty and candidates["share"].notna().any():
                # Use OpenAI proportions
                for _, w in candidates.iterrows():
                    rows.append({
                        "iso_week_start": w["week_start"], 
                        value_col: r[value_col] * w["share"]
                    })
            else:
                # Fallback to even distribution across ISO weeks in the month
                week_starts = pd.date_range(m, m + pd.offsets.MonthEnd(0), freq=ISO_WEEK_START_DAY)
                
                # Ensure we include the week containing the month start
                if len(week_starts) == 0 or (len(week_starts) > 0 and week_starts[0] != m.normalize()):
                    week_starts = pd.date_range(
                        m - pd.offsets.Week(weekday=0), 
                        m + pd.offsets.MonthEnd(0), 
                        freq=ISO_WEEK_START_DAY
                    )
                
                if len(week_starts) == 0:
                    continue
                
                share = r[value_col] / len(week_starts)
                for ws in week_starts:
                    rows.append({"iso_week_start": ws.normalize(), value_col: share})
        
        out = pd.DataFrame(rows)
        if out.empty:
            return out
        return out.groupby("iso_week_start", as_index=False)[value_col].sum()

    else:
        # Default to even_by_day
        days = _expand_monthly_to_daily(base, date_col=date_col, value_col=value_col)

    # Aggregate daily records to ISO weeks (Monday start)
    days["iso_week_start"] = days["day"] - pd.to_timedelta(days["day"].dt.weekday, unit="D")
    out = days.groupby(["iso_week_start"], as_index=False)[value_col].sum()
    
    return out
