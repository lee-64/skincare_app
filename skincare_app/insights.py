from dash import Dash, html, dcc, Input, Output
import dash_cytoscape as cyto
from flask import session, current_app, render_template
from itertools import permutations
from skincare_app.auth import sign_in_required


def init_dashboard(server):
    cyto.load_extra_layouts()

    # Important: /insights_cytoscape/ is the url of the dashboard which is what everything in init_dashboard creates.
    # The actual URL that the user views is /insights/, which has the typical HTML/jinja templating with an iframe
    # elements that references /insights_cytoscape/, the graph generated in this function.
    dash_app = Dash(
        server=server,
        routes_pathname_prefix='/insights_cytoscape/',
        assets_url_path=''
    )

    # define the layout
    dash_app.layout = html.Div(children=[
        # html.H1(children='Dashboard', className='hi'),
        html.Div([
            dcc.RadioItems(
                id='toggle-cytoscape-value',
                options=[
                    {
                        'label': html.Div(['Conflicts'], style={'color': 'red'}),
                        'value': 'Conflicts'
                    },
                    {
                        'label': html.Div(['Synergies'], style={'color': 'green'}),
                        'value': 'Synergies'
                    }
                ],
                value='Conflicts'  # conflicts is the default value
            ),
            cyto.Cytoscape(
                id='cytoscape-conflicts-synergies',
                layout={'name': 'spread'},
                style={'width': '100%', 'height': '700px'},
                elements={},
                stylesheet=[
                    {
                        'selector': 'node',
                        'style': {
                            'label': 'data(id)'
                        }
                    },
                    {
                        'selector': 'edge',
                        'style': {
                            'label': 'data(label)',
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'vee'
                        }
                    }
                ],
                minZoom=0.5,
                maxZoom=4
            )
        ])
    ])

    init_callbacks(dash_app)

    # Important: /insights_cytoscape/ is the url of the dashboard which is what everything in init_dashboard creates.
    # The actual URL that the user views is /insights/, which has the typical HTML/jinja templating with an iframe
    # elements that references /insights_cytoscape/, the graph generated in this function.
    @server.route('/insights/')
    @sign_in_required
    def render_insights_page():
        return render_template('insights.html')

    return dash_app


def init_callbacks(dash_app):
    @dash_app.callback(
        Output('cytoscape-conflicts-synergies', 'elements'),
        Input('toggle-cytoscape-value', 'value')
    )
    def toggle_conflict_or_synergy(view_chosen):
        routine = session.get('routine')
        print(routine)

        # print(view_chosen)
        if view_chosen == 'Conflicts':
            nodes = create_nodes(routine)
            edges = create_edges(routine, conflict_flag=True)
            elements = nodes + edges
        else:
            nodes = create_nodes(routine)
            edges = create_edges(routine, conflict_flag=False)
            elements = nodes + edges

        return elements


def get_product_ingredients(product_name):
    product_df = current_app.config.get('PRODUCT_DF')
    ingredients = product_df.loc[product_df['hyphen_sep'] == product_name, 'important_ingreds'].tolist()
    return set(ingredient.lower() for ingredient in ingredients[0]) if ingredients else set()


def create_nodes(routine):
    nodes = []
    for section in routine:
        for product in section[1]:
            nodes.append({'data': {'id': product, 'label': product}})

    return nodes


# conflict_flag = True means finding edges for conflicts
# False means finding edges for synergies
def create_edges(routine, conflict_flag: bool):
    edges = []

    products = [product for section in routine for product in section[1]]

    # edges represent conflicts
    if conflict_flag:
        # direction of an edge matters; the (ordered) permutations of product pairings is what we iterate through
        for product1, product2 in permutations(products, 2):
            ingredients1 = get_product_ingredients(product1)
            ingredients2 = get_product_ingredients(product2)
            incompatible_combo, conflict = check_incompatible_combo(ingredients1, ingredients2)
            if incompatible_combo:
                edges.append({
                    'data': {
                        'id': product1 + product2,
                        'source': product1,
                        'target': product2,
                        'label': conflict[0]
                    }
                })

    # edges represent synergies
    else:
        # direction of an edge matters; the (ordered) permutations of product pairings is what we iterate through
        for product1, product2 in permutations(products, 2):
            ingredients1 = get_product_ingredients(product1)
            ingredients2 = get_product_ingredients(product2)
            synergy_combo, synergy = check_synergy_combo(ingredients1, ingredients2)
            if synergy_combo:
                edges.append({
                    'data': {
                        'id': product1 + product2,
                        'source': product1,
                        'target': product2,
                        'label': synergy[0]
                    }
                })

    return edges


def check_incompatible_combo(ingredients1, ingredients2):
    incompatible_ingredients = {
        "retinoid": ["benzoyl peroxide", "aha", "bha"],
        "benzoyl peroxide": ["retinoid", "vitamin c"],
        "aha": ["vitamin c", "retinoid"],
        "bha": ["vitamin c", "retinoid"],
        "vitamin c": ["aha", "bha", "benzoyl peroxide"],
    }

    for ingred1 in ingredients1:
        for ingred2 in ingredients2:
            if (
                (ingred1 in incompatible_ingredients and ingred2 in incompatible_ingredients[ingred1]
            ) or
                (ingred2 in incompatible_ingredients and ingred1 in incompatible_ingredients[ingred2])
            ):
                return True, [ingred1, ingred2]

    return False, None


def check_synergy_combo(ingredients1, ingredients2):
    synergy_ingredients = {
        "aha": ["bha"],
        "bha": ["aha"],
        "ceramides": ["niacinamide"],
        "niacinamide": ["ceramides"],
        "vitamin c": ["vitamin e"],
        "vitamin e": ["vitamin c"],
        "retinoid": ["peptides"],
        "peptides": ["retinoid"]
    }

    for ingred1 in ingredients1:
        for ingred2 in ingredients2:
            if (
                (ingred1 in synergy_ingredients and ingred2 in synergy_ingredients[ingred1]
            ) or
                (ingred2 in synergy_ingredients and ingred1 in synergy_ingredients[ingred2])
            ):
                return True, [ingred1, ingred2]

    return False, None

