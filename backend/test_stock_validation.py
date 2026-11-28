
import pandas as pd

from app.services.stock_data_service import validate_stock_data


def sample_data():
    return pd.DataFrame(
        {
            "Open": [100, 110, 120],
            "High": [110, 120, 130],
            "Low": [95, 105, 115],
            "Close": [105, 115, 125],
            "Volume": [1000, 2000, 3000],
        },
        index=pd.to_datetime([
            "2026-01-01",
            "2026-01-02",
            "2026-01-03",
        ])
    )


# Test 1: Missing values
def test_missing_values():
    data = sample_data()
    data.loc[data.index[1], "Close"] = None

    result = validate_stock_data(data)

    assert len(result) == 2
    print("PASS: Missing values handled correctly")


# Test 2: Duplicate dates
def test_duplicate_dates():
    data = sample_data()

    duplicate = data.iloc[[1]].copy()
    duplicate["Close"] = 118

    data = pd.concat([data, duplicate])

    result = validate_stock_data(data)

    assert not result.index.duplicated().any()
    assert result.loc[pd.Timestamp("2026-01-02"), "Close"] == 118

    print("PASS: Duplicate dates removed correctly")


# Test 3: Inconsistent OHLC values
def test_inconsistent_prices():
    data = sample_data()

    data.loc[data.index[0], "High"] = 90

    try:
        validate_stock_data(data)
        raise AssertionError("Invalid OHLC data was accepted")

    except ValueError as error:
        assert "inconsistent" in str(error).lower()
        print("PASS: Inconsistent OHLC data rejected correctly")


# Test 4: Negative volume
def test_negative_volume():
    data = sample_data()
    data.loc[data.index[0], "Volume"] = -100

    try:
        validate_stock_data(data)
        raise AssertionError("Negative volume was accepted")

    except ValueError as error:
        assert "volume" in str(error).lower()
        print("PASS: Negative volume rejected correctly")


if __name__ == "__main__":
    test_missing_values()
    test_duplicate_dates()
    test_inconsistent_prices()
    test_negative_volume()

    print("\nAll validation tests passed!")
