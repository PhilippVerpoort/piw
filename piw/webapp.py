import pickle
import re
from abc import ABC
from pathlib import Path
from typing import Callable, Optional, Type, Final

import plotly.io as pio
import plotly.graph_objects as go
from dash import Dash
from dash.dependencies import Input, State
import dash_bootstrap_components as dbc

from piw.abstract_plot import AbstractPlot
from piw.callbacks import set_callbacks
from piw.layout import create_layout
from piw.styles import default_styles


# allowed export formats
ALLOWED_EXPORT_FORMATS: Final[list[str]] = ['png', 'svg', 'pdf']


# class Webapp
class Webapp(ABC):
    def __init__(self, piw_id: str, title: str, desc: Optional[str] = None, authors: Optional[list[str]] = None,
                 root_path: str = '/', date: Optional[str] = None, pages: Optional[dict[str, str]] = None,
                 links: Optional[dict[str, str]] = None, load: Optional[list[Callable]] = None,
                 ctrls: Optional[list[Callable]] = None, update: Optional[list[Callable]] = None,
                 generate_args: Optional[list[Input | State]] = None, proc: Optional[list[Callable]] = None,
                 glob_cfg: Optional[dict] = None, styles: Optional[dict] = None,
                 plots: Optional[list[Type[AbstractPlot]]] = None, output: Optional[str | Path] = None,
                 sort_figs: Optional[list[str]] = None, default_template: str = 'piw', input_caching: bool = False,
                 input_caching_dir: Optional[str | Path] = None, debug: bool = False):
        # check arguments are valid
        if not (isinstance(piw_id, str) and re.match(r"^[a-zA-Z0-9]+(-[a-zA-Z0-9]+)*$", piw_id)):
            raise Exception(f"Argument 'piw_id' of class Webapp has to be a string containing only lowercase letters, "
                            f"potentially separated by single hyphens (e.g. 'name-of-app').")
        if not (isinstance(root_path, str) and root_path.startswith('/') and root_path.endswith('/')):
            raise Exception(f"Argument 'root_path' of class Webapp has to be a string and start and end with a '/'.")
        if not isinstance(title, str):
            raise Exception(f"Argument 'title' of class Webapp has to be a string.")
        if not (desc is None or isinstance(desc, str)):
            raise Exception(f"Argument 'desc' of class Webapp has to be a string.")
        if not (authors is None or (isinstance(authors, list) and all(isinstance(a, str) for a in authors))):
            raise Exception(f"Argument 'authors' of class Webapp has to be a list of strings (one string for each "
                            f"author name).")
        if not (date is None or isinstance(date, str)):
            raise Exception(f"Argument 'date' of class Webapp has to be a string.")
        if not (pages is None or (isinstance(pages, dict) and all(isinstance(k, str) for k in pages) and
                                  all(isinstance(v, str) for v in pages.values()))):
            raise Exception(f"Argument 'pages' of class Webapp has to be a dict of strings "
                            f"(e.g. {{'': 'Main', 'adv': 'Advanced'}}.")
        if not (links is None or (isinstance(links, dict) and all(isinstance(k, str) for k in links) and
                                  all(isinstance(v, str) for v in links.values()))):
            raise Exception(f"Argument 'links' of class Webapp has to be a dict of strings "
                            f"(e.g. {{'Imprint': 'https:// ...', 'Project page': 'https:// ...'}}.")
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
        if not (styles is None or isinstance(styles, dict)):
            raise Exception(f"Argument 'styles' of class Webapp has to be a dict.")
        if not (plots is not None or (isinstance(plots, list) and
                                      all(isinstance(p, type(AbstractPlot)) for p in plots))):
            raise Exception(f"Argument 'plots' must be a list of AbstractPlot objects.")
        if not (output is None or isinstance(output, str) or isinstance(output, Path)):
            raise Exception(f"Argument 'output' of class Webapp has to be a string or Path object containing the "
                            f"output directory for exported plots.")
        if not (sort_figs is None or isinstance(sort_figs, list)):
            raise Exception(f"Argument 'sort_figs' of class Webapp has to be a list of figure names provided as "
                            f"strings.")
        if not isinstance(default_template, str):
            raise Exception(f"Argument 'default_template' must be a string.")
        if not isinstance(input_caching, bool):
            raise Exception(f"Argument 'input_caching' of class Webapp has to be boolean (True/False).")
        if not (input_caching_dir is None or isinstance(input_caching_dir, str) or isinstance(input_caching_dir, Path)):
            raise Exception(f"Argument 'input_caching_dir' of class Webapp has to be a string or Path object.")
        if not isinstance(debug, bool):
            raise Exception(f"Argument 'debug' of class Webapp has to be boolean (True/False).")

        # save constructor arguments as class fields
        self._piw_id: str = piw_id
        self._root_path: str = root_path
        self._title: str = title
        self._desc: Optional[str] = desc
        self._authors: Optional[list[str]] = authors
        self._date: Optional[str] = date
        self._pages: dict[str, str] = pages if pages is not None else {'': 'Default'}
        self._links: dict[str, str] = links
        self._load: list[Callable] = load if load is not None else []
        self._ctrls: list[Callable] = ctrls if ctrls is not None else []
        self._update: list[Callable] = update if update is not None else []
        self._generate_args: list[Input | State] = generate_args if generate_args is not None else []
        self._proc: list[Callable] = proc if proc is not None else []
        self._glob_cfg: dict = glob_cfg if glob_cfg is not None else {}
        self._styles: dict = styles or default_styles
        self._plots: list[AbstractPlot] = [Plot(self._glob_cfg, self._styles) for Plot in plots] \
                                          if plots is not None else []
        self._output: Path = Path.cwd() if output is None else Path(output) if isinstance(output, str) else output
        self._sort_figs: Optional[list] = sort_figs
        self._default_template: str = default_template
        self._input_caching: bool = input_caching
        self._input_caching_dir: Path = Path.cwd() if input_caching_dir is None else Path(input_caching_dir) \
                                                   if isinstance(input_caching_dir, str) else input_caching_dir
        self._debug: bool = debug

    @property
    def piw_id(self) -> str:
        return self._piw_id

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
        return self._dash_app.server

    # start webapp
    def start(self):
        # set plotly template
        self._set_template()

        # load default input data (from raw or from cache)
        self._load_def_inputs()

        # produce default figures for initial display
        fig_names_default = [
            figName for plot in self._plots
            for figName, figSpecs in plot.figs.items()
            if 'display' in figSpecs and '' in figSpecs['display']
        ]
        subfig_plots_init = self.display(self._def_inputs, fig_names_default)

        # create Dash app
        self._create_dash_app()

        # create app layout
        create_layout(self._dash_app, self._pages, self._links, self._ctrls, self._plots, self._sort_figs, self._title,
                      self._desc, self._authors, self._date, self._def_inputs)

        # set callback
        set_callbacks(self._dash_app, self._plots, subfig_plots_init, self._generate_args, self._def_inputs,
                      self._update, self.display, self._root_path)

    # run app locally
    def run(self):
        self._dash_app.run_server(debug=self.debug)

    # produce figures for export to file
    def export(self, fig_names: Optional[list] = None, export_formats: str | list[str] = 'png', dpi: float = 300.0):
        # check format argument is valid
        if not isinstance(export_formats, list):
            if not isinstance(export_formats, str):
                raise Exception(f"Formats must be a list of str or a single str. Found: {export_formats}.")
            export_formats = [export_formats]
        if any(f not in ALLOWED_EXPORT_FORMATS for f in export_formats):
            raise Exception(f"Illegal format option found. Allowed: "
                            f"{', '.join(ALLOWED_EXPORT_FORMATS)}. Found: '{export_formats}'.")

        # set plotly template
        self._set_template()

        # load input data
        self._load_def_inputs()
        inputs = self._def_inputs

        # process input data
        outputs = self._proc_inputs(inputs)

        # plot
        self._output.mkdir(parents=True, exist_ok=True)
        for plot in self._plots:
            plot.update(target='print', dpi=dpi)
            subfig_plots = plot.produce(inputs, outputs, fig_names)

            for subfig_name, subfig_plot in subfig_plots.items():
                size = plot.get_subfig_size(subfig_name)
                if subfig_plot is None:
                    continue
                for file_format in export_formats:
                    subfig_plot.write_image(self._output / f"{subfig_name}.{file_format}", **size)

    # produce figures for display in webapp
    def display(self, inputs: dict, fig_names: list) -> dict[str, go.Figure]:
        # process input data
        outputs = self._proc_inputs(inputs)

        # produce figures requested
        subfig_plots = {}
        for plot in self._plots:
            plot.update(target='webapp')
            subfig_plots |= plot.produce(inputs, outputs, fig_names)

        return subfig_plots

    # load default input data
    def _load_def_inputs(self):
        # set up caching framework
        if self._input_caching:
            if self._input_caching_dir.exists() and self._input_caching_dir.is_dir():
                self._cache_path = self._input_caching_dir / f"inputs_cached_{self._piw_id.replace('-', '_')}.pkl"
            else:
                raise Exception('Input caching directory does not exist.')

        # load cached inputs from binary file if it exists
        if self._input_caching and self._cache_path.exists():
            with open(self._cache_path, 'rb') as f:
                self._def_inputs = pickle.load(f)
                return

        # execute all load functions
        inputs: dict = {}
        for load_func in self._load:
            load_func(inputs)
        self._def_inputs = inputs

        # cache inputs in binary file
        if self._input_caching:
            with open(self._cache_path, 'wb') as f:
                pickle.dump(inputs, f)

    # process input to generate outputs
    def _proc_inputs(self, inputs: dict) -> dict:
        outputs = {}

        for proc_func in self._proc:
            proc_func(inputs, outputs)

        return outputs

    # set plotly template
    def _set_template(self):
        if self._default_template == 'piw':
            from piw.template import piw_template
            pio.templates['piw'] = piw_template
        if self._default_template not in pio.templates:
            raise Exception("Argument 'default_template' must be the string identifier of a plotly template "
                            "registered in 'pio.templates'.")
        pio.templates.default = self._default_template

    # create dash app
    def _create_dash_app(self):
        self._dash_app = Dash(
            f"piw--{self._piw_id}",
            title=self._title,
            external_stylesheets=[dbc.themes.BOOTSTRAP, 'assets/base.css', 'assets/piw.css'],
            meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}],
            requests_pathname_prefix=self._root_path,
            routes_pathname_prefix='/',
        )

        # turn on debug if requested
        if self._debug:
            self._dash_app.enable_dev_tools(debug=self._debug)
