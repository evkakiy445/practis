from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from wtforms import StringField, IntegerField, FloatField, DateField, SelectField, SelectMultipleField, SubmitField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
import datetime
from models import db, City, Tours, Excursions, Flights, Airline, Hotel, Room, TourImages # импорт моделей и db
from sqlalchemy import text
import os
from werkzeug.utils import secure_filename
import uuid
from flask import current_app
import logging
from flask import flash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/travel_agency'
app.config['SECRET_KEY'] = 'secret'
db.init_app(app) 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === ФОРМЫ ===

class TourForm(FlaskForm):
    name = StringField('Название тура', validators=[DataRequired()])
    city = SelectField('Город', coerce=int, validators=[DataRequired()])
    new_city = StringField('Новый город')
    duration = IntegerField('Продолжительность (дней)', validators=[DataRequired()])
    date = DateField('Дата начала', default=datetime.date.today)
    price = FloatField('Цена', validators=[DataRequired()])

    excursions = SelectMultipleField('Экскурсии', coerce=int, choices=[])
    hotels = SelectMultipleField('Отели', coerce=int, choices=[])
    rooms = SelectField('Комната', coerce=int, choices=[], validate_choice=False)
    airline = SelectField('Авиакомпания', coerce=int, choices=[], validate_choice=False)
    flights = SelectMultipleField('Авиабилеты', coerce=int, choices=[], validate_choice=False)

    submit = SubmitField('Создать тур')


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/create_tour', methods=['GET', 'POST'])
def create_tour():
    form = TourForm()
    cities = City.query.all()
    form.city.choices = [(c.CityID, c.Name) for c in cities]
    selected_city = None

    # Загрузка данных для SelectField и прочего
    airlines = Airline.query.all()
    if airlines:
        form.airline.choices = [(a.AirlineID, a.Name) for a in airlines]
        if not form.airline.data:
            form.airline.data = airlines[0].AirlineID
    else:
        form.airline.choices = []

    selected_city_id = form.city.data or (cities[0].CityID if cities else None)
    if form.new_city.data:
        selected_city_id = None

    if selected_city_id:
        form.excursions.choices = [(e.ExcursionID, e.Name) for e in Excursions.query.filter_by(CityID=selected_city_id).all()]
        form.hotels.choices = [(h.HotelID, h.Name) for h in Hotel.query.filter_by(CityID=selected_city_id).all()]
    else:
        form.excursions.choices = []
        form.hotels.choices = []

    if form.airline.data:
        flights = Flights.query.filter_by(AirlineID=form.airline.data).all()
        form.flights.choices = [(f.FlightID, f.Name) for f in flights]
    else:
        form.flights.choices = []

    if request.method == 'POST' and form.validate():
        try:
            # Добавляем новый город, если введён
            if form.new_city.data:
                new_city = City(Name=form.new_city.data)
                db.session.add(new_city)
                db.session.commit()
                city_id = new_city.CityID
            else:
                city_id = form.city.data

            # Создаём объект тура с основными полями
            new_tour = Tours(
                Name=form.name.data,
                CityID=city_id,
                Duration=form.duration.data,
                Date=form.date.data,
                Price=form.price.data,
                AirlineID=form.airline.data if form.airline.data else None,
                FlightID=form.flights.data if form.flights.data else None,
                HotelID=form.hotels.data[0] if form.hotels.data else None,
                RoomID=form.rooms.data if form.rooms.data else None
            )
            db.session.add(new_tour)
            db.session.commit()  # Сохраняем тур, чтобы получить TourID

            # Связываем тур с экскурсиями (many-to-many)
            if form.excursions.data:
                for exc_id in form.excursions.data:
                    excursion = Excursions.query.get(exc_id)
                    if excursion:
                        db.session.execute(
                            text("INSERT INTO tours_excursions (tour_id, excursion_id) VALUES (:tour_id, :exc_id)"),
                            {'tour_id': new_tour.TourID, 'exc_id': excursion.ExcursionID}
                        )

            files = request.files.getlist('tour_images')
            upload_folder = os.path.join(current_app.root_path, 'static/uploads/tours')
            os.makedirs(upload_folder, exist_ok=True)

            for file in files:
                if file and allowed_file(file.filename):
                    original_filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
                    filepath = os.path.join(upload_folder, unique_filename)
                    file.save(filepath)

                    img = TourImages(TourID=new_tour.TourID, filename=unique_filename)
                    db.session.add(img)

            db.session.commit()

            flash('Тур успешно создан!', 'success')
            return redirect(url_for('create_tour'))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при создании тура: {e}", exc_info=True)
            flash(f'Ошибка при создании тура: {str(e)}', 'danger')

    return render_template('create_tour.html', form=form, datetime=datetime, airlines=airlines, selected_city=selected_city, cities=cities)



