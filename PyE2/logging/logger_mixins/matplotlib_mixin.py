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

from datetime import datetime as dt

class _MatplotlibMixin(object):
  """
  Mixin for matplotlib functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_MatplotlibMixin, self).__init__()
    return

  @staticmethod
  def add_copyright_to_plot(plt, push_right=False, annotation=None):
    if annotation is None:
      annotation = "Lummetry.AI SEER Product Dynamics"

    if push_right:
      _right = 1.2
    else:
      _right = 1.05

    plt.annotate(
      annotation,
      xy=(_right, -0.07), xytext=(0, 2),
      xycoords=('axes fraction'),
      textcoords='offset points',
      size=9, ha='right', va='top',
      bbox=dict(boxstyle="round,pad=0.3", fc="lightgray", ec="lightgray", lw=1),
    )

    return

  def save_plot(self, plt, label='',
                include_prefix=True,
                just_label=False,
                full_path=None):
    """
    saves current figure to file
    """
    _, short_file = self.output_pyplot_image(
      plt=plt,
      label=label,
      include_prefix=include_prefix,
      just_label=just_label,
      full_path=full_path
    )

    return short_file

  def output_pyplot_image(self, plt, label='',
                          include_prefix=True,
                          use_single_prefix=True,
                          just_label=False,
                          full_path=None):
    """
    saves current figure to a file
    """
    if full_path is None:
      if include_prefix:
        file_prefix = dt.now().strftime("%Y%m%d_%H%M%S")
        if use_single_prefix:
          file_prefix = self.file_prefix
        part_file_name = "FIG_{}_{}{}".format(file_prefix, label, ".png")
      else:
        file_prefix = ""
        part_file_name = "{}{}".format(label, ".png")

      file_name = os.path.join(self._outp_dir, part_file_name)
    else:
      file_name = full_path

    _folder, _fn = os.path.split(file_name)
    self.verbose_log("Saving pic '{}' in [..{}]".format(_fn, _folder[-30:]))
    plt.savefig(file_name)
    return file_name, _fn

  def output_image(self, arr, label=''):
    """
    saves array to a file as image
    """
    label = label.replace(">", "_")
    file_prefix = dt.now().strftime("%Y%m%d_%H%M%S_")
    if ".png" not in label:
      label += '.png'
    file_name = os.path.join(self._outp_dir, file_prefix + label)
    self.verbose_log("Saving {} to figure [...{}]".format(
      arr.shape, file_name[-40:]))
    if os.path.isfile(file_name):
      self.verbose_log("Aborting image saving. File already exists.")
    else:
      import matplotlib.pyplot as plt
      plt.imsave(file_name, arr)
    return file_name

  def save_image(self, **kwargs):
    return self.output_image(**kwargs)

  @staticmethod
  def grid_plot_images(images, labels, is_matrix=False, fig_dim=None, title=None):
    import matplotlib.pyplot as plt
    n_images = len(images)
    if fig_dim is None:
      rows = int(np.round(np.sqrt(n_images)))
      columns = int(rows + 1 * (n_images != rows ** 2))
    else:
      rows, columns = fig_dim
    fig = plt.figure(figsize=(columns * 3, rows * 3))
    axs = []
    for i in range(len(images)):
      ax = fig.add_subplot(rows, columns, i + 1)
      axs.append(ax)
      if is_matrix:
        ax.matshow(images[i])
      else:
        ax.imshow(images[i])
      ax.set_title(labels[i])
    if title is not None:
      fig.suptitle(title, fontsize=30)
    plt.subplots_adjust(wspace=0.1, hspace=0.1)
    plt.show()
