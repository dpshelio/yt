from __future__ import print_function
from yt.testing import assert_equal, fake_random_ds
from yt.data_objects.particle_filters import add_particle_filter, particle_filter


def test_add_particle_filter():
    """Test particle filters created via add_particle_filter

    This accesses a deposition field using the particle filter, which was a
    problem in previous versions on this dataset because there are chunks with
    no stars in them.

    """

    def stars(pfilter, data):
        filter_field = (pfilter.filtered_type, "particle_mass")
        return data[filter_field] > 0.5

    add_particle_filter("stars", function=stars, filtered_type='all',
                        requires=["particle_mass"])
    ds = fake_random_ds(16, nprocs=8, particles=16)
    ds.add_particle_filter('stars')
    assert ('deposit', 'stars_cic') in ds.derived_field_list


def test_add_particle_filter_overriding():
    """Test the add_particle_filter overriding"""
    from yt.data_objects.particle_filters import filter_registry
    from yt.funcs import mylog

    def star_0(pfilter, data):
        pass

    def star_1(pfilter, data):
        pass

    # Use a closure to store whether the warning was called
    def closure(status):
        def warning_patch(*args, **kwargs):
            status[0] = True

        def was_called():
            return status[0]

        return warning_patch, was_called

    ## Test 1: we add a dummy particle filter
    add_particle_filter("dummy", function=star_0, filtered_type='all',
                        requires=["creation_time"])
    assert 'dummy' in filter_registry
    assert_equal(filter_registry['dummy'].function, star_0)

    ## Test 2: we add another dummy particle filter.
    ##         a warning is expected. We use the above closure to
    ##         check that.
    # Store the original warning function
    warning = mylog.warning
    monkey_warning, monkey_patch_was_called = closure([False])
    mylog.warning = monkey_warning
    add_particle_filter("dummy", function=star_1, filtered_type='all',
                        requires=["creation_time"])
    assert_equal(filter_registry['dummy'].function, star_1)
    assert_equal(monkey_patch_was_called(), True)

    # Restore the original warning function
    mylog.warning = warning

def test_particle_filter():
    """Test the particle_filter decorator"""

    @particle_filter(filtered_type='all', requires=['particle_mass'])
    def heavy_stars(pfilter, data):
        filter_field = (pfilter.filtered_type, "particle_mass")
        return data[filter_field] > 0.5

    ds = fake_random_ds(16, nprocs=8, particles=16)
    ds.add_particle_filter('heavy_stars')
    assert 'heavy_stars' in ds.particle_types
    assert ('deposit', 'heavy_stars_cic') in ds.derived_field_list

def test_particle_filter_dependency():
    """
    Test dataset add_particle_filter which should automatically add
    the dependency of the filter.
    """

    @particle_filter(filtered_type='all', requires=['particle_mass'])
    def h_stars(pfilter, data):
        filter_field = (pfilter.filtered_type, "particle_mass")
        return data[filter_field] > 0.5

    @particle_filter(filtered_type='h_stars', requires=['particle_mass'])
    def hh_stars(pfilter, data):
        filter_field = (pfilter.filtered_type, "particle_mass")
        return data[filter_field] > 0.9

    ds = fake_random_ds(16, nprocs=8, particles=16)
    ds.add_particle_filter('hh_stars')
    assert 'hh_stars' in ds.particle_types
    assert 'h_stars' in ds.particle_types
    assert ('deposit', 'hh_stars_cic') in ds.derived_field_list
    assert ('deposit', 'h_stars_cic') in ds.derived_field_list

def test_covering_grid_particle_filter():
    @particle_filter(filtered_type='all', requires=['particle_mass'])
    def heavy_stars(pfilter, data):
        filter_field = (pfilter.filtered_type, "particle_mass")
        return data[filter_field] > 0.5

    ds = fake_random_ds(16, nprocs=8, particles=16)
    ds.add_particle_filter('heavy_stars')

    for grid in ds.index.grids:
        cg = ds.covering_grid(grid.Level, grid.LeftEdge, grid.ActiveDimensions)

        assert_equal(cg['heavy_stars', 'particle_mass'].shape[0],
                     grid['heavy_stars', 'particle_mass'].shape[0])
        assert_equal(cg['heavy_stars', 'particle_mass'].shape[0],
                     grid['heavy_stars', 'particle_mass'].shape[0])
