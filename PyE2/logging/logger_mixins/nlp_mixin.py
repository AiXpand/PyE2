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

### TODO flatten2dlist

class _NLPMixin(object):
  """
  Mixin for NLP functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_HistogramMixin`:
    - self.show_text_histogram
  """

  def __init__(self):
    super(_NLPMixin, self).__init__()

    try:
      from .histogram_mixin import _HistogramMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _NLPMixin without having _HistogramMixin")

    return

  def _text_to_observation(self, sent, tokenizer_func, max_size, dct_word2idx,
                           unk_word_func=None,
                           get_embeddings=True, embeddings=None,
                           PAD_ID=0, UNK_ID=1, left_pad=False, cut_left=False):
    if type(sent) != str:
      self.raise_error("sent must be a string")
    if unk_word_func is None:
      unk_word_func = lambda x: UNK_ID
    ids, tokens = tokenizer_func(sent, dct_word2idx, unk_word_func)
    ids = ids[-max_size:] if cut_left else ids[:max_size]
    n_unks = ids.count(UNK_ID)

    all_unk_indices = [i for i, x in enumerate(ids) if x == UNK_ID]
    all_unk_words = set([tokens[i] for i in all_unk_indices])

    if len(ids) < max_size:
      if left_pad:
        ids = [PAD_ID] * (max_size - len(ids)) + ids
      else:
        ids = ids + [PAD_ID] * (max_size - len(ids))
    if get_embeddings:
      np_output = np.array([embeddings[i] for i in ids])
    else:
      np_output = np.array(ids)
    return np_output, n_unks, list(all_unk_words)

  def corpus_to_batch(self, sents, tokenizer_func, max_size, dct_word2idx,
                      get_embeddings=True, embeddings=None,
                      unk_word_func=None,
                      PAD_ID=0, UNK_ID=1, left_pad=False, cut_left=False):
    """
    sents: list of sentence
    dct_word2idx : word to word-id dict
    tokenizer_func: function with signature (sentence, dict, unk_word_tokenizer_func)
    max_size : max obs size
    embeddinds :  matrix
    get_embeddings: return embeds no ids
    PAD_ID : pad id
    UNK_ID : unknown word id
    left_pad : pad to the left
    cur_left : cut to the left
    """
    if type(sents) != list or type(sents[0]) != str:
      self.raise_error("sents must be a list of strings")

    result = [
      self._text_to_observation(
        sent=x,
        tokenizer_func=tokenizer_func,
        max_size=max_size,
        dct_word2idx=dct_word2idx,
        unk_word_func=unk_word_func,
        get_embeddings=get_embeddings,
        embeddings=embeddings,
        PAD_ID=PAD_ID,
        UNK_ID=UNK_ID,
        left_pad=left_pad,
        cut_left=cut_left
      )
      for x in sents
    ]

    output, n_unks, all_unk_words = list(zip(*result))
    np_batch = np.array(list(output))
    self.P("Tokenized {} sentences to {}. Found {} unknown words: {}".format(
      len(sents), np_batch.shape, sum(n_unks), self.flatten_2d_list(list(all_unk_words))))
    return np_batch

  def load_documents(self, folder, doc_ext='.txt', label_ext='.label',
                     doc_folder=None, label_folder=None,
                     return_labels_list=True, exclude_list=[],
                     min_label_freq=0):
    """
     loads either from a _data folder or from other folder all documents and
     their labels for NLP tasks
     doc_ext : the documents extension
     label_ext : the label files extension
     doc_folder, label_folder : if documents and labels are separated...

     returns:
       list of documents (strings)
       list of labels (lists)
    """

    path = self.get_data_subfolder(folder)
    if path is None:
      path = folder if os.path.isdir(folder) else None
    if path is None:
      raise ValueError("Cannot find folder '{}'".format(path))

    if doc_folder is not None:
      path_docs = os.path.join(path, doc_folder)
    else:
      path_docs = path

    if label_folder is not None:
      path_labels = os.path.join(path, label_folder)
    else:
      path_labels = path

    if not os.path.isdir(path_docs):
      raise ValueError("Cannot find folder '{}'".format(path_docs))
    if not os.path.isdir(path_labels):
      raise ValueError("Cannot find folder '{}'".format(path_labels))

    self.P("Searching docs in '...{}' ...".format(path_docs[-25:]))
    all_files = os.listdir(path_docs)
    n_labels = 0
    lst_docs = []
    lst_labels = []
    dct_labels = {}
    set_labels = set()

    for fn in all_files:
      if fn[-len(doc_ext):] == doc_ext:
        fn_full = os.path.join(path_docs, fn)
        fn_name = fn[:-len(doc_ext)]
        fn_label = fn_name + label_ext
        fn_label_full = os.path.join(path_labels, fn_label)
        txt_doc = None
        txt_labels = None
        with open(fn_full, 'rt', encoding='utf-8') as f_doc:
          txt_doc = f_doc.read()
        if os.path.isfile(fn_label_full):
          with open(fn_label_full, 'rt') as f_lab:
            txt_labels = f_lab.readlines()
            txt_labels = [x.replace('\n', '') for x in txt_labels]
            for _str in exclude_list:
              txt_labels = [x.replace(_str, '') for x in txt_labels]
            txt_labels = list(filter(lambda x: x != '', txt_labels))
            for txt_label in txt_labels:
              if txt_label in dct_labels.keys():
                dct_labels[txt_label] += 1
              else:
                dct_labels[txt_label] = 1
            n_labels += len(txt_labels)
            set_labels.update(txt_labels)
        lst_docs.append(txt_doc)
        lst_labels.append(txt_labels)
    n_lab_files = len(lst_labels) - lst_labels.count(None)

    occurences = list(dct_labels.values())
    min_occ = np.min(occurences)
    max_occ = np.max(occurences)
    avg_occ = np.mean(occurences)
    med_occ = np.median(occurences)

    self.P("Loaded {} docs, {} lbl files:".format(len(lst_docs), n_lab_files))
    self.P("  {} unique labels with occurence/doc min/max/avg/med: {:.1f}/{:.1f}/{:.1f}/{:.1f}".format(
      len(set_labels), min_occ, max_occ, avg_occ, med_occ))
    self.P("  Overall {:.1f} lbl/doc and {} unlabeled docs".format(
      n_labels / len(lst_docs),
      lst_labels.count(None)))

    if min_label_freq > 0:
      dct_new_labels = {k: v for k, v in dct_labels.items() if v >= min_label_freq}
      set_new_labels = set_labels & set(list(dct_new_labels.keys()))
      lst_new_labels = []
      n_labels = 0
      for l in lst_labels:
        lst_new_labels.append(list(filter(lambda x: x in dct_new_labels.keys(), l)))
        n_labels += len(lst_new_labels[-1])

      lst_labels = lst_new_labels
      set_labels = set_new_labels

      occurences = list(dct_new_labels.values())
      min_occ = np.min(occurences)
      max_occ = np.max(occurences)
      avg_occ = np.mean(occurences)
      med_occ = np.median(occurences)

      self.P("  [after processing min label freq = {}]:".format(min_label_freq))
      self.P("  {} unique labels with occurence/doc min/max/avg/med: {:.1f}/{:.1f}/{:.1f}/{:.1f}".format(
        len(set_labels), min_occ, max_occ, avg_occ, med_occ))
      self.P("  Overall {:.1f} lbl/doc and {} unlabeled docs".format(
        n_labels / len(lst_docs),
        lst_labels.count(None)))
    # endif

    self.show_text_histogram(
      data=[len(x) for x in lst_docs],
      caption='Documents length (chars) distribution',
      show_both_ends=True
    )

    if return_labels_list:
      return lst_docs, lst_labels, list(set_labels)
    else:
      return lst_docs, lst_labels
