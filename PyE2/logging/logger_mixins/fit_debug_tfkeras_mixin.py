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

class _FitDebugTFKerasMixin(object):
  """
  Mixin for tf keras fit debug functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.

  * Obs: This mixin uses also attributes/methods of `_TimersMixin`:
    - self.start_timer
    - self.end_timer
  """

  def __init__(self):
    super(_FitDebugTFKerasMixin, self).__init__()

    try:
      from .timers_mixin import _TimersMixin
    except ModuleNotFoundError:
      raise ModuleNotFoundError("Cannot use _FitDebugTFKerasMixin without having _TimersMixin")

    return

  def fit_debug(self, model, x_train, y_train,
                first_iters=1, max_grad=10, max_weight=10,
                validation_data=None,
                batch_size=32, epochs=0, mode='keras'):
    from tensorflow.python.eager import context
    import tensorflow as tf

    K = tf.keras.backend
    mode = mode.upper()
    optimizer = tf.keras.optimizers.get(model.optimizer)
    loss = model.loss
    output_names = [x.name.split('/')[0] for x in model.outputs]
    # Prepare loss functions.
    if isinstance(loss, dict):
      for name in loss:
        if name not in output_names:
          raise ValueError(
            'Unknown entry in loss '
            'dictionary: "' + name + '". '
                                     'Only expected the following keys: ' + str(self.output_names))
      loss_functions = []
      for name in output_names:
        if name not in loss:
          self.P(
            'Output "' + name + '" missing from loss dictionary. '
                                'We assume this was done on purpose, '
                                'and we will not be expecting '
                                'any data to be passed to "' + name + '" during training.')
        loss_functions.append(tf.keras.losses.get(loss.get(name)))
    elif isinstance(loss, list):
      if len(loss) != len(model.outputs):
        raise ValueError('When passing a list as loss, '
                         'it should have one entry per model outputs. '
                         'The model has ' + str(len(model.outputs)) +
                         ' outputs, but you passed loss=' + str(loss))
      loss_functions = [tf.keras.losses.get(l) for l in loss]
    else:
      loss_function = tf.keras.losses.get(loss)
      loss_functions = [loss_function for _ in range(len(output_names))]

    if mode == 'KERAS':
      x_tensors = model.inputs
      y_tensors = []
      for output in model.outputs:
        y_tensors.append(tf.keras.layers.Input(batch_shape=output.shape))
      yh_tensors = model.outputs

      tf_loss = 0
      for i, loss_func in enumerate(loss_functions):
        tf_temp_loss = loss_func(y_tensors[i], yh_tensors[i])
        tf_loss += K.mean(tf_temp_loss)

      tf_grads = K.gradients(tf_loss, model.trainable_variables)
      get_updates = optimizer.get_updates(loss=tf_loss,
                                          params=model.trainable_variables)
      train_func = K.function(inputs=x_tensors + y_tensors,
                              outputs=[tf_loss] + tf_grads,
                              updates=get_updates)
      loss_func = K.function(inputs=x_tensors + y_tensors,
                             outputs=[tf_loss])
    elif mode == 'TF':
      raise ValueError("Not implemented yet")
    elif mode == 'EAGER':
      if not context.executing_eagerly():
        raise ValueError("Cannot debug in EAGER mode without eager execution!")
      raise ValueError("Not implemented yet")

    if isinstance(x_train, list):
      train_size = x_train[0].shape[0]
    elif isinstance(x_train, np.ndarray):
      train_size = x_train.shape[0]
      x_train = [x_train]

    if not isinstance(y_train, list):
      y_train = [y_train]

    iters = range(train_size // batch_size + 1) if first_iters in [None, 0] else range(first_iters)
    s_epochs = "{:>" + str(len(str(epochs)) + 1) + "}"
    prints = 20
    print_every = max(len(iters) // prints, 1)
    self.P("Debug training for {} epochs and {} iters".format(
      epochs, iters))
    epochs = max(epochs, 1)
    for epoch in range(epochs):
      _s = s_epochs.format(epoch + 1)
      self.P("Training epoch {}...".format(_s))
      self.start_timer("DEBUG_FIT_LOGGER_EPOCH")
      for b in iters:
        start = b * batch_size
        end = start + batch_size
        if end > train_size:
          end = train_size
        if not (end > start):
          break
        x_batch = [x[start:end] for x in x_train]
        y_batch = [y[start:end] for y in y_train]

        res = train_func(x_batch + y_batch)
        loss_after = loss_func(x_batch + y_batch)[0]
        loss = res[0]
        grads = res[1:]
        if (b % print_every) == 0:
          print("\rTraining batches {:.1f}% loss: {:.5f} loss (post GD): {:.5f}".format(
            b / len(iters) * 100, loss, loss_after
          ), end="", flush=True)
      # epoch end
      print("")
      self.debug_weights_grads(grads, model=model, max_grad=max_grad, max_weight=max_weight)
      elapsed = self.end_timer("DEBUG_FIT_LOGGER_EPOCH")
      self.P("Done epoch {} in {:.1f}s".format(_s, elapsed))
      if validation_data:
        results = model.evaluate(validation_data[0], validation_data[1], verbose=0)
        self.P("Epoch {} validation results:".format(_s))
        for i, metric in enumerate(model.metrics_names):
          self.P(" Val {:<14} {:.3f}".format(metric[:13] + ":", results[i]))
      else:
        results = model.evaluate(x_batch, y_batch, verbose=0)
        if not isinstance(results, list):
          results = [results]
        self.P("Epoch {} training results (no val data) on last batch:".format(_s))
        for i, metric in enumerate(model.metrics_names):
          self.P(" Train {:<14} {:.3f}".format(metric[:13] + ":", results[i]))

    return

  def debug_weights_grads(self, grads, model, max_grad=10, max_weight=10):
    import tensorflow.keras.backend as K
    layers_info = OrderedDict()
    lr = K.eval(model.optimizer.lr)
    var_names = []
    for i, _var in enumerate(model.trainable_variables):
      _name = _var.name.split(":")[0]
      l_name, w_name = _name.split("/")
      var_name = l_name[:15] + "/" + w_name
      var_name = var_name[:19]
      var_names.append(var_name)
    weights = model.get_weights()
    self.P(" Checking weights for model with lr={:.1e}".format(lr))
    for i, var_name in enumerate(var_names):
      _var = model.trainable_variables[i]
      var_shape = K.int_shape(_var)
      w = weights[i]
      _min = w.min()
      _max = w.max()
      _med = np.median(w)
      _avg = w.mean()
      _norm = np.linalg.norm(w)
      has_nans = np.isnan(w).any()
      aprox_zero = (w <= K.epsilon()) & (w >= -K.epsilon())
      prc_aprox_zero = aprox_zero.sum() / aprox_zero.size
      nr_big = (w >= max_weight) | (w <= -max_weight)
      prc_big = nr_big.sum() / nr_big.size
      has_issues = False
      if has_nans:
        s_issue = "  NaN weights !!!"
        has_issues = True

      if prc_aprox_zero >= 0.25:
        s_issue = "    {:.1f}% zero-weights !".format(prc_aprox_zero * 100)
        has_issues = True

      if prc_big >= 0.25:
        s_issue = "    {:.1f}% big weights !".format(prc_big * 100)
        has_issues = True

      s1 = str(var_shape)
      check = 'OK' if not has_issues else 'NOT OK'
      self.P("  Weights for  {:<19} {:<15}: {}".format(var_name, s1, check))
      if has_issues:
        self.P(s_issue)
        self.P("    Norm:    {:>8.1e}".format(_norm))
        self.P("    Range:   {:>8.1e} - {:>8.1e}".format(_min, _max))
        self.P("    Avg/Med: {:>8.1e} / {:>8.1e}".format(_avg, _med))

    self.P(" Debugging gradients")
    for i, var_name in enumerate(var_names):
      _var = model.trainable_variables[i]
      var_shape = K.int_shape(_var)
      grad = grads[i]
      has_nans = np.isnan(grad).any()
      aprox_zero = (grad <= K.epsilon()) & (grad >= -K.epsilon())
      prc_aprox_zero = aprox_zero.sum() / aprox_zero.size
      nr_big = (grad >= max_grad) | (grad <= -max_grad)
      prc_big = nr_big.sum() / nr_big.size
      has_issues = False

      if has_nans:
        s_issue = "  NaN gradient !!!"
        has_issues = True

      if prc_aprox_zero >= 0.25:
        s_issue = "    {:.1f}% zero-grads !".format(prc_aprox_zero * 100)
        has_issues = True

      if prc_big >= 0.25:
        s_issue = "    {:.1f}% big grads !".format(prc_big * 100)
        has_issues = True

      _min = grad.min()
      _max = grad.max()
      _med = np.median(grad)
      _avg = grad.mean()
      _norm = np.linalg.norm(grad)
      layer = {"shape": var_shape, "grad_min": _min, "grad_norm": _norm}
      check = 'OK' if not has_issues else 'NOT OK'
      s1 = str(var_shape)
      self.P("  Grads for  {:<19} {:<15}: {}".format(var_name, s1, check))
      if has_issues:
        self.P(s_issue)
        self.P("    Norm:    {:>8.1e}".format(_norm))
        self.P("    Range:   {:>8.1e} - {:>8.1e}".format(_min, _max))
        self.P("    Avg/Med: {:>8.1e} / {:>8.1e}".format(_avg, _med))
      layers_info[var_name] = layer
    return layers_info
