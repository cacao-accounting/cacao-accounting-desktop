from cacao_accounting.server import app
from flaskwebgui import FlaskUI

if __name__ == "__main__":

  FlaskUI(app=app, server="flask", port=9871).run()
