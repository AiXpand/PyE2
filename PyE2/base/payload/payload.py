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
@author: Lummetry\.AI - Stefan Saraev
@project: 
@description:
"""

import base64
import io
from collections import UserDict

import numpy as np
from PIL import Image


class Payload(UserDict):
  """
  This class enriches the default python dict, providing
  helpful methods to process the payloads received from AiXp nodes.
  """

  def get_image_as_np(self, key='IMG'):
    """
    Extract the image from the payload.
    The image is returned as a numpy array.

    Parameters
    ----------
    key : str, optional
        The key from which to extract the image, by default 'IMG'.
        Can be modified if the user wants to extract an image from a different key

    Returns
    -------
    NDArray[Any] | None
        The image if it was found or None otherwise.
    """
    return np.array(self.get_image_as_PIL(key))

  def get_image_as_PIL(self, key='IMG'):
    """
    Extract the image from the payload.
    The image is returned as a PIL image.

    Parameters
    ----------
    key : str, optional
        The key from which to extract the image, by default 'IMG'.
        Can be modified if the user wants to extract an image from a different key

    Returns
    -------
    Image | None
        The image if it was found or None otherwise.
    """
    base64_img = self.data.get(key, None)
    if base64_img is None:
      return None
    return self._image_from_b64(base64_img)

  def _image_from_b64(self, base64_img):
    base64_decoded = base64.b64decode(base64_img)
    image = Image.open(io.BytesIO(base64_decoded))
    return image
