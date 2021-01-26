import collections

import numpy as np

import scipy.stats as stats


def skew_functor(array, nan_policy='omit', **kwargs):
    """Return the skewness value of the array
    """

    skew = stats.skew(array, nan_policy=nan_policy, **kwargs)

    value = skew.data.item() if np.isnan(array).any() else skew

    return value


def kurtosis_functor(array, nan_policy='omit', **kwargs):
    """Return the kurtosis value of the array
    """

    kurtosis = stats.kurtosis(array, nan_policy=nan_policy, **kwargs)

    return kurtosis


statistical_functions = collections.OrderedDict()
statistical_functions['mean'] = np.nanmean
statistical_functions['std'] = np.nanstd
statistical_functions['median'] = np.nanmedian
statistical_functions['1st quantile'] = lambda v, *args, **kwargs: np.nanquantile(v, q=0.25, *args, **kwargs)
statistical_functions['3rd quantile'] = lambda v, *args, **kwargs: np.nanquantile(v, q=0.75, *args, **kwargs)
statistical_functions['skew'] = lambda v, *args, **kwargs: skew_functor(v, nan_policy='omit', *args, **kwargs)
statistical_functions['kurtosis'] = lambda v, *args, **kwargs: kurtosis_functor(v, nan_policy='omit', *args, **kwargs)
statistical_functions['n'] = lambda a, *args, **kwargs: np.count_nonzero(~np.isnan(a))
