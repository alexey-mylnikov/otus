#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time


def catcher(logger, exceptions=None):
    exceptions = exceptions or (Exception, )

    def decorator(func):
        def wrapped(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
            except exceptions as e:
                logger.exception(e)
                time.sleep(0.1)
                raise

            return result
        return wrapped
    return decorator
