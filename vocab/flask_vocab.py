"""
Flask web site with vocabulary matching game
(identify vocabulary words that can be made 
from a scrambled string)
"""

import flask
import logging

# Our own modules
from letterbag import LetterBag
from vocab import Vocab
from jumble import jumbled
import config

###
# Globals
###
app = flask.Flask(__name__)

CONFIG = config.configuration()
app.secret_key = CONFIG.SECRET_KEY  # Should allow using session variables

#
# One shared 'Vocab' object, read-only after initialization,
# shared by all threads and instances.  Otherwise we would have to
# store it in the browser and transmit it on each request/response cycle,
# or else read it from the file on each request/responce cycle,
# neither of which would be suitable for responding keystroke by keystroke.

WORDS = Vocab(CONFIG.VOCAB)

###
# Pages
###


@app.route("/")
@app.route("/index")
def index():
    """The main page of the application"""
    flask.g.vocab = WORDS.as_list()
    flask.session["target_count"] = min(
        len(flask.g.vocab), CONFIG.SUCCESS_AT_COUNT)
    flask.session["jumble"] = jumbled(
        flask.g.vocab, flask.session["target_count"])
    flask.session["matches"] = []
    app.logger.debug("Session variables have been set")
    assert flask.session["matches"] == []
    assert flask.session["target_count"] > 0
    app.logger.debug("At least one seems to be set correctly")
    return flask.render_template('vocab.html')


@app.route("/keep_going")
def keep_going():
    """
    After initial use of index, we keep the same scrambled
    word and try to get more matches
    """
    flask.g.vocab = WORDS.as_list()
    return flask.render_template('vocab.html')


@app.route("/success")
def success():
    return flask.render_template('success.html')

###############
# AJAX request handlers
#   These return JSON, rather than rendering pages.
###############


@app.route("/_check")
def check():
    """
    Called on each keystroke with the current contents ('text')
    of the input field.  We respond with JSON describing whether
    the text is a new word on the vocabulary list (therefore
    correctly spelled), made only from the jumble letters, and
    not a word they already found.  The page decides what to do
    with the result; no page is rendered here.  When 'final' is
    set (the user pressed Enter), we also say if the word isn't
    on the list; otherwise that would flag every partial word.
    """
    app.logger.debug("Entering check")

    # The data we need, from the request and from the cookie
    text = flask.request.args.get("text", "", type=str).strip()
    final = flask.request.args.get("final", "") == "true"
    jumble = flask.session.get("jumble", "")
    matches = flask.session.get("matches", [])  # Default to empty list
    target_count = flask.session.get("target_count", 1)

    # Is it good?
    in_jumble = LetterBag(jumble).contains(text)
    matched = WORDS.has(text)
    already_found = text in matches

    # Respond appropriately
    new_match = False
    message = ""
    if matched and in_jumble and not already_found:
        # Cool, they found a new word
        matches.append(text)
        flask.session["matches"] = matches
        new_match = True
    elif already_found:
        message = "You already found {}".format(text)
    elif text and not in_jumble:
        message = '"{}" can\'t be made from the letters {}'.format(
            text, jumble)
    elif text and final and not matched:
        message = "{} isn't in the list of words".format(text)

    rslt = {
        "new_match": new_match,
        "word": text,
        "matches": matches,
        "message": message,
        "solved": len(matches) >= target_count,
        "success_url": flask.url_for("success"),
    }
    return flask.jsonify(result=rslt)


@app.route("/_example")
def example():
    """
    Example ajax request handler
    """
    app.logger.debug("Got a JSON request")
    rslt = {"key": "value"}
    return flask.jsonify(result=rslt)


#################
# Functions used within the templates
#################

@app.template_filter('filt')
def format_filt(something):
    """
    Example of a filter that can be used within
    the Jinja2 code
    """
    return "Not what you asked for"

###################
#   Error handlers
###################


@app.errorhandler(404)
def error_404(e):
    app.logger.warning("++ 404 error: {}".format(e))
    return flask.render_template('404.html'), 404


@app.errorhandler(500)
def error_500(e):
    app.logger.warning("++ 500 error: {}".format(e))
    assert not True  # I want to invoke the debugger
    return flask.render_template('500.html'), 500


@app.errorhandler(403)
def error_403(e):
    app.logger.warning("++ 403 error: {}".format(e))
    return flask.render_template('403.html'), 403


####

if __name__ == "__main__":
    if CONFIG.DEBUG:
        app.debug = True
        app.logger.setLevel(logging.DEBUG)
        app.logger.info(
            "Opening for global access on port {}".format(CONFIG.PORT))
        app.run(port=CONFIG.PORT, host="0.0.0.0")
