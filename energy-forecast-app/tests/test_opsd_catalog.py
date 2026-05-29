from energy_forecast.seeders.opsd_catalog import build_zone_catalog


def test_build_catalog_from_fake_datapackage() -> None:
    datapackage = {
        "resources": [
            {
                "path": "time_series_60min_singleindex.csv",
                "schema": {
                    "fields": [
                        {
                            "description": "Total load in DE-LU (bidding zone) in MW as published on ENTSO-E Transparency Platform",
                            "opsdProperties": {
                                "Region": "DE-LU",
                                "Variable": "load_actual_entsoe_transparency",
                            },
                        }
                    ]
                },
            }
        ]
    }

    catalog = build_zone_catalog(datapackage)

    assert catalog.to_dict("records") == [
        {
            "code": "DE-LU",
            "name": "DE-LU",
            "kind": "bidding_zone",
            "source_variable": "load_actual_entsoe_transparency",
            "source_description": "Total load in DE-LU (bidding zone) in MW as published on ENTSO-E Transparency Platform",
        }
    ]
