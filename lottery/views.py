# IMPORTS
import copy
import logging

from flask import Blueprint, render_template, request, flash
from flask_login import current_user, login_required

from app import db, requires_roles
from models import Draw, User
# CONFIG
lottery_blueprint = Blueprint('lottery', __name__, template_folder='templates')

# VIEWS
# view lottery page
@lottery_blueprint.route('/lottery')
@login_required
@requires_roles('user')
def lottery():
    return render_template('lottery.html')


@lottery_blueprint.route('/add_draw', methods=['POST'])
def add_draw():
    submitted_draw = ''
    for i in range(6):
        submitted_draw += request.form.get('no' + str(i + 1)) + ' '
    submitted_draw.strip()

    # create a new draw with the form data.
    new_draw = Draw(user_id=current_user.id, draw=submitted_draw, win=False, round=0, draw_key=current_user.draw_key)

    # add the new draw to the database
    db.session.add(new_draw)
    db.session.commit()

    # re-render lottery.page
    flash('Draw %s submitted.' % submitted_draw)
    return lottery()


# view all draws that have not been played
@lottery_blueprint.route('/view_draws', methods=['POST'])
def view_draws():
    # get all draws that have not been played [played=0]
    playable_draws = Draw.query.filter_by(played=False, user_id=current_user.id).all()  # TODO: filter playable draws for current user

    # create a list of copied objects that can be altered
    draw_copies = list(map(lambda x: copy.deepcopy(x), playable_draws))

    # empty list for decrypted draws
    decrypted_draws = []

    for draw in draw_copies:
        draw.view_draw(current_user.draw_key)
        decrypted_draws.append(draw)

    # if playable draws exist
    if len(playable_draws) != 0:
        # re-render lottery page with playable draws
        return render_template('lottery.html', playable_draws=decrypted_draws)
    else:
        flash('No playable draws.')
        return lottery()


# view lottery results
@lottery_blueprint.route('/check_draws', methods=['POST'])
def check_draws():
    # get played draws
    played_draws = Draw.query.filter_by(played=True, user_id=current_user.id).all()  # TODO: filter played draws for current user

    # create a list of copied objects that can be altered
    draw_copies = list(map(lambda x: copy.deepcopy(x), played_draws))

    # empty list for decrypted draws
    decrypted_draws = []

    for draw in draw_copies:
        draw.view_draw(current_user.draw_key)
        decrypted_draws.append(draw)

    # if played draws exist
    if len(played_draws) != 0:
        return render_template('lottery.html', results=decrypted_draws, played=True)

    # if no played draws exist [all draw entries have been played therefore wait for next lottery round]
    else:
        flash("Next round of lottery yet to play. Check you have playable draws.")
        return lottery()


# delete all played draws
@lottery_blueprint.route('/play_again', methods=['POST'])
def play_again():
    delete_played = Draw.__table__.delete().where(Draw.played, Draw.user_id == current_user.id)  # TODO: delete played draws for current user only
    db.session.execute(delete_played)
    db.session.commit()

    flash("All played draws deleted.")
    return lottery()


