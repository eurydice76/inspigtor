import collections

import numpy as np

import scipy

import scipy.stats as stats

statistical_functions = collections.OrderedDict()
statistical_functions['mean'] = np.nanmean
statistical_functions['std'] = np.nanstd
statistical_functions['median'] = np.nanmedian
statistical_functions['1st quantile'] = lambda v, *args, **kwargs: np.nanquantile(v, q=0.25, *args, **kwargs)
statistical_functions['3rd quantile'] = lambda v, *args, **kwargs: np.nanquantile(v, q=0.75, *args, **kwargs)
statistical_functions['skew'] = lambda v, *args, **kwargs: stats.skew(v, nan_policy='omit', *args, **kwargs).data
statistical_functions['kurtosis'] = lambda v, *args, **kwargs: stats.kurtosis(v, nan_policy='omit', *args, **kwargs).data
statistical_functions['n'] = lambda a, *args, **kwargs: [len([v for v in row if not np.isnan(v)]) for row in a]
