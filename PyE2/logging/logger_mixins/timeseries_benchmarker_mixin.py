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

import os
import numpy as np

class _TimeseriesBenchmakerMixin(object):
  """
  Mixin for timeseries benchmarker functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_MatplotlibMixin`:
    - self.add_copyright_to_plot
  """

  def __init__(self):
    super(_TimeseriesBenchmakerMixin, self).__init__()

    try:
      from .matplotlib_mixin import _MatplotlibMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _TimeseriesBenchmakerMixin without having _MatplotlibMixin")

    self.timeseries_benchmarker = None
    self.bp = None
    return

  def _setup_benchmarker(self, **kwargs):
    try:
      from libraries.ts import TimeseriesBenchmarker
    except:
      from ts import TimeseriesBenchmarker

    self.timeseries_benchmarker = TimeseriesBenchmarker(log=self, **kwargs)
    self.bp = self.timeseries_benchmarker
    return

  def supress_benchmarker_messages(self):
    self.P("Supressing BP messages!")
    self.timeseries_benchmarker.DEBUG = False
    return

  def get_baseline_desc(self, **kwargs):
    return self.timeseries_benchmarker.get_baseline_desc(**kwargs)

  def compare_timeseries_results(self, **kwargs):
    return self.timeseries_benchmarker.compare_timeseries_results(**kwargs)

  def multiperiod_compare_timeseries_results(self, **kwargs):
    return self.timeseries_benchmarker.multiperiod_compare_timeseries_results(**kwargs)

  def calc_timeseries_error(self, **kwargs):
    return self.timeseries_benchmarker.calc_timeseries_error(**kwargs)

  def autoregression(self, **kwargs):
    return self.timeseries_benchmarker.autoregression(**kwargs)

  def start_autoregression_benchmark(self, **kwargs):
    return self.timeseries_benchmarker.start_autoregression_benchmark(**kwargs)

  def add_autoregression_benchmark(self, **kwargs):
    return self.timeseries_benchmarker.add_autoregression_benchmark(**kwargs)

  def get_autoregression_benchmark(self, **kwargs):
    return self.timeseries_benchmarker.get_autoregression_benchmark(**kwargs)

  def get_autoregression_model_history(self, **kwargs):
    return self.timeseries_benchmarker.get_autoregression_model_history(**kwargs)

  def get_baseline_prediction(self, **kwargs):
    return self.timeseries_benchmarker.get_baseline_prediction(**kwargs)

  def debug_series(self, **kwargs):
    return self.timeseries_benchmarker.debug_series(**kwargs)

  def autoregression_baselines(self, **kwargs):
    return self.timeseries_benchmarker.autoregression_baselines(**kwargs)

  def get_model_result_dict(self, **kwargs):
    return self.timeseries_benchmarker._get_model_result_dict(**kwargs)

  def show_series(self,
                  dct_series,
                  reality=None,
                  title='Series',
                  xticks=None,
                  save_png=True,
                  vertical_lines=None,
                  style='-'
                  ):
    """
    Parameters
    ----------
    dct_series : dict
      dictionary with each series (prediction if reality is also added).

    reality : ndarray or dict, optional
      vector with reality values to be plotted against each series. The default is None.

    title : str, optional
      name of the series. The default is 'Series'.

    xticks : TYPE, optional
      labels of the series. The default is None.

    vertical_lines: list, optional
      list of x positions where to draw vertical lines

    Returns
    -------
    Name of the png file.

    """
    import matplotlib.pyplot as plt
    plt.style.use('ggplot')
    names = sorted(list(dct_series.keys()))
    values = {}
    nr_steps = dct_series[names[0]].shape[0]
    nr_series = len(dct_series)
    self.P("Plotting {} series with {} steps {}".format(
      nr_series,
      nr_steps,
      "with reality" if reality is not None else "without reality/baseline"))
    if reality is not None:
      assert type(reality) in [dict, list, np.ndarray], "reality must be a vector or dict"
    if type(reality) in [list, np.ndarray]:
      if type(reality) == np.ndarray:
        assert len(reality.shape) == 1, "reality must be a vector"
      dct_reality = {n: reality for n in names}
    else:
      dct_reality = reality

    for name in names:
      vals = dct_series[name]
      assert type(vals) in [np.ndarray, list], "the dictionary must contain vectors"
      vals = np.array(vals)
      assert len(vals.shape) == 1, "the dictionary must contain vectors"
      assert vals.shape[0] == nr_steps, "all series must have same size"
      values[name] = vals

    vlines = []
    if xticks is not None:
      assert len(xticks) == nr_steps, "x labels number different from series nr of steps"
      assert type(xticks[0]) == str, "x labels must be list of strings"
      vlines = np.argwhere(np.array(xticks) == 'Su').ravel()
      _xticks = xticks
    else:
      _xticks = [str(x) for x in range(1, nr_steps + 1)]

    _w = 13
    _h = 8 * nr_series
    fig, ax = plt.subplots(nr_series, 1, figsize=(_w, _h))

    if dct_reality is not None:
      for real_name in dct_reality:
        if real_name not in values:
          raise ValueError("Something is wrong. Reality series '{}' not found in series {}".format(
            real_name, list(values.keys())))

    for i, name in enumerate(values):
      vals = values[name]
      ax[i].plot(range(nr_steps), vals, 'b' + style, label=name)
      max_steps = nr_steps
      if dct_reality is not None:
        _real = dct_reality.get(name)
        if _real is not None:
          max_steps = max(max_steps, len(_real))
          ax[i].plot(np.arange(len(_real)), _real, 'g' + style, label='reality')
      if xticks is not None:
        ax[i].set_xticks(range(max_steps))
        ax[i].set_xticklabels(_xticks)
      ax[i].set_title('Series: ' + name)
      for vl in vlines:
        ax[i].axvline(vl, color='r')
      if vertical_lines is not None:
        if type(vertical_lines) == int:
          vertical_lines = [vertical_lines]
        for vl2 in vertical_lines:
          ax[i].axvline(vl2, color='k', linestyle='--')
      ax[i].legend()

    fig.suptitle(title, fontsize=20)

    self.add_copyright_to_plot(ax[i])

    fig.tight_layout()
    offset = max(0, (3 - nr_series) * 0.05)
    fig.subplots_adjust(top=0.95 - offset)
    if save_png:
      fn = os.path.join(self._outp_dir, title + '.png')
      plt.savefig(fn)
      self.P("Saved '{}'".format(fn))
    plt.show()
    return