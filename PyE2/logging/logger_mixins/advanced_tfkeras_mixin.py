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
@author: Lummetry.AI - Laurentiu
@project: 
@description:
"""

import os
import numpy as np

from datetime import datetime as dt

class _AdvancedTFKerasMixin(object):
  """
  Mixin for advanced tf keras functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_BasicTFKerasMixin`:
    - self.load_keras_model
    - self.save_keras_model

  * Obs: This mixin uses also attributes/methods of `_PickleSerializationMixin`:
    - self.load_pickle_from_models
  """

  def __init__(self):
    super(_AdvancedTFKerasMixin, self).__init__()

    try:
      from .basic_tfkeras_mixin import _BasicTFKerasMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _AdvancedTFKerasMixin without having _BasicTFKerasMixin")

    try:
      from .pickle_serialization_mixin import _PickleSerializationMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _AdvancedTFKerasMixin without having _PickleSerializationMixin")


    return

  @staticmethod
  def _create_layer(layer):
    import tensorflow.compat.v1 as tf
    ltype = type(layer)
    if ltype == tf.keras.layers.CuDNNLSTM:
      new_layer = tf.keras.layers.LSTM(
        units=layer.units,
        return_sequences=layer.return_sequences,
        return_state=layer.return_state,
        stateful=layer.stateful,
        name='cpu_' + layer.name,

        recurrent_activation='sigmoid',  # must!
      )
    elif ltype == tf.keras.layers.CuDNNGRU:
      new_layer = tf.keras.layers.GRU(
        units=layer.units,
        return_sequences=layer.return_sequences,
        return_state=layer.return_state,
        stateful=layer.stateful,
        name='cpu_' + layer.name,

        reset_after=True,  # must!
        recurrent_activation='sigmoid',  # must!
      )
    else:
      new_layer = layer.__class__.from_config(layer.get_config())
    return new_layer

  def model_cuda_to_cpu(self, model):
    import tensorflow.compat.v1 as tf
    new_model = tf.keras.models.clone_model(model, clone_function=_AdvancedTFKerasMixin._create_layer)
    cpus = 0
    self.P("  Converting model {} with {} layers...".format(model.name, len(model.layers)))
    for i, layer in enumerate(model.layers):
      new_layer = new_model.layers[i]
      ltype = type(layer)
      weights = layer.get_weights()
      if len(weights) > 0:
        if ltype in [tf.keras.layers.CuDNNLSTM, tf.keras.layers.CuDNNGRU]:
          new_weights = _AdvancedTFKerasMixin._convert_rnn_weights(new_layer, weights=weights)
          cpus += 1
        else:
          new_weights = weights
        new_layer.set_weights(new_weights)
    self.P("  Model {} saved with {} GPU to CPU conversions".format(model.name, cpus))
    return new_model

  def models_file_cuda_to_cpu(self, model_file):
    model_name = os.path.splitext(model_file)[0]
    model = self.load_keras_model(model_file)
    if model is not None:
      new_model = self.model_cuda_to_cpu(model)
      self.save_keras_model(new_model, label=model_name + '_cpu.h5')
    else:
      self.P("Model {} could not be loaded. Aborting conversion.".format(model_file))

  @staticmethod
  def _convert_rnn_weights(layer, weights):
    """Converts weights for RNN layers between native and CuDNN format.
    Input kernels for each gate are transposed and converted between Fortran
    and C layout, recurrent kernels are transposed. For LSTM biases are summed/
    split in half, for GRU biases are reshaped.
    Weights can be converted in both directions between `LSTM` and`CuDNNSLTM`
    and between `CuDNNGRU` and `GRU(reset_after=True)`. Default `GRU` is not
    compatible with `CuDNNGRU`.
    For missing biases in `LSTM`/`GRU` (`use_bias=False`),
    no conversion is made.
    # Arguments
        layer: Target layer instance.
        weights: List of source weights values (input kernels, recurrent
            kernels, [biases]) (Numpy arrays).
    # Returns
        A list of converted weights values (Numpy arrays).
    # Raises
        ValueError: for incompatible GRU layer/weights or incompatible biases
    """

    def transform_kernels(kernels, func, n_gates):
      """Transforms kernel for each gate separately using given function.
      # Arguments
          kernels: Stacked array of kernels for individual gates.
          func: Function applied to kernel of each gate.
          n_gates: Number of gates (4 for LSTM, 3 for GRU).
      # Returns
          Stacked array of transformed kernels.
      """
      return np.hstack([func(k) for k in np.hsplit(kernels, n_gates)])

    def transpose_input(from_cudnn):
      """Makes a function that transforms input kernels from/to CuDNN format.
      It keeps the shape, but changes between the layout (Fortran/C). Eg.:
      ```
      Keras                 CuDNN
      [[0, 1, 2],  <--->  [[0, 2, 4],
       [3, 4, 5]]          [1, 3, 5]]
      ```
      It can be passed to `transform_kernels()`.
      # Arguments
          from_cudnn: `True` if source weights are in CuDNN format, `False`
              if they're in plain Keras format.
      # Returns
          Function that converts input kernel to the other format.
      """
      order = 'F' if from_cudnn else 'C'

      def transform(kernel):
        return kernel.T.reshape(kernel.shape, order=order)

      return transform

    target_class = layer.__class__.__name__

    # convert the weights between CuDNNLSTM and LSTM
    if target_class in ['LSTM', 'CuDNNLSTM'] and len(weights) == 3:
      # determine if we're loading a CuDNNLSTM layer
      # from the number of bias weights:
      # CuDNNLSTM has (units * 8) weights; while LSTM has (units * 4)
      # if there's no bias weight in the file, skip this conversion
      units = weights[1].shape[0]
      bias_shape = weights[2].shape
      n_gates = 4

      if bias_shape == (2 * units * n_gates,):
        source = 'CuDNNLSTM'
      elif bias_shape == (units * n_gates,):
        source = 'LSTM'
      else:
        raise ValueError('Invalid bias shape: ' + str(bias_shape))

      def convert_weights(weights, from_cudnn=True):
        # transpose (and reshape) input and recurrent kernels
        kernels = transform_kernels(weights[0],
                                    transpose_input(from_cudnn),
                                    n_gates)
        recurrent_kernels = transform_kernels(weights[1], lambda k: k.T, n_gates)
        if from_cudnn:
          # merge input and recurrent biases into a single set
          biases = np.sum(np.split(weights[2], 2, axis=0), axis=0)
        else:
          # Split single set of biases evenly to two sets. The way of
          # splitting doesn't matter as long as the two sets sum is kept.
          biases = np.tile(0.5 * weights[2], 2)
        return [kernels, recurrent_kernels, biases]

      if source != target_class:
        weights = convert_weights(weights, from_cudnn=source == 'CuDNNLSTM')
    # end if LSTM

    # convert the weights between CuDNNGRU and GRU(reset_after=True)
    if target_class in ['GRU', 'CuDNNGRU'] and len(weights) == 3:
      # We can determine the source of the weights from the shape of the bias.
      # If there is no bias we skip the conversion
      # since CuDNNGRU always has biases.

      units = weights[1].shape[0]
      bias_shape = weights[2].shape
      n_gates = 3

      def convert_weights(weights, from_cudnn=True):
        kernels = transform_kernels(weights[0],
                                    transpose_input(from_cudnn),
                                    n_gates)
        recurrent_kernels = transform_kernels(weights[1], lambda k: k.T, n_gates)
        biases = np.array(weights[2]).reshape((2, -1) if from_cudnn else -1)
        return [kernels, recurrent_kernels, biases]

      if bias_shape == (2 * units * n_gates,):
        source = 'CuDNNGRU'
      elif bias_shape == (2, units * n_gates):
        source = 'GRU(reset_after=True)'
      elif bias_shape == (units * n_gates,):
        source = 'GRU(reset_after=False)'
      else:
        raise ValueError('Invalid bias shape: ' + str(bias_shape))

      if target_class == 'CuDNNGRU':
        target = 'CuDNNGRU'
      elif layer.reset_after:
        target = 'GRU(reset_after=True)'
      else:
        target = 'GRU(reset_after=False)'

      # only convert between different types
      if source != target:
        # types = (source, target)
        # if 'GRU(reset_after=False)' in types:
        #    raise ValueError('%s is not compatible with %s' % types)
        if source == 'CuDNNGRU':
          weights = convert_weights(weights, from_cudnn=True)
        elif source == 'GRU(reset_after=True)':
          weights = convert_weights(weights, from_cudnn=False)
    # end if GRU

    return weights

  @staticmethod
  def evaluate_summary(model, res):
    """
    inputs:
      model: tf.keras model
      res: results from `evaluate` or `train_on_batch` calls

    returns:
      string with the summary info
    """
    if type(res) not in [tuple, list, np.ndarray]:
      res = [res]
    metrics = model.metrics_names
    s_res = ""
    for i, metric in enumerate(metrics):
      s_res += "{}: {:.4f}  ".format(metric, res[i])
    s_res = s_res[:-1]
    return s_res

  def tfdataset_to_generator(self, tf_ds):
    """
    this function will take a prepared tf.data.Dataset
    and will create a infinite generator out of it
    Observations:
      The `tf_ds` prepared Dataset should have a predefined .batch()
      and also preferably a .prefetch()
    """
    import tensorflow as tf
    if tf.executing_eagerly():
      while True:
        for batch in tf_ds:
          yield batch
    else:
      tf_iter = tf.compat.v1.data.make_initializable_iterator(tf_ds)
      tf_batch = tf_iter.get_next()
      tf_data_init = tf_iter.initializer
      sess = tf.compat.v1.keras.backend.get_session()
      sess.run(tf_data_init)
      gen_iter = 0
      while True:
        try:
          batch = sess.run(tf_batch)
          gen_iter += 1
          yield batch
        except:
          sess.run(tf_data_init)
          self.P("Dataset finished as iter {}. Resetting iterator".format(gen_iter))
          gen_iter = 0

  def check_dataset_datetime_tensors(self, x_tensors, idx_md, idx_m, idx_wd, year,
                                     offset_month=1, offset_day=1):
    md = int(x_tensors[idx_md][0, 0, 0]) + offset_day
    wd = int(x_tensors[idx_wd][0, 0, 0])
    m = int(x_tensors[idx_m][0, 0, 0]) + offset_month
    first_day = dt(year=year, month=m, day=md)
    if wd != first_day.weekday():
      self.raise_error("Week day {} of start date {} differs from dataset {}".format(
        first_day.weekday(), first_day, wd))
    else:
      self.P("Dataset datetime start check ok: start Y:{} M:{} D:{} (wd:{}) on day {}".format(
        year, m, md, first_day.weekday(), wd))
    return

  @staticmethod
  def get_tf_optimizer(str_optimizer):
    import tensorflow.compat.v1 as tf
    str_optimizers = ['rmsprop', 'sgd', 'adam', 'nadam', 'adagrad']
    assert str_optimizer in str_optimizers

    if str_optimizer == 'rmsprop':
      return tf.train.RMSPropOptimizer
    if str_optimizer == 'sgd':
      return tf.train.GradientDescentOptimizer
    if str_optimizer == 'adam':
      return tf.train.AdamOptimizer
    if str_optimizer == 'nadam':
      return tf.contrib.opt.NadamOptimizer
    if str_optimizer == 'adagrad':
      return tf.train.AdagradOptimizer

  def save_optimizer_weights(self, optimizer, fn, subfolder_path=None):
    import tensorflow as tf
    symbolic_weights = getattr(optimizer, 'weights')
    weight_values = tf.keras.backend.batch_get_value(symbolic_weights)
    return self.save_pickle_to_models(data=weight_values, fn=fn, subfolder_path=subfolder_path)

  @staticmethod
  def safe_keras_predict(model, X, batch_size=None, verbose=0):
    import tensorflow as tf

    if batch_size is None:
      batch_size = 32

    if not isinstance(X, list):
      X = [X]

    is_numpy = isinstance(X[0], np.ndarray)

    nr_observations_per_tensor = [x.shape[0] for x in X]
    assert len(set(nr_observations_per_tensor)) == 1
    nr_obeservations = nr_observations_per_tensor[0]

    nr_batches = nr_obeservations // batch_size
    if nr_obeservations % batch_size != 0:
      nr_batches += 1

    R = range(nr_batches)
    if verbose > 0:
      from tqdm import tqdm
      R = tqdm(R)

    y_hat = None
    for batch_step in R:
      start = batch_step * batch_size
      end = (batch_step + 1) * batch_size
      X_batch = [x[start:end] for x in X]

      if is_numpy:
        X_batch = [tf.convert_to_tensor(x) for x in X_batch]

      crt_y_hat = model(X_batch)

      if not isinstance(crt_y_hat, list):
        crt_y_hat = [crt_y_hat]

      nr_outputs = len(crt_y_hat)
      crt_y_hat = [y.numpy() for y in crt_y_hat]

      if y_hat is None:
        y_hat = [[] for _ in range(nr_outputs)]

      for idx_output in range(nr_outputs):
        y_hat[idx_output].append(crt_y_hat[idx_output])
    # endfor

    y_hat = [np.concatenate(y) for y in y_hat]
    if len(y_hat) == 1:
      y_hat = y_hat[0]

    return y_hat

  def compare_keras_models(self, model1, model2):
    layers1 = model1.layers
    layers2 = model2.layers
    _equal = True
    if len(layers1) != len(layers2):
      self.P("Number of layers differs!")
      _equal = False
    if _equal:
      for i in range(len(layers1)):
        w1_list = layers1[i].get_weights()
        w2_list = layers2[i].get_weights()
        for j in range(len(w1_list)):
          w1 = w1_list[j]
          w2 = w2_list[j]
          diff = np.sum((w1 == w2) == False)
          if diff > 0:
            self.P("Found {} diffs in layers {}/{} on weights:{}".format(
              diff, layers1[i].name, layers2[i].name, j
            ))
            _equal = False
    if not _equal:
      self.P("Models comparison failed!")
    else:
      self.P("Models are equal...")
    return _equal