@app.route('/get_city_options/<int:city_id>')
def get_city_options(city_id):
    excursions = [{'id': e.ExcursionID, 'name': e.Name} for e in Excursions.query.filter_by(CityID=city_id).all()]
    hotels = [{'id': h.HotelID, 'name': h.Name} for h in Hotel.query.filter_by(CityID=city_id).all()]
    flights = [{'id': f.FlightID, 'name': f.Name} for f in Flights.query.filter_by(FromCity=city_id).all()]
    return jsonify({'excursions': excursions, 'hotels': hotels, 'flights': flights})

@app.route('/get_rooms/<int:hotel_id>')
def get_rooms(hotel_id):
    rooms = Room.query.filter_by(HotelID=hotel_id).all()
    room_data = [{'id': r.RoomID, 'name': r.Name, 'type': r.Type, 'price': r.Price} for r in rooms]
    return jsonify({'rooms': room_data})

@app.route('/get_excursion_info/<int:excursion_id>')
def get_excursion_info(excursion_id):
    e = Excursions.query.get(excursion_id)
    if e:
        return jsonify({
            'name': e.Name,
            'guide': e.Guide,
            'route': e.Route,
            'date': e.Date.strftime('%Y-%m-%d'),
            'price': e.Price
        })
    return jsonify({'error': 'Экскурсия не найдена'}), 404

@app.route('/create_excursion_ajax', methods=['POST'])
def create_excursion_ajax():
    city_id = request.form.get('city_id')
    if not city_id:
        return jsonify(success=False, error='Город не выбран')

    name = request.form.get('name')
    if not name:
        return jsonify(success=False, error='Название экскурсии обязательно')

    guide = request.form.get('guide')
    route = request.form.get('route')
    date_str = request.form.get('date')
    price_str = request.form.get('price')

    try:
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
    except:
        date = None

    try:
        price = float(price_str) if price_str else None
    except:
        price = None

    new_excursion = Excursions(
        Name=name,
        Guide=guide,
        Route=route,
        Date=date,
        Price=price,
        CityID=int(city_id)
    )
    db.session.add(new_excursion)
    db.session.commit()

    return jsonify(success=True, excursion={
        'id': new_excursion.ExcursionID,
        'name': new_excursion.Name
    })

@app.route('/get_flights_by_airline/<int:airline_id>')
def get_flights_by_airline(airline_id):
    city_id = request.args.get('city_id', type=int)
    date_str = request.args.get('date')
    
    query = Flights.query.filter_by(AirlineID=airline_id)
    
    if city_id:
        query = query.filter_by(ToCity=city_id)

    if date_str:
        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            query = query.filter(Flights.Date == date)
        except ValueError:
            pass  # игнорируем неправильную дату

    flights = query.all()
    return jsonify([{'id': f.FlightID, 'name': f.Name} for f in flights])


@app.route('/create_city_ajax', methods=['POST'])
def create_city_ajax():
    name = request.form.get('name')
    if name:
        city = City(Name=name)
        db.session.add(city)
        db.session.commit()
        return jsonify({'id': city.CityID, 'name': city.Name})
    return jsonify({'error': 'Missing name'}), 400

