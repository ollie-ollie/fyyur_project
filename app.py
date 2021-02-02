#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import babel
import dateutil.parser
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form
from forms import *
import json
import logging
from logging import Formatter, FileHandler
from sqlalchemy.dialects.postgresql import ENUM
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500))

    shows = db.relationship('Show', backref='venue')

    def __repr__(self):
        return '<Venue {}>'.format(self.name)


class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500), nullable=False)

    shows = db.relationship('Show', backref='artist')

    def __repr__(self):
        return '<Artist {}>'.format(self.name)


class Show(db.Model):
    __tablename__ = 'shows'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)

    def __repr__(self):
        return '<Show at {} with {}>'.format(self.venue, self.artist)


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    recent_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    recent_venues = Venue.query.order_by(Venue.id.desc()).limit(10).all()

    return render_template(
        'pages/home.html',
        artists=recent_artists,
        venues=recent_venues
    )

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []
    areas = db.session.query(Venue.city, Venue.state).order_by('state', 'city').distinct()

    for a in areas:
        venues_in_area = Venue.query.filter_by(city=a.city).all()

        data_to_add = {
            'city': a.city,
            'state': a.state,
            'venues': [
                {
                  'id': v.id,
                  'name': v.name,
                  'num_upcoming_shows': Show.query.filter(Show.venue_id == v.id, Show.start_time >= datetime.now()).count()
                } for v in venues_in_area
            ]
        }

        data.append(data_to_add)

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()

    response = {
        'count': len(venues),
        'data': [
            {
              'id': v.id,
              'name': v.name,
              'num_upcoming_shows': Show.query.filter(Show.venue_id == v.id, Show.start_time >= datetime.now()).count()
            } for v in venues
        ]
    }

    return render_template(
        'pages/search_venues.html',
        results=response,
        search_term=request.form.get('search_term', '')
    )

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).one_or_none()

    data = {
      'id': venue.id,
      'name': venue.name,
      'genres': venue.genres,
      'address': venue.address,
      'city': venue.city,
      'state': venue.state,
      'phone': venue.phone,
      'website': venue.website,
      'facebook_link': venue.facebook_link,
      'seeking_talent': venue.seeking_talent,
      'seeking_description': venue.seeking_description,
      'image_link': venue.image_link,
      'past_shows': [
        {
          'artist_id': show.artist_id,
          'artist_name': show.artist.name,
          'artist_image_link': show.artist.image_link,
          'start_time': str(show.start_time)
        } for show in Show.query.filter(Show.venue_id == venue.id, Show.start_time < datetime.now()).all()
      ],
      'upcoming_shows': [
        {
          'artist_id': show.artist_id,
          'artist_name': show.artist.name,
          'artist_image_link': show.artist.image_link,
          'start_time': str(show.start_time)
        } for show in Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now()).all()
      ],
      'past_shows_count': Show.query.filter(Show.venue_id == venue.id, Show.start_time < datetime.now()).count(),
      'upcoming_shows_count': Show.query.filter(Show.venue_id == venue.id, Show.start_time >= datetime.now()).count()
    }

    return render_template(
        'pages/show_venue.html', 
        venue=data
    )

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()

  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    error = False
    form = VenueForm(request.form)

    try:
        venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website=form.website.data,
            genres=form.genres.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(venue)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        
    return render_template('pages/home.html')
  

@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    error = False

    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()

    if not error:
        flash('Venue deleted.')

    else:
        flash('Error: could not delete venue.')

    return redirect(url_for('venues'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = db.session.query(Artist.id, Artist.name).order_by('name').all()

    data = [{"id": a.id, "name": a.name} for a in artists]

    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    artists = Venue.query.filter(ARtist.name.ilike(f'%{search_term}%')).all()

    response = {
        "count": len(artists),
        "data":[
            {
                'id': a.id,
                'name': a.name,
                'num_upcoming_shows': Show.query.filter(Show.artist_id == a.id, Show.start_time >= datetime.now()).count()
            } for a in artists
        ]
    }

    return render_template(
        'pages/search_artists.html', 
        results=response, 
        search_term=search_term
    )

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.filter(Artist.id == artist_id).one()

    past_shows_query = Show.query.filter(
        Show.artist_id == artist_id, 
        Show.start_time < datetime.now()
    )
    upcoming_shows_query = Show.query.filter(
        Show.artist_id == artist_id, 
        Show.start_time >= datetime.now()
    )

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': [
            {
                'venue_id': show.venue_id,
                'venue_name': show.venue.name,
                'venue_image_link': show.venue.image_link,
                'start_time': str(show.start_time)
            } for show in past_shows_query.all()
        ],
        'upcoming_shows': [
            {
                'venue_id': show.venue_id,
                'venue_name': show.venue.name,
                'venue_image_link': show.venue.image_link,
                'start_time': str(show.start_time)
            } for show in upcoming_shows_query.all()
        ],
        'past_shows_count': past_shows_query.count(),
        'upcoming_shows_count': upcoming_shows_query.count()
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.filter(Artist.id == artist_id).one()
    form = ArtistForm(obj=artist)

    return render_template(
        'forms/edit_artist.html',
        form=form,
        artist=artist
    )

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    form = ArtistForm(request.form)
    artist = Artist.query.filter(Artist.id == artist_id)

    try:
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.website = form.website.data
        artist.genres = form.genres.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')

    else:
        flash('Artist ' + request.form['name'] + ' was successfully edited!')
        
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artists/<artist_id>', methods=['POST'])
def delete_artist(artist_id):
    error = False

    try:
        Artist.query.filter_by(id=artist_id).delete()
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()

    if not error:
        flash('Artist deleted.')

    else:
        flash('Error: could not delete artist.')

    return redirect(url_for('artists'))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.filter(Venue.id == venue_id).one()
    form = VenueForm(obj=venue)

    return render_template(
        'forms/edit_venue.html', 
        form=form, 
        venue=venue
    )

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    error = False
    form = VenueForm(request.form)
    venue = Venue.query.filter(Venue.id == venue_id)

    try:
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.image_link = form.image_link.data
        venue.facebook_link = form.facebook_link.data
        venue.website = form.website.data
        venue.genres = form.genres.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')

    else:
        flash('Venue ' + request.form['name'] + ' was successfully edited!')

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    error = False
    form = ArtistForm(request.form)

    try:
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website=form.website.data,
            genres=form.genres.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data
        )
        db.session.add(artist)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    shows = Show.query.order_by('venue_id', 'start_time').all()

    data = [
        {
            'venue_id': show.venue_id,
            'venue_name': show.venue.name,
            'artist_id': show.artist_id,
            'artist_name': show.artist.name,
            'artist_image_link': show.artist.image_link,
            'start_time': str(show.start_time)
        } for show in shows
    ]

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
    form = ShowForm()
    
    return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    error = False
    form = ShowForm(request.form)

    try:
        show = Show(
            venue_id=form.venue_id.data,
            artist_id=form.artist_id.data,
            start_time=format_datetime(str(form.start_time.d))
        )
        db.session.add(show)
        db.session.commit()

    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())

    finally:
        db.session.close()

    if error:
        flash('An error occured. Show could not be listed.')

    else:
        flash('Show was successfully listed!')

    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
