#
#
#

class Adapter(object):

    def __init__(self, obj, **kwargs):
        setattr(self, 'obj', obj)
        self.__dict__.update(kwargs)

    def __getattr__(self, attr, val=None):
        oga = object.__getattribute__
        try:
            return oga(self, attr)
        except AttributeError:
            return oga(oga(self, 'obj'), attr)
