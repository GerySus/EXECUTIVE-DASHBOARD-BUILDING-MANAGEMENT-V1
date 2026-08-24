import os

from flask import Flask, jsonify, render_template

from data_processing import get_dashboard_data

app = Flask(__name__)


def kpi_card_bg(color):
    return (f'linear-gradient(160deg,var(--panel1),var(--panel2)) padding-box,'
            f'linear-gradient(150deg,{color}F2 0%,{color}48 45%,{color}0F 100%) border-box')


def flow_box_style(color):
    bg = (f'linear-gradient(160deg,{color}26,{color}0A) padding-box,'
          f'linear-gradient(150deg,{color}F2 0%,{color}55 45%,{color}12 100%) border-box')
    return (f'background:{bg};'
            f'box-shadow:0 10px 22px -12px rgba(0,0,0,.6), 0 0 24px -3px {color}D9, '
            f'inset 0 1px 0 rgba(255,255,255,.12), inset 0 -12px 20px -14px {color}55')


app.jinja_env.globals.update(kpi_bg=kpi_card_bg, flow_style=flow_box_style)


@app.route("/")
def index():
    return render_template("index.html", d=get_dashboard_data())


@app.route("/api/refresh", methods=["POST"])
def refresh():
    """Force-refetch the Google Sheet, bypassing the in-memory cache."""
    get_dashboard_data(force_refresh=True)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
