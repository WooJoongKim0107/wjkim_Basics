import numpy as np
from numpy import matmul
import matplotlib.pyplot as plt
from itertools import zip_longest
from matplotlib import rcParams
from matplotlib.transforms import IdentityTransform, Transform

print('wjkim.pyplot: Modify rcParams')
rcParams['text.usetex'] = False
rcParams['svg.fonttype'] = 'none'
rcParams["font.family"] = ["sans-serif"]
rcParams['font.sans-serif'] = ['Arial']
rcParams['font.size'] = 8.0


class ExFigure(plt.Figure):
    def add_axes(self, *locators, ha=-1, va=-1, **kwargs):
        """
        locator: [(x, transform), (y, transform), (w, transform), (h, transform)]
        transform: Transform object that maps given position into display coordinate position

                    1)      0 / 'figure'      (use when given data is already in figure coordinate)
                    2)      'display'         (use when given data is in display coordinate)
                    3)   'inch' or 'inches'   (use when given data is in inches)
                    4)  Axes or ax.transAxes  (use when given data is in Axes coordinate)
                    5)     ax.transData       (use when given data is in Data coordinate)
                    6)   Transform object

        locator of form [(x0, transform0, x1, transform1, ...) ,...] will be converted as xywh0 + xywh1 + ...
        """
        xywh = sum(self.translate(locator) for locator in locators)
        xywh_aligned = self.align(xywh, ha=ha, va=va)
        return super().add_axes(xywh_aligned, **kwargs)

    def translate(self, locator):
        xywh = np.zeros(4)
        for _xywh, _transforms in self.unzip(locator):
            transforms = [self.convert(t) for t in _transforms]
            xywh += self.analyze(_xywh, transforms)
        return xywh

    @staticmethod
    def align(xywh, ha=-1, va=-1):
        x, y, w, h = xywh
        x -= w*(ha+1)/2
        y -= h*(va+1)/2
        return np.array([x, y, w, h])

    @staticmethod
    def analyze(xywh, transforms):
        x, _ = transforms[0].transform([xywh[0], 0])
        _, y = transforms[1].transform([0, xywh[1]])
        w, _ = transforms[2].transform([xywh[2], 0]) - transforms[2].transform([0, 0])
        _, h = transforms[3].transform([0, xywh[3]]) - transforms[3].transform([0, 0])
        return np.array([x, y, w, h])

    @staticmethod
    def unzip(locator):
        return zip(*[zip_longest(*locator, fillvalue=0)]*2)

    def convert(self, t):
        if (t == 0) or (t in ['fig', 'figure']):
            return IdentityTransform()
        elif t == 'display':
            return self.transFigure.inverted()
        elif t in ['inch', 'inches']:
            return self.dpi_scale_trans + self.transFigure.inverted()
        elif isinstance(t, plt.Axes):
            return t.transAxes + self.transFigure.inverted()
        elif isinstance(t, Transform):
            return t + self.transFigure.inverted()
        else:
            raise ValueError

