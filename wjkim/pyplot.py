from collections.abc import Sequence
import numpy as np
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.axes._axes import Axes
from matplotlib.transforms import IdentityTransform  #, Transform


def modify_rcparams():
    """
    findfont: Generic family 'sans-serif' not found because none of the following families were found: Arial

    If above error occurs, do the followings:
        sudo apt install msttcorefonts -qq
        rm ~/.cache/matplotlib -rf
    """
    print('wjkim.pyplot: Modify rcParams')
    rcParams['text.usetex'] = False
    rcParams['svg.fonttype'] = 'none'
    rcParams['font.sans-serif'] = ['Arial']
    rcParams['font.size'] = 8.
    rcParams['figure.dpi'] = 300.


class AxesLocator:
    def __init__(self, fig: Figure, lbwh, unit='figure'):
        self.fig = fig
        self.pos = self.translate_lbwh(lbwh, self.fig, unit=unit)

    @classmethod
    def clone(cls, axis: Axes):
        return cls(axis.figure, [0, 0, 1, 1], unit=axis)

    def adjust(self, xywh: Sequence = (), unit='figure', x=0, y=0, w=0, h=0):
        xywh = xywh if xywh else [x, y, w, h]
        self.pos += self.translate_xywh(xywh, fig=self.fig, unit=unit)
        return self
    
    def magnify(self, wh):
        self.pos[2:4] *= wh
        return self

    def create(self, ha=-1, va=-1, **kwargs):
        aligned_lbwh = self.align(self.pos, ha=ha, va=va)
        return self.fig.add_axes(aligned_lbwh, **kwargs)
    
    @classmethod
    def translate_xywh(cls, xywh, fig, unit='figure'):
        """
        Let `lbwh` of `axis` be [0.1, 0.1, 0.3, 0.3] in figure unit.
        Then `translate_xywh([1, 1, 1, 1])` will be
        
            [0.3, 0.3, 0.3, 0.3]

        i.e., all elements are considered as 'length'
        """
        transform = cls.get_transform(fig, unit)
        xy = transform(xywh[0:2]) - transform([0, 0])
        wh = transform(xywh[2:4]) - transform([0, 0])
        return np.array([*xy, *wh])
    
    @classmethod
    def translate_lbwh(cls, lbwh, fig, unit='figure'):
        """
        Let `lbwh` of `axis` be [0.1, 0.1, 0.3, 0.3] in figure unit, then
        Then `translate_lbwh([1, 1, 1, 1])` will be
        
            [0.4, 0.4, 0.3, 0.3]

        i.e., `lb` are considered as 'position'
        while `wh` are considered as 'length'
        """
        transform = cls.get_transform(fig, unit)
        lb = transform(lbwh[0:2])
        wh = transform(lbwh[2:4]) - transform([0, 0])
        return np.array([*lb, *wh])
    
    @staticmethod
    def get_transform(fig, unit):
        match unit:
            case 'fig' | 'figure':
                return IdentityTransform().transform
            case 'dis' | 'display':
                return fig.transFigure.inverted().transform
            case 'inc' | 'inch':
                return (fig.dpi_scale_trans + fig.transFigure.inverted()).transform
            case Axes():
                return (unit.transAxes + fig.transFigure.inverted()).transform
            # case Transform():
                # return (unit + self.transFigure.inverted()).transform
        raise ValueError(f'Cannot recognize {unit}')
    
    @staticmethod
    def align(lbwh, ha=-1, va=-1):
        l, b, w, h = lbwh
        l -= w*(ha+1)/2
        b -= h*(va+1)/2
        return np.array([l, b, w, h])


al = AxesLocator
