from abc import ABC, abstractmethod
from typing import Final, Optional

import plotly.graph_objects as go


inch_per_mm: Final[float] = 0.03937

class AbstractPlot(ABC):
    _cfg: dict = {}

    def __init__(self, glob_cfg: dict):
        self._globCfg: dict = glob_cfg
        self._figCfgs: dict = {figName: (self._globCfg | self._cfg | figSpecs['config']) for figName, figSpecs in self.figs.items()}

        self._target = 'print'
        self._dpi = 300.0

    @property
    @abstractmethod
    def figs(self) -> dict:
        pass

    @property
    def subfigs(self) -> dict:
        subSpecs = ['size']
        ret = {}
        for figName, figSpecs in self.figs.items():
            if 'subfigs' in figSpecs:
                ret |= {subfigName:
                    {k: v for k, v in subfigSpecs.items() if k in subSpecs} | {'parent': figName}
                    for subfigName, subfigSpecs in figSpecs['subfigs'].items()
                }
            else:
                ret |= {figName:
                    {k:v for k, v in figSpecs.items() if k in subSpecs} | {'parent': figName}
                }
        return ret

    def update(self, target: Optional[str] = None, dpi: Optional[float] = None):
        if target is not None:
            self._target = target
        if dpi is not None:
            self._dpi = dpi

    def produce(self, inputs: dict, outputs: dict, figNames: Optional[list]) -> dict:
        subfigNames = [
            subfig for subfig, subfigSpecs in self.subfigs.items()
            if figNames is None or subfigSpecs['parent'] in figNames
        ]
        subfigs = self.plot(inputs, outputs, subfigNames) if subfigNames else {}

        self._decorate(inputs, outputs, subfigs)

        if self._target == 'webapp':
            self._addPlaceholders(subfigs)

        return subfigs

    @abstractmethod
    def plot(self, inputs: dict, outputs: dict, subfigNames: list) -> dict:
        pass

    def _decorate(self, inputs: dict, outputs: dict, subfigs: dict):
        return

    # add placeholder plots for webapp for plots that were not produced
    def _addPlaceholders(self, subfigs: dict):
        for subfigName in self.subfigs:
            if subfigName not in subfigs or subfigs[subfigName] is None:
                f = go.Figure()
                f.add_annotation(
                    text='<b>Press GENERATE to<br>display this plot.</b>',
                    xanchor='center',
                    xref='x domain',
                    x=0.5,
                    yanchor='middle',
                    yref='y domain',
                    y=0.5,
                    showarrow=False,
                    bordercolor='black',
                    borderwidth=2,
                    borderpad=3,
                    bgcolor='white',
                )
                subfigs[subfigName] = f

    def getSubfigSize(self, subfigName: str):
        subfigSize = self.subfigs[subfigName]['size']['print']

        return {
            key: self._dpi * inch_per_mm * val
            for key, val in subfigSize.items()
        }
