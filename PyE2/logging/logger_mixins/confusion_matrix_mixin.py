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
import itertools

class _ConfusionMatrixMixin(object):
  """
  Mixin for confusion matrix functionalities that are attached to `libraries.libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_MatplotlibMixin`:
    - self.add_copyright_to_plot
    - self.save_plot
  """

  def __init__(self):
    super(_ConfusionMatrixMixin, self).__init__()

    try:
      from .matplotlib_mixin import _MatplotlibMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _ConfusionMatrixMixin without having _MatplotlibMixin")

    return

  def plot_confusion_matrix(self,
                            cm, classes=["0", "1"],
                            normalize=True,
                            title='Confusion matrix',
                            no_save=False,
                            cmap=None,
                            figsize=None,
                            titlefontsize=None,
                            axesfontsize=None,
                            ):
    """
    This function prints and plots the confusion matrix.
    Normalization can be applied by setting `normalize=True`.

    Parameters
    ----------
    cm : ndarray
      confusion matrix from sklearn.metric.confusion_matrix or identic format.
    classes : list of strings, optional
      label for each class. The default is ["0", "1"].
    normalize : bool, optional
      normalize cells (lines will add to 100%). The default is True.
    title : string, optional
      Title of plot. The default is 'Confusion matrix'.
    no_save : bool, optional
      skip save. The default is False.
    cmap : colormap, optional
      pyplot colormap. The default is None.
    figsize : int/tuple, optional
      int or tuple for figsize. The default is None.
    titlefontsize, axesfontsize: int, optional
      font size for title and axes


    Returns
    -------
    None.

    """

    if normalize:
      cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
      s_title = title + " [norm]"
    else:
      s_title = title + " [raw]"

    if len(classes) != cm.shape[0]:
      classes = [str(x) for x in range(cm.shape[0])]

    if len(classes) < 4:
      MIN_FIG_SIZE = 9
    else:
      MIN_FIG_SIZE = 13

    import matplotlib.pyplot as plt
    from textwrap import wrap

    if figsize is None:
      figsize = (MIN_FIG_SIZE, MIN_FIG_SIZE)
    else:
      if type(figsize) == int:
        figsize = (figsize, figsize)
      if figsize[0] < MIN_FIG_SIZE or figsize[1] < MIN_FIG_SIZE:
        raise ValueError("Figsize must be at least {} for a decent plot".format(
          MIN_FIG_SIZE))

    titlefontsize = 20 if titlefontsize is None else titlefontsize
    axesfontsize = 16 if axesfontsize is None else axesfontsize

    if cmap is None:
      cmap = plt.cm.Blues
    fig = plt.figure(figsize=figsize)
    plt.imshow(cm, cmap=cmap, interpolation='nearest')
    plt.colorbar()
    plt.ylabel(
      'Reality (each line add to total 100%)' if normalize else 'Reality (count)',
      labelpad=25,
      fontsize=axesfontsize,
    )
    plt.xlabel(
      'Predicted ' + ('percentages' if normalize else 'counts') + ' for each class',
      labelpad=25,
      fontsize=axesfontsize,
    )

    tick_marks = np.arange(start=-1, stop=cm.shape[0] + 1)
    lbs = [' '] + classes + [' ']
    plt.xticks(ticks=tick_marks, labels=lbs, rotation=45)
    plt.yticks(ticks=tick_marks, labels=lbs)

    plt.title(
      "\n".join(wrap(s_title, 30)),
      y=1.05,
      loc='center',
      # family="Times New Roman",
      fontsize=titlefontsize,
      fontweight='bold',
      color='navy',
      wrap=True,
    )

    thresh = cm.max() / 2.
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
      num = "{:.2f}".format(cm[i, j]) if normalize else cm[i, j]
      plt.text(j, i, num,
               horizontalalignment="center",
               color="white" if cm[i, j] > thresh else "black")

    self.add_copyright_to_plot(plt, push_right=True)

    # fig.tight_layout()
    # offset = max(0,(3-nr_series) * 0.05)
    # fig.subplots_adjust(top=0.95 - offset)
    if not no_save:
      _lbl = s_title.replace(" ", "_").lower()
      self.save_plot(plt, label=_lbl, include_prefix=False, just_label=True)
    plt.show()
    return

  def log_confusion_matrix(self,
                           cm=None,
                           y_true=None, y_pred=None,
                           classes=None,
                           title='Confusion Matrix',
                           normalize=None,
                           hide_zeroes=False,
                           hide_diagonal=False,
                           hide_threshold=None,
                           ):
    """
    pretty print for confusion matrixes. You must pass either a CM or y_true, y_pred
    """
    from sklearn.metrics import confusion_matrix

    if cm is None and (y_true is None or y_pred is None):
      self.raise_error("You must either have `cm` `y_true`/`y_pred`")

    if cm is not None and classes is None:
      self.raise_error("If you provide `cm` please also provide labels")

    if y_true is not None and y_pred is not None:
      classes = [str(x) for x in np.unique(y_true)]
      cm = confusion_matrix(y_true=y_true, y_pred=y_pred)

    labels = classes
    columnwidth = max([len(x) for x in labels] + [8])  # 5 is value length
    empty_cell = " " * columnwidth
    full_str = "         " + empty_cell + "Preds\n"
    n_classes = cm.shape[0]

    if len(labels) != n_classes:
      self.raise_error("Confusion matrix classes differ from number of labels")
    if n_classes > 2:
      max_lab = max([len(x) for x in labels])
      s1 = "  {:>" + str(max_lab) + "}"
      self.P("{} class breakdown:".format(title))
      self.P((s1 + " {:>7} {:>7} [{:>7} {:>7} {:>7}]").format(
        " " * max_lab,
        "TP",
        "GT",
        "REC",
        "PRE",
        "F1"
      ))
      f1scores = []
      for i, k in enumerate(labels):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        gt = cm[i].sum()
        rec = tp / gt
        pre = tp / (tp + fp)
        f1 = 2 * (pre * rec) / (pre + rec)
        f1scores.append(f1)
        self.P((s1 + ":{:>7}/{:>7} [{:>6.1f}% {:>6.1f}% {:>6.1f}%]").format(
          k, tp, gt, rec * 100, pre * 100, f1 * 100))
      f1macro = np.mean(f1scores)
      self.P("  Macro F1: {:.2f}%".format(f1macro * 100))
    if normalize is None:
      if cm.shape[0] > 2:
        normalize = True
      else:
        normalize = False

    if normalize:
      cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    full_str += "    " + empty_cell + " "
    for label in labels:
      full_str += "%{0}s".format(columnwidth) % label + " "
    full_str += "\n"
    # Print rows
    for i, label1 in enumerate(labels):
      if i == 0:
        full_str += "GT  %{0}s".format(columnwidth) % label1 + " "
      else:
        full_str += "    %{0}s".format(columnwidth) % label1 + " "
      for j in range(len(labels)):
        num = round(cm[i, j], 2) if normalize else cm[i, j]
        # cell = '{num:{fill}{width}}'.format(num=num, fill=' ', width=columnwidth)
        cell = ('{:>' + str(columnwidth) + '.2f}').format(num) if normalize else '{num:{fill}{width}}'.format(num=num,
                                                                                                              fill=' ',
                                                                                                              width=columnwidth)
        # "%{0}.0f".format(columnwidth) % cm[i, j]
        if hide_zeroes:
          cell = cell if float(cm[i, j]) != 0 else empty_cell
        if hide_diagonal:
          cell = cell if i != j else empty_cell
        if hide_threshold:
          cell = cell if cm[i, j] > hide_threshold else empty_cell
        full_str += cell + " "
      full_str += "\n"
    self.P("{}:\n{}".format(title, full_str))
    return
