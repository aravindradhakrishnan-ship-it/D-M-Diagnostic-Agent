import pandas as pd


def get_kpi_data(engine, country: str, week: str, client: str = None, kpi_id: str = None, limit: int = 200) -> pd.DataFrame:
    """
    Fetch a small, safe slice of KPI data using the existing calculation engine.

    Args:
        engine: KPICalculationEngine instance
        country: Country filter
        week: Week filter
        client: Client filter (optional)
        kpi_id: If provided, limit to this KPI’s filtered data
        limit: Max rows to return

    Returns:
        pd.DataFrame trimmed to `limit` rows.
    """
    if not week or not country:
        return pd.DataFrame()

    if kpi_id:
        df = engine.get_filtered_kpi_data(kpi_id, country, week, client)
    else:
        # Fallback: try default source; this may be refined if needed
        df = engine.get_filtered_kpi_data(engine.catalogue.iloc[0]['kpi_id'], country, week, client)

    if df is None or df.empty:
        return pd.DataFrame()

    # Drop obvious PII-like columns (extend as needed)
    pii_like = [c for c in df.columns if 'email' in c.lower() or 'phone' in c.lower()]
    df = df.drop(columns=pii_like, errors='ignore')

    return df.head(limit)
