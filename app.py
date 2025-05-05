from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField,TextAreaField, FloatField, SelectMultipleField,Form, BooleanField, SubmitField
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
    melee_weapon_links = db.relationship('CharacterMeleeWeapon', backref='character', lazy=True, cascade="all, delete-orphan")
    ranged_weapon_links = db.relationship('CharacterRangedWeapon', backref='character', lazy=True, cascade="all, delete-orphan")
    parry_weapon_links = db.relationship('CharacterParryWeapon', backref='character', lazy=True, cascade="all, delete-orphan")
    armor_links = db.relationship('CharacterArmor', backref='character', lazy=True, cascade="all, delete-orphan")

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

# Basisklasse für alle Waffen
class Weapon(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

# Nahkampfwaffen
class MeleeWeapon(Weapon):
    __tablename__ = 'melee_weapon'
    be = db.Column(db.Integer, default=0)  # Behinderung
    tp = db.Column(db.String(20), nullable=False)  # z.B. "1W6+4"
    tp_kk_schwelle = db.Column(db.Integer, default=0)  # Ab welcher KK gibt es Bonus
    tp_kk_schritt = db.Column(db.Integer, default=0)  # Nach wie vielen Punkten über der Schwelle +1 TP
    ini_mod = db.Column(db.Integer, default=0)  # Initiative-Modifikator
    at_mod = db.Column(db.Integer, default=0)  # Attacke-Modifikator
    pa_mod = db.Column(db.Integer, default=0)  # Parade-Modifikator
    character_links = db.relationship('CharacterMeleeWeapon', backref='weapon', lazy=True, cascade="all, delete-orphan")

# Fernkampfwaffen
class RangedWeapon(Weapon):
    __tablename__ = 'ranged_weapon'
    be = db.Column(db.Integer, default=0)  # Behinderung
    tp = db.Column(db.String(20), nullable=False)  # z.B. "1W6+4"
    reichweite = db.Column(db.String(50), nullable=False)  # z.B. "5/10/15/25/40"
    tp_mod_entfernung = db.Column(db.String(50), nullable=False)  # z.B. "+2/+1/0/-1/-3"
    ladezeit_einzeln = db.Column(db.Integer, default=1)  # Ladezeit innerhalb eines Magazins
    ladezeit_magazin = db.Column(db.Integer, nullable=True)  # Ladezeit für Magazinwechsel, NULL wenn kein Magazin
    munition_max = db.Column(db.Integer, default=0)  # Maximale Munition
    character_links = db.relationship('CharacterRangedWeapon', backref='weapon', lazy=True, cascade="all, delete-orphan")

# Parierwaffen
class ParryWeapon(Weapon):
    __tablename__ = 'parry_weapon'
    ini_mod = db.Column(db.Integer, default=0)  # Initiative-Modifikator
    at_mod = db.Column(db.Integer, default=0)  # Attacke-Modifikator
    pa_mod = db.Column(db.Integer, default=0)  # Parade-Modifikator
    character_links = db.relationship('CharacterParryWeapon', backref='weapon', lazy=True, cascade="all, delete-orphan")


# Verbindungstabellen für Ausrüstung (Character-Weapon Beziehungen)
class CharacterMeleeWeapon(db.Model):
    __tablename__ = 'character_melee_weapon'
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    weapon_id = db.Column(db.Integer, db.ForeignKey('melee_weapon.id'), nullable=False)
    equipped = db.Column(db.Boolean, default=False)
 
class CharacterRangedWeapon(db.Model):
    __tablename__ = 'character_ranged_weapon'
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    weapon_id = db.Column(db.Integer, db.ForeignKey('ranged_weapon.id'), nullable=False)
    equipped = db.Column(db.Boolean, default=False)
    # Zusätzliche charakterspezifische Attribute für die Waffe
    munition_aktuell = db.Column(db.Integer, default=0)  # Aktuelle Munition

class CharacterParryWeapon(db.Model):
    __tablename__ = 'character_parry_weapon'
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    weapon_id = db.Column(db.Integer, db.ForeignKey('parry_weapon.id'), nullable=False)
    equipped = db.Column(db.Boolean, default=False)

# Armor model
class Armor(db.Model):
    __tablename__ = 'armor'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rs_wert = db.Column(db.Integer, default=0)  # Rüstungsschutz (armor value)
    be = db.Column(db.Integer, default=0)  # Behinderung (encumbrance)
    character_links = db.relationship('CharacterArmor', backref='armor', lazy=True, cascade="all, delete-orphan")

# Verbindungstabelle Character-Armor
class CharacterArmor(db.Model):
    __tablename__ = 'character_armor'
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False)
    armor_id = db.Column(db.Integer, db.ForeignKey('armor.id'), nullable=False)
    equipped = db.Column(db.Boolean, default=False)

# Inventory model für allgemeine Gegenstände
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('character.id'), nullable=False, unique=True)
    money = db.Column(db.Float, default=0.0)  # Geldmenge
    character = db.relationship('Character', backref=db.backref('inventory', uselist=False, cascade="all, delete-orphan"))
    general_items = db.relationship('InventoryItem', backref='inventory', lazy=True, cascade="all, delete-orphan")
    
# Allgemeiner Inventargegenstand
class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)




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
    erschwernis = IntegerField('Erschwernis', default=0)  # Neues Feld für Erschwernis
    submit = SubmitField('Probe durchführen')

class AttributProbeForm(FlaskForm):
    attribut = SelectField('Attribut', choices=[
        ('MU', 'Mut'), ('KL', 'Klugheit'), ('IN', 'Intuition'), ('CH', 'Charisma'),
        ('FF', 'Fingerfertigkeit'), ('GE', 'Gewandtheit'), ('KO', 'Konstitution'), ('KK', 'Körperkraft')
    ], validators=[DataRequired()])
    w1 = IntegerField('Würfel (1-20)', validators=[NumberRange(min=1, max=20)])
    erschwernis = IntegerField('Erschwernis', default=0)
    submit = SubmitField('Attributprobe durchführen')

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

# Formularklassen für Waffen
class MeleeWeaponForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    be = IntegerField('Behinderung (BE)', validators=[NumberRange(min=0)], default=0)
    tp = StringField('Trefferpunkte (z.B. "1W6+4")', validators=[DataRequired()])
    tp_kk_schwelle = IntegerField('KK-Schwelle für TP-Bonus', validators=[NumberRange(min=0)], default=0)
    tp_kk_schritt = IntegerField('KK-Schrittweite für TP-Bonus', validators=[NumberRange(min=0)], default=0)
    ini_mod = IntegerField('Initiative-Modifikator', default=0)
    at_mod = IntegerField('Attacke-Modifikator', default=0)
    pa_mod = IntegerField('Parade-Modifikator', default=0)
    submit = SubmitField('Speichern')

class RangedWeaponForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    be = IntegerField('Behinderung (BE)', validators=[NumberRange(min=0)], default=0)
    tp = StringField('Trefferpunkte (z.B. "1W6+4")', validators=[DataRequired()])
    reichweite = StringField('Entfernungsklassen (z.B. "5/10/15/25/40")', validators=[DataRequired()])
    tp_mod_entfernung = StringField('TP-Modifikator nach Entfernung (z.B. "+2/+1/0/-1/-3")', validators=[DataRequired()])
    ladezeit_einzeln = IntegerField('Ladezeit (einzeln)', validators=[NumberRange(min=0)], default=1)
    ladezeit_magazin = IntegerField('Ladezeit (Magazin)', validators=[NumberRange(min=0)])
    munition_max = IntegerField('Maximale Munition', validators=[NumberRange(min=0)], default=0)
    submit = SubmitField('Speichern')

class ParryWeaponForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    ini_mod = IntegerField('Initiative-Modifikator', default=0)
    at_mod = IntegerField('Attacke-Modifikator', default=0)
    pa_mod = IntegerField('Parade-Modifikator', default=0)
    submit = SubmitField('Speichern')

# Formulare für das Zuweisen von Waffen zu Charakteren
class AssignWeaponForm(FlaskForm):
    character_id = SelectField('Charakter', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Waffe zuweisen')

class CharacterWeaponForm(FlaskForm):
    munition_aktuell = IntegerField('Aktuelle Munition', validators=[NumberRange(min=0)], default=0)
    equipped = BooleanField('Ausgerüstet')
    submit = SubmitField('Speichern')

# Rüstungsformular
class ArmorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    rs_wert = IntegerField('Rüstungsschutz (RS)', validators=[NumberRange(min=0)], default=0)
    be = IntegerField('Behinderung (BE)', validators=[NumberRange(min=0)], default=0)
    submit = SubmitField('Speichern')

# Formular für die Zuweisung von Rüstungen zu Charakteren
class AssignArmorForm(FlaskForm):
    character_id = SelectField('Charakter', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Rüstung zuweisen')

# Formular für die Bearbeitung der Rüstung eines Charakters
class CharacterArmorForm(FlaskForm):
    equipped = BooleanField('Ausgerüstet')
    submit = SubmitField('Speichern')

# Formular für Inventargegenstände
class InventoryItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Beschreibung')
    submit = SubmitField('Speichern')

# Formular für Geldverwaltung
class MoneyForm(FlaskForm):
    amount = FloatField('Betrag', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Speichern')

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
    
    form = ProbeForm()
    form.talent_id.choices = [(t.id, t.name) for t in talents]
    
    # Neues Formular für Attributproben
    attr_form = AttributProbeForm()
    
    result = None
    details = None
    attr_result = None
    attr_details = None
    probe_type = "talent"  # Standard-Probentyp ist Talentprobe
    
    if not talents:
        flash('Füge zuerst ein Talent für diesen Charakter hinzu!', 'warning')
        # Obwohl keine Talente vorhanden sind, können immer noch Attributproben durchgeführt werden
    
    # Initialisiere mit Standardwerten, wenn keine Würfel gesetzt sind
    if not form.w1.data:
        form.w1.data = 10
    if not form.w2.data:
        form.w2.data = 10
    if not form.w3.data:
        form.w3.data = 10
    if not attr_form.w1.data:
        attr_form.w1.data = 10
    
    # Bestimme welche Art von Probe durchgeführt wird
    if request.method == 'POST':
        probe_type = request.form.get('probe_type', 'talent')
        
        # Speichere das ausgewählte Talent oder Attribut
        if probe_type == 'talent':
            selected_talent = request.form.get('talent_id')
            if selected_talent:
                form.talent_id.data = int(selected_talent)
        
        # Wenn "Würfeln" für Talentprobe geklickt wurde
        if 'wuerfeln' in request.form and probe_type == 'talent':
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
            
            # Flash-Nachricht zur Bestätigung
            flash(f'Gewürfelt: {w1}, {w2}, {w3}', 'info')
            
            # Kein validate_on_submit, sondern direkt das Template rendern
            return render_template('probe.html', 
                                  form=form, 
                                  attr_form=attr_form, 
                                  character=character, 
                                  result=None, 
                                  details=None,
                                  attr_result=None,
                                  attr_details=None,
                                  probe_type=probe_type)
        
        # Wenn "Würfeln" für Attributprobe geklickt wurde
        elif 'attr_wuerfeln' in request.form:
            # Würfelwert generieren
            w1 = random.randint(1, 20)
            
            # Formular-Daten setzen
            attr_form.w1.data = w1
            
            # Flash-Nachricht zur Bestätigung
            flash(f'Gewürfelt: {w1}', 'info')
            
            return render_template('probe.html', 
                                  form=form, 
                                  attr_form=attr_form, 
                                  character=character, 
                                  result=None, 
                                  details=None,
                                  attr_result=None,
                                  attr_details=None,
                                  probe_type='attribut')
    
    # Talentprobe durchführen
    if form.validate_on_submit() and 'submit' in request.form and probe_type == 'talent':
        talent = db.session.get(Talent, form.talent_id.data)
        if talent is None:
            flash('Talent nicht gefunden.', 'error')
            return redirect(url_for('character_talents', character_id=character_id))
        
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
        
        # Erschwernis vom Talentwert abziehen
        erschwernis = form.erschwernis.data or 0
        
        # Effektiver Talentwert berechnen (BE wird vom Talentwert abgezogen)
        effektiver_talentwert = talent.talentwert
        if talent.be_relevant and character.be > 0:
            effektiver_talentwert = max(0, talent.talentwert - be_wert)
        
        # Erschwernis vom effektiven Talentwert abziehen
        effektiver_talentwert = max(0, effektiver_talentwert - erschwernis)
        
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
                'erschwernis': erschwernis,
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
                'erschwernis': erschwernis,
                'is_critical': is_critical
            }
    
    # Attributprobe durchführen
    elif attr_form.validate_on_submit() and 'attr_submit' in request.form:
        # Ausgewähltes Attribut und Wert abrufen
        attribut = attr_form.attribut.data
        attr_value = character.get_attribute(attribut)
        erschwernis = attr_form.erschwernis.data or 0
        
        # Effektiver Attributwert berechnen (mit Erschwernis)
        effektiver_attributwert = max(0, attr_value - erschwernis)
        
        # Würfelwert auswerten
        wuerfel = attr_form.w1.data
        
        # Erfolg/Misserfolg ermitteln
        if wuerfel <= effektiver_attributwert:
            attr_result = True
            # Prüfen auf kritischen Erfolg (1 gewürfelt)
            is_critical = (wuerfel == 1)
        else:
            attr_result = False
            # Prüfen auf kritischen Fehlschlag (20 gewürfelt)
            is_critical = (wuerfel == 20)
        
        # Details zusammenfassen
        attr_details = {
            'attribut': attribut,
            'attribut_name': dict(attr_form.attribut.choices).get(attribut),
            'attr_value': attr_value,
            'effektiver_attributwert': effektiver_attributwert,
            'wuerfel': wuerfel,
            'erschwernis': erschwernis,
            'is_critical': is_critical,
            'diff': wuerfel - effektiver_attributwert if wuerfel > effektiver_attributwert else effektiver_attributwert - wuerfel
        }
        
        probe_type = 'attribut'
    
    return render_template('probe.html', 
                          form=form, 
                          attr_form=attr_form, 
                          character=character, 
                          result=result, 
                          details=details,
                          attr_result=attr_result,
                          attr_details=attr_details,
                          probe_type=probe_type)
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


# Überarbeitete Waffen-Routen für app.py

# Allgemeine Waffendatenbank
@app.route('/weapons')
def all_weapons():
    melee_weapons = MeleeWeapon.query.all()
    ranged_weapons = RangedWeapon.query.all()
    parry_weapons = ParryWeapon.query.all()
    
    return render_template('all_weapons.html',
                           melee_weapons=melee_weapons,
                           ranged_weapons=ranged_weapons,
                           parry_weapons=parry_weapons)

# Charakterspezifische Waffenübersicht
@app.route('/character/<int:character_id>/weapons')
def character_weapons(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    
    # Abfragen durch den Join mit dem Waffentyp
    melee_weapons = (db.session.query(CharacterMeleeWeapon)
                     .filter(CharacterMeleeWeapon.character_id == character_id)
                     .join(MeleeWeapon, CharacterMeleeWeapon.weapon_id == MeleeWeapon.id)
                     .all())
    
    ranged_weapons = (db.session.query(CharacterRangedWeapon)
                      .filter(CharacterRangedWeapon.character_id == character_id)
                      .join(RangedWeapon, CharacterRangedWeapon.weapon_id == RangedWeapon.id)
                      .all())
    
    parry_weapons = (db.session.query(CharacterParryWeapon)
                     .filter(CharacterParryWeapon.character_id == character_id)
                     .join(ParryWeapon, CharacterParryWeapon.weapon_id == ParryWeapon.id)
                     .all())
    
    return render_template('character_weapons.html', 
                           character=character,
                           melee_weapons=melee_weapons,
                           ranged_weapons=ranged_weapons,
                           parry_weapons=parry_weapons)

# Nahkampfwaffen-Verwaltung
@app.route('/weapon/melee/new', methods=['GET', 'POST'])
def new_melee_weapon():
    form = MeleeWeaponForm()
    
    if form.validate_on_submit():
        weapon = MeleeWeapon(
            name=form.name.data,
            be=form.be.data,
            tp=form.tp.data,
            tp_kk_schwelle=form.tp_kk_schwelle.data,
            tp_kk_schritt=form.tp_kk_schritt.data,
            ini_mod=form.ini_mod.data,
            at_mod=form.at_mod.data,
            pa_mod=form.pa_mod.data
        )
        db.session.add(weapon)
        db.session.commit()
        flash(f'Nahkampfwaffe "{weapon.name}" wurde hinzugefügt!', 'success')
        return redirect(url_for('all_weapons'))
    
    return render_template('melee_weapon_form.html', form=form, title='Neue Nahkampfwaffe')

@app.route('/weapon/melee/<int:weapon_id>/edit', methods=['GET', 'POST'])
def edit_melee_weapon(weapon_id):
    weapon = db.session.get(MeleeWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    form = MeleeWeaponForm(obj=weapon)
    if form.validate_on_submit():
        weapon.name = form.name.data
        weapon.be = form.be.data
        weapon.tp = form.tp.data
        weapon.tp_kk_schwelle = form.tp_kk_schwelle.data
        weapon.tp_kk_schritt = form.tp_kk_schritt.data
        weapon.ini_mod = form.ini_mod.data
        weapon.at_mod = form.at_mod.data
        weapon.pa_mod = form.pa_mod.data
        
        db.session.commit()
        flash(f'Nahkampfwaffe "{weapon.name}" wurde aktualisiert!', 'success')
        return redirect(url_for('all_weapons'))
    
    return render_template('melee_weapon_form.html', form=form, title='Nahkampfwaffe bearbeiten')

@app.route('/weapon/melee/<int:weapon_id>/delete')
def delete_melee_weapon(weapon_id):
    weapon = db.session.get(MeleeWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    name = weapon.name
    db.session.delete(weapon)
    db.session.commit()
    flash(f'Nahkampfwaffe "{name}" wurde gelöscht!', 'success')
    return redirect(url_for('all_weapons'))

@app.route('/weapon/melee/<int:weapon_id>/assign', methods=['GET', 'POST'])
def assign_melee_weapon(weapon_id):
    weapon = db.session.get(MeleeWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    assigned_chars = (db.session.query(CharacterMeleeWeapon)
                     .filter(CharacterMeleeWeapon.weapon_id == weapon_id)
                     .join(Character, CharacterMeleeWeapon.character_id == Character.id)
                     .all())
    
    form = AssignWeaponForm()
    # Holen aller Charaktere für das Dropdown
    characters = Character.query.all()
    form.character_id.choices = [(c.id, c.name) for c in characters]
    
    if form.validate_on_submit():
        character_id = form.character_id.data
        
        # Prüfen, ob der Charakter die Waffe bereits hat
        existing = CharacterMeleeWeapon.query.filter_by(
            character_id=character_id, 
            weapon_id=weapon_id
        ).first()
        
        if existing:
            flash(f'Der Charakter hat diese Waffe bereits!', 'warning')
            return redirect(url_for('assign_melee_weapon', weapon_id=weapon_id))
        
        # Neue Verknüpfung erstellen
        equipped = request.form.get('equipped') == 'on'
        char_weapon = CharacterMeleeWeapon(
            character_id=character_id,
            weapon_id=weapon_id,
            equipped=equipped
        )
        
        db.session.add(char_weapon)
        db.session.commit()
        
        character = db.session.get(Character, character_id)
        flash(f'Nahkampfwaffe "{weapon.name}" wurde {character.name} zugewiesen!', 'success')
        
        return redirect(url_for('character_weapons', character_id=character_id))
    
    return render_template('assign_weapon.html', 
                          form=form, 
                          weapon=weapon, 
                          weapon_type='melee',
                          assigned_chars=assigned_chars)

@app.route('/character_weapon/melee/<int:link_id>/toggle-equip')
def toggle_equip_melee(link_id):
    char_weapon = db.session.get(CharacterMeleeWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    char_weapon.equipped = not char_weapon.equipped
    db.session.commit()
    
    weapon = db.session.get(MeleeWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, char_weapon.character_id)
    
    if char_weapon.equipped:
        flash(f'"{weapon.name}" wurde von {character.name} ausgerüstet!', 'success')
    else:
        flash(f'"{weapon.name}" wurde von {character.name} abgelegt!', 'success')
    
    return redirect(url_for('character_weapons', character_id=char_weapon.character_id))

@app.route('/character_weapon/melee/<int:link_id>/edit', methods=['GET', 'POST'])
def edit_character_melee_weapon(link_id):
    char_weapon = db.session.get(CharacterMeleeWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    weapon = db.session.get(MeleeWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, char_weapon.character_id)
    
    form = CharacterWeaponForm(obj=char_weapon)
    
    if form.validate_on_submit():
        char_weapon.equipped = form.equipped.data
        
        db.session.commit()
        flash(f'Einstellungen für "{weapon.name}" wurden aktualisiert!', 'success')
        return redirect(url_for('character_weapons', character_id=character.id))
    
    return render_template('character_weapon_form.html',
                          form=form,
                          weapon=weapon, 
                          character=character,
                          is_melee=True,
                          is_ranged=False,
                          is_parry=False,
                          title='Nahkampfwaffe bearbeiten')

@app.route('/character_weapon/melee/<int:link_id>/remove')
def remove_character_melee_weapon(link_id):
    char_weapon = db.session.get(CharacterMeleeWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    character_id = char_weapon.character_id
    weapon = db.session.get(MeleeWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, character_id)
    
    db.session.delete(char_weapon)
    db.session.commit()
    
    flash(f'"{weapon.name}" wurde von {character.name} entfernt!', 'success')
    return redirect(url_for('character_weapons', character_id=character_id))

# Fernkampfwaffen-Verwaltung
@app.route('/weapon/ranged/new', methods=['GET', 'POST'])
def new_ranged_weapon():
    form = RangedWeaponForm()
    
    if form.validate_on_submit():
        weapon = RangedWeapon(
            name=form.name.data,
            be=form.be.data,
            tp=form.tp.data,
            reichweite=form.reichweite.data,
            tp_mod_entfernung=form.tp_mod_entfernung.data,
            ladezeit_einzeln=form.ladezeit_einzeln.data,
            ladezeit_magazin=form.ladezeit_magazin.data if form.ladezeit_magazin.data else None,
            munition_max=form.munition_max.data
        )
        db.session.add(weapon)
        db.session.commit()
        flash(f'Fernkampfwaffe "{weapon.name}" wurde hinzugefügt!', 'success')
        return redirect(url_for('all_weapons'))
    
    return render_template('ranged_weapon_form.html', form=form, title='Neue Fernkampfwaffe')

@app.route('/weapon/ranged/<int:weapon_id>/edit', methods=['GET', 'POST'])
def edit_ranged_weapon(weapon_id):
    weapon = db.session.get(RangedWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    form = RangedWeaponForm(obj=weapon)
    if form.validate_on_submit():
        weapon.name = form.name.data
        weapon.be = form.be.data
        weapon.tp = form.tp.data
        weapon.reichweite = form.reichweite.data
        weapon.tp_mod_entfernung = form.tp_mod_entfernung.data
        weapon.ladezeit_einzeln = form.ladezeit_einzeln.data
        weapon.ladezeit_magazin = form.ladezeit_magazin.data if form.ladezeit_magazin.data else None
        weapon.munition_max = form.munition_max.data
        
        db.session.commit()
        flash(f'Fernkampfwaffe "{weapon.name}" wurde aktualisiert!', 'success')
        return redirect(url_for('all_weapons'))
    
    return render_template('ranged_weapon_form.html', form=form, title='Fernkampfwaffe bearbeiten')

@app.route('/weapon/ranged/<int:weapon_id>/delete')
def delete_ranged_weapon(weapon_id):
    weapon = db.session.get(RangedWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    name = weapon.name
    db.session.delete(weapon)
    db.session.commit()
    flash(f'Fernkampfwaffe "{name}" wurde gelöscht!', 'success')
    return redirect(url_for('all_weapons'))

@app.route('/weapon/ranged/<int:weapon_id>/assign', methods=['GET', 'POST'])
def assign_ranged_weapon(weapon_id):
    weapon = db.session.get(RangedWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    assigned_chars = (db.session.query(CharacterRangedWeapon)
                     .filter(CharacterRangedWeapon.weapon_id == weapon_id)
                     .join(Character, CharacterRangedWeapon.character_id == Character.id)
                     .all())
    
    form = AssignWeaponForm()
    # Holen aller Charaktere für das Dropdown
    characters = Character.query.all()
    form.character_id.choices = [(c.id, c.name) for c in characters]
    
    if form.validate_on_submit():
        character_id = form.character_id.data
        
        # Prüfen, ob der Charakter die Waffe bereits hat
        existing = CharacterRangedWeapon.query.filter_by(
            character_id=character_id, 
            weapon_id=weapon_id
        ).first()
        
        if existing:
            flash(f'Der Charakter hat diese Waffe bereits!', 'warning')
            return redirect(url_for('assign_ranged_weapon', weapon_id=weapon_id))
        
        # Neue Verknüpfung erstellen
        equipped = request.form.get('equipped') == 'on'
        munition_aktuell = request.form.get('munition_aktuell', type=int) or 0
        
        char_weapon = CharacterRangedWeapon(
            character_id=character_id,
            weapon_id=weapon_id,
            munition_aktuell=munition_aktuell,
            equipped=equipped
        )
        
        db.session.add(char_weapon)
        db.session.commit()
        
        character = db.session.get(Character, character_id)
        flash(f'Fernkampfwaffe "{weapon.name}" wurde {character.name} zugewiesen!', 'success')
        
        return redirect(url_for('character_weapons', character_id=character_id))
    
    return render_template('assign_weapon.html', 
                          form=form, 
                          weapon=weapon, 
                          weapon_type='ranged',
                          assigned_chars=assigned_chars)

@app.route('/character_weapon/ranged/<int:link_id>/toggle-equip')
def toggle_equip_ranged(link_id):
    char_weapon = db.session.get(CharacterRangedWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    char_weapon.equipped = not char_weapon.equipped
    db.session.commit()
    
    weapon = db.session.get(RangedWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, char_weapon.character_id)
    
    if char_weapon.equipped:
        flash(f'"{weapon.name}" wurde von {character.name} ausgerüstet!', 'success')
    else:
        flash(f'"{weapon.name}" wurde von {character.name} abgelegt!', 'success')
    
    return redirect(url_for('character_weapons', character_id=char_weapon.character_id))

@app.route('/character_weapon/ranged/<int:link_id>/edit', methods=['GET', 'POST'])
def edit_character_ranged_weapon(link_id):
    char_weapon = db.session.get(CharacterRangedWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    weapon = db.session.get(RangedWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, char_weapon.character_id)
    
    form = CharacterWeaponForm(obj=char_weapon)
    
    if form.validate_on_submit():
        char_weapon.munition_aktuell = form.munition_aktuell.data
        char_weapon.equipped = form.equipped.data
        
        db.session.commit()
        flash(f'Einstellungen für "{weapon.name}" wurden aktualisiert!', 'success')
        return redirect(url_for('character_weapons', character_id=character.id))
    
    return render_template('character_weapon_form.html',
                          form=form,
                          weapon=weapon, 
                          character=character,
                          is_melee=False,
                          is_ranged=True,
                          is_parry=False,
                          title='Fernkampfwaffe bearbeiten')

@app.route('/character_weapon/ranged/<int:link_id>/remove')
def remove_character_ranged_weapon(link_id):
    char_weapon = db.session.get(CharacterRangedWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    character_id = char_weapon.character_id
    weapon = db.session.get(RangedWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, character_id)
    
    db.session.delete(char_weapon)
    db.session.commit()
    
    flash(f'"{weapon.name}" wurde von {character.name} entfernt!', 'success')
    return redirect(url_for('character_weapons', character_id=character_id))

# Parierwaffen-Verwaltung
@app.route('/weapon/parry/new', methods=['GET', 'POST'])
def new_parry_weapon():
    form = ParryWeaponForm()
    
    if form.validate_on_submit():
        weapon = ParryWeapon(
            name=form.name.data,
            ini_mod=form.ini_mod.data,
            at_mod=form.at_mod.data,
            pa_mod=form.pa_mod.data
        )
        db.session.add(weapon)
        db.session.commit()
        flash(f'Parierwaffe "{weapon.name}" wurde hinzugefügt!', 'success')
        return redirect(url_for('all_weapons'))
    
    return render_template('parry_weapon_form.html', form=form, title='Neue Parierwaffe')

@app.route('/weapon/parry/<int:weapon_id>/edit', methods=['GET', 'POST'])
def edit_parry_weapon(weapon_id):
    weapon = db.session.get(ParryWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    form = ParryWeaponForm(obj=weapon)
    if form.validate_on_submit():
        weapon.name = form.name.data
        weapon.ini_mod = form.ini_mod.data
        weapon.at_mod = form.at_mod.data
        weapon.pa_mod = form.pa_mod.data
        
        db.session.commit()
        flash(f'Parierwaffe "{weapon.name}" wurde aktualisiert!', 'success')
        return redirect(url_for('all_weapons'))
    
    return render_template('parry_weapon_form.html', form=form, title='Parierwaffe bearbeiten')

@app.route('/weapon/parry/<int:weapon_id>/delete')
def delete_parry_weapon(weapon_id):
    weapon = db.session.get(ParryWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    name = weapon.name
    db.session.delete(weapon)
    db.session.commit()
    flash(f'Parierwaffe "{name}" wurde gelöscht!', 'success')
    return redirect(url_for('all_weapons'))

@app.route('/weapon/parry/<int:weapon_id>/assign', methods=['GET', 'POST'])
def assign_parry_weapon(weapon_id):
    weapon = db.session.get(ParryWeapon, weapon_id)
    if weapon is None:
        abort(404)
    
    assigned_chars = (db.session.query(CharacterParryWeapon)
                     .filter(CharacterParryWeapon.weapon_id == weapon_id)
                     .join(Character, CharacterParryWeapon.character_id == Character.id)
                     .all())
    
    form = AssignWeaponForm()
    # Holen aller Charaktere für das Dropdown
    characters = Character.query.all()
    form.character_id.choices = [(c.id, c.name) for c in characters]
    
    if form.validate_on_submit():
        character_id = form.character_id.data
        
        # Prüfen, ob der Charakter die Waffe bereits hat
        existing = CharacterParryWeapon.query.filter_by(
            character_id=character_id, 
            weapon_id=weapon_id
        ).first()
        
        if existing:
            flash(f'Der Charakter hat diese Waffe bereits!', 'warning')
            return redirect(url_for('assign_parry_weapon', weapon_id=weapon_id))
        
        # Neue Verknüpfung erstellen
        equipped = request.form.get('equipped') == 'on'
        char_weapon = CharacterParryWeapon(
            character_id=character_id,
            weapon_id=weapon_id,
            equipped=equipped
        )
        
        db.session.add(char_weapon)
        db.session.commit()
        
        character = db.session.get(Character, character_id)
        flash(f'Parierwaffe "{weapon.name}" wurde {character.name} zugewiesen!', 'success')
        
        return redirect(url_for('character_weapons', character_id=character_id))
    
    return render_template('assign_weapon.html', 
                          form=form, 
                          weapon=weapon, 
                          weapon_type='parry',
                          assigned_chars=assigned_chars)

@app.route('/character_weapon/parry/<int:link_id>/toggle-equip')
def toggle_equip_parry(link_id):
    char_weapon = db.session.get(CharacterParryWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    char_weapon.equipped = not char_weapon.equipped
    db.session.commit()
    
    weapon = db.session.get(ParryWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, char_weapon.character_id)
    
    if char_weapon.equipped:
        flash(f'"{weapon.name}" wurde von {character.name} ausgerüstet!', 'success')
    else:
        flash(f'"{weapon.name}" wurde von {character.name} abgelegt!', 'success')
    
    return redirect(url_for('character_weapons', character_id=char_weapon.character_id))

@app.route('/character_weapon/parry/<int:link_id>/edit', methods=['GET', 'POST'])
def edit_character_parry_weapon(link_id):
    char_weapon = db.session.get(CharacterParryWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    weapon = db.session.get(ParryWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, char_weapon.character_id)
    
    form = CharacterWeaponForm(obj=char_weapon)
    
    if form.validate_on_submit():
        char_weapon.equipped = form.equipped.data
        
        db.session.commit()
        flash(f'Einstellungen für "{weapon.name}" wurden aktualisiert!', 'success')
        return redirect(url_for('character_weapons', character_id=character.id))
    
    return render_template('character_weapon_form.html',
                          form=form,
                          weapon=weapon, 
                          character=character,
                          is_melee=False,
                          is_ranged=False,
                          is_parry=True,
                          title='Parierwaffe bearbeiten')

@app.route('/character_weapon/parry/<int:link_id>/remove')
def remove_character_parry_weapon(link_id):
    char_weapon = db.session.get(CharacterParryWeapon, link_id)
    if char_weapon is None:
        abort(404)
    
    character_id = char_weapon.character_id
    weapon = db.session.get(ParryWeapon, char_weapon.weapon_id)
    character = db.session.get(Character, character_id)
    
    db.session.delete(char_weapon)
    db.session.commit()
    
    flash(f'"{weapon.name}" wurde von {character.name} entfernt!', 'success')
    return redirect(url_for('character_weapons', character_id=character_id))

# Alle Rüstungen anzeigen
@app.route('/armors')
def all_armors():
    armors = Armor.query.all()
    return render_template('all_armors.html', armors=armors)

# Neue Rüstung erstellen
@app.route('/armor/new', methods=['GET', 'POST'])
def new_armor():
    form = ArmorForm()
    
    if form.validate_on_submit():
        armor = Armor(
            name=form.name.data,
            rs_wert=form.rs_wert.data,
            be=form.be.data
        )
        db.session.add(armor)
        db.session.commit()
        flash(f'Rüstung "{armor.name}" wurde hinzugefügt!', 'success')
        return redirect(url_for('all_armors'))
    
    return render_template('armor_form.html', form=form, title='Neue Rüstung')

# Rüstung bearbeiten
@app.route('/armor/<int:armor_id>/edit', methods=['GET', 'POST'])
def edit_armor(armor_id):
    armor = db.session.get(Armor, armor_id)
    if armor is None:
        abort(404)
    
    form = ArmorForm(obj=armor)
    if form.validate_on_submit():
        armor.name = form.name.data
        armor.rs_wert = form.rs_wert.data
        armor.be = form.be.data
        
        db.session.commit()
        flash(f'Rüstung "{armor.name}" wurde aktualisiert!', 'success')
        return redirect(url_for('all_armors'))
    
    return render_template('armor_form.html', form=form, title='Rüstung bearbeiten')

# Rüstung löschen
@app.route('/armor/<int:armor_id>/delete')
def delete_armor(armor_id):
    armor = db.session.get(Armor, armor_id)
    if armor is None:
        abort(404)
    
    name = armor.name
    db.session.delete(armor)
    db.session.commit()
    flash(f'Rüstung "{name}" wurde gelöscht!', 'success')
    return redirect(url_for('all_armors'))

# Rüstung einem Charakter zuweisen
@app.route('/armor/<int:armor_id>/assign', methods=['GET', 'POST'])
def assign_armor(armor_id):
    armor = db.session.get(Armor, armor_id)
    if armor is None:
        abort(404)
    
    assigned_chars = (db.session.query(CharacterArmor)
                    .filter(CharacterArmor.armor_id == armor_id)
                    .join(Character, CharacterArmor.character_id == Character.id)
                    .all())
    
    form = AssignArmorForm()
    # Alle Charaktere für das Dropdown holen
    characters = Character.query.all()
    form.character_id.choices = [(c.id, c.name) for c in characters]
    
    if form.validate_on_submit():
        character_id = form.character_id.data
        
        # Prüfen, ob der Charakter die Rüstung bereits hat
        existing = CharacterArmor.query.filter_by(
            character_id=character_id, 
            armor_id=armor_id
        ).first()
        
        if existing:
            flash(f'Der Charakter hat diese Rüstung bereits!', 'warning')
            return redirect(url_for('assign_armor', armor_id=armor_id))
        
        # Neue Verknüpfung erstellen
        equipped = request.form.get('equipped') == 'on'
        char_armor = CharacterArmor(
            character_id=character_id,
            armor_id=armor_id,
            equipped=equipped
        )
        
        # Wenn ausgerüstet, andere Rüstungen ablegen
        if equipped:
            other_armors = CharacterArmor.query.filter(
                CharacterArmor.character_id == character_id,
                CharacterArmor.equipped == True
            ).all()
            for other in other_armors:
                other.equipped = False
            
            # Character RS und BE aktualisieren
            character = db.session.get(Character, character_id)
            character.rs_wert = armor.rs_wert
            character.be = armor.be
        
        db.session.add(char_armor)
        db.session.commit()
        
        character = db.session.get(Character, character_id)
        flash(f'Rüstung "{armor.name}" wurde {character.name} zugewiesen!', 'success')
        
        return redirect(url_for('character_inventory', character_id=character_id))
    
    return render_template('assign_armor.html', 
                        form=form, 
                        armor=armor,
                        assigned_chars=assigned_chars)

# Rüstung an-/ablegen
@app.route('/character_armor/<int:link_id>/toggle-equip')
def toggle_equip_armor(link_id):
    char_armor = db.session.get(CharacterArmor, link_id)
    if char_armor is None:
        abort(404)
    
    # Wenn Rüstung angelegt werden soll, alle anderen Rüstungen ablegen
    if not char_armor.equipped:
        other_armors = CharacterArmor.query.filter(
            CharacterArmor.character_id == char_armor.character_id,
            CharacterArmor.id != char_armor.id,
            CharacterArmor.equipped == True
        ).all()
        for other in other_armors:
            other.equipped = False
    
    char_armor.equipped = not char_armor.equipped
    
    armor = db.session.get(Armor, char_armor.armor_id)
    character = db.session.get(Character, char_armor.character_id)
    
    if char_armor.equipped:
        # Character RS und BE aktualisieren
        character.rs_wert = armor.rs_wert
        character.be = armor.be
        db.session.commit()
        flash(f'"{armor.name}" wurde von {character.name} angelegt! RS und BE wurden aktualisiert.', 'success')
    else:
        # Character RS und BE zurücksetzen
        character.rs_wert = 0
        character.be = 0
        db.session.commit()
        flash(f'"{armor.name}" wurde von {character.name} abgelegt! RS und BE wurden zurückgesetzt.', 'success')
    
    return redirect(url_for('character_inventory', character_id=char_armor.character_id))

# Character Inventar anzeigen
@app.route('/character/<int:character_id>/inventory')
def character_inventory(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    
    # Inventar abrufen oder erstellen falls nicht vorhanden
    inventory = db.session.query(Inventory).filter_by(character_id=character_id).first()
    if inventory is None:
        inventory = Inventory(character_id=character_id)
        db.session.add(inventory)
        db.session.commit()
    
    # Waffen abrufen
    melee_weapons = (db.session.query(CharacterMeleeWeapon)
                    .filter(CharacterMeleeWeapon.character_id == character_id)
                    .join(MeleeWeapon, CharacterMeleeWeapon.weapon_id == MeleeWeapon.id)
                    .all())
    
    ranged_weapons = (db.session.query(CharacterRangedWeapon)
                    .filter(CharacterRangedWeapon.character_id == character_id)
                    .join(RangedWeapon, CharacterRangedWeapon.weapon_id == RangedWeapon.id)
                    .all())
    
    parry_weapons = (db.session.query(CharacterParryWeapon)
                    .filter(CharacterParryWeapon.character_id == character_id)
                    .join(ParryWeapon, CharacterParryWeapon.weapon_id == ParryWeapon.id)
                    .all())
    
    # Rüstungen abrufen
    armors = (db.session.query(CharacterArmor)
            .filter(CharacterArmor.character_id == character_id)
            .join(Armor, CharacterArmor.armor_id == Armor.id)
            .all())
    
    # Allgemeine Gegenstände abrufen
    general_items = inventory.general_items
    
    return render_template('character_inventory.html', 
                        character=character,
                        inventory=inventory,
                        melee_weapons=melee_weapons,
                        ranged_weapons=ranged_weapons,
                        parry_weapons=parry_weapons,
                        armors=armors,
                        general_items=general_items)

# Gegenstand zum Inventar hinzufügen
@app.route('/character/<int:character_id>/inventory/add_item', methods=['GET', 'POST'])
def add_inventory_item(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    
    # Inventar abrufen oder erstellen
    inventory = db.session.query(Inventory).filter_by(character_id=character_id).first()
    if inventory is None:
        inventory = Inventory(character_id=character_id)
        db.session.add(inventory)
        db.session.commit()
    
    form = InventoryItemForm()
    
    if form.validate_on_submit():
        item = InventoryItem(
            name=form.name.data,
            description=form.description.data,
            inventory_id=inventory.id
        )
        db.session.add(item)
        db.session.commit()
        flash(f'Gegenstand "{item.name}" wurde zum Inventar hinzugefügt!', 'success')
        return redirect(url_for('character_inventory', character_id=character_id))
    
    return render_template('inventory_item_form.html',
                        form=form,
                        character=character,
                        title='Gegenstand hinzufügen')

# Inventargegenstand bearbeiten
@app.route('/inventory_item/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_inventory_item(item_id):
    item = db.session.get(InventoryItem, item_id)
    if item is None:
        abort(404)
    
    inventory = db.session.get(Inventory, item.inventory_id)
    character = db.session.get(Character, inventory.character_id)
    
    form = InventoryItemForm(obj=item)
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.description = form.description.data
        
        db.session.commit()
        flash(f'Gegenstand "{item.name}" wurde aktualisiert!', 'success')
        return redirect(url_for('character_inventory', character_id=character.id))
    
    return render_template('inventory_item_form.html',
                        form=form,
                        character=character,
                        title='Gegenstand bearbeiten')

# Inventargegenstand löschen
@app.route('/inventory_item/<int:item_id>/delete')
def delete_inventory_item(item_id):
    item = db.session.get(InventoryItem, item_id)
    if item is None:
        abort(404)
    
    inventory = db.session.get(Inventory, item.inventory_id)
    character_id = inventory.character_id
    
    name = item.name
    db.session.delete(item)
    db.session.commit()
    
    flash(f'Gegenstand "{name}" wurde aus dem Inventar entfernt!', 'success')
    return redirect(url_for('character_inventory', character_id=character_id))

# Geld zum Inventar hinzufügen
@app.route('/character/<int:character_id>/inventory/add_money', methods=['GET', 'POST'])
def add_money(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    
    # Inventar abrufen oder erstellen
    inventory = db.session.query(Inventory).filter_by(character_id=character_id).first()
    if inventory is None:
        inventory = Inventory(character_id=character_id)
        db.session.add(inventory)
        db.session.commit()
    
    form = MoneyForm()
    
    if form.validate_on_submit():
        amount = form.amount.data
        inventory.money += amount
        db.session.commit()
        flash(f'{amount} Münzen wurden zum Inventar hinzugefügt!', 'success')
        return redirect(url_for('character_inventory', character_id=character_id))
    
    return render_template('money_form.html',
                        form=form,
                        character=character,
                        inventory=inventory,
                        title='Geld hinzufügen',
                        action_type='add')

# Geld vom Inventar abziehen
@app.route('/character/<int:character_id>/inventory/remove_money', methods=['GET', 'POST'])
def remove_money(character_id):
    character = db.session.get(Character, character_id)
    if character is None:
        abort(404)
    
    # Inventar abrufen oder erstellen
    inventory = db.session.query(Inventory).filter_by(character_id=character_id).first()
    if inventory is None:
        inventory = Inventory(character_id=character_id)
        db.session.add(inventory)
        db.session.commit()
    
    form = MoneyForm()
    
    if form.validate_on_submit():
        amount = form.amount.data
        if amount > inventory.money:
            flash(f'Nicht genug Geld vorhanden! (Verfügbar: {inventory.money})', 'danger')
        else:
            inventory.money -= amount
            db.session.commit()
            flash(f'{amount} Münzen wurden vom Inventar abgezogen!', 'success')
            return redirect(url_for('character_inventory', character_id=character_id))
    
    return render_template('money_form.html',
                        form=form,
                        character=character,
                        inventory=inventory,
                        title='Geld abziehen',
                        action_type='remove')

@app.route('/character_armor/<int:link_id>/edit', methods=['GET', 'POST'])
def edit_character_armor(link_id):
    char_armor = db.session.get(CharacterArmor, link_id)
    if char_armor is None:
        abort(404)
    
    armor = db.session.get(Armor, char_armor.armor_id)
    character = db.session.get(Character, char_armor.character_id)
    
    form = CharacterArmorForm(obj=char_armor)
    
    if form.validate_on_submit():
        was_equipped = char_armor.equipped
        char_armor.equipped = form.equipped.data
        
        # Wenn ausgerüstet wird, andere Rüstungen ablegen
        if not was_equipped and char_armor.equipped:
            other_armors = CharacterArmor.query.filter(
                CharacterArmor.character_id == char_armor.character_id,
                CharacterArmor.id != char_armor.id,
                CharacterArmor.equipped == True
            ).all()
            for other in other_armors:
                other.equipped = False
        
        # Character RS und BE aktualisieren
        if not was_equipped and char_armor.equipped:
            # Rüstung wurde neu angelegt
            character.rs_wert = armor.rs_wert
            character.be = armor.be
            flash(f'"{armor.name}" wurde angelegt und RS/BE aktualisiert.', 'success')
        elif was_equipped and not char_armor.equipped:
            # Rüstung wurde abgelegt
            character.rs_wert = 0
            character.be = 0
            flash(f'"{armor.name}" wurde abgelegt und RS/BE zurückgesetzt.', 'success')
        else:
            flash(f'Einstellungen für "{armor.name}" wurden aktualisiert!', 'success')
        
        db.session.commit()
        return redirect(url_for('character_inventory', character_id=character.id))
    
    return render_template('character_armor_form.html',
                          form=form,
                          armor=armor, 
                          character=character,
                          title='Rüstung bearbeiten')

@app.route('/character_armor/<int:link_id>/remove')
def remove_character_armor(link_id):
    char_armor = db.session.get(CharacterArmor, link_id)
    if char_armor is None:
        abort(404)
    
    character_id = char_armor.character_id
    armor = db.session.get(Armor, char_armor.armor_id)
    character = db.session.get(Character, character_id)
    
    # Wenn die Rüstung angelegt war, RS und BE zurücksetzen
    if char_armor.equipped:
        character.rs_wert = 0
        character.be = 0
    
    db.session.delete(char_armor)
    db.session.commit()
    
    flash(f'"{armor.name}" wurde von {character.name} entfernt!', 'success')
    return redirect(url_for('character_inventory', character_id=character_id))


@app.route('/init_db')
def init_db():
    db.create_all()
    flash('Datenbank initialisiert!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Erstellt die Datenbank automatisch beim Start
    app.run(debug=True)