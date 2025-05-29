from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class City(db.Model):
    CityID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    Attractions = db.Column(db.Text)

tours_excursions = db.Table('tours_excursions',
    db.Column('tour_id', db.Integer, db.ForeignKey('tours.TourID'), primary_key=True),
    db.Column('excursion_id', db.Integer, db.ForeignKey('excursions.ExcursionID'), primary_key=True)
)
class Tours(db.Model):
    __tablename__ = 'tours'
    TourID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    CityID = db.Column(db.Integer, db.ForeignKey('city.CityID'))
    Duration = db.Column(db.Integer)
    Date = db.Column(db.Date)
    Price = db.Column(db.Float)

    # Добавленные связи:
    AirlineID = db.Column(db.Integer, db.ForeignKey('Airlines.AirlineID'), nullable=True)
    FlightID = db.Column(db.Integer, db.ForeignKey('flights.FlightID'), nullable=True)
    HotelID = db.Column(db.Integer, db.ForeignKey('hotel.HotelID'), nullable=True)
    RoomID = db.Column(db.Integer, db.ForeignKey('room.RoomID'), nullable=True)

    airline = db.relationship('Airline', backref='tours')
    flight = db.relationship('Flights', backref='tours')
    hotel = db.relationship('Hotel', backref='tours')
    room = db.relationship('Room', backref='tours')

    excursions = db.relationship('Excursions',
                                 secondary=tours_excursions,
                                 backref=db.backref('tours', lazy='dynamic'),
                                 lazy='dynamic')

class Excursions(db.Model):
    ExcursionID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100))
    Guide = db.Column(db.String(100))
    Route = db.Column(db.Text)
    Date = db.Column(db.Date)
    Price = db.Column(db.Float)
    CityID = db.Column(db.Integer, db.ForeignKey('city.CityID'))

class Flights(db.Model):
    FlightID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100), nullable=False)
    
    FromCity = db.Column(db.Integer, db.ForeignKey('city.CityID'), nullable=False)
    ToCity = db.Column(db.Integer, db.ForeignKey('city.CityID'), nullable=False)
    
    Date = db.Column(db.Date, nullable=False)
    DepartureTime = db.Column(db.Time, nullable=False)
    ArrivalTime = db.Column(db.Time, nullable=False)
    
    TicketPrice = db.Column(db.Numeric(10, 2), nullable=False)

    AirlineID = db.Column(db.Integer, db.ForeignKey('Airlines.AirlineID'), nullable=False)  # исправлено имя поля
    airline = db.relationship('Airline', back_populates='flights')

    from_city = db.relationship('City', foreign_keys=[FromCity], backref='departing_flights')
    to_city = db.relationship('City', foreign_keys=[ToCity], backref='arriving_flights')

class Airline(db.Model):
    __tablename__ = 'Airlines'
    AirlineID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100))
    Country = db.Column(db.String(100))
    IATA_Code = db.Column(db.String(2))
    ICAO_Code = db.Column(db.String(3))
    flights = db.relationship('Flights', back_populates='airline')

class Hotel(db.Model):
    HotelID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100))
    Stars = db.Column(db.Integer)
    CityID = db.Column(db.Integer, db.ForeignKey('city.CityID'))

class Room(db.Model):
    RoomID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(100))
    Type = db.Column(db.String(100))
    Price = db.Column(db.Float)
    HotelID = db.Column(db.Integer, db.ForeignKey('hotel.HotelID'))

class TourImages(db.Model):
    __tablename__ = 'tour_images'
    ImageID = db.Column(db.Integer, primary_key=True)
    TourID = db.Column(db.Integer, db.ForeignKey('tours.TourID'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)

    tour = db.relationship('Tours', backref=db.backref('images', cascade='all, delete-orphan'))
