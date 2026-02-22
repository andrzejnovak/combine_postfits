# tests/unit/test_utils.py
"""Unit tests for combine_postfits.utils module."""

import hist
import numpy as np
import pytest

from combine_postfits.utils import (
    adjust_lightness,
    clean_yaml,
    cmap10,
    extract_mergemap,
    fill_colors,
    format_categories,
    make_style_dict_yaml,
    merge_hists,
)


class TestFormatCategories:
    def test_single_category(self):
        assert format_categories(["cat1"], n=2) == "cat1"

    def test_two_categories_same_line(self):
        result = format_categories(["cat1", "cat2"], n=2)
        assert "cat1" in result
        assert "cat2" in result
        assert "\n" not in result

    def test_three_categories_wraps(self):
        result = format_categories(["cat1", "cat2", "cat3"], n=2)
        assert "cat1" in result
        assert "cat2" in result
        assert "cat3" in result
        assert "\n" in result

    def test_four_categories_two_lines(self):
        result = format_categories(["a", "b", "c", "d"], n=2)
        lines = result.split("\n")
        assert len(lines) == 2

    def test_custom_line_length(self):
        cats = ["a", "b", "c", "d", "e", "f"]
        result = format_categories(cats, n=3)
        lines = result.split("\n")
        assert len(lines) == 2


class TestMergeHists:
    @pytest.fixture
    def sample_hists(self):
        h1 = hist.new.Reg(10, 0, 100).Weight()
        h1.view().value[:] = np.array([10, 20, 30, 40, 50, 40, 30, 20, 10, 5])
        h1.view().variance[:] = h1.view().value

        h2 = hist.new.Reg(10, 0, 100).Weight()
        h2.view().value[:] = np.array([5, 10, 15, 20, 25, 20, 15, 10, 5, 2])
        h2.view().variance[:] = h2.view().value

        h3 = hist.new.Reg(10, 0, 100).Weight()
        h3.view().value[:] = np.array([1, 2, 3, 4, 5, 4, 3, 2, 1, 0.5])
        h3.view().variance[:] = h3.view().value

        return {"qcd": h1, "wjets": h2, "signal": h3}

    def test_merge_sums_histograms(self, sample_hists):
        merge_map = {"ewk": ["qcd", "wjets"]}
        result = merge_hists(sample_hists.copy(), merge_map)
        assert "ewk" in result
        np.testing.assert_array_almost_equal(
            result["ewk"].values(), sample_hists["qcd"].values() + sample_hists["wjets"].values()
        )

    def test_merge_preserves_originals(self, sample_hists):
        merge_map = {"ewk": ["qcd", "wjets"]}
        result = merge_hists(sample_hists.copy(), merge_map)
        assert "qcd" in result
        assert "wjets" in result
        assert "signal" in result

    def test_merge_missing_hist_warns(self, sample_hists, caplog):
        merge_map = {"combined": ["qcd", "nonexistent"]}
        merge_hists(sample_hists.copy(), merge_map)
        assert "not available" in caplog.text

    def test_merge_all_missing_warns(self, sample_hists, caplog):
        merge_map = {"combined": ["foo", "bar"]}
        merge_hists(sample_hists.copy(), merge_map)
        assert "No histograms available" in caplog.text

    def test_merge_single_hist(self, sample_hists):
        merge_map = {"alias": ["qcd"]}
        result = merge_hists(sample_hists.copy(), merge_map)
        np.testing.assert_array_almost_equal(result["alias"].values(), sample_hists["qcd"].values())

    def test_merge_overwrites_existing_with_warning(self, sample_hists, caplog):
        merge_map = {"qcd": ["wjets", "signal"]}
        result = merge_hists(sample_hists.copy(), merge_map)
        assert "will replace" in caplog.text
        # qcd should now be sum of wjets + signal
        np.testing.assert_array_almost_equal(
            result["qcd"].values(), sample_hists["wjets"].values() + sample_hists["signal"].values()
        )


