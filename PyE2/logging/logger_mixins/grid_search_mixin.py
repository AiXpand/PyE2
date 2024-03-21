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

import itertools
from collections import OrderedDict

class _GridSearchMixin(object):
  """
  Mixin for grid search functionalities that are attached to `pye2.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `pye2.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_GridSearchMixin, self).__init__()
    return

  def get_grid_iterations(self, params_grid, exceptions=None, fixed=None, priority_keys=None, verbose=2, **kwargs):
    """
    this function si a simple wrapper around basic grid search utilities

    Parameters:
    -----------
    params_grid : the actual grid dict where each param is a list

    exceptions : list of exceptions - see `grid_pos_to_params`

    priority_keys : list of keys on which the iterations will be grouped.

    verbose : int, optional
      Logging verbosity. Set 0 for no prints. Set 1 for summar prints. Set >=2 for DEBUG prints.
      Verbosity >= 2 accomodates the old parameter DEBUG.
      Default is 2.

    **kwargs:
      Available for backward compatibility.

    Returns:
    --------
      list with dictionaries
    """

    if kwargs.get('DEBUG', False):
      verbose = 2

    if verbose >= 1:
      self.P("Generating grid-search iterations from {} params dictionary".format(len(params_grid)))

    combs, params = self.grid_dict_to_values(params_grid=params_grid, priority_keys=priority_keys)
    iterations = []
    skipped = []
    n_options = len(combs)
    for i in range(n_options):
      comb = combs[i]
      func_args = self.grid_pos_to_params(comb, params, exceptions=exceptions, fixed=fixed)
      if func_args is None:
        skipped.append(self.grid_pos_to_params(comb, params))
      else:
        iterations.append(func_args)

    if verbose >= 1:
      self.P("  Generating {}/{} options.".format(len(iterations), n_options))

    if verbose >= 2:
      self.P("    Exclusions ({}):".format(len(skipped)))
      for excl in skipped:
        self.P("      {}".format(excl))
    return iterations

  def grid_dict_to_values(self, params_grid, priority_keys=None, sort_keys=True):
    """
    method to convert a grid serach dict into a list of all combinations
    returns combinations and param names for each combination entry
    """
    priority_keys = priority_keys or []
    all_keys = list(params_grid.keys())
    if sort_keys:
      priority_keys.sort()
      all_keys.sort()
    # endif sort_keys

    if len(priority_keys) > 0:
      non_priority_keys = list(set(all_keys) - set(priority_keys))
      if sort_keys:
        non_priority_keys.sort()
      # endif sort_keys
    else:
      non_priority_keys = all_keys

    assert len(set(priority_keys) & set(all_keys)) == len(priority_keys)

    params = []
    values = []
    for k in priority_keys + non_priority_keys:
      params.append(k)
      assert type(params_grid[k]) is list, 'All grid-search params must be lists. Error: {}'.format(k)
      values.append(params_grid[k])
    combs = list(itertools.product(*values))
    return combs, params

  @staticmethod
  def grid_pos_to_params(grid_data, params, exceptions=None, fixed=None):
    """
    converts a grid search combination to a dict for callbacks that expect kwargs

    exceptions: list of dicts where if certain conditions are met then we skip the position by
                returning `None` (each dict must contain a couple params and each with a list of
                excepted values - any combination will generate an exception)
    """
    func_kwargs = {}

    for j, k in enumerate(params):
      func_kwargs[k] = grid_data[j]

    if exceptions is not None:
      for exception in exceptions:
        cond = 0
        for k, v in exception.items():
          if type(v) not in [list, tuple]:
            raise ValueError("Provided exceptions must be in list format")
          if func_kwargs[k] in v:
            cond += 1
        if cond == len(exception):
          # exception met
          return None

    if fixed is not None:
      for fix in fixed:
        cond = 0
        for k,v in fix.items():
          if type(v) not in [list, tuple]:
            raise ValueError("Provided fixed params must be in list format")
          if func_kwargs[k] in v:
            cond += 1
          #endif
        #endfor
        if not (cond == 0 or cond == len(fix)):
          return None

    return func_kwargs

  @staticmethod
  def grid_dict_to_results(params_grid, value_keys):
    """
     will take a grid search dict and return a results dict
     for later dataframe conversion
     inputs:
       params_grid: grid search dict
       value_keys : the name (str) or names (list, tuple) of the test oucome
                 such as "recall" or "accuracy" or "no_episodes"
     returns:
       dict of empty lists
    """
    if type(value_keys) is str:
      value_keys = [value_keys]
    dict_results = OrderedDict()
    for vkey in value_keys:
      dict_results[vkey] = []
    for k in params_grid:
      dict_results[k] = []
    return dict_results

  @staticmethod
  def add_results(d_results, d_grid_pos, values, value_keys):
    """
     adds results to a existing results dict see `grid_dict_to_results`
     inputs:
       d_grid_pos : dict returned from grid_pos_to_params
       d_results : results dict

    """
    value_keys = [value_keys] if type(value_keys) == str else value_keys
    values = [values] if type(values) in [int, float] else values
    for k in d_grid_pos:
      d_results[k].append(d_grid_pos[k])
    for i, k in enumerate(value_keys):
      d_results[k].append(values[i])
    return d_results

  def grid_dict_to_generator(self, dict_grid, priority_keys=None):
    _combs, _params = self.grid_dict_to_values(params_grid=dict_grid, priority_keys=priority_keys)
    for _c in _combs:
      dict_pos = self.grid_pos_to_params(_c, _params)
      yield dict_pos
