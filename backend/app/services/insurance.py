from datetime import date, timedelta

SOURCE = "https://www.floodsmart.gov/get-insured/buy-a-policy"


def _season_end(d: date) -> date:
    end = date(d.year, 11, 30)
    return end if d <= end else date(d.year + 1, 11, 30)


async def insurance_countdown(purchase_date: str | None = None) -> dict:
    """NFIP policies generally take effect 30 days after purchase. Hurricane season ends Nov 30."""
    try:
        pd = date.fromisoformat(purchase_date) if purchase_date else date.today()
    except ValueError:
        pd = date.today()
    eff = pd + timedelta(days=30)
    end = _season_end(pd)
    covered = eff <= end
    mcode = "ins.covered" if covered else "ins.late"
    if covered:
        msg = (f"A policy bought {pd:%b %d} generally starts {eff:%b %d}. Until then you have NO flood coverage. "
               f"That is still before hurricane season ends ({end:%b %d}).")
    else:
        msg = (f"A policy bought {pd:%b %d} generally starts {eff:%b %d}, after this hurricane season ends "
               f"({end:%b %d}). Buy earlier next year: there is a 30-day wait.")
    return {"purchase_date": pd.isoformat(), "effective_date": eff.isoformat(), "days_wait": 30,
            "season_end": end.isoformat(), "covered_before_season_end": covered, "message": msg, "message_code": mcode,
            "message_params": {"pd": pd.isoformat(), "eff": eff.isoformat(), "end": end.isoformat()}, "source": SOURCE}
