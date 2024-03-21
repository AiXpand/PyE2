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
import json
import numpy as np
import pickle

from collections import OrderedDict
from datetime import datetime as dt

class _BasicTFKerasMixin(object):
  """
  Mixin for basic tf keras functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_JSONSerializationMixin`"
    - self.save_json

  * Obs: This mixin uses also attributes/methods of `_MatplotlibMixin`:
    - self.add_copyright_to_plot
    - self.output_pyplot_image

  * Obs: This mixin uses also attributess/mthods of `_PublicTFKerasMixin`:
    - self._check_tf_avail
  """

  def __init__(self):
    super(_BasicTFKerasMixin, self).__init__()

    try:
      from .pickle_serialization_mixin import _PickleSerializationMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _BasicTFKerasMixin without having _PickleSerializationMixin")

    try:
      from .matplotlib_mixin import _MatplotlibMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _BasicTFKerasMixin without having _MatplotlibMixin")

    # self.gpu_mem = None
    # self.TF = False
    # self.TF_VER = None
    # self.TF_KERAS_VER = None
    # self.KERAS = False
    # self.KERAS_VER = None
    # self.devices = {}
    self._model_save_history = []
    self._model_save_last = []
    return

  def initializers(self, seed=123):
    import tensorflow as tf
    self._check_tf_avail()

    dct = {
      'zeros': tf.keras.initializers.Zeros(),
      'glorot_uniform': tf.keras.initializers.glorot_uniform(seed=seed),
      'uniform': tf.keras.initializers.RandomUniform(seed=seed),
      'orthogonal': tf.keras.initializers.orthogonal(seed=seed)
    }
    return dct

  def plot_keras_model(self, model, label='', verbose=True):
    """
    plots a model or generates a model text summary file
    """
    from tensorflow.keras.utils import plot_model
    if label == '':
      label = model.name
    _fn = os.path.join(self.get_output_folder(), label)
    if verbose:
      self.P("Plotting model '{}'...".format(model.name))
    try:
      fn = _fn + '_graph.png'
      res = plot_model(
        model,
        to_file=fn,
        show_shapes=True,
        show_layer_names=True,
        )
      if verbose and res is not None:
        self.P("  Model plotted and saved to '{}'.".format(fn[-40:]))
      if res is None:
        self.P("ERROR: plot_model probably failed!")
    except:
      fn = _fn + '.txt'
      s_model = self.get_keras_model_summary(model)
      with open(fn, 'wt') as f:
        f.write(s_model)
      self.P("  Model plot failed. Saved model descr in '{}'".format(fn[-40:]))
      self.P("  Please use 'conda install -c anaconda pydot' in order to plot models")
    return

  @staticmethod
  def get_keras_model_desc(model):
    """
    gets keras model short description
    """
    short_name = ""
    nr_l = len(model.layers)
    for i in range(nr_l):
      layer = model.layers[i]
      s_layer = "{}".format(layer.name)
      c_layer = s_layer.upper()[0:4]
      if c_layer == "CONV":
        c_layer = "Conv{}".format(layer.filters)

      if c_layer == "DENS":
        c_layer = "DNS{}".format(layer.units)

      if c_layer == "DROP":
        c_layer = "DRP"

      c_layer += "+"

      short_name += c_layer
    short_name = short_name[:-1]
    return short_name

  def save_model_notes(self, l_notes, model_name, cfg, DEBUG=False):
    if DEBUG:
      self.P("  Saving {} notes for {}".format(len(l_notes), model_name))
    fn = os.path.join(self.get_models_folder(), model_name + '.txt')
    with open(fn, "w") as fp:
      fp.write("Model: {} [{}]\n\n".format(
        model_name, dt.now().strftime("%Y-%m-%d %H:%M:%S")))
      for _l in l_notes:
        fp.write("{}\n".format(_l))
    self._save_model_config(model_name, cfg)
    return

  def _save_model_config(self, label, cfg, DEBUG=False):
    if cfg is not None:
      if type(cfg) is bool:
        cfg = self.config_data
      elif type(cfg) is dict:
        pass
      cfg['INFERENCE'] = label
      if DEBUG:
        self.verbose_log("  Saving cfg [{}] to models...".format(label))
      file_path = os.path.join(self.get_models_folder(), label + '.json')
      with open(file_path, 'w') as fp:
        json.dump(cfg, fp, sort_keys=False, indent=4)
    return

  def delete_model(self, model_name):
    return self.remove_model(model_name)

  def remove_model(self, model_name):
    if model_name[-3:].lower() != '.h5':
      model_name += '.h5'
    return self._delete_h5_model(model_name)

  def _delete_h5_model(self, _fn):
    folder = self.get_models_folder()
    fn = os.path.join(folder, _fn)
    result = False
    if os.path.isfile(fn):
      if '.h5' in fn:
        try:
          os.remove(fn)
          self.P("  Model file '{}' deleted!".format(fn[-50:]))
          result = True
        except:
          pass
    else:
      result = True  # file does not exist anyway
    return result

  def _delete_model_file(self, _fn):
    folder = self.get_models_folder()
    fn = os.path.join(folder, _fn)
    result = False
    if os.path.isfile(fn):
      try:
        os.remove(fn)
        self.P("  File '{}' deleted!".format(fn[-50:]))
        result = True
      except:
        pass
    else:
      result = True  # file does not exist anyway
    return result

  def clean_all_h5(self):
    folder = self.get_models_folder()
    all_files = os.listdir(folder)
    errs = []
    self.P("Cleaning all .h5 files from {}".format(folder))

    for _fn in all_files:
      if not self._delete_h5_model(_fn):
        errs.append(_fn)

    for fn in errs:
      if not self._delete_h5_model(fn):
        self.P("  ERROR: file '{}' could not be deleted".format(fn[-50:]))

    return

  def save_keras_model_def_and_weights(self, model, label, subfolder_path=None):
    """
    saves the definition of the keras model, as well as all the weights
    """

    save_folder = self.get_models_folder()
    if subfolder_path is not None:
      save_folder = os.path.join(save_folder, subfolder_path.lstrip('/'))

    if not os.path.exists(save_folder):
      os.makedirs(save_folder)

    path_model_json = os.path.join(save_folder, label + '_model_def.json')
    path_model_weights = os.path.join(save_folder, label + '_weights.h5')

    model_json = json.loads(model.to_json())
    self.save_json(model_json, path_model_json)
    self.P("Saved model json   : '...{}'".format(path_model_json[-40:]))

    model.save_weights(filepath=path_model_weights)
    self.P("Saved model weights: '...{}'".format(path_model_weights[-40:]))

    return

  def save_keras_model_weights(self, filename, model, layers, ):
    """
    save the weights of 'layers' list in file
    """
    assert len(layers) > 0, 'Unknown list of selected layers'
    file_name = os.path.join(self.get_models_folder(), filename + ".pkl")
    self.P("Saving weights for {} layers in {}...".format(len(layers), file_name))
    w_dict = OrderedDict()
    for layer in layers:
      w_dict[layer] = model.get_layer(layer).get_weights()
    with open(file_name, 'wb') as f:
      pickle.dump(w_dict, f)
    self.P("Done saving weights [{}].".format(layers), show_time=True)
    return

  def reset_saved_models_history(self):
    done = False
    while not done:
      if len(self._model_save_history) > 0:
        self._delete_model_history()
      else:
        done = True
    self._model_save_history = []
    self._model_save_last = []
    return

  def _delete_model_history(self):
    deleted_files = []
    for fn in self._model_save_history:
      if os.path.isfile(fn):
        try:
          os.remove(fn)
          deleted_files.append(fn)
        except:
          self.P("    Error deleting {}".format(fn))
      else:
        deleted_files.append(fn)
    self._model_save_history = [x for x in self._model_save_history if x not in deleted_files]
    return

  def save_keras_model(self, model, label, use_prefix=False,
                       use_single_prefix=False,
                       cfg=None,
                       include_optimizer=True, DEBUG=True,
                       only_weights=False,
                       delete_previous=False, record_previous=False,
                       save_model_and_weights=False,
                       to_models=True,
                       subfolder_path=None):
    """
    saves keras model to a file

    Parameters:
    -----------
    model : keras model
    label : name of the model
    use_prefix : will add date-time prefix if True (default False)
    use_single_prefix :  will use only one timestamp prefix for all saved models
    save_model_and_weights :  True if you want to save them both!

    subfolder_path : str, optional
      A path relative to '_models' or '_output' (_output if `to_models=False`) where the model is saved
      Default is None.
    """
    save_model = (not only_weights) or save_model_and_weights
    save_weights = only_weights or save_model_and_weights

    MDL_EXT = '.h5'
    WGH_EXT = '.h5'
    file_prefix = ""
    if label == "":
      label = self.get_keras_model_desc(model)
    label = label.replace(">", "_")  # [:30]

    if use_single_prefix:
      file_prefix = self.file_prefix
    elif use_prefix:
      file_prefix = dt.now().strftime("%Y%m%d_%H%M%S_")

    save_folder = self.get_models_folder()
    if not to_models:
      save_folder = self.get_output_folder()

    if subfolder_path is not None:
      save_folder = os.path.join(save_folder, subfolder_path.lstrip('/'))

    if not os.path.exists(save_folder):
      os.makedirs(save_folder)

    file_name = os.path.join(save_folder, file_prefix + label)
    if file_name[-len(MDL_EXT):] == MDL_EXT:
      file_name = file_name[:-len(MDL_EXT)]
    if DEBUG:
      self.verbose_log("Saving [...{}]".format(file_name[-40:]))

    save_file_name1 = None
    save_file_name2 = None
    config_file = None

    if save_weights:
      self.P("  Saving model weights...")
      self.P("    WARNING: Model weights and model config saved separately")
      save_file_name1 = file_name + "_weights" + WGH_EXT
      config_file = os.path.join(save_folder, label) + "_mdl_cfg.pkl"
      model.save_weights(save_file_name1)
      dct_cfg = model.get_config()
      with open(config_file, "wb") as f:
        pickle.dump(dct_cfg, f)
      self.P("    Saved: {}".format(save_file_name1))
      self.P("    Saved: {}".format(config_file))

    if save_model:
      self.P("  Saving model...")
      save_file_name2 = file_name + MDL_EXT
      model.save(save_file_name2, include_optimizer=include_optimizer)
      self.P("    Saved: {}".format(save_file_name2))

    self._save_model_config(label, cfg)

    if delete_previous:
      record_previous = True
      for last_saved in self._model_save_last:
        self._model_save_history.append(last_saved)
      self._delete_model_history()

    if record_previous:
      self._model_save_last = []
      for fn in [save_file_name1, save_file_name2, config_file]:
        if fn:
          self._model_save_last.append(fn)

    return file_name + MDL_EXT

  def plot_keras_history(self, keras_history_object,
                         styles=['b-', 'r-'], model_name="",
                         skip_first_epochs=0,
                         plot_pairs=True,
                         plot_all=True,
                         show=False,
                         epochs_thr=4,
                         plot_title='Training history',
                         include_prefix=True,
                         use_single_prefix=True):
    """
    skip_fist_epochs :  skips first history steps  - default 1


    PyPlot style "manual":
        '-' 	solid line style
        '--' 	dashed line style
        '-.' 	dash-dot line style
        ':' 	dotted line style
        '.' 	point marker
        ',' 	pixel marker
        'o' 	circle marker
        'v' 	triangle_down marker
        '^' 	triangle_up marker
        '<' 	triangle_left marker
        '>' 	triangle_right marker
        '1' 	tri_down marker
        '2' 	tri_up marker
        '3' 	tri_left marker
        '4' 	tri_right marker
        's' 	square marker
        'p' 	pentagon marker
        '*' 	star marker
        'h' 	hexagon1 marker
        'H' 	hexagon2 marker
        '+' 	plus marker
        'x' 	x marker
        'D' 	diamond marker
        'd' 	thin_diamond marker
        '|' 	vline marker
        '_' 	hline marker

        The following color abbreviations are supported:
        character 	color
        ‘b’ 	blue
        ‘g’ 	green
        ‘r’ 	red
        ‘c’ 	cyan
        ‘m’ 	magenta
        ‘y’ 	yellow
        ‘k’ 	black
        ‘w’ 	white
    """
    import matplotlib.pyplot as plt
    plt.style.use('ggplot')
    if styles is None:
      styles = ['b-', 'r-']

    keys_lists = [
      ['lr'],
    ]

    plots = []

    if type(keras_history_object) is dict:
      hist = keras_history_object
    else:
      hist = keras_history_object.history

    metrics = list(set(['_'.join(x.split('_')[1:]) for x in hist]))
    ds_keys = list(set(x.split('_')[0] for x in hist))

    for m in metrics:
      keys_lists.append([ds + '_' + m for ds in ds_keys])

    if len(list(hist.values())[0]) < epochs_thr:
      self.P("Cannot show training history with less than {} epochs".format(epochs_thr))
      return
    if plot_pairs:
      found_keys = []
      for keys in keys_lists:
        vals_dict = {}
        for k in keys:
          if k in hist.keys():
            vals_dict[k] = hist[k]
            found_keys.append(k)
        if vals_dict != {}:
          plots.append(vals_dict)
      if plot_all:
        for metric in hist:
          if metric not in found_keys:
            plots.append({metric: hist[metric]})
    else:
      for metric in hist:
        plots.append({metric: hist[metric]})

    nr_plots = len(plots)
    epochs = min([len(hist[x]) for x in hist])  # len(hist[list(hist.keys())[0]])
    nr_sample = min(10, epochs)
    sample_epochs = [0] + np.linspace(1, epochs - 1, nr_sample, dtype=int).tolist()
    fig, ax = plt.subplots(nr_plots, 1, figsize=(20, 5 * nr_plots), sharex=True)
    if nr_plots == 1: ax = [ax]
    max_label = 7
    min_epoch = 1
    max_epoch = epochs + 1
    self.P("Model history results:")
    for pidx, plot in enumerate(plots):
      s_plot = list(plot.keys())
      plot_name = model_name + " "
      short_name = "{}_".format(model_name)
      for i in range(len(s_plot) - 1):
        plot_name += "{} vs. ".format(s_plot[i])
        short_name += "{}VS".format(s_plot[i])
      plot_name += s_plot[-1]
      short_name += s_plot[-1]
      self.P(" Plotting '{}' for {} epochs...".format(plot_name, epochs))
      max_len = max_label
      fmt = "  {:<" + str(max_len + 1) + "} {}"
      s_vals = ""
      for j in sample_epochs:
        s_vals += "{:>5}  ".format(j)
      k = 'Epoch'
      self.P(fmt.format(k + ':', s_vals))
      for i, k in enumerate(plot.keys()):
        vals = plot[k]
        s_vals = ""
        if 'float' in str(type(vals[0])):  # isinstance fails and type fails even worse
          for j in sample_epochs:
            s_vals += "{:>5.3f}  ".format(vals[j])
        else:
          for j in sample_epochs:
            s_vals += "{:>5}  ".format(vals[j])
        self.P(fmt.format(k[:max_label] + ':', s_vals))
        vv = vals[skip_first_epochs:]
        if len(vv) > epochs:
          start_epoch = 0
          min_epoch = 0
          end_epoch = len(vv)
        else:
          start_epoch = 1
          end_epoch = len(vv) + 1
        ax[pidx].plot(np.arange(start_epoch, end_epoch), vv,
                      styles[i], label=k)
      ax[pidx].legend()
      if nr_plots > 1:
        ax[pidx].set_title(plot_name)
    ax[pidx].set_xticks(np.arange(min_epoch, max_epoch))
    self.add_copyright_to_plot(ax[-1])
    fig.tight_layout()
    fig.subplots_adjust(top=0.93)
    s = " " + plot_name if nr_plots == 1 else ""
    fig.suptitle(plot_title + s, fontsize=28)
    self.output_pyplot_image(plt=plt, label=model_name + "_TRAIN_HIST",
                             include_prefix=include_prefix,
                             use_single_prefix=use_single_prefix)
    if show:
      plt.show()  # after show a new figure is created
      self.P("Model history saved and figure shown.")
    else:
      plt.close(fig)
      self.P("Model history saved and figure closed.")
    return
