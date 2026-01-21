import os
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, FloatField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'farm_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///farm_database.db'

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- მონაცემთა ბაზა ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    phone = db.Column(db.String(20), nullable=False)  # <-- ახალი სვეტი ტელეფონისთვის
    is_admin = db.Column(db.Boolean, default=False)
    machines = db.relationship('Machine', backref='owner', lazy=True)

class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ფორმები ---
class RegisterForm(FlaskForm):
    username = StringField('სახელი', validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('ტელეფონის ნომერი', validators=[DataRequired()]) # <-- ტელეფონის ველი
    password = PasswordField('პაროლი', validators=[DataRequired()])
    confirm_password = PasswordField('გაიმეორეთ პაროლი', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('რეგისტრაცია')

class LoginForm(FlaskForm):
    username = StringField('მომხმარებელი', validators=[DataRequired()])
    password = PasswordField('პაროლი', validators=[DataRequired()])
    submit = SubmitField('შესვლა')

class MachineForm(FlaskForm):
    name = StringField('ტექნიკის დასახელება', validators=[DataRequired()])
    category = StringField('კატეგორია', validators=[DataRequired()])
    price = FloatField('ფასი დღიურად (₾)', validators=[DataRequired()])
    description = TextAreaField('აღწერა')
    image = FileField('ატვირთეთ ფოტო', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('შენახვა')



@app.route('/')
def index():
    search_query = request.args.get('search')
    if search_query:
        machines = Machine.query.filter(
            (Machine.name.contains(search_query)) |
            (Machine.category.contains(search_query))
        ).all()
    else:
        machines = Machine.query.all()
    return render_template('index.html', machines=machines)

@app.route('/machine/<int:machine_id>')
def machine_details(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    return render_template('machine_details.html', machine=machine)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, phone=form.phone.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('ანგარიში შეიქმნა!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            return redirect(url_for('index'))
        flash('არასწორი მონაცემები', 'danger')
    return render_template('login.html', form=form)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_machine():
    form = MachineForm()
    if form.validate_on_submit():
        image_name = 'default.jpg'
        if form.image.data:
            f = form.image.data
            image_name = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))

        new_item = Machine(
            name=form.name.data,
            category=form.category.data,
            price=form.price.data,
            description=form.description.data,
            owner=current_user,
            image_file=image_name
        )
        db.session.add(new_item)
        db.session.commit()
        flash('განცხადება დაემატა!', 'success')
        return redirect(url_for('index'))
    return render_template('add_machine.html', form=form, title="ტექნიკის დამატება")

@app.route('/edit/<int:machine_id>', methods=['GET', 'POST'])
@login_required
def edit_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    if machine.owner != current_user and not current_user.is_admin:
        abort(403)
    form = MachineForm()
    if form.validate_on_submit():
        if form.image.data:
            f = form.image.data
            image_name = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
            machine.image_file = image_name

        machine.name = form.name.data
        machine.category = form.category.data
        machine.price = form.price.data
        machine.description = form.description.data
        db.session.commit()
        flash('განახლდა!', 'success')
        return redirect(url_for('index'))
    elif request.method == 'GET':
        form.name.data = machine.name
        form.category.data = machine.category
        form.price.data = machine.price
        form.description.data = machine.description
    return render_template('add_machine.html', form=form, title="რედაქტირება")

@app.route('/delete/<int:machine_id>', methods=['POST'])
@login_required
def delete_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    if machine.owner != current_user and not current_user.is_admin:
        abort(403)
    db.session.delete(machine)
    db.session.commit()
    flash('წაიშალა!', 'info')
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            # ადმინისთვისაც ვამატებთ სატესტო ნომერს
            admin = User(username='admin', password='123', phone='555000000', is_admin=True)
            db.session.add(admin)
            db.session.commit()
    app.run(debug=False)