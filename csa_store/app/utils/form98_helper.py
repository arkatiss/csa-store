from datetime import datetime, timedelta


def sqlserver_weekday(dt):

    return ((dt.weekday() + 1) % 7) + 1


def calculate_week_ending_date(sc_eow_last_run):

    sc_eow_last_run = sc_eow_last_run.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    if sqlserver_weekday(sc_eow_last_run) == 1:
        return sc_eow_last_run

    return (
        sc_eow_last_run +
        timedelta(
            days=8-sqlserver_weekday(sc_eow_last_run)
        )
    )


def calculate_last_date_open(
        sc_open_days,
        week_ending_date):

    last_date_open = week_ending_date

    if "1" not in sc_open_days:
        last_date_open = week_ending_date - timedelta(days=1)

    if (
        "1" not in sc_open_days and
        "7" not in sc_open_days
    ):
        last_date_open = week_ending_date - timedelta(days=2)

    if (
        "1" not in sc_open_days and
        "7" not in sc_open_days and
        "6" not in sc_open_days
    ):
        last_date_open = week_ending_date - timedelta(days=3)

    if (
        "1" not in sc_open_days and
        "7" not in sc_open_days and
        "6" not in sc_open_days and
        "5" not in sc_open_days
    ):
        last_date_open = week_ending_date - timedelta(days=4)

    if (
        "1" not in sc_open_days and
        "7" not in sc_open_days and
        "6" not in sc_open_days and
        "5" not in sc_open_days and
        "4" not in sc_open_days
    ):
        last_date_open = week_ending_date - timedelta(days=5)

    if (
        "1" not in sc_open_days and
        "7" not in sc_open_days and
        "6" not in sc_open_days and
        "5" not in sc_open_days and
        "4" not in sc_open_days and
        "3" not in sc_open_days
    ):
        last_date_open = week_ending_date - timedelta(days=6)

    return last_date_open