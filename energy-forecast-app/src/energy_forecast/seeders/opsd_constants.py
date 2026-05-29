OPSD_VERSION = "2020-10-06"
OPSD_BASE_URL = f"https://data.open-power-system-data.org/time_series/{OPSD_VERSION}"
OPSD_RAW_FILENAME = "time_series_60min_singleindex.csv"
OPSD_DATAPACKAGE_FILENAME = "datapackage.json"
OPSD_RAW_URL = f"{OPSD_BASE_URL}/{OPSD_RAW_FILENAME}"
OPSD_DATAPACKAGE_URL = f"{OPSD_BASE_URL}/{OPSD_DATAPACKAGE_FILENAME}"

UTC_TIMESTAMP_COLUMN = "utc_timestamp"
LOAD_SUFFIX = "_load_actual_entsoe_transparency"
TARGET_VARIABLE = "load_actual_entsoe_transparency"
MIN_CONTINUOUS_HOURS = 8760

ZONES_FILENAME = "opsd_zones.csv"
