from os import environ

def is_debug_mode():
  return environ.get('LOGGER_DEBUG', '0') == '1'

def maybe_print(msg):
  """
  This method was added for the libraries user to be able to ignore the debug messages
  by setting the "LOGGER_DEBUG" environment variable to '1'.
  Parameters
  ----------
  msg - str
    The message to be printed
  """
  if is_debug_mode():
    print(msg)
  return


__logger_can_use_full_logger = False
__logger_can_use_small_logger = False
try:
  from .full_logger import Logger, SBLogger
  __logger_can_use_full_logger = True
except Exception as e:
  maybe_print(
    f'Failed to import Full Logger class due to the following exception: \"{e}\"'
    f'\nTrying to import from .small_logger instead.'
  )

if not __logger_can_use_full_logger:
  try:
    # TODO: create a new logger class that will be used by default
    from .small_logger import Logger, SBLogger
    __logger_can_use_small_logger = True
  except Exception as e:
    maybe_print(
      f'Failed to import Small Logger class due to the following exception: \"{e}\"'
    )

if not __logger_can_use_full_logger and not __logger_can_use_small_logger:
  if is_debug_mode():
    raise ImportError("Failed to import Logger class from any of the available sources.")
  else:
    raise ImportError("Failed to import Logger class from any of the available sources."
                      "Set Environment Variable \"LOGGER_DEBUG\" to '1' to see the missing packages.")
