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
    assert_series_equal(sankey._get_sorted_classes(), pd.Series([1, 2, 4, 3]), check_names=False)


def test_plot_parameters(sankey):
    """Test that plot parameters are generated correctly."""
    params = sankey._generate_plot_parameters()
    node_labels = ["start", "start", "start", "end", "end", "end", "end"]
    label = [
        "Agriculture",
        "Developed",
        "Other",
        "Agriculture",
        "Developed",
        "Forest",
        "Other",
    ]
    link_labels = [
        "<b>100%</b> of <b>Agriculture</b> remained <b>Agriculture</b>",
        "<b>50%</b> of <b>Developed</b> remained <b>Developed</b>",
        "<b>50%</b> of <b>Developed</b> became <b>Forest</b>",
        "<b>100%</b> of <b>Other</b> remained <b>Other</b>",
    ]
    node_palette = [
        "#efff6b",
        "#ff2ff8",
        "#a1a1a1",
        "#efff6b",
        "#ff2ff8",
        "#1b9d0c",
        "#a1a1a1",
    ]
    link_palette = ["#efff6b", "#ff2ff8", "#ff2ff8", "#a1a1a1"]
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


def test_duplicate_classes_merged():
    """Test that classes with identical labels and colors are merged together."""
    data = pd.DataFrame(
        {
            "start": [1, 1, 1, 2, 2, 4],
            "end": [1, 1, 1, 2, 3, 4],
        }
    )

    # The labels and palette combine classes 2, 3, and 4 into a single class "Class B"
    labels = {
        1: "Class A",
        2: "Class B",
        3: "Class B",
        4: "Class B",
    }
    palette = {
        1: "#ff0000",
        2: "#00ff00",
        3: "#00ff00",
        4: "#00ff00",
    }

    plot = sankee.plotting.SankeyPlot(
        data=data,
        labels=labels,
        palette=palette,
        title="",
        samples=None,
        label_type="class",
        theme="default",
    )

    # Classes 3 and 4 should be merged into class 2
    assert plot.data["start"].tolist() == [1, 1, 1, 2, 2, 2]
    assert plot.data["end"].tolist() == [1, 1, 1, 2, 2, 2]
    # The duplicated classes should be merged to just two observations
    assert len(plot.df) == 2
    # The correct class labels should be used
    assert plot.df["source_label"].tolist() == ["Class A", "Class B"]


def test_duplicate_labels_not_merged():
    """Test that classes with duplicated labels but distinct colors are preserved."""
    data = pd.DataFrame(
        {
            "start": [1, 1, 1, 2, 2, 4],
            "end": [1, 1, 1, 2, 3, 4],
        }
    )

    # Same labels for classes 2, 3, and 4, but different colors
    labels = {
        1: "Class A",
        2: "Class B",
        3: "Class B",
        4: "Class B",
    }
    palette = {
        1: "#ff0000",
        2: "#00ff00",
        3: "#008300",
        4: "#809c80",
    }
    plot = sankee.plotting.SankeyPlot(
        data=data,
        labels=labels,
        palette=palette,
        title="",
        samples=None,
        label_type="class",
        theme="default",
    )
    assert plot.data["start"].tolist() == [1, 1, 1, 2, 2, 4]
    assert plot.data["end"].tolist() == [1, 1, 1, 2, 3, 4]


def test_duplicate_colors_not_merged():
    """Test that classes with duplicated labels but distinct colors are preserved."""
    data = pd.DataFrame(
        {
            "start": [1, 1, 1, 2, 2, 4],
            "end": [1, 1, 1, 2, 3, 4],
        }
    )

    # Same colors for classes 2, 3, and 4, but different labels
    labels = {
        1: "Class A",
        2: "Class B",
        3: "Class C",
        4: "Class D",
    }
    palette = {
        1: "#ff0000",
        2: "#00ff00",
        3: "#00ff00",
        4: "#00ff00",
    }
    plot = sankee.plotting.SankeyPlot(
        data=data,
        labels=labels,
        palette=palette,
        title="",
        samples=None,
        label_type="class",
        theme="default",
    )
    assert plot.data["start"].tolist() == [1, 1, 1, 2, 2, 4]
    assert plot.data["end"].tolist() == [1, 1, 1, 2, 3, 4]
