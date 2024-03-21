"""
Copyright 2019-2022 Lummetry.AI (Knowledge Investment Group SRL). All Rights Reserved.


* NOTICE:  All information contained herein is, and remains
* the property of Knowledge Investment Group SRL.  
* The intellectual and technical concepts contained
* herein are proprietary to Knowledge Investment Group SRL
* and may be covered by Romanian and Foreign Patents,
* patents in process, and are protected by trade secret or copyright law.
* Dissemination of this information or reproduction of this material
* is strictly forbidden unless prior written permission is obtained
* from Knowledge Investment Group SRL.


@copyright: Lummetry.AI
@author: Lummetry.AI
@project: 
@description:
"""

import numpy as np
from collections import OrderedDict

class _ComplexNumpyOperationsMixin(object):
  """
  Mixin for complex numpy operations functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_ComplexNumpyOperationsMixin, self).__init__()

  @staticmethod
  def sliding_window(data, size, stepsize=1, padded=False, axis=-1, copy=True):
    """
    Calculate a sliding window over a signal
    Parameters
    ----------
    data : numpy array
        The array to be slided over.
    size : int
        The sliding window size
    stepsize : int
        The sliding window stepsize. Defaults to 1.
    axis : int
        The axis to slide over. Defaults to the last axis.
    copy : bool
        Return strided array as copy to avoid sideffects when manipulating the
        output array.
    Returns
    -------
    data : numpy array
        A matrix where row in last dimension consists of one instance
        of the sliding window.
    Notes
    -----
    - Be wary of setting `copy` to `False` as undesired sideffects with the
      output values may occurr.
    Examples
    --------
    >>> a = numpy.array([1, 2, 3, 4, 5])
    >>> sliding_window(a, size=3)
    array([[1, 2, 3],
           [2, 3, 4],
           [3, 4, 5]])
    >>> sliding_window(a, size=3, stepsize=2)
    array([[1, 2, 3],
           [3, 4, 5]])
    See Also
    --------
    pieces : Calculate number of pieces available by sliding
    """
    if axis >= data.ndim:
      raise ValueError(
        "Axis value out of range"
      )

    if stepsize < 1:
      raise ValueError(
        "Stepsize may not be zero or negative"
      )

    if size > data.shape[axis]:
      raise ValueError(
        "Sliding window size may not exceed size of selected axis"
      )

    shape = list(data.shape)
    shape[axis] = np.floor(data.shape[axis] / stepsize - size / stepsize + 1).astype(int)
    shape.append(size)

    strides = list(data.strides)
    strides[axis] *= stepsize
    strides.append(data.strides[axis])

    strided = np.lib.stride_tricks.as_strided(
      data, shape=shape, strides=strides
    )

    if copy:
      return strided.copy()
    else:
      return strided

  @staticmethod
  def np_ffill(arr):
    """
    Utilitar that uses ffill method row-wise on 2D array to fill 0 values
    and np.nan values

    Parameters
    ----------
    arr : np.ndarray (just 2D)
      The array on which is applied the method

    Returns
    -------
    out : np.ndarray
      The result

    """
    mask = arr == 0
    mask = mask | np.isnan(arr)
    idx = np.where(~mask, np.arange(mask.shape[1]), 0)
    np.maximum.accumulate(idx, axis=1, out=idx)
    out = arr[np.arange(idx.shape[0])[:, None], idx]
    return out

  # enddef

  @staticmethod
  def np_bfill(arr):
    """
    Utilitar that uses bfill method row-wise on 2D array to fill 0 values
    and np.nan values

    Parameters
    ----------
    arr : np.ndarray (just 2D)
      The array on which is applied the method

    Returns
    -------
    out : np.ndarray
      The result

    """
    mask = arr == 0
    mask = mask | np.isnan(arr)
    idx = np.where(~mask, np.arange(mask.shape[1]), mask.shape[1] - 1)
    idx = np.minimum.accumulate(idx[:, ::-1], axis=1)[:, ::-1]
    out = arr[np.arange(idx.shape[0])[:, None], idx]
    return out

  # enddef

  def distrib(self, np_v, label='', verbose=True, indent=4, digits=1):
    """
    will take a 1D numpy vector and will return the quantiles as a Pandas series
    inputs:
       `np_v`     : np.ndarray (1D) with values
       `label`    : optional printable label
       `verbose`  : show or not the distrib (default True)
       `indent`   : default indent spaces for `verbose=True`
    outputs:
      pd.Series with distribution of data including mean, median, std, etc

    """
    assert type(np_v) == np.ndarray
    assert len(np_v.shape) == 1
    import pandas as pd
    ser = pd.Series(np_v)
    info = ser.describe()
    if verbose:
      if label != '':
        self.P("{}Distrib '{}'".format(' ' * (indent // 2), label))
      max_s = len(str(round(info.max(), digits)))
      fmt = "{}{:<5}: {:>" + str(max_s) + "}"
      for k, v in info.items():
        self.P(fmt.format(' ' * indent, k, round(v, digits)))
    return info

  @staticmethod
  def idx_to_proba(idx, thr_50, thr_0):
    """
    Transforms indexes to probabilities.
    Params:
      thr_50: the index for which the probability is 0.5
      thr_0 : the index for which the probability is 0

    a1 * 0 + b1 = 1
    a1 * thr_50 + b1 = 0.5

    a2 * thr_50 + b2 = 0.5
    a2 * thr_0 + b2 = 0
    """

    b1 = 1
    a1 = -0.5 / thr_50

    a2 = 0.5 / (thr_50 - thr_0)
    b2 = -a2 * thr_0

    if type(idx) in [int, float, np.int16, np.int32, np.int64, np.float32, np.float64]:
      idx = [idx]
    if type(idx) is list:
      idx = np.array(idx)

    idx = idx * 1.0
    wh_50 = np.where(idx <= thr_50)
    wh_0 = np.where((idx > thr_50) & (idx <= thr_0))
    idx[wh_50] = a1 * idx[wh_50] + b1
    idx[wh_0] = a2 * idx[wh_0] + b2
    if thr_0 < idx.max():
      wh_abs_0 = np.where((idx > thr_0) & (idx <= idx.max()))
      idx[wh_abs_0] = 0

    return idx


  def timeseries_r2_score(self, y_true, y_pred,
                          return_series=False,
                          df_return=None,
                          name='',
                          verbose=False):
    """
      numpy implementation of r2 score for time series

      y_true, y_pred: the 2D/3D vectors ()

      return_series:  True will return the R2 for each series instead of the average

      df_return:      (default `None`) True to return a dataframe with indicators or
                      actual dataframe to concatenate to

      verbose:        (default `False`) True to log all information and indicators

      name:           (default '') name for Model column in returned stats df
    """
    import pandas as pd

    if return_series and df_return:
      raise ValueError("Can not return both series and stats dataframe")
    p_shape = y_pred.shape
    t_shape = y_true.shape
    if p_shape != t_shape:
      raise ValueError("{} != {}".format(t_shape, p_shape))
    if len(t_shape) == 3:
      if t_shape[2] > 1:
        raise ValueError("For time-series cannot compute R2 on more than one signal")
      y_pred = y_pred.squeeze(axis=-1)
      y_true = y_true.squeeze(axis=-1)
    if len(t_shape) == 1:
      raise ValueError("r2_score works only for 2D/3D tensors")
    n_series = t_shape[0]
    SS_res = np.sum(np.square(y_true - y_pred), axis=1)
    yt_means = np.mean(y_true, axis=1, keepdims=True)
    SS_tot = np.sum(np.square(y_true - yt_means), axis=1)
    SS_tot = np.clip(SS_tot, 1e-7, None)
    all_R2 = 1 - SS_res / SS_tot
    all_R2 = np.clip(all_R2, -1.5, None)
    r2_min = all_R2.min()
    r2_max = all_R2.max()
    r2p = np.percentile(all_R2, q=[25, 50, 75])
    r2_25 = r2p[0]
    r2_50 = r2p[1]
    r2_75 = r2p[2]
    above_0 = (all_R2 > 0).sum()
    above_0_sers = all_R2[all_R2 > 0]
    above_0_mean = above_0_sers.mean() if above_0_sers.size > 0 else -1
    above_15 = (all_R2 > 0.15).sum()
    dict_stats = OrderedDict({
      "R2": all_R2.mean(),
      "R2_Min": r2_min,
      "R2_Q25": r2_25,
      "R2_Q50": r2_50,
      "R2_Q75": r2_75,
      "R2_Max": r2_max,
      "s_ovr_0p": above_0 / all_R2.shape[0],
      "s_ovr_0": int(above_0),
      "s_ovr_15": above_15 / all_R2.shape[0],
      "ovr_0_avg": above_0_mean,
      "ovr_0_med": np.median(above_0_sers) if len(above_0_sers) > 0 else -1,
    })
    if verbose:
      self.P("Stats for {} series".format(n_series))
    for _stat in dict_stats:
      if verbose:
        val = dict_stats[_stat]
        _format = "  {:<11} {:>6.1f}{}" if type(val) != int else "  {:<11} {:>6}"
        self.P(_format.format(
          _stat + ":",
          val * 100 if type(val) != int else val,
          "%" if type(val) != int else ""))
      dict_stats[_stat] = [dict_stats[_stat]]
    dict_stats['Model'] = name
    if return_series:
      return all_R2
    elif df_return is not None:
      df_temp = pd.DataFrame(dict_stats)
      if isinstance(df_return, pd.DataFrame):
        return pd.concat((df_return, df_temp))
      else:
        return df_temp
    else:
      return np.mean(all_R2)

  def r2_score(*args, **kwargs):
    print("DeprecationWarning! `r2_score` is deprecated. Please use `timeseries_r2_score` instead")
    return _ComplexNumpyOperationsMixin.timeseries_r2_score(*args, **kwargs)
