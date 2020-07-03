tenma API
=========

.. contents::

Instantiation
-------------

You can use the tenma class you deem necessary by directly creating an instance of 
the class referencing your model.

The api can autodetect the model and return a proper instance (or a default one which
may or may not suit your limits) by simply using the provided function::

   from tenma import instantiate_tenma_class_from_device_response
   tenma = instantiate_tenma_class_from_device_response('/dev/ttyUSB0')

or the more manual (with your own knowledge) approach::

   from tenma import Tenma72_2550
   tenma = Tenma72_2550('/dev/ttyUSB0')

In case something does not work as you would expect, instantiate the class with the 
debug option enabled so all the transmissions to and from the unit are printed to
stdout::

   from tenma import Tenma72_2550
   tenma = Tenma72_2550('/dev/ttyUSB0')


API Documentation
-----------------

.. automodule:: tenma.tenmaDcLib
   :members:
