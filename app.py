from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SelectMultipleField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange
import random
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dsa_proben.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelle
class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mut = db.Column(db.Integer, nullable=False)
    klugheit = db.Column(db.Integer, nullable=False)
    intuition = db.Column(db.Integer, nullable=False)
    charisma = db.Column(db.Integer, nullable=False)
    fingerfertigkeit = db.Column(db.Integer, nullable=False)
    gewandtheit = db.Column(db.Integer, nullable=False)
    konstitution = db.Column(db.Integer, nullable=False)
    koerperkraft = db.Column(db.Integer, nullable=False)
    be = db.Column(db.Integer, default=0)
    talente = db.relationship('Talent', backref='character', lazy=True, cascade="all, delete-orphan")

    def get_attribute(self, attr_key):
        attr_map = {
            'MU': self.mut,
            'KL': self.klugheit,
            'IN': self.intuition,
            'CH': self.charisma,
            'FF': self.fingerfertigkeit,
            'GE': self.gewandtheit,
            'KO': self.konstitution,
            'KK': self.koerperkraft
        }
        return attr_map.get(attr_key, 0)

class Talent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    attr1 = db.Column(db.String(2), nullable=False)
    attr2 = db.Column(db.String(2), nullable=False)
    attr3 = db.Column(db.String(2), nullable=False)
    talentwert = db.Column(db.Integer, nullable=False, default=0)
    be_relevant = db.Column(db.Boolean, default=False)
    be_faktor = db.Column(db.String(10), default="1")  # Faktor als String, z.B. "2" für *2 oder "+2" für absolut
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)

# Formulare
class CharacterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    mut = IntegerField('Mut (MU)', validators=[DataRequired(), NumberRange(min=1, max=30)])
    klugheit = IntegerField('Klugheit (KL)', validators=[DataRequired(), NumberRange(min=1, max=30)])
    intuition = IntegerField('Intuition (IN)', validators=[DataRequired(), NumberRange(min=1, max=30)])
    charisma = IntegerField('Charisma (CH)', validators=[DataRequired(), NumberRange(min=1, max=30)])
    fingerfertigkeit = IntegerField('Fingerfertigkeit (FF)', validators=[DataRequired(), NumberRange(min=1, max=30)])
    gewandtheit = IntegerField('Gewandtheit (GE)', validators=[DataRequired(), NumberRange(min=1, max=30)])
    konstitution = IntegerField('Konstitution (KO)', validators=[DataRequired(), NumberRange(min=1, max=30)])
    koerperkraft = IntegerField('Körperkraft (KK)', validators=[DataRequired(), NumberRange(min=1, max=30)])
    be = IntegerField('Behinderung (BE)', validators=[NumberRange(min=0, max=10)], default=0)
    submit = SubmitField('Speichern')

class TalentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    attr1 = SelectField('Attribut 1', choices=[
        ('MU', 'Mut'), ('KL', 'Klugheit'), ('IN', 'Intuition'), ('CH', 'Charisma'),
        ('FF', 'Fingerfertigkeit'), ('GE', 'Gewandtheit'), ('KO', 'Konstitution'), ('KK', 'Körperkraft')
    ], validators=[DataRequired()])
    attr2 = SelectField('Attribut 2', choices=[
        ('MU', 'Mut'), ('KL', 'Klugheit'), ('IN', 'Intuition'), ('CH', 'Charisma'),
        ('FF', 'Fingerfertigkeit'), ('GE', 'Gewandtheit'), ('KO', 'Konstitution'), ('KK', 'Körperkraft')
    ], validators=[DataRequired()])
    attr3 = SelectField('Attribut 3', choices=[
        ('MU', 'Mut'), ('KL', 'Klugheit'), ('IN', 'Intuition'), ('CH', 'Charisma'),
        ('FF', 'Fingerfertigkeit'), ('GE', 'Gewandtheit'), ('KO', 'Konstitution'), ('KK', 'Körperkraft')
    ], validators=[DataRequired()])
    talentwert = IntegerField('Talentwert', validators=[NumberRange(min=0)], default=0)
    be_relevant = BooleanField('BE relevant')
    be_faktor = StringField('BE-Faktor (z.B. "2" für *2, "-1" für -1 usw.)', default="1")
    submit = SubmitField('Speichern')

class ProbeForm(FlaskForm):
    talent_id = SelectField('Talent', coerce=int)
    w1 = IntegerField('Würfel 1 (1-20)', validators=[NumberRange(min=1, max=20)])
    w2 = IntegerField('Würfel 2 (1-20)', validators=[NumberRange(min=1, max=20)])
    w3 = IntegerField('Würfel 3 (1-20)', validators=[NumberRange(min=1, max=20)])
    submit = SubmitField('Probe durchführen')

# Routen
@app.route('/')
def index():
    characters = Character.query.all()
    return render_template('index.html', characters=characters)