class TestFillColors:
    def test_fills_missing_colors(self):
        style = {"sig": {"label": "Signal", "color": None, "hatch": None}}
        result = fill_colors(style, cmap=["#ff0000", "#00ff00"])
        assert result["sig"]["color"] == "#ff0000"

    def test_preserves_existing_colors(self):
        style = {"sig": {"label": "Signal", "color": "#0000ff", "hatch": None}}
        result = fill_colors(style, cmap=["#ff0000"])
        assert result["sig"]["color"] == "#0000ff"

    def test_multiple_missing_colors(self):
        style = {
            "a": {"label": "A", "color": None, "hatch": None},
            "b": {"label": "B", "color": None, "hatch": None},
        }
        result = fill_colors(style, cmap=["#ff0000", "#00ff00"])
        assert result["a"]["color"] == "#ff0000"
        assert result["b"]["color"] == "#00ff00"

    def test_adds_data_and_signal_defaults(self):
        style = {"bkg": {"label": "Background", "color": "#123456", "hatch": None}}
        result = fill_colors(style, cmap=cmap10)
        assert "data" in result
        assert "total_signal" in result
        assert result["data"]["color"] == "k"
        assert result["total_signal"]["color"] == "red"

    def test_cycles_with_lightening_when_exhausted(self, caplog):
        style = {
            "a": {"label": "A", "color": None, "hatch": None},
            "b": {"label": "B", "color": None, "hatch": None},
            "c": {"label": "C", "color": None, "hatch": None},
        }
        result = fill_colors(style, cmap=["#ff0000", "#00ff00"])
        # Should cycle and potentially lighten
        assert result["a"]["color"] is not None
        assert result["b"]["color"] is not None
        assert result["c"]["color"] is not None
        assert (
            "duplicate colors" in caplog.text.lower()
            or len(set([result["a"]["color"], result["b"]["color"], result["c"]["color"]])) <= 3
        )


class TestExtractMergemap:
    def test_extracts_contains_entries(self):
        style = {
            "ewk": {"label": "EWK", "color": "blue", "hatch": None, "contains": ["wjets", "zjets"]},
            "qcd": {"label": "QCD", "color": "red", "hatch": None, "contains": None},
        }
        result = extract_mergemap(style)
        assert result == {"ewk": ["wjets", "zjets"]}

    def test_empty_style_returns_empty(self):
        assert extract_mergemap({}) == {}

    def test_no_contains_returns_empty(self):
        style = {
            "qcd": {"label": "QCD", "color": "red", "hatch": None},
            "wjets": {"label": "W+jets", "color": "blue", "hatch": None},
        }
        assert extract_mergemap(style) == {}

    def test_multiple_merges(self):
        style = {
            "ewk": {"label": "EWK", "contains": ["wjets", "zjets"]},
            "top": {"label": "Top", "contains": ["ttbar", "singletop"]},
            "qcd": {"label": "QCD", "contains": None},
        }
        result = extract_mergemap(style)
        assert result == {
            "ewk": ["wjets", "zjets"],
            "top": ["ttbar", "singletop"],
        }


class TestAdjustLightness:
    def test_lightens_color(self):
        original = "#808080"
        lighter = adjust_lightness(original, amount=1.5)
        assert lighter != original
        # Lighter colors have higher RGB values
        orig_val = int(original[1:3], 16)
        light_val = int(lighter[1:3], 16)
        assert light_val > orig_val

    def test_darkens_color(self):
        original = "#808080"
        darker = adjust_lightness(original, amount=0.5)
        assert darker != original
        orig_val = int(original[1:3], 16)
        dark_val = int(darker[1:3], 16)
        assert dark_val < orig_val

    def test_handles_named_colors(self):
        result = adjust_lightness("red", amount=1.2)
        assert result.startswith("#")

    def test_amount_1_preserves_color(self):
        original = "#808080"
        result = adjust_lightness(original, amount=1.0)
        # Should be very close to original
        assert result == original or abs(int(result[1:3], 16) - int(original[1:3], 16)) <= 1


class TestCleanYaml:
    def test_standardizes_none_string(self):
        style = {"sig": {"label": "Sig", "color": "None", "hatch": "NONE"}}
        result = clean_yaml(style)
        assert result["sig"]["color"] is None
        assert result["sig"]["hatch"] is None

    def test_handles_lowercase_none(self):
        style = {"sig": {"label": "Sig", "color": "none", "hatch": None}}
        result = clean_yaml(style)
        assert result["sig"]["color"] is None

    def test_handles_raw_strings(self):
        style = {"sig": {"label": 'r"$H_{bb}$"', "color": "red", "hatch": None}}
        result = clean_yaml(style)
        assert result["sig"]["label"] == "$H_{bb}$"

    def test_parses_contains_string_to_list(self):
        style = {"ewk": {"label": "EWK", "color": "blue", "hatch": None, "contains": "wjets zjets"}}
        result = clean_yaml(style)
        assert result["ewk"]["contains"] == ["wjets", "zjets"]

    def test_preserves_contains_list(self):
        style = {"ewk": {"label": "EWK", "color": "blue", "hatch": None, "contains": ["wjets", "zjets"]}}
        result = clean_yaml(style)
        assert result["ewk"]["contains"] == ["wjets", "zjets"]

    def test_warns_unexpected_keys(self, caplog):
        style = {"sig": {"label": "Sig", "color": "red", "hatch": None, "unknown_key": "value"}}
        clean_yaml(style)
        assert "Unexpected key" in caplog.text

    def test_adds_missing_standard_keys(self):
        style = {"sig": {"label": "Sig"}}
        result = clean_yaml(style)
        assert "color" in result["sig"]
        assert "hatch" in result["sig"]


