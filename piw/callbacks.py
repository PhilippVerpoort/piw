from copy import deepcopy
from typing import Callable

from dash import Dash
from dash import callback_context as ctx
from dash.dependencies import Input, Output, State

from piw.abstract_plot import AbstractPlot


def set_callbacks(dash_app: Dash, plots: list[AbstractPlot], subfig_plots_init: dict, generate_args: list,
                  def_inputs: dict, ctrls_tables_modal: dict[str, list[str]], update: list[Callable],
                  display: Callable, root_path: str):
    # create lists containing all fig_names and subfig_names
    fig_names = [figName for plot in plots for figName in plot.figs]
    subfig_names = [subfigName for plot in plots for subfigName in plot.subfigs]

    # helper function for stripping root path off routes
    def _strip_route(route: str) -> str:
        if not route.startswith(root_path):
            raise Exception('Error in route: does not start with root path.')
        return route[len(root_path):]

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
            show if 'display' in fig_specs and route in fig_specs['display'] else hide
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
                if 'display' in fig_specs and route in fig_specs['display']
            ]

            # get figures
            subfigs_generated = display(inputs_updated, fig_names_req)

        # sort generated subfigs and return
        subfigs_return = dict(sorted(subfigs_generated.items(), key=lambda t: subfig_names.index(t[0])))
        return *subfigs_return.values(),

    # callback for updating tables in controls
    @dash_app.callback(
        [*(Output(t, 'data') for t in ctrls_tables_modal),
         Output('ctrl-tables-modal', 'is_open'),
         Output('ctrl-tables-modal-open', 'data'),
         Output('ctrl-tables-modal-textfield', 'value'),],
        [*(Input(t, 'active_cell') for t in ctrls_tables_modal),
         Input('ctrl-tables-modal-ok', 'n_clicks'),
         Input('ctrl-tables-modal-cancel', 'n_clicks'),],
        [*(State(t, 'data') for t in ctrls_tables_modal),
         State('ctrl-tables-modal-textfield', 'value'),
         State('ctrl-tables-modal-open', 'data'),],
    )
    def callback_advanced_modal(*args):
        active_cell = {p: args[i] for i, p in enumerate(list(ctrls_tables_modal.keys()))}
        current_data = {p: args[i - len(ctrls_tables_modal) - 2] for i, p in enumerate(list(ctrls_tables_modal.keys()))}
        text_field_data = args[-2]
        origin_saved = args[-1]

        if not ctx.triggered:
            return *current_data.values(), False, '', ''
        else:
            origin = ctx.triggered[0]['prop_id'].split('.')[0]

            if origin in ctrls_tables_modal:
                row = active_cell[origin]['row']
                col = active_cell[origin]['column_id']

                if col not in ctrls_tables_modal[origin]:
                    return *current_data.values(), False, '', ''
                else:
                    return *current_data.values(), True, origin, str(current_data[origin][row][col])
            elif origin == 'ctrl-tables-modal-cancel':
                return *current_data.values(), False, '', ''
            elif origin == 'ctrl-tables-modal-ok':
                row = active_cell[origin_saved]['row']
                col = active_cell[origin_saved]['column_id']

                current_data[origin_saved][row][col] = text_field_data
                return *current_data.values(), False, '', ''
            else:
                raise Exception('Unknown button pressed!')