@app.route('/character/new', methods=['GET', 'POST'])
def new_character():
    form = CharacterForm()
    if form.validate_on_submit():
        character = Character(
            name=form.name.data,
            mut=form.mut.data,
            klugheit=form.klugheit.data,
            intuition=form.intuition.data,
            charisma=form.charisma.data,
            fingerfertigkeit=form.fingerfertigkeit.data,
            gewandtheit=form.gewandtheit.data,
            konstitution=form.konstitution.data,
            koerperkraft=form.koerperkraft.data,
            be=form.be.data
        )
        db.session.add(character)
        db.session.commit()
        flash(f'Charakter "{character.name}" wurde erstellt!', 'success')
        return redirect(url_for('index'))
    return render_template('character_form.html', form=form, title='Neuer Charakter')

@app.route('/character/<int:character_id>/edit', methods=['GET', 'POST'])
def edit_character(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)  # Manuelles Werfen eines 404-Fehlers
    form = CharacterForm(obj=character)
    if form.validate_on_submit():
        character.name = form.name.data
        character.mut = form.mut.data
        character.klugheit = form.klugheit.data
        character.intuition = form.intuition.data
        character.charisma = form.charisma.data
        character.fingerfertigkeit = form.fingerfertigkeit.data
        character.gewandtheit = form.gewandtheit.data
        character.konstitution = form.konstitution.data
        character.koerperkraft = form.koerperkraft.data
        character.be = form.be.data
        db.session.commit()
        flash(f'Charakter "{character.name}" wurde aktualisiert!', 'success')
        return redirect(url_for('index'))
    return render_template('character_form.html', form=form, title='Charakter bearbeiten')

