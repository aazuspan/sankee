import pandas as pd
import pytest
from pandas.testing import assert_series_equal

import sankee

from .data import TEST_DATA, TEST_DATASET


@pytest.fixture()
def sankey():
    """Generate a SankeyPlot for testing."""
    return sankee.plotting.SankeyPlot(
        data=TEST_DATA,
        labels=TEST_DATASET.labels,
        palette=TEST_DATASET.palette,
        title="",
        samples=None,
        label_type="class",
        theme="default",
    )


def test_get_sorted_classes(sankey):
    """Test that classes are correctly sorted."""
    assert_series_equal(sankey.get_sorted_classes(), pd.Series([1, 2, 4, 3]), check_names=False)


def test_plot_parameters(sankey):
    """Test that plot parameters are generated correctly."""
    params = sankey.generate_plot_parameters()
    node_labels = ["start", "start", "start", "end", "end", "end", "end"]
    label = [
        "Agriculture",
        "Developed",
        "Non-Forest Wetland",
        "Agriculture",
        "Developed",
        "Forest",
        "Non-Forest Wetland",
    ]
    link_labels = [
        "<b>100%</b> of <b>Agriculture</b> remained <b>Agriculture</b>",
        "<b>50%</b> of <b>Developed</b> remained <b>Developed</b>",
        "<b>50%</b> of <b>Developed</b> became <b>Forest</b>",
        "<b>100%</b> of <b>Non-Forest Wetland</b> remained <b>Non-Forest Wetland</b>",
    ]
    node_palette = [
        "#efff6b",
        "#ff2ff8",
        "#97ffff",
        "#efff6b",
        "#ff2ff8",
        "#1b9d0c",
        "#97ffff",
    ]
    link_palette = ["#efff6b", "#ff2ff8", "#ff2ff8", "#97ffff"]
    source = [0, 1, 1, 2]
    target = [3, 4, 5, 6]
    value = [3, 1, 1, 1]

    assert params.node_labels.tolist() == node_labels
    assert params.label.tolist() == label
    assert params.link_labels.tolist() == link_labels
    assert params.node_palette.tolist() == node_palette
    assert params.link_palette.tolist() == link_palette
    assert params.source.tolist() == source
    assert params.target.tolist() == target
    assert params.value.tolist() == value


def test_update_layout(sankey):
    """Test that `update_layout` is applied to the plot."""
    sankey.update_layout(width=128, height=256)

    assert sankey.plot.layout.width == 128
    assert sankey.plot.layout.height == 256
