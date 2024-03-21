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
import pickle

class _HistogramMixin(object):
  """
  Mixin for histogram functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_HistogramMixin, self).__init__()
    return

  def show_histogram(self, data, bins=10, caption=None, non_negative_only=True,
                     show_both_ends=False):
    return self.show_text_histogram(data, bins,
                                    caption, non_negative_only,
                                    show_both_ends)

  def show_text_histogram(self, data, bins=10, caption=None, non_negative_only=True,
                          show_both_ends=False):
    """
    displays a text histogram of input 1d array
    """
    hist = True
    data = np.array(data)
    if ('u' in data.dtype.str) or ('i' in data.dtype.str):
      hist = False

    if caption is None:
      caption = ''

    if hist:
      caption += " - Histogram"
    else:
      caption += ' - Bin-count'

    if hist:
      res = np.histogram(data, bins=bins)
      y_inp = res[0]
      x_inp = res[1]
      x_format = '{num:{fill}{width}.3f}'
    else:
      x_format = '{num:{fill}{width}.0f}'
      res = np.bincount(data)
      _min = data.min()
      _max = data.max()
      y_inp = res[_min:]
      x_inp = np.arange(_min, _max + 1)
      if non_negative_only:
        non_neg = (y_inp != 0)
        y_inp = y_inp[non_neg]
        x_inp = x_inp[non_neg]
      if bins < y_inp.shape[0]:
        if not show_both_ends:
          cutoff = bins // 2
          caption += ' (showing both {} ends)'.format(cutoff)
          y_inp = np.concatenate((y_inp[:cutoff], y_inp[-cutoff:]))
          x_inp = np.concatenate((x_inp[:cutoff], x_inp[-cutoff:]))
      else:
        show_both_ends = False

    bins = y_inp.shape[0] if bins > y_inp.shape[0] else bins
    _x = []
    _y = []
    if show_both_ends:
      self.P("{} first ({} bins):".format(caption, bins))
      for i in range(bins):
        _y.append('{num:{fill}{width}.0f}'.format(num=y_inp[i], fill=' ', width=8))
        _x.append(x_format.format(num=x_inp[i], fill=' ', width=8))
      self.P("    Y: " + ''.join([y for y in _y]))
      self.P("    X: " + ''.join([x for x in _x]))
      _x = []
      _y = []
      self.P("{} last ({} bins):".format(caption, bins))
      for i in range(x_inp.shape[0] - bins, x_inp.shape[0], 1):
        _y.append('{num:{fill}{width}.0f}'.format(num=y_inp[i], fill=' ', width=8))
        _x.append(x_format.format(num=x_inp[i], fill=' ', width=8))
      self.P("    Y: " + ''.join([y for y in _y]))
      self.P("    X: " + ''.join([x for x in _x]))
    else:
      self.P("{} ({} bins):".format(caption, bins))
      for i in range(bins):
        _y.append('{num:{fill}{width}.0f}'.format(num=y_inp[i], fill=' ', width=8))
        _x.append(x_format.format(num=x_inp[i], fill=' ', width=8))
      self.P("    Y: " + ''.join([y for y in _y]))
      self.P("    X: " + ''.join([x for x in _x]))
    return res

  @staticmethod
  def plot_histogram(distributions, colors=None, legends=None, labels=None,
                     figsize=None, dpi=None, bins=None,
                     logscale=False, xticks=None, rotation_xticks=None, title=None,
                     xlabel=None, ylabel=None, save_img_path=None,
                     close_fig=False, save_fig_pickle=False, xlim=None, ylim=None,
                     vline=None):
    """
    Plots a distribution or multiple distributions (list of ndarrays or lists)
    - distributions: should be a list, where each element in the list is a distribution
                     that will be plotted
    - colors: list which specifies the colors (as string) for each distribution
    """
    # import seaborn as sns
    import matplotlib.pyplot as plt
    plt.style.use('ggplot')
    assert type(distributions) == list, '`distributions` must be a list of lists or list of ndarrays'
    assert type(distributions[0]) in [list, np.ndarray], '`distributions` must be a list of lists or list of ndarrays'

    if legends:
      assert type(legends) == list
      assert len(distributions) == len(legends)

    if colors:
      assert type(colors) == list
      if len(distributions) > len(colors):
        colors += ['blue'] * (len(distributions) - len(colors))
    else:
      colors = ['blue'] * len(distributions)

    n_distrib = len(distributions)
    if figsize and dpi:
      figsize = (figsize[0] / dpi, figsize[1] / dpi)
    elif figsize is None:
      figsize = (13, 8)

    _w = figsize[0]
    _h = figsize[1] * n_distrib
    fig, axs = plt.subplots(n_distrib, 1, figsize=(_w, _h), dpi=dpi)

    if type(axs) not in [list, np.ndarray]:
      axs = [axs]

    for i, distribution in enumerate(distributions):
      # plot = sns.distplot(distribution, hist=True, kde=False,
      #                     bins=bins, color=colors[i], hist_kws={'edgecolor': 'black'})
      label = labels[i] if labels is not None else ''
      axs[i].hist(distribution, color=colors[i], bins=bins)
      axs[i].set_title(label, fontsize=20)
      if xticks is not None:
        axs[i].set_xticks(xticks[i])
      if xlim is not None:
        axs[i].set_xlim(xlim)
      if ylim is not None:
        axs[i].set_ylim(ylim)
      if logscale:
        axs[i].set_yscale('log')
      # if rotation_xticks is not None:
      #   plt.xticks(rotation=rotation_xticks)
      if xlabel is not None:
        axs[i].set(xlabel=xlabel)
      if ylabel is not None:
        axs[i].set(ylabel=ylabel)

      if vline is not None:
        # __min = min(distribution)
        # __max = max(distribution)
        axs[i].axvline(vline, color='k', linestyle='--', linewidth=2)

    if title is not None:  plt.set_title(title)

    fig.tight_layout()
    plt.subplots_adjust(hspace=0.15)

    from .matplotlib_mixin import _MatplotlibMixin
    _MatplotlibMixin.add_copyright_to_plot(plt)

    if save_img_path is not None:
      if not save_img_path.endswith('.png'):
        save_img_path += '.png'
      fig.savefig(save_img_path)
      if save_fig_pickle:
        with open(save_img_path + '.pickle', 'wb') as handle:
          pickle.dump(fig, handle, protocol=pickle.HIGHEST_PROTOCOL)

    if close_fig: plt.close()
    return