@app.route('/character/<int:character_id>/delete')
def delete_character(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    name = character.name
    db.session.delete(character)
    db.session.commit()
    flash(f'Charakter "{name}" wurde gelöscht!', 'success')
    return redirect(url_for('index'))

@app.route('/character/<int:character_id>/talents')
def character_talents(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    talents = Talent.query.filter_by(character_id=character_id).all()
    return render_template('talents.html', character=character, talents=talents)

@app.route('/character/<int:character_id>/talent/new', methods=['GET', 'POST'])
def new_talent(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    form = TalentForm()
    if form.validate_on_submit():
        talent = Talent(
            name=form.name.data,
            attr1=form.attr1.data,
            attr2=form.attr2.data,
            attr3=form.attr3.data,
            talentwert=form.talentwert.data,
            be_relevant=form.be_relevant.data,
            be_faktor=form.be_faktor.data,
            character_id=character.id
        )
        db.session.add(talent)
        db.session.commit()
        flash(f'Talent "{talent.name}" wurde hinzugefügt!', 'success')
        return redirect(url_for('character_talents', character_id=character.id))
    return render_template('talent_form.html', form=form, character=character, title='Neues Talent')

@app.route('/talent/<int:talent_id>/edit', methods=['GET', 'POST'])
def edit_talent(talent_id):
    talent = db.session.get(Talent, talent_id)
    if talent is None:
        abort(404)
    form = TalentForm(obj=talent)
    if form.validate_on_submit():
        talent.name = form.name.data
        talent.attr1 = form.attr1.data
        talent.attr2 = form.attr2.data
        talent.attr3 = form.attr3.data
        talent.talentwert = form.talentwert.data
        talent.be_relevant = form.be_relevant.data
        talent.be_faktor = form.be_faktor.data
        db.session.commit()
        flash(f'Talent "{talent.name}" wurde aktualisiert!', 'success')
        return redirect(url_for('character_talents', character_id=talent.character_id))
    return render_template('talent_form.html', form=form, character=talent.character, title='Talent bearbeiten')

@app.route('/talent/<int:talent_id>/delete')
def delete_talent(talent_id):
    talent = db.session.get(Talent, talent_id)
    if talent is None:
        abort(404)
    character_id = talent.character_id
    name = talent.name
    db.session.delete(talent)
    db.session.commit()
    flash(f'Talent "{name}" wurde gelöscht!', 'success')
    return redirect(url_for('character_talents', character_id=character_id))

@app.route('/character/<int:character_id>/probe', methods=['GET', 'POST'])
def probe(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    talents = Talent.query.filter_by(character_id=character_id).all()
    
    form = ProbeForm()
    form.talent_id.choices = [(t.id, t.name) for t in talents]
    
    result = None
    details = None
    
    if not talents:
        flash('Füge zuerst ein Talent für diesen Charakter hinzu!', 'warning')
        return redirect(url_for('character_talents', character_id=character_id))
    
    # Initialisiere mit Standardwerten, wenn keine Würfel gesetzt sind
    if not form.w1.data:
        form.w1.data = 10  # Default-Wert
    if not form.w2.data:
        form.w2.data = 10  # Default-Wert
    if not form.w3.data:
        form.w3.data = 10  # Default-Wert
    
    if request.method == 'POST':
        # Speichere das ausgewählte Talent
        selected_talent = request.form.get('talent_id')
        if selected_talent:
            form.talent_id.data = int(selected_talent)
        
        # Wenn "Würfeln" geklickt wurde
        if 'wuerfeln' in request.form:
            # Würfelwerte generieren
            w1 = random.randint(1, 20)
            w2 = random.randint(1, 20)
            w3 = random.randint(1, 20)
            
            # Debug-Ausgabe
            print(f"Würfelwerte: {w1}, {w2}, {w3}")
            
            # Formular-Daten setzen
            form.w1.data = w1
            form.w2.data = w2
            form.w3.data = w3
            
            # Debug-Ausgabe der Form-Daten
            print(f"Form-Daten nach Setzen: w1={form.w1.data}, w2={form.w2.data}, w3={form.w3.data}")
            
            # Flash-Nachricht zur Bestätigung
            flash(f'Gewürfelt: {w1}, {w2}, {w3}', 'info')
            
            # Kein validate_on_submit, sondern direkt das Template rendern
            return render_template('probe.html', form=form, character=character, result=None, details=None)
    
    # Separate if-Anweisung für "Probe durchführen" (kein elif)
    if form.validate_on_submit() and 'submit' in request.form:
        talent = db.session.get(Talent, form.talent_id.data)
        if talent is None:
            flash('Talent nicht gefunden.', 'error')
            return redirect(url_for('character_talents', character_id=character_id))
        
        # Attribute abrufen
        attr1_value = character.get_attribute(talent.attr1)
        attr2_value = character.get_attribute(talent.attr2)
        attr3_value = character.get_attribute(talent.attr3)
        talent = db.session.get(Talent, form.talent_id.data)
        
        # Attribute abrufen
        attr1_value = character.get_attribute(talent.attr1)
        attr2_value = character.get_attribute(talent.attr2)
        attr3_value = character.get_attribute(talent.attr3)
        
        # BE-Wert für die Probe berechnen
        be_wert = 0
        be_faktor = talent.be_faktor or "1"
        if talent.be_relevant and character.be > 0:
            # Prüfen, ob es ein Faktor oder ein absoluter Wert ist
            if be_faktor.startswith("+") or be_faktor.startswith("-"):
                # Absoluter Wert
                be_wert = character.be + int(be_faktor)
            else:
                # Faktor
                try:
                    be_wert = character.be * int(be_faktor)
                except ValueError:
                    be_wert = character.be  # Fallback wenn kein gültiger Faktor
            
        
        # Effektiver Talentwert berechnen (BE wird vom Talentwert abgezogen)
        effektiver_talentwert = talent.talentwert
        if talent.be_relevant and character.be > 0:
            effektiver_talentwert = max(0, talent.talentwert - be_wert)
        
        # Differenzen berechnen
        diff1 = form.w1.data - attr1_value
        diff2 = form.w2.data - attr2_value
        diff3 = form.w3.data - attr3_value
        
        # Negative Differenzen auf 0 setzen
        diff1 = max(0, diff1)
        diff2 = max(0, diff2)
        diff3 = max(0, diff3)
        
        # Gesamtdifferenz berechnen
        total_diff = diff1 + diff2 + diff3
        
        # Ergebnis ermitteln
        if total_diff <= effektiver_talentwert:
            result = True
            remaining_points = effektiver_talentwert - total_diff
            
            # Prüfen auf kritischen Erfolg (mindestens eine 1 gewürfelt)
            is_critical = (form.w1.data == 1 or form.w2.data == 1 or form.w3.data == 1)
            
            details = {
                'talent': talent,
                'w1': form.w1.data,
                'w2': form.w2.data,
                'w3': form.w3.data,
                'attr1': {'key': talent.attr1, 'value': attr1_value, 'diff': diff1},
                'attr2': {'key': talent.attr2, 'value': attr2_value, 'diff': diff2},
                'attr3': {'key': talent.attr3, 'value': attr3_value, 'diff': diff3},
                'total_diff': total_diff,
                'talentwert': talent.talentwert,
                'effektiver_talentwert': effektiver_talentwert,
                'remaining_points': remaining_points,
                'be_applied': talent.be_relevant and character.be > 0,
                'be': character.be,
                'be_faktor': be_faktor,
                'be_wert': be_wert,
                'is_critical': is_critical
            }
        else:
            result = False
            remaining_points = total_diff - effektiver_talentwert
            
            # Prüfen auf kritischen Fehlschlag (mindestens eine 20 gewürfelt)
            is_critical = (form.w1.data == 20 or form.w2.data == 20 or form.w3.data == 20)
            
            details = {
                'talent': talent,
                'w1': form.w1.data,
                'w2': form.w2.data,
                'w3': form.w3.data,
                'attr1': {'key': talent.attr1, 'value': attr1_value, 'diff': diff1},
                'attr2': {'key': talent.attr2, 'value': attr2_value, 'diff': diff2},
                'attr3': {'key': talent.attr3, 'value': attr3_value, 'diff': diff3},
                'total_diff': total_diff,
                'talentwert': talent.talentwert,
                'effektiver_talentwert': effektiver_talentwert,
                'remaining_points': remaining_points,
                'be_applied': talent.be_relevant and character.be > 0,
                'be': character.be,
                'be_faktor': be_faktor,
                'be_wert': be_wert,
                'is_critical': is_critical
            }
    
    return render_template('probe.html', form=form, character=character, result=result, details=details)

@app.route('/init_db')
def init_db():
    db.create_all()
    flash('Datenbank initialisiert!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Erstellt die Datenbank automatisch beim Start
    app.run(debug=True)