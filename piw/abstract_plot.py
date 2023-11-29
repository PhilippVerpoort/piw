from abc import ABC, abstractmethod
from typing import Final, Optional

import plotly.graph_objects as go


inch_per_mm: Final[float] = 0.03937


class AbstractPlot(ABC):
    def __init__(self, glob_cfg: Optional[dict], styles_by_target: Optional[dict]):
        self._glob_cfg: dict = glob_cfg | {}
        self._styles_by_target: dict = styles_by_target | {}

        self._subfig_cfgs: dict = {
            subfig_name: (self.cfg | subfig_specs['config'] if 'config' in subfig_specs else {})
            for subfig_name, subfig_specs in self.subfigs.items()
        }

        self._target = 'print'
        self._dpi = 300.0

    @property
    @abstractmethod
    def figs(self) -> dict:
        pass

    @property
    @abstractmethod
    def cfg(self) -> dict:
        pass

    _subfigs: dict = None

    @property
    def subfigs(self) -> dict:
        if self._subfigs is None:
            sub_specs = ['size', 'config']
            self._subfigs = {}
            for fig_name, fig_specs in self.figs.items():
                if 'subfigs' in fig_specs:
                    self._subfigs |= {
                        subfig_name: {k: v for k, v in subfig_specs.items() if k in sub_specs} | {'parent': fig_name}
                        for subfig_name, subfig_specs in fig_specs['subfigs'].items()
                    }
                else:
                    self._subfigs |= {
                        fig_name: {k: v for k, v in fig_specs.items() if k in sub_specs} | {'parent': fig_name}
                    }

        return self._subfigs

    def update(self, target: Optional[str] = None, dpi: Optional[float] = None):
        if target is not None:
            self._target = target
            self._styles = self._styles_by_target[target] if target in self._styles_by_target else {}
        if dpi is not None:
            self._dpi = dpi

    def produce(self, inputs: dict, outputs: dict, fig_names: Optional[list]) -> dict:
        subfig_names = [
            subfig for subfig, subfig_specs in self.subfigs.items()
            if fig_names is None or subfig_specs['parent'] in fig_names
        ]
        subfigs = self.plot(inputs, outputs, subfig_names) if subfig_names else {}

        self._decorate(inputs, outputs, subfigs)

        if self._target == 'webapp':
            self._add_placeholders(subfigs)

        return subfigs

    @abstractmethod
    def plot(self, inputs: dict, outputs: dict, subfig_names: list) -> dict:
        pass

    def _decorate(self, inputs: dict, outputs: dict, subfigs: dict):
        return

    # add placeholder plots for webapp for plots that were not produced
    def _add_placeholders(self, subfigs: dict):
        for subfig_name in self.subfigs:
            if subfig_name not in subfigs or subfigs[subfig_name] is None:
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
                subfigs[subfig_name] = f

    def get_subfig_size(self, subfig_name: str):
        subfig_size = self.subfigs[subfig_name]['size']['print']

        return {
            key: self._dpi * inch_per_mm * val
            for key, val in subfig_size.items()
        }
