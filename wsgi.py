from rpm2cpe import Rpm
from rpm2cpe import Repo
import flask
application = flask.Flask(__name__)


@application.route('/rpm')
def flask_rpm():
    rpmnames = flask.request.args.getlist('name')
    strict_arg = flask.request.args.get('strict')

    if strict_arg in ['True', 'true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'uh-huh']:
        strict = True
    else:
        strict = False

    result = dict()
    for rpmname in rpmnames:
        print rpmname
        rpm2cpe = Rpm(rpmname, strict)
        result.update(dict(rpm2cpe))

    return flask.jsonify(result) 

@application.route('/repo')
def flask_repo():
    reponames = flask.request.args.getlist('name')
    strict_arg = flask.request.args.get('strict')

    if strict_arg in ['True', 'true', '1', 't', 'y', 'yes', 'yeah', 'yup', 'uh-huh']:
        strict = True
    else:
        strict = False

    result = dict()
    for reponame in reponames:
        repo = Repo(reponame, strict)
        result.update(dict(repo))
    return flask.jsonify(result)

@application.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    application.run()