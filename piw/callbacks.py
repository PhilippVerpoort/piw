from copy import deepcopy
from pathlib import Path
from typing import Callable

from dash import Dash
from dash import callback_context as ctx
from dash.dependencies import Input, Output, State
from flask import send_file

from piw.abstract_plot import AbstractPlot


ASSETS = Path(__file__).parent / 'assets'


def set_callbacks(dash_app: Dash, plots: list[AbstractPlot], subfig_plots_init: dict, generate_args: list,
                  def_inputs: dict, update: list[Callable], display: Callable, root_path: str):
    # create lists containing all fig_names and subfig_names
    fig_names = [figName for plot in plots for figName in plot.figs]
    subfig_names = [subfigName for plot in plots for subfigName in plot.subfigs]

    # helper function for stripping root path off routes
    def _strip_route(route: str) -> str:
        if not route.startswith(root_path):
            raise Exception('Error in route: does not start with root path.')
        return route[len(root_path):]

    # serving asset files
    @dash_app.server.route('/assets/<path>')
    def serve_assets(path: str):
        return send_file(ASSETS / path, as_attachment=True)

    # show/hide figure cards
    @dash_app.callback(
        [*(Output(f"card-{fig_name}", 'style') for fig_name in fig_names)],
        [Input('url', 'pathname')]
    )
    def show_fig_cards(route):
        show = {}
        hide = {'display': 'none'}

        route = _strip_route(route)

        return [
            show if route in fig_specs['display'] else hide
            for plot in plots
            for fig_name, fig_specs in plot.figs.items()
        ]

    # general callback for (re-)generating plots
    @dash_app.callback(
        [*(Output(subfig_name, 'figure') for subfig_name in subfig_names), ],
        [*generate_args,
         State('url', 'pathname'), ])
    def callback_update(*args):
        route = _strip_route(args[-1])

        if not ctx.triggered:
            # load default figures for initial display
            subfigs_generated = subfig_plots_init
        else:
            # get name of button pressed
            try:
                btn_pressed = ctx.triggered[0]['prop_id'].split('.')[0]
            except Exception:
                btn_pressed = None

            # get new input and output data
            inputs_updated = deepcopy(def_inputs)
            for u in update:
                u(inputs_updated, btn_pressed, args)

            # get list of figs required
            fig_names_req = [
                fig_name
                for plot in plots
                for fig_name, fig_specs in plot.figs.items()
                if route in fig_specs['display']
            ]

            # get figures
            subfigs_generated = display(inputs_updated, fig_names_req)

        # sort generated subfigs and return
        subfigs_return = dict(sorted(subfigs_generated.items(), key=lambda t: subfig_names.index(t[0])))
        return *subfigs_return.values(),
