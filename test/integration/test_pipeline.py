from pathlib import Path

from assetflow import Asset
from .loaders import CSVLoader, MultiCSVLoader


def test_pipeline():
    patients = Asset(
        loader=[CSVLoader(path=p) for p in Path(r"../data/simulated/generated/patients").iterdir()]
    )

    assert len(patients.load()) == 2
    assert len(patients.children) == 2
    assert patients.load()[0].collect().equals(patients.children[0].load().collect())
    assert patients.load()[1].collect().equals(patients.children[1].load().collect())

    glucometers = Asset(
        loader=CSVLoader(
            path="../data/simulated/generated/glucometers.csv"
        )
    )

    assert isinstance(glucometers.children, list)
    assert len(glucometers.children) == 0
    assert glucometers.load().collect().equals(glucometers.loader.load().collect())

    appointments = Asset(
        loader=CSVLoader(
            path="../data/simulated/generated/appointments.csv"
        )
    )

    assert isinstance(appointments.children, list)
    assert len(appointments.children) == 0
    assert appointments.load().collect().equals(appointments.loader.load().collect())

    glycemia = Asset(
        loader=MultiCSVLoader(path="../data/simulated/generated/glycemia")
    )

    assert len(glycemia.load()) > 2
    assert len(glycemia.children) > 2
    assert glycemia.load()[0].collect().equals(glycemia.children[0].load().collect())
    assert glycemia.load()[1].collect().equals(glycemia.children[1].load().collect())

    print("debug")