import pandas as pd
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, jsonify, current_app, session
)
from werkzeug.exceptions import abort

from skincare_app.auth import sign_in_required
from skincare_app.db import set_routine

bp = Blueprint('routine', __name__)


@bp.route('/')
def routine_home():
    print(session.get('routine'))
    print(type(session.get('routine')))
    return render_template('routine/routine_home.html')


@bp.route('/edit_routine', methods=['GET', 'POST'])
@sign_in_required
def edit_routine():
    return render_template("routine/edit_routine_page.html")


@bp.route('/search', methods=['GET'])
@sign_in_required
def search_products():
    # Check if the request is an AJAX request
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return redirect(url_for('routine.routine_home'))

    product_df = current_app.config.get('PRODUCT_DF')

    query = request.args.get('query', '').lower()
    search_terms = query.split()  # the list of words the user entered
    product_df['match_count'] = 0  # initialize match_count column with every value set to 0

    filter_condition = pd.Series(False, index=product_df.index)
    for term in search_terms:
        term_condition = (
                product_df['product'].str.lower().str.contains(term, na=False) |
                product_df['brand'].str.lower().str.contains(term, na=False)
        )

        product_df.loc[term_condition, 'match_count'] += 1  # increment match_count for rows with term_condition True

        filter_condition |= term_condition

    results = product_df[filter_condition]
    # grab the first 10 results sorted by highest match_count
    results = results.sort_values(by='match_count', ascending=False)[:10]

    product_brands_names = (results['hyphen_sep']).tolist()
    return jsonify(product_brands_names)


@bp.route('/submit_routine', methods=['POST', 'GET'])
@sign_in_required
def submit_routine_button():
    """
    TODO: Do not allow user to submit product that doesn't exist in the dataset
    """
    # Check if the request is an AJAX request
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return redirect(url_for('routine.routine_home'))

    data = request.json
    # routine_raw is a list of dictionaries in form [{'section': name, 'products': [1, 2, ...]}, {'section': name, ...}]
    routine_raw = data.get('routine', [])

    # routine will be a list of tuples in form [(section name, products list), (section name, products list), ...]
    routine = []
    for section in routine_raw:
        section_title = section.get('section', '')
        if section_title == '':
            section_title = 'Unnamed step'

        raw_products_list = section.get('products', [])
        products_list = []
        for product in raw_products_list:
            # print("product", product)
            if product != '':
                products_list.append(product)

        section_tuple = (section_title, products_list)
        routine.append(section_tuple)

    # insert routine into users db
    set_routine(session.get('username'), routine)
    session['routine'] = routine
    # print(g.user['routine'])
    # print(routine)

    return jsonify({'status': 'success', 'redirect_url': url_for('routine.routine_home')})
