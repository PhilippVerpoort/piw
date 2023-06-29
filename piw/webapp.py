import pickle
import re
from abc import ABC
from pathlib import Path
from typing import Callable, Optional, Type

import plotly.io as pio
import plotly.graph_objects as go
from dash import Dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, State

from piw.abstract_plot import AbstractPlot
from piw.callbacks import setCallbacks
from piw.layout import createLayout
from piw.template import piw_template


class Webapp(ABC):
    def __init__(self, piwID: str, title: str, desc: Optional[str] = None, authors: Optional[list[str]] = None,
                 date: Optional[str] = None, pages: Optional[dict[str, str]] = None,
                 links: Optional[dict[str, str]] = None, load: Optional[list[Callable]] = None,
                 ctrls: Optional[list[Callable]] = None, update: Optional[list[Callable]] = None,
                 generate_args: Optional[list[Input | State]] = None, proc: Optional[list[Callable]] = None,
                 glob_cfg: Optional[dict] = None, plots: Optional[list[Type[AbstractPlot]]] = None,
                 output: Optional[str | Path] = None, sort_figs: Optional[list[str]] = None,
                 input_caching: bool = False, input_caching_dir: Optional[str | Path] = None, debug: bool = False):
        # check arguments are valid
        if not isinstance(piwID, str) or not re.match(r"^[a-z]+(-[a-z]+)*$", piwID):
            raise Exception(f"Argument 'piwID' of class Webapp has to be a string containing only lowercase letters, potentially separated by single hyphens (e.g. 'name-of-app').")
        if not isinstance(title, str):
            raise Exception(f"Argument 'title' of class Webapp has to be a string.")
        if not (desc is None or isinstance(desc, str)):
            raise Exception(f"Argument 'desc' of class Webapp has to be a string.")
        if not (authors is None or (isinstance(authors, list) and all(isinstance(a, str) for a in authors))):
            raise Exception(f"Argument 'authors' of class Webapp has to be a list of strings (one string for each author name).")
        if not (date is None or isinstance(date, str)):
            raise Exception(f"Argument 'date' of class Webapp has to be a string.")
        if not (pages is None or (isinstance(pages, dict) and all(isinstance(k, str) for k in pages) and all(isinstance(v, str) for v in pages.values()))):
            raise Exception(f"Argument 'pages' of class Webapp has to be a dict of strings (e.g. {{'': 'Main', 'adv': 'Advanced'}}.")
        if not (links is None or (isinstance(links, dict) and all(isinstance(k, str) for k in links) and all(isinstance(v, str) for v in links.values()))):
            raise Exception(f"Argument 'links' of class Webapp has to be a dict of strings (e.g. {{'Impressum': 'https:// ...', 'Projekt page': 'https:// ...'}}.")
        if not (load is None or (isinstance(load, list) and all(isinstance(f, Callable) for f in load))):
            raise Exception(f"Argument 'load' of class Webapp has to be a list of callable functions.")
        if not (ctrls is None or (isinstance(ctrls, list) and all(isinstance(f, Callable) for f in ctrls))):
            raise Exception(f"Argument 'ctrls' of class Webapp has to be a list of callable functions.")
        if not (update is None or (isinstance(update, list) and all(isinstance(f, Callable) for f in update))):
            raise Exception(f"Argument 'update' of class Webapp has to be a list of callable functions.")
        if not (proc is None or (isinstance(proc, list) and all(isinstance(f, Callable) for f in proc))):
            raise Exception(f"Argument 'proc' of class Webapp has to be a list of callable functions.")
        if not (glob_cfg is None or isinstance(glob_cfg, dict)):
            raise Exception(f"Argument 'globCfg' of class Webapp has to be a dict.")
        if not (output is None or isinstance(output, str) or isinstance(output, Path)):
            raise Exception(f"Argument 'output' of class Webapp has to be a string or Path object containing the output directory for exported plots.")
        if not (sort_figs is None or isinstance(sort_figs, list)):
            raise Exception(f"Argument 'sort_figs' of class Webapp has to be a list of figure names provided as strings.")
        if not isinstance(input_caching, bool):
            raise Exception(f"Argument 'input_caching' of class Webapp has to be boolean (True/False).")
        if not (input_caching_dir is None or isinstance(input_caching_dir, str) or isinstance(input_caching_dir, Path)):
            raise Exception(f"Argument 'input_caching_dir' of class Webapp has to be a string or Path object.")
        if not isinstance(debug, bool):
            raise Exception(f"Argument 'debug' of class Webapp has to be boolean (True/False).")

        # save constructor arguments as class fields
        self._piwID: str = piwID
        self._title: str = title
        self._desc: Optional[str] = desc
        self._authors: Optional[list[str]] = authors
        self._date: Optional[str] = date
        self._pages: dict[str, str] = pages if pages is not None else {'': 'Default'}
        self._links: dict[str, str] = links
        self._load: list[Callable] = load if load is not None else []
        self._ctrls: list[Callable] = ctrls if ctrls is not None else []
        self._update: list[Callable] = update if update is not None else []
        self._generateArgs: list[Input | State] = generate_args if generate_args is not None else []
        self._proc: list[Callable] = proc if proc is not None else []
        self._globCfg: dict = glob_cfg if glob_cfg is not None else {}
        self._plots: list[AbstractPlot] = [Plot(self._globCfg) for Plot in plots] if plots is not None else []
        self._output: Path = Path.cwd() if output is None else Path(output) if isinstance(output, str) else output
        self._sortFigs: Optional[list] = sort_figs
        self._inputCaching: bool = input_caching
        self._inputCachingDir: Path = Path.cwd() if input_caching_dir is None else Path(input_caching_dir) if isinstance(input_caching_dir, str) else input_caching_dir
        self._debug: bool = debug

    @property
    def piwID(self) -> str:
        return self._piwID

    @property
    def title(self) -> str:
        return self._title

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def pages(self) -> dict:
        return self._pages

    @property
    def figures(self) -> list:
        return []

    @property
    def flask_app(self):
        return self._dashApp.server

    # start webapp
    def start(self):
        # set plotly template
        self._setTemplate()

        # load default input data (from raw or from cache)
        self._loadDefInputs()

        # produce default figures for initial display
        figNamesDefault = [figName for plot in self._plots for figName, figSpecs in plot.figs.items() if '' in figSpecs['display']]
        subfigPlotsInit = self.display(self._defInputs, figNamesDefault)

        # create Dash app
        self._createDashApp()

        # create app layout
        createLayout(self._dashApp, self._pages, self._links, self._ctrls, self._plots, self._sortFigs,
                     self._title, self._desc, self._authors, self._date, self._defInputs)

        # set callback
        setCallbacks(self._dashApp, self._plots, subfigPlotsInit, self._generateArgs, self._defInputs, self._update, self.display)

    # run app locally
    def run(self):
        self._dashApp.run_server(debug=self.debug)

    # produce figures for export to file
    def export(self, figNames: Optional[list] = None, formats: str = 'png', dpi: float = 300.0):
        # check format argument is valid
        allowedFormat = ['png', 'svg']
        if not isinstance(formats, list):
            if not isinstance(formats, str):
                raise Exception(f"Formats must be a list of str or a single str. Found: {formats}.")
            formats = [formats]
        if any(f not in allowedFormat for f in formats):
            raise Exception(f"Illegal format option found. Allowed: {', '.join(allowedFormat)}. Found: '{formats}'.")

        # load input data
        self._loadDefInputs()
        inputs = self._defInputs

        # process input data
        outputs = self._procInputs(inputs)

        # plot
        for plot in self._plots:
            plot.update(target='print', dpi=dpi)
            subfigPlots = plot.produce(inputs, outputs, figNames)

            for subfigName, subfigPlot in subfigPlots.items():
                size = plot.getSubfigSize(subfigName)
                for format in formats:
                    subfigPlot.write_image(self._output / f"{subfigName}.{format}", **size)

    # produce figures for display in webapp
    def display(self, inputs: dict, figNames: list) -> dict[str, go.Figure]:
        # process input data
        outputs = self._procInputs(inputs)

        # produce figures requested
        subfigPlots = {}
        for plot in self._plots:
            plot.update(target='webapp')
            subfigPlots |= plot.produce(inputs, outputs, figNames)

        return subfigPlots

    # load default input data
    def _loadDefInputs(self):
        # set up caching framework
        if self._inputCaching:
            if self._inputCachingDir.exists() and self._inputCachingDir.is_dir():
                self._cachePath = self._inputCachingDir / f"inputs_cached_{self._piwID.replace('-', '_')}.pkl"
            else:
                raise Exception('Input caching directory does not exist.')

        if self._inputCaching and self._cachePath.exists():
            with open(self._cachePath, 'rb') as f:
                self._defInputs = pickle.load(f)
                return

        inputs = {}

        for loadFunc in self._load:
            loadFunc(inputs)

        self._defInputs = inputs

        if self._inputCaching:
            with open(self._cachePath, 'wb') as f:
                pickle.dump(inputs, f)

    # process input to generate outputs
    def _procInputs(self, inputs: dict) -> dict:
        outputs = {}

        for procFunc in self._proc:
            procFunc(inputs, outputs)

        return outputs

    # set plotly template
    def _setTemplate(self):
        pio.templates['piw'] = piw_template
        pio.templates.default = 'piw'

    # create dash app
    def _createDashApp(self):
        self._dashApp = Dash(
            f"piw--{self._piwID}",
            title=self._title,
            external_stylesheets=[dbc.themes.BOOTSTRAP, 'assets/base.css', 'assets/piw.css'],
            meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
        )

        # turn on debug if requested
        if self._debug:
            self._dashApp.enable_dev_tools(debug=self._debug)
