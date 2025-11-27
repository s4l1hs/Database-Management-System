from flask import Blueprint, render_template

about_bp = Blueprint("about", __name__)

@about_bp.route("/about")
def about():
    members = [
        {"name": "Gülbahar Karabaş", "number": "150210085"},
        {"name": "Salih Sefer", "number": "820230313"},
        {"name": "Muhammet Tuncer", "number": "820230314"},
        {"name": "Atahan Evintan", "number": "820230334"},
        {"name": "Fatih Serdar Çakmak", "number": "820230326"},
    ]
    return render_template("about.html", members=members)
