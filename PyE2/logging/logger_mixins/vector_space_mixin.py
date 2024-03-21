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
from time import time as tm

class _VectorSpaceMixin(object):
  """
  Mixin for vector space functionalities that are attached to `pye2.Logger`:
    - embeddings
    - co-occurence matrix

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_MatplotlibMixin`:
    - self.add_copyright_to_plot
    - self.save_plot
  """

  def __init__(self):
    super(_VectorSpaceMixin, self).__init__()

    try:
      from .matplotlib_mixin import _MatplotlibMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _VectorSpaceMixin without having _MatplotlibMixin")

    return

  @staticmethod
  def _calc_delta(np_vsm):
    """
    method to calculate vector space model smoothing delta matrix. the input vsm can be a mco
    or even a non-square matrix
    """
    col_totals = np.array(np_vsm).sum(axis=0)
    row_totals = np.array(np_vsm).sum(axis=1)
    cm = [col_totals for _ in range(np_vsm.shape[0])]
    col_mat = np.vstack(cm)
    row_mat = row_totals.reshape((-1, 1))
    rm = [row_mat for _ in range(np_vsm.shape[1])]
    row_mat = np.hstack(rm)
    d1 = np_vsm / (np_vsm + 1)
    mins = np.minimum(col_mat, row_mat)
    d2 = mins / (mins + 1)
    delta = d1 * d2
    return delta

  @staticmethod
  def _csr_calc_delta(np_vsm):
    """
    method to calculate vector space model smoothing delta matrix. the input vsm can be a mco
    or even a non-square matrix
    """
    col_totals = np.array(np_vsm).sum(axis=0)
    row_totals = np.array(np_vsm).sum(axis=1)
    cm = [col_totals for _ in range(np_vsm.shape[0])]
    col_mat = np.vstack(cm)
    row_mat = row_totals.reshape((-1, 1))
    rm = [row_mat for _ in range(np_vsm.shape[1])]
    row_mat = np.hstack(rm)
    d1 = np_vsm / (np_vsm + 1)
    mins = np.minimum(col_mat, row_mat)
    d2 = mins / (mins + 1)
    delta = d1 * d2
    return delta

  @staticmethod
  def pmi(np_mco, positive=True, delta='raw'):
    """
    This function computes the (positive) Pointwise Mutual Information for a matrix of
    products co-occurence and includes the discounting approach

    np_mco :  np.ndarray
      The MCO matrix

    positive :  bool optional (True)
      all values will be positive (better usually)

    delta : str optional (default='raw')
      if delta is not None then the PMI will be discounted. 'pmi' will calculate
      the discount uwing the PMI and 'raw' will calculate based on MCO


    The output is a matrix where M[x,y] indicates the degree x and y co-occure together

    TODO:
      - percentual relationship strength

    """
    assert type(np_mco) in [np.ndarray]
    assert delta in [None, 'raw', 'pmi']

    str_msg = "Computing {}{}PMI on {}".format(
      "discounted ({}) ".format(delta) if delta is not None else "",
      "positive " if positive else "",
      np_mco.shape)
    np_col_totals = np_mco.sum(axis=0)
    total = np_col_totals.sum()
    np_row_totals = np_mco.sum(axis=1)
    np_expected = np.outer(np_row_totals, np_col_totals) / total
    np_oe = np_mco / np_expected
    with np.errstate(divide='ignore'):
      np_pmi = np.log(np_oe)
    np_pmi[np.isinf(np_pmi)] = 0.0
    if positive:
      np_pmi[np_pmi < 0] = 0.0
    if delta is not None:
      delta = _VectorSpaceMixin._csr_calc_delta(np_pmi if delta == 'pmi' else np_mco)
      np_pmi = np_pmi * delta
    return np_pmi.astype(np.float32)

  @staticmethod
  def csr_pmi2(csr_mco, positive=True, delta=None, batch_size=1000, DEBUG_STOP_AFTER_ITERS=0):
    """
    This function computes the (positive) Pointwise Mutual Information for a matrix of
    products co-occurence and includes the discounting approach

    np_mco :  np.ndarray
      The MCO matrix

    positive :  bool optional (True)
      all values will be positive (better usually)

    delta : str optional (default='pmi')
      if delta is not None then the PMI will be discounted. 'pmi' will calculate
      the discount uwing the PMI and 'raw' will calculate based on MCO


    The output is a matrix where M[x,y] indicates the degree x and y co-occure together

    TODO:
      - percentual relationship strength

    """
    from scipy import sparse
    assert type(csr_mco) in [sparse.csr.csr_matrix]
    assert delta in [None, 'raw', 'pmi']

    str_msg = "Computing {}{}PMI on sparse matrix {}".format(
      "discounted ({}) ".format(delta) if delta is not None else "",
      "positive " if positive else "",
      csr_mco.shape)

    np_col_totals = np.array(csr_mco.sum(axis=0)).flatten()
    np_row_totals = np.array(csr_mco.sum(axis=1)).flatten()
    total = np_col_totals.sum()
    csr_pmi = None
    batch_start = 0
    itrs = 0
    n_rows = csr_mco.shape[0]
    timings = []
    print("\r  " + str_msg + "...", flush=True, end='')
    while batch_start < n_rows:
      t_start = tm()
      batch_end = min(batch_start + batch_size, n_rows)
      np_batch_expected = np.outer(np_row_totals[batch_start:batch_end], np_col_totals) / total
      np_batch_aoe = csr_mco[batch_start:batch_end].toarray() / np_batch_expected
      np_batch_pmi = np.ma.log(np_batch_aoe).filled(0)
      if positive:
        np_batch_pmi[np_batch_pmi < 0] = 0.0
      csr_batch_pmi = sparse.csr_matrix(np_batch_pmi, dtype='float32')
      csr_pmi = sparse.vstack([csr_pmi, csr_batch_pmi], format='csr')
      t_end = tm()
      t_per_100 = (t_end - t_start) / (batch_end - batch_start) * 100
      timings.append(t_per_100)
      print("\r  " + str_msg + " {:.1f}%  - {:.3f} sec/ 100x rows".format(
        batch_end / n_rows * 100, np.mean(timings)), flush=True, end='')
      batch_start = batch_end
      itrs += 1
      if 0 < DEBUG_STOP_AFTER_ITERS <= itrs:
        break
    # end while
    if delta is not None:
      csr_delta = _VectorSpaceMixin._csr_calc_delta(csr_pmi if delta == 'pmi' else csr_mco)
      csr_pmi = csr_pmi * csr_delta
    return csr_pmi

  @staticmethod
  def csr_pmi(csr_mco, positive=True, delta=None, batch_size=2000, DEBUG_STOP_AFTER_ITERS=0):
    """
    This function computes the (positive) Pointwise Mutual Information for a matrix of
    products co-occurence and includes the discounting approach

    np_mco :  np.ndarray
      The MCO matrix

    positive :  bool optional (True)
      all values will be positive (better usually)

    delta : str optional (default='pmi')
      if delta is not None then the PMI will be discounted. 'pmi' will calculate
      the discount uwing the PMI and 'raw' will calculate based on MCO


    The output is a matrix where M[x,y] indicates the degree x and y co-occure together

    TODO:
      - percentual relationship strength

    """
    from scipy import sparse
    assert type(csr_mco) in [sparse.csr.csr_matrix]
    assert delta in [None, 'raw', 'pmi']

    str_msg = "Computing {}{}PMI on sparse matrix {}".format(
      "discounted ({}) ".format(delta) if delta is not None else "",
      "positive " if positive else "",
      csr_mco.shape)

    np_col_totals = np.array(csr_mco.sum(axis=0)).flatten()
    np_row_totals = np.array(csr_mco.sum(axis=1)).flatten()
    total = np_col_totals.sum()
    csr_pmi = None
    batch_start = 0
    itrs = 0
    n_rows = csr_mco.shape[0]
    timings = []
    print("\r  " + str_msg + "...", flush=True, end='')
    while batch_start < n_rows:
      t_start = tm()
      batch_end = min(batch_start + batch_size, n_rows)
      np_mco_batch = csr_mco[batch_start:batch_end].toarray()
      np_batch_expected = (np.outer(np_row_totals[batch_start:batch_end], np_col_totals) / total).astype(np.float32)
      np_batch_aoe = (np_mco_batch / np_batch_expected).astype(np.float32)
      csr_batch_pmi = sparse.csr_matrix(np_batch_aoe, dtype='float32')
      csr_batch_pmi.data = np.log(csr_batch_pmi.data)
      if positive:
        csr_batch_pmi[csr_batch_pmi < 0] = 0.0
      csr_pmi = sparse.vstack([csr_pmi, csr_batch_pmi], format='csr')
      t_end = tm()
      t_per_100 = (t_end - t_start) / (batch_end - batch_start) * 100
      timings.append(t_per_100)
      print("\r  " + str_msg + " {:.1f}%  - {:.3f} sec/ 100x rows".format(
        batch_end / n_rows * 100, np.mean(timings)), flush=True, end='')
      batch_start = batch_end
      itrs += 1
      if 0 < DEBUG_STOP_AFTER_ITERS <= itrs:
        break
    # end while
    if delta is not None:
      csr_delta = _VectorSpaceMixin._csr_calc_delta(csr_pmi if delta == 'pmi' else csr_mco)
      csr_pmi = csr_pmi * csr_delta
    return csr_pmi

  def get_embeds_map(self, embed_matrix, figsize=None, labels=None, colors=None, plot=True,
                     title='Embedding map', return_fig=False):
    from sklearn.manifold import TSNE
    import matplotlib.pyplot as plt
    assert len(embed_matrix.shape) == 2
    nr_embs = embed_matrix.shape[0]
    if nr_embs > 1000:
      self.P("Number of embeddings quite large. Map calculcation will take some time...")
    if labels is not None:
      assert len(labels) == nr_embs, "Number of labels {} must equal number of obs in emb space {}".format(
        len(labels), nr_embs)
    self.P("Calculating map for embeds {}...".format(embed_matrix.shape))
    tsne = TSNE(verbose=2)
    tsne.fit(embed_matrix)
    self.P(" Done calculating map for embeds {}.".format(embed_matrix.shape), show_time=True)
    if plot:
      x = tsne.embedding_[:, 0]
      y = tsne.embedding_[:, 1]
      fig, ax = plt.subplots(figsize=figsize)
      ax.scatter(x, y, c=colors)
      if labels is not None:
        for i, label in enumerate(labels):
          ax.annotate(label, (x[i], y[i]))
      plt.title(title)
      self.add_copyright_to_plot(plt)
      plt.show()
      self.save_plot(plt, label=title)
    if return_fig:
      return tsne.embedding_, plt
    else:
      return tsne.embedding_

  @staticmethod
  def _measure_changes(Y, Y_prev):
    """
    this helper function measures changes in the embedding matrix
    between previously step of the retrofiting loop and the current one
    """
    return np.abs(np.mean(np.linalg.norm(
      np.squeeze(Y_prev) - np.squeeze(Y),
      ord=2
    )))