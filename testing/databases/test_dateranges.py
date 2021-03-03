from datetime import date

import pytest

from sources.databases.daterange_util import Daterange, DaterangeUtility


# A...B...A...B
@pytest.fixture()
def instersecting_dateranges_type_1():
    return (Daterange(date(2018, 1, 1), date(2018, 5, 5)),
            Daterange(date(2018, 3, 3), date(2018, 6, 6)))


# A...B....B...A
@pytest.fixture()
def instersecting_dateranges_type_2():
    return (Daterange(date(2018, 1, 1), date(2018, 5, 5)),
            Daterange(date(2018, 2, 5), date(2018, 4, 4)))


# A...A...B....B
@pytest.fixture()
def non_intersecting_dateranges():
    return (Daterange(date(2018, 1, 1), date(2018, 3, 7)),
            Daterange(date(2019, 2, 5), date(2019, 4, 4)))


def test_intersection_test(instersecting_dateranges_type_1,
                           instersecting_dateranges_type_2,
                           non_intersecting_dateranges):
    # ARRANGE
    assert DaterangeUtility.intersects(*instersecting_dateranges_type_1) == True
    assert DaterangeUtility.intersects(*instersecting_dateranges_type_2) == True
    assert DaterangeUtility.intersects(*non_intersecting_dateranges) == False
    # SYMMETRIC CASES
    assert DaterangeUtility.intersects(
        *reversed(instersecting_dateranges_type_1)) == True
    assert DaterangeUtility.intersects(*reversed(
        instersecting_dateranges_type_2)) == True
    assert DaterangeUtility.intersects(*reversed(
        non_intersecting_dateranges)) == False


def test_reduction_on_intersecting(instersecting_dateranges_type_1,
                                   instersecting_dateranges_type_2):
    reduced_1 = DaterangeUtility.reduce_ranges(set(
        instersecting_dateranges_type_1))
    reduced_2 = DaterangeUtility.reduce_ranges(set(
        instersecting_dateranges_type_2))

    assert reduced_1 == {Daterange(date(2018, 1, 1), date(2018, 6, 6))}
    assert reduced_2 == {Daterange(date(2018, 1, 1), date(2018, 5, 5))}


def test_reduction_on_nonintersection_does_nothing(non_intersecting_dateranges):
    reduced_1 = DaterangeUtility.reduce_ranges(set(
        non_intersecting_dateranges))
    assert reduced_1 == set(non_intersecting_dateranges)


@pytest.fixture
def complex_with_merging():
    return {Daterange(date(2018, 1, 1), date(2018, 5, 5)),
            Daterange(date(2018, 3, 3), date(2018, 6, 6)),
            Daterange(date(2018, 6, 6), date(2018, 9, 7)),

            Daterange(date(2019, 2, 5), date(2019, 4, 4)),

            Daterange(date(2020, 5, 1), date(2020, 5, 5)),
            Daterange(date(2020, 5, 5), date(2021, 4, 4))
            }


@pytest.fixture
def complex_reduction_result():
    return {Daterange(date(2018, 1, 1), date(2018, 9, 7)),
            Daterange(date(2019, 2, 5), date(2019, 4, 4)),
            Daterange(date(2020, 5, 1), date(2021, 4, 4))}


def test_complex_reduction(complex_with_merging,
                           complex_reduction_result):
    assert DaterangeUtility.reduce_ranges(
        complex_with_merging) == complex_reduction_result


# Test Remove Interval from range

# A...B...A...B
@pytest.fixture
def remove_interval_type_1():
    return (Daterange(date(2020, 5, 1), date(2020, 5, 5)),  # remove
            Daterange(date(2020, 4, 1), date(2020, 4, 6)))


# B...A...B...A
@pytest.fixture
def remove_interval_type_2():
    return (Daterange(date(2020, 4, 1), date(2020, 4, 6)),  # remove
            Daterange(date(2020, 5, 1), date(2020, 5, 5)),
            )


# A...B...B...A
@pytest.fixture
def remove_interval_type_3():
    return (Daterange(date(2020, 5, 1), date(2020, 5, 5)),  # remove
            Daterange(date(2020, 4, 1), date(2020, 6, 6)))


# B...A..A...B
@pytest.fixture
def remove_interval_type_4():
    return (Daterange(date(2019, 5, 1), date(2021, 5, 5)),  # remove
            Daterange(date(2020, 4, 1), date(2020, 4, 6)))


def test_remove_interval_from_range(remove_interval_type_1,
                                    remove_interval_type_2,
                                    remove_interval_type_3,
                                    remove_interval_type_4):

    assert DaterangeUtility.remove_interval_from_range(
        *remove_interval_type_1) == [Daterange(date(2020, 4, 1),
                                              date(2020, 5, 1))]
    assert DaterangeUtility.remove_interval_from_range(
        *remove_interval_type_2) == [Daterange(date(2020, 4, 6),
                                              date(2020, 5, 5))]
    assert DaterangeUtility.remove_interval_from_range(
        *remove_interval_type_3) == \
           [Daterange(date(2020, 4, 1), date(2020, 5, 1)),
            Daterange(date(2020, 5, 5), date(2020, 6, 6))]
    assert DaterangeUtility.remove_interval_from_range(
        *remove_interval_type_4) == []