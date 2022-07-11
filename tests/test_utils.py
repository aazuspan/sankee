import ee

import sankee


def test_get_shared_bands_with_some_shared():
    image_list = [
        ee.Image.constant([0, 0]).rename("a", "b"),
        ee.Image.constant([0, 0]).rename("a", "c"),
        ee.Image.constant([0, 0]).rename("d", "a"),
    ]
    shared_bands = sankee.utils.get_shared_bands(image_list)
    assert shared_bands == ["a"]


def test_get_shared_bands_with_none_shared():
    image_list = [
        ee.Image.constant([0, 0]).rename("a", "b"),
        ee.Image.constant([0, 0]).rename("a", "c"),
        ee.Image.constant([0, 0]).rename("f", "g"),
    ]
    shared_bands = sankee.utils.get_shared_bands(image_list)
    assert shared_bands == []


def test_get_shared_bands_with_all_shared():
    image_list = [
        ee.Image.constant([0, 0]).rename("a", "b"),
        ee.Image.constant([0, 0]).rename("a", "b"),
    ]
    shared_bands = sankee.utils.get_shared_bands(image_list)
    assert shared_bands == ["a", "b"]
