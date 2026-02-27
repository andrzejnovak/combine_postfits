
import unittest
from unittest.mock import MagicMock
from combine_postfits.utils import make_style_dict_yaml
import numpy as np

class MockHist:
    def __init__(self, value):
        self._value = value

    def values(self):
        return np.array([self._value])

    def __getattr__(self, name):
        return MagicMock()

class MockDir:
    def __init__(self, data):
        self.data = data

    def keys(self):
        return self.data.keys()

    def __getitem__(self, key):
        if key in self.data:
            mock_obj = MagicMock()
            mock_obj.to_hist.return_value = MockHist(self.data[key])
            return mock_obj
        raise KeyError(key)

    def __contains__(self, key):
        return key in self.data

def verify_cycles():
    # Setup mock data structure with cycles
    # sample1 has two cycles: cycle 1 with value 10, cycle 2 with value 20.
    # We expect only cycle 2 (value 20) to be counted.
    # sample2 has one cycle: cycle 1 with value 5.

    mock_channel_data = {
        "sample1;1": 10,
        "sample1;2": 20,
        "sample2;1": 5
    }

    mock_fit_diag = MagicMock()
    mock_fit_diag.__contains__.side_effect = lambda k: k == "shapes_fit_s"

    mock_channel_dir = MockDir(mock_channel_data)

    # Mock the directory structure: fitDiag["shapes_fit_s"]["channel1"] -> mock_channel_dir
    mock_fit_s_dir = MagicMock()
    mock_fit_s_dir.__contains__.side_effect = lambda k: k == "channel1"
    mock_fit_s_dir.__getitem__.side_effect = lambda k: mock_channel_dir if k == "channel1" else MagicMock()

    # We also need to mock the initial sample discovery which uses list(fitDiag[...].keys())
    # The function first discovers fit types, then channels, then samples.
    # avail_fit_types = ["fit_s"]
    # avail_channels = ["channel1"]

    # We need to ensure get_samples_fitDiag finds "sample1" and "sample2"
    # It does: [k[:-2] for k in fitDiag[f"shapes_{fit}/{ch}"].keys()]
    # So we need fitDiag["shapes_fit_s/channel1"].keys() to return ["sample1;1", "sample1;2", "sample2;1"]

    def get_item_side_effect(key):
        if key == "shapes_fit_s":
            return mock_fit_s_dir
        if key == "shapes_fit_s/channel1":
             return mock_channel_dir
        if key == "shapes_fit_s/channel1/sample1;1": # Mock direct access for initial scan if used
            return MagicMock()
        return MagicMock()

    mock_fit_diag.__getitem__.side_effect = get_item_side_effect

    # Mock __contains__ for the fit types
    mock_fit_diag.__contains__.side_effect = lambda k: k == "shapes_fit_s" or k == "shapes_fit_s/channel1"

    # Run the function
    # Note: make_style_dict_yaml uses fill_colors which needs a list of colors.
    # If the mock setup is incomplete, fill_colors might fail with empty cmap.
    # We ensure sample keys are found correctly.

    # Mock the keys() call for fit_diag["shapes_fit_s"] to return ["channel1;1"]
    mock_fit_s_dir.keys.return_value = ["channel1;1"]

    # Mock the keys() call for fit_diag["shapes_fit_s/channel1"]
    mock_channel_dir.keys = lambda: ["sample1;1", "sample1;2", "sample2;1"]

    # In get_samples_fitDiag, the code iterates over:
    # [k[:-2] for k in fitDiag[f"shapes_{fit}/{ch}"].keys()]
    # This keys() call is ON THE CHANNEL DIRECTORY, which is mock_channel_dir.
    # mock_channel_dir.keys() returns ["sample1;1", ...].
    # So snames becomes ["sample1", "sample1", "sample2"].
    # set(snames) -> {"sample1", "sample2"}.
    # sorted(...) -> ["sample1", "sample2"].
    # So get_samples_fitDiag should return correct keys.
    # Wait, the failure says "sample1 not found in style dict".
    # This implies sample_keys is empty or incomplete, or the subsequent loop fails.

    # Check if mock_channel_dir.keys() works as expected.
    # The MockDir class defines keys() as returning self.data.keys().
    # But later we OVERRODE it with a lambda: mock_channel_dir.keys = lambda: ...
    # This override is on the instance, but MockDir might be using the class method or something?
    # No, MockDir is a custom class.
    # However, uproot directory objects behave like dicts but also have a keys() method.
    # The code calls: fitDiag[f"shapes_{fit}/{ch}"].keys()
    # In our mock: fitDiag["shapes_fit_s/channel1"] returns mock_channel_dir.
    # So it calls mock_channel_dir.keys().

    # The MockDir implementation:
    # class MockDir:
    #    def keys(self): return self.data.keys()
    # But we did: mock_channel_dir.keys = lambda: ...
    # This replaces the method on the instance.

    # Let's verify what mock_channel_dir.keys() returns.
    print("DEBUG: mock_channel_dir.keys() ->", mock_channel_dir.keys())


    # The previous setup already does this: if key == "shapes_fit_s/channel1": return mock_channel_dir

    # Issue with fill_colors failing due to empty cmap or similar.
    # fill_colors calls plt.rcParams["axes.prop_cycle"].by_key()["color"] if cmap is None or empty.
    # But here we pass cmap="tab10".
    # The error says "len(cmap) after cleaning is 0".
    # This happens if all colors in cmap are already taken by samples.
    # In our mock, we have sample1 and sample2.
    # tab10 has 10 colors.
    # However, fill_colors implementation has a check:
    # if no_duplicates: for c in taken: if c in cmap_clean: cmap_clean.remove(c)
    # Since our mocked samples don't have colors initially, taken should be empty (except for data/total_signal which get default colors).

    # Let's ensure matplotlib is importable and has tab10
    import matplotlib.pyplot as plt
    try:
        _ = plt.get_cmap("tab10")
    except:
        # Fallback if tab10 not found (e.g. old mpl)
        pass

    style = make_style_dict_yaml(mock_fit_diag, cmap="tab10", sort=False)

    # Verification
    print("Style keys:", style.keys())

    # Check yields
    # sample1 should be 20 (from cycle 2), NOT 30 (sum) and NOT 10 (cycle 1)
    if "sample1" in style:
        yield1 = style["sample1"]["yield"]
        print(f"Yield for sample1: {yield1}")
        if yield1 == 20:
            print("SUCCESS: sample1 yield is correct (highest cycle used).")
        else:
            print(f"FAILURE: sample1 yield is {yield1}, expected 20.")
    else:
        print("FAILURE: sample1 not found in style dict.")

    if "sample2" in style:
        yield2 = style["sample2"]["yield"]
        print(f"Yield for sample2: {yield2}")
        if yield2 == 5:
            print("SUCCESS: sample2 yield is correct.")
        else:
            print(f"FAILURE: sample2 yield is {yield2}, expected 5.")

if __name__ == "__main__":
    verify_cycles()
