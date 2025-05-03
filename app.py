from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SelectMultipleField,Form, BooleanField, SubmitField
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
    lp = db.Column(db.Integer, nullable=False)
    ap = db.Column(db.Integer, nullable=False)
    op = db.Column(db.Integer, nullable=False)
    chi = db.Column(db.Integer, nullable=False, default=0)  # Neue Spalte für Chi-Punkte
    rs_wert = db.Column(db.Integer, nullable=False)
    pa_basis = db.Column(db.Integer, nullable=False)
    at_basis = db.Column(db.Integer, nullable=False)
    wundschwelle = db.Column(db.Integer, nullable=False)
    damage = db.Column(db.Integer, nullable=False)
    wunden = db.Column(db.Integer, nullable=False)
    initiative = db.Column(db.Integer, nullable=False)
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

class CombatSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    attack = db.Column(db.Integer, nullable=False)
    parade = db.Column(db.Integer, nullable=False)
    be_relevant = db.Column(db.Boolean, default=False)
    be_faktor = db.Column(db.String(10), default="1")
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)


# Formulare
class CharacterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    lp = IntegerField('Lebenspunkte (LP)', validators=[DataRequired(), NumberRange(min=1)])
    ap = IntegerField('Ausdauerpunkte (AP)', validators=[DataRequired(), NumberRange(min=0)])
    op = IntegerField('Odempunkte (OP)', validators=[NumberRange(min=0)], default=0)
    chi = IntegerField('Chi-Punkte', validators=[NumberRange(min=0)], default=0)
    rs_wert = IntegerField('Rüstungsschutz (RS)', validators=[NumberRange(min=0)], default=0)
    pa_basis = IntegerField('Parade-Basiswert (PA)', validators=[DataRequired(), NumberRange(min=0)], default=6)
    at_basis = IntegerField('Attacke-Basiswert (AT)', validators=[DataRequired(), NumberRange(min=0)], default=6)
    wundschwelle = IntegerField('Wundschwelle', validators=[DataRequired(), NumberRange(min=1)])
    damage = IntegerField('Erhaltener Schaden', validators=[NumberRange(min=0)], default=0)
    wunden = IntegerField('Wunden', validators=[NumberRange(min=0)], default=0)
    initiative = IntegerField('Initiative (INI)', validators=[DataRequired(), NumberRange(min=1)])
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

class CombatSkillForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    attack = IntegerField('Attackwert', validators=[NumberRange(min=0)])
    parade = IntegerField('Paradewert', validators=[NumberRange(min=0)])
    be_relevant = BooleanField('BE relevant')
    be_faktor = StringField('BE-Faktor', default="1")
    submit = SubmitField('Speichern')

class CombatProbeForm(FlaskForm):
    skill_id = SelectField('Kampffähigkeit', coerce=int)
    wert_typ = SelectField('Typ', choices=[('attacke', 'Angriff'), ('parade', 'Parade')])
    w1 = IntegerField('Würfel (1-20)', validators=[NumberRange(min=1, max=20)])
    erschwernis = IntegerField('Erschwernis', default=0)
    submit = SubmitField('Probe durchführen')



# Routen
@app.route('/')
def index():
    characters = Character.query.all()
    return render_template('index.html', characters=characters)