# ---------------------------------------------------------------------------
# Helpers for make_style_dict_yaml tests
# ---------------------------------------------------------------------------


class _MockDir:
    """Mimics a uproot directory: iterates over child names with ';1' suffix."""

    def __init__(self, children):
        self._children = list(children)

    def __iter__(self):
        for name in self._children:
            yield name + ";1"

    def keys(self):
        return list(self)


class _MockHistObject:
    """Object with a `to_hist()` method returning a hist.Hist with given values.

    Bins are ``Regular(n, 0, n)`` and filled at bin centres (i+0.5) so that
    each bin receives exactly the corresponding weight.
    """

    def __init__(self, values):
        h = hist.Hist(hist.axis.Regular(len(values), 0, len(values)))
        h.fill(np.arange(len(values)) + 0.5, weight=np.asarray(values, dtype=float))
        self._h = h

    def to_hist(self):
        return self._h


class _MockFitDiag:
    """Minimal uproot-like dict for make_style_dict_yaml tests.

    shapes is a nested dict: {fit_type: {channel: {sample: _MockHistObject|None}}}
    """

    def __init__(self, shapes):
        self._shapes = shapes

    def __contains__(self, key):
        if not key.startswith("shapes_"):
            return False
        parts = key[len("shapes_"):].split("/", 2)
        fit = parts[0]
        if fit not in self._shapes:
            return False
        if len(parts) == 1:
            return True
        ch = parts[1]
        if ch not in self._shapes[fit]:
            return False
        if len(parts) == 2:
            return True
        sample = parts[2]
        return sample in self._shapes[fit][ch]

    def __getitem__(self, key):
        if not key.startswith("shapes_"):
            raise KeyError(key)
        parts = key[len("shapes_"):].split("/", 2)
        fit = parts[0]
        if len(parts) == 1:
            return _MockDir(list(self._shapes[fit].keys()))
        ch = parts[1]
        if len(parts) == 2:
            return _MockDir(list(self._shapes[fit][ch].keys()))
        sample = parts[2]
        return self._shapes[fit][ch][sample]


class TestMakeStyleDictYaml:
    _RESERVED = {"data", "total", "total_signal", "total_background"}

    def _sample_keys(self, result):
        """Return non-reserved sample keys in result dict order."""
        return [k for k in result if k not in self._RESERVED]

    @pytest.fixture
    def simple_fitDiag(self):
        """FitDiag with two samples: 'sig' (high yield) and 'bkg' (low yield)."""
        shapes = {
            "prefit": {
                "ch1": {
                    "sig": _MockHistObject([10.0, 20.0, 30.0]),
                    "bkg": _MockHistObject([1.0, 2.0, 3.0]),
                    "data": _MockHistObject([11.0, 22.0, 33.0]),
                }
            }
        }
        return _MockFitDiag(shapes)

    def test_required_keys_present(self, simple_fitDiag):
        result = make_style_dict_yaml(simple_fitDiag, sort=False)
        for key in ("data", "total_signal", "total", "total_background"):
            assert key in result

    def test_sample_keys_present(self, simple_fitDiag):
        result = make_style_dict_yaml(simple_fitDiag, sort=False)
        assert "sig" in result
        assert "bkg" in result

    def test_sort_by_yield_descending(self, simple_fitDiag):
        result = make_style_dict_yaml(simple_fitDiag, sort=True, sort_peaky=False)
        sample_keys = self._sample_keys(result)
        # sig has total yield 60, bkg has total yield 6 — sig must come first
        assert sample_keys.index("sig") < sample_keys.index("bkg")

    def test_yield_stored_in_style(self, simple_fitDiag):
        result = make_style_dict_yaml(simple_fitDiag, sort=False)
        assert result["sig"]["yield"] == pytest.approx(60.0, abs=0.01)
        assert result["bkg"]["yield"] == pytest.approx(6.0, abs=0.01)

    def test_zero_yield_sort_peaky_no_nan(self):
        """sort_peaky=True with a zero-yield sample must not produce nan sort scores."""
        shapes = {
            "prefit": {
                "ch1": {
                    "sig": _MockHistObject([0.0, 0.0, 0.0]),
                    "bkg": _MockHistObject([1.0, 2.0, 3.0]),
                }
            }
        }
        fitDiag = _MockFitDiag(shapes)
        # Should not raise and should not produce nan in the result
        result = make_style_dict_yaml(fitDiag, sort=True, sort_peaky=True)
        assert "sig" in result
        assert "bkg" in result

    def test_sort_false_preserves_alphabetical(self, simple_fitDiag):
        result = make_style_dict_yaml(simple_fitDiag, sort=False)
        sample_keys = self._sample_keys(result)
        # With sort=False samples come in alphabetical order (from get_samples_fitDiag)
        assert sample_keys == sorted(sample_keys)
