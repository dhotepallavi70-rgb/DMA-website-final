from flask import Flask, render_template, request, flash, redirect, url_for

app = Flask(__name__)
app.secret_key = "change-this-secret-key"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/founder")
def founder():
    return render_template("founder.html")

@app.route("/courses")
def courses():
    return render_template("courses.html")

@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/testimonials")
def testimonials():
    return render_template("testimonials.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        flash(f"Thank you {name}! Your admission enquiry has been received. We will contact you soon.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")

if __name__ == "__main__":
    app.run(debug=True)