@app.route('/character/new', methods=['GET', 'POST'])
def new_character():
    form = CharacterForm()
    
    # Wenn das Formular abgesendet wird
    if form.validate_on_submit():
        # Erstelle den Charakter
        character = Character(
            name=form.name.data,
            lp=form.lp.data,
            ap=form.ap.data,
            op=form.op.data,
            chi=form.chi.data,
            rs_wert=form.rs_wert.data,
            pa_basis=form.pa_basis.data,
            at_basis=form.at_basis.data,
            wundschwelle=form.wundschwelle.data,
            damage=0,  # Default immer 0
            wunden=0,  # Default immer 0
            initiative=form.initiative.data,
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
    
    # Wenn das Formular abgesendet wird
    if form.validate_on_submit():
        character.name = form.name.data
        character.lp = form.lp.data
        character.ap = form.ap.data
        character.op = form.op.data
        character.chi = form.chi.data
        character.rs_wert = form.rs_wert.data
        character.pa_basis = form.pa_basis.data
        character.at_basis = form.at_basis.data
        character.wundschwelle = form.wundschwelle.data
        character.damage = form.damage.data
        character.wunden = form.wunden.data
        character.initiative = form.initiative.data
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
    
    s = select(Talent).where(Talent.character_id == character_id)
    talents = db.session.execute(s).scalars().all() 
    #talents = Talent.query.filter_by(character_id=character_id).all()
    
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

# Liste der Kampffähigkeiten für einen Charakter
@app.route('/character/<int:character_id>/combat_skills')
def character_combat_skills(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    skills = CombatSkill.query.filter_by(character_id=character_id).all()
    return render_template('combat_skills.html', character=character, combat_skills=skills)

# Neue Kampffähigkeit anlegen
@app.route('/character/<int:character_id>/combat_skill/new', methods=['GET', 'POST'])
def new_combat_skill(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    form = CombatSkillForm()
    if form.validate_on_submit():
        cs = CombatSkill(
            name=form.name.data,
            attack=form.attack.data,
            parade=form.parade.data,
            be_relevant=form.be_relevant.data,
            be_faktor=form.be_faktor.data,
            character_id=character_id
        )
        db.session.add(cs)
        db.session.commit()
        flash(f'Kampffähigkeit "{cs.name}" wurde hinzugefügt!', 'success')
        return redirect(url_for('character_combat_skills', character_id=character_id))
    return render_template('combat_skill_form.html', form=form, character=character, title='Neue Kampffähigkeit')

# Kampffähigkeit bearbeiten
@app.route('/combat_skill/<int:skill_id>/edit', methods=['GET', 'POST'])
def edit_combat_skill(skill_id):
    cs = db.session.get(CombatSkill, skill_id)
    if cs is None:
        abort(404)
    form = CombatSkillForm(obj=cs)
    if form.validate_on_submit():
        cs.name = form.name.data
        cs.attack = form.attack.data
        cs.parade = form.parade.data
        cs.be_relevant = form.be_relevant.data
        cs.be_faktor = form.be_faktor.data
        db.session.commit()
        flash(f'Kampffähigkeit "{cs.name}" wurde aktualisiert!', 'success')
        return redirect(url_for('character_combat_skills', character_id=cs.character_id))
    return render_template('combat_skill_form.html', form=form, character=cs.character, title='Kampffähigkeit bearbeiten')

# Kampffähigkeit löschen
@app.route('/combat_skill/<int:skill_id>/delete')
def delete_combat_skill(skill_id):
    cs = db.session.get(CombatSkill, skill_id)
    if cs is None:
        abort(404)
    character_id = cs.character_id
    name = cs.name
    db.session.delete(cs)
    db.session.commit()
    flash(f'Kampffähigkeit "{name}" wurde gelöscht!', 'success')
    return redirect(url_for('character_combat_skills', character_id=character_id))


# Zusätzliche Route für Combat-Proben
@app.route('/character/<int:character_id>/combat_probe', methods=['GET', 'POST'])
def combat_probe(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    
    
    form = CombatProbeForm()

    s = select(CombatSkill).where(CombatSkill.character_id == character_id)
    combat_skills = db.session.execute(s).scalars().all() 
    
    form.skill_id.choices = [(cs.id, cs.name) for cs in combat_skills]
    
    result = None
    details = None
    
    
    if not combat_skills:
        flash('Füge zuerst eine Kampffähigkeit für diesen Charakter hinzu!', 'warning')
        return redirect(url_for('character_combat_skills', character_id=character_id))
    
    # Initialisiere Würfelwert mit Default
    if not form.w1.data:
        form.w1.data = 10
    
    if request.method == 'POST':
        # Speichere das ausgewählte Talent
        skill = request.form.get('skill_id')
        if skill:
            form.skill_id.data = int(skill)
        # Würfel-Generierung
        if 'wuerfeln' in request.form:
            w1 = random.randint(1, 20)
            form.w1.data = w1
            flash(f'Gewürfelt: {w1}', 'info')
            return render_template('combat_probe.html', 
                                form=form, 
                                character=character, 
                                result=None, 
                                details=None)
    
    if form.validate_on_submit() and 'submit' in request.form:
        skill = db.session.get(CombatSkill, skill)
        if not skill:
            flash('Kampffähigkeit nicht gefunden', 'error')
            return redirect(url_for('combat_probe', character_id=character_id))
        
        typ = ""
        # Basiswert bestimmen (Angriff oder Parade)
        if form.wert_typ.data == 'attacke':
            basiswert = skill.attack
            typ = "Angriff"
        else:
            basiswert = skill.parade
            typ = "Verteidigung"
        
        # BE-Berechnung
        be_wert = 0
        be_faktor = skill.be_faktor or "1"
        if skill.be_relevant and character.be > 0:
            if be_faktor.startswith(('+', '-')):
                try:
                    be_wert = max(0,character.be + int(be_faktor))
                except ValueError:
                    be_wert = character.be
            else:
                try:
                    be_wert = character.be * int(be_faktor)
                except ValueError:
                    be_wert = character.be
        
        # Effektiver Basiswert
        effektiv_basis = max(0, basiswert - be_wert)
        
        # Erschwernis verarbeiten
        erschwernis = form.erschwernis.data or 0
        effektiver_wert = max(0, effektiv_basis - erschwernis)
        
        # Probe auswerten
        wuerfel = form.w1.data
        success = wuerfel <= effektiver_wert
        

        # Kritische Ergebnisse
        is_critical_success = wuerfel == 1
        is_critical_failure = wuerfel == 20
        
        if is_critical_failure:
            wuerfel = random.randint(1,20)
            is_critical_failure = wuerfel > effektiver_wert
        else:
            is_critical_failure = False 

        if is_critical_success:
            wuerfel = random.randint(1,20)
            is_critical_success = wuerfel <= effektiver_wert
        else:
            is_critical_success = False


        details = {
            'skill': skill,
            'wert_typ': typ,
            'erschwernis': erschwernis,
            'wuerfel': wuerfel,
            "diff": effektiver_wert

        }
        
        result = {
            'success': success,
            'message': 'Erfolg!' if success else 'Fehlschlag!',
            'is_critical': is_critical_success or is_critical_failure
        }
    
    return render_template('combat_probe.html',
                         form=form,
                         character=character,
                         result=result,
                         details=details)


@app.route('/init_db')
def init_db():
    db.create_all()
    flash('Datenbank initialisiert!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Erstellt die Datenbank automatisch beim Start
    app.run(debug=True)