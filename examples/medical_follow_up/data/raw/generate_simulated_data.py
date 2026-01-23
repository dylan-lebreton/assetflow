from datetime import date
from pathlib import Path

import numpy as np
import polars as pl


def random_dates(start, end, n, seed=None):
    rng_ = np.random.default_rng(seed)
    start = np.datetime64(start, "D")
    end = np.datetime64(end, "D")

    return (
            start
            + rng_.integers(
        0,
        (end - start).astype('timedelta64[D]').astype(int) + 1,
        size=n
    ).astype('timedelta64[D]')
    )


def random_dates_from_starts(start_dates_, end_date, seed=None):
    rng_ = np.random.default_rng(seed)

    start_dates_ = start_dates_.astype("datetime64[D]")
    end_date = np.datetime64(end_date, "D")

    max_delta = (end_date - start_dates_).astype("timedelta64[D]").astype(int)
    offsets = rng_.integers(0, max_delta + 1).astype("timedelta64[D]")

    return start_dates_ + offsets


if __name__ == "__main__":
    N = 100
    SEED = 42
    rng = np.random.default_rng(SEED)

    # ---------------------------------
    # Patients
    # ---------------------------------

    patients = (
        pl.read_csv(Path(r"./source.csv").resolve(), separator=";")
        .filter(pl.col("periode") >= 1926)
        .filter(pl.col("periode") <= 1997)
        .filter(~pl.col("prenom").str.contains(r"[ÀÂÄàâäÇçÉÈÊËéèêëÎÏîïÔÖôöÙÛÜùûü]"))
    )

    weights = patients.get_column("valeur").to_numpy()
    weights = weights.astype(float)
    weights /= weights.sum()

    idx = rng.choice(len(patients), size=N, replace=True, p=weights)

    patients = patients[idx]

    birth_seconds = rng.integers(0, 365 * 24 * 3600, size=N)
    patients = patients.with_columns(
        (pl.datetime(pl.col("periode"), 1, 1) + pl.duration(seconds=pl.Series(birth_seconds))).alias(
            "birthdate").dt.truncate("1d").cast(pl.Date))

    patients = patients.with_row_index(name="patient_id")

    patients = (
        patients.drop(["periode", "valeur"])
        .rename({"prenom": "name", "sexe": "sex"})
    )

    # ---------------------------------
    # Glucometers
    # ---------------------------------

    glucometers = pl.DataFrame({
        "gm_id": [1, 2, 3, 4, 5],
        "model_name": ["Contour Plus One",
                       "Accu-Chek Guide",
                       "FreeStyle Lite",
                       "OneTouch Verio Flex",
                       "GlucoMen Areo"],
        "manufacturer": ["Ascensia", "Roche", "Abbott", "LifeScan", "A. Minarine"],
        "year": [2016, 2017, 2015, 2016, 2018],
        "class": ["Bluetooth", "Bluetooth", "Optical", "Bluetooth", "NFC"]
    })

    # ---------------------------------
    # Appointments
    # ---------------------------------

    # Heights per patient
    # ---------------------------------

    sex = patients.get_column("sex").to_numpy()
    heights = np.where(
        sex == 1,
        rng.normal(178, 7, size=N),  # men
        rng.normal(165, 6, size=N)  # women
    )
    # bounds
    heights = np.where(sex == 1, np.clip(heights, 150, 200), np.clip(heights, 145, 185))
    appointments = patients.with_columns(
        pl.Series('height', heights).cast(pl.Int64)
    )

    # Weights per patient
    # ---------------------------------

    bmi = np.where(
        sex == 1,
        rng.normal(26, 3, size=N),  # men
        rng.normal(25, 4, size=N)  # women
    )

    weights = bmi * (heights / 100) ** 2

    # bornes poids
    weights = np.where(sex == 1, np.clip(weights, 50, 160), np.clip(weights, 40, 140))

    # ajout au dataframe patient
    appointments = appointments.with_columns([
        pl.Series("weight_mean", weights).round(1)
    ])

    # Glucometer model ID per appointment
    # ---------------------------------
    gm = glucometers
    gm_ids = gm.get_column("gm_id").to_numpy()
    gm_ids = rng.choice(gm_ids, size=len(appointments), replace=True)

    appointments = appointments.with_columns(
        pl.Series("gm_id", gm_ids)
    )

    # Dates of appointments per patient
    # ---------------------------------

    # Start date and end date for patient follow-up
    start_dates = random_dates(
        start=date(2015, 1, 1),
        end=date(2020, 1, 1),
        n=N,
        seed=SEED
    )
    end_dates = random_dates_from_starts(
        start_dates_=start_dates + np.timedelta64(32, "D"),
        end_date=date(2020, 12, 31),
        seed=SEED
    )
    appointments = (
        appointments
        .with_columns(
            pl.date_ranges(
                start=pl.Series('start_date', start_dates).dt.truncate("1mo"),
                end=pl.Series('end_date', end_dates).dt.truncate("1mo"),
                interval="1mo"
            )
            .alias("date")
        )
        .explode('date')
    )

    # Add of 1-5 days random delta for each appointment date
    days_delta = rng.integers(0, 6, size=len(appointments))
    appointments = (
        appointments
        .with_columns(
            (pl.col('date') + pl.Series(days_delta) * pl.duration(days=1)).alias("date")
        )
    )

    # Add of hour between 9h and 17h15 for each appointment date
    hour_slots = np.array([h for h in range(9 * 4, 18 * 4)])
    minute_offsets = (rng.choice(hour_slots, size=len(appointments)) * 15).astype(int)

    appointments = appointments.with_columns(
        (
                pl.col("date").cast(pl.Datetime)
                + pl.Series(minute_offsets) * pl.duration(minutes=1)
        ).alias("date")
    )

    # Weights per appointment (small delta)
    # ---------------------------------

    weight_deltas = rng.normal(loc=0, scale=1.0, size=len(appointments))  # ±1 kg variation
    appointments = appointments.with_columns(
        (pl.col("weight_mean") + pl.Series(weight_deltas)).alias("weight").round(1)
    )

    # Glycemia per appointment
    # ---------------------------------
    # Normal range ~70–110 mg/dL, but population has higher variance
    glycemia = rng.normal(loc=95, scale=15, size=len(appointments))
    glycemia = np.clip(glycemia, 60, 250)  # cap extreme outliers
    appointments = appointments.with_columns(
        pl.Series("glycemia", glycemia)
    )

    # Blood pressure per appointment
    # ---------------------------------

    # Systolic: mean 125 mmHg, Diastolic: mean 80 mmHg
    bp_sys = rng.normal(loc=125, scale=15, size=len(appointments))
    bp_dia = rng.normal(loc=80, scale=10, size=len(appointments))

    # Bound values to realistic ranges
    bp_sys = np.clip(bp_sys, 90, 200)
    bp_dia = np.clip(bp_dia, 50, 130)

    appointments = appointments.with_columns([
        pl.Series("bp_sys", bp_sys).round(0),
        pl.Series("bp_dia", bp_dia).round(0)
    ])

    # Final formatting
    # ---------------------------------

    appointments = (
        appointments
        .sample(fraction=0.9)
        .drop(
            [
                'weight_mean',
                'sex',
                'name',
                'birthdate'
            ]
        )
        .select(
            'date',
            'patient_id',
            'height',
            'weight',
            'gm_id',
            'glycemia',
            'bp_sys',
            'bp_dia'
        )
    )

    # ---------------------------------
    # Glycemia measures
    # ---------------------------------

    glycemia = (
        appointments
        .group_by('patient_id')
        .agg(
            pl.col('date').min().alias('start'),
            pl.col('date').max().alias('end')
        )
        .with_columns(
            pl.date_ranges(
                start=pl.col('start').dt.offset_by("24h"),
                end=pl.col('end').dt.offset_by("-24h"),
                interval='1d'
            )
            .alias('date')
        )
        .explode('date')
        .drop(['start', 'end'])
        .with_columns(
            pl.lit(['08', '14', '20']).alias('hour')
        )
        .explode('hour')
        .with_columns(
            pl.col('date').dt.strftime("%Y-%m-%d")
        )
        .with_columns(
            (pl.col('date') + pl.lit("T") + pl.col('hour') + pl.lit(':00:00'))
            .alias('date')
            .cast(pl.Datetime)
        )
        .drop('hour')
    )
    glycemia = (
        glycemia
        .with_columns(
            pl.Series("delta", rng.normal(loc=0, scale=5, size=len(glycemia)))
            .cast(pl.Int64)
            .cast(pl.Utf8)
            + pl.lit('m')
        )
        .with_columns(
            pl.col('date').dt.offset_by(by=pl.col('delta'))
        )
        .drop('delta')
        .join(
            appointments
            .group_by('patient_id')
            .agg(
                pl.col('gm_id').unique().first()
            ),
            on='patient_id',
            how='left'
        )
    )

    glycemia_values = rng.normal(loc=95, scale=15, size=len(glycemia))
    glycemia_values = np.clip(glycemia_values, 60, 250)  # cap extreme outliers

    glycemia = (
        glycemia
        .with_columns(
            pl.Series("glycemia", glycemia_values)
        )
    )

    print(patients)
    print(glucometers)
    print(appointments)
    print(glycemia)

    simulation_path = Path(r"./generated")
    simulation_path.mkdir(exist_ok=True, parents=True)
    patients_path = simulation_path / "patients"
    patients_path.mkdir(exist_ok=True, parents=True)

    patients.filter(pl.col('sex') == 1).write_csv(patients_path / "1.csv")
    patients.filter(pl.col('sex') == 2).write_csv(patients_path / "2.csv")

    glucometers.write_csv(r"./generated/glucometers.csv")

    appointments.write_csv(r"./generated/appointments.csv")

    for date in glycemia['date'].dt.year().unique():
        path = simulation_path / "glycemia"
        path.mkdir(exist_ok=True, parents=True)
        glycemia.filter(pl.col('date').dt.year() == date).write_csv(path / f"{date}.csv")