@app.route('/get_flight_info/<int:flight_id>')
def get_flight_info(flight_id):
    flight = Flights.query.get(flight_id)
    if not flight:
        return jsonify({'error': 'Авиабилет не найден'})

    return jsonify({
        'id': flight.FlightID,
        'name': flight.Name,
        'airline': flight.airline.Name if flight.airline else 'Не указано',
        'from_city': flight.from_city.Name if flight.from_city else 'Не указано',
        'to_city': flight.to_city.Name if flight.to_city else 'Не указано',
        'date': flight.Date.strftime('%d.%m.%Y') if flight.Date else '—',
        'departure_time': flight.DepartureTime.strftime('%H:%M') if flight.DepartureTime else '—',
        'arrival_time': flight.ArrivalTime.strftime('%H:%M') if flight.ArrivalTime else '—',
        'price': str(flight.TicketPrice) + ' руб.'
    })

@app.route('/create_hotel_modal', methods=['POST'])
def create_hotel_modal():
    name = request.form.get('name')
    stars = request.form.get('stars')
    city_id = request.form.get('city_id')

    if not (name and stars and city_id):
        return jsonify(success=False, error="Все поля обязательны."), 400

    try:
        new_hotel = Hotel(Name=name, Stars=int(stars), CityID=int(city_id))
        db.session.add(new_hotel)
        db.session.commit()
        return jsonify(success=True, hotel={"id": new_hotel.HotelID, "name": new_hotel.Name})
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500


@app.route('/create_room', methods=['POST'])
def create_room():
    hotel_id = request.form.get('hotel_id')
    name = request.form.get('name')
    room_type = request.form.get('type')
    price = request.form.get('price')

    if not hotel_id or not name or not room_type or not price:
        return jsonify(success=False, error='Все поля обязательны'), 400

    try:
        price = float(price)
        hotel_id = int(hotel_id)
    except ValueError:
        return jsonify(success=False, error='Некорректные данные'), 400

    new_room = Room(
        HotelID=hotel_id,
        Name=name,
        Type=room_type,
        Price=price
    )

    try:
        db.session.add(new_room)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error='Ошибка сохранения в базу: ' + str(e)), 500

    return jsonify(success=True, room={
        'id': new_room.RoomID,
        'name': new_room.Name,
        'type': new_room.Type,
        'price': new_room.Price
    })

@app.route('/create_airline', methods=['POST'])
def create_airline():
    name = request.form.get('name')
    country = request.form.get('country')
    iata_code = request.form.get('iata_code')
    icao_code = request.form.get('icao_code')

    # Проверка обязательных полей
    if not name or not country or not iata_code or not icao_code:
        return jsonify(success=False, error='Все поля обязательны'), 400

    # Валидация кодов IATA (2 символа) и ICAO (3 символа)
    if len(iata_code) != 2 or len(icao_code) != 3:
        return jsonify(success=False, error='Неверная длина кода IATA или ICAO'), 400

    # Проверка уникальности по кодам (по желанию)
    existing_iata = Airline.query.filter_by(IATA_Code=iata_code).first()
    existing_icao = Airline.query.filter_by(ICAO_Code=icao_code).first()
    if existing_iata or existing_icao:
        return jsonify(success=False, error='Авиакомпания с таким кодом уже существует'), 400

    new_airline = Airline(
        Name=name,
        Country=country,
        IATA_Code=iata_code.upper(),
        ICAO_Code=icao_code.upper()
    )

    try:
        db.session.add(new_airline)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error='Ошибка сохранения в базу: ' + str(e)), 500

    return jsonify(success=True, airline={
        'id': new_airline.AirlineID,
        'name': new_airline.Name,
        'country': new_airline.Country,
        'iata_code': new_airline.IATA_Code,
        'icao_code': new_airline.ICAO_Code
    })

@app.route("/create-flight", methods=["POST"])
def create_flight():
    name = request.form["name"]
    from_city = request.form["from_city"]
    to_city_name = request.form["to_city"]

    to_city = City.query.filter_by(Name=to_city_name).first()
    if not to_city:
        return "Город назначения не найден", 400

    flight = Flights(
        Name=name,
        FromCity=int(from_city),
        ToCity=to_city.CityID,
        Date=request.form["date"],
        DepartureTime=request.form["departure_time"],
        ArrivalTime=request.form["arrival_time"],
        TicketPrice=request.form["ticket_price"],
        AirlineID=request.form["airline_id"]
    )
    db.session.add(flight)
    db.session.commit()

    return "OK"




if __name__ == '__main__':
    app.run(debug=True)
