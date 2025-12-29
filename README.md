# musicapi

This project is intended to automatically handle the download of music from supported download handlers and
store the url to the downloaded songs and albums in a database, 
thus preventing them from being downloaded multiple times.
You can also download all albums and eps of an artist by  providing the link to that artist. 
When toggling download future albums of an artist all future albums of that  artist will be downloaded as well.
To enable this feature you have to run a recurring job on the machine that calls the "auto_download_artist.py" 
script periodically. 

The exact behavior could differ by handler to handler.


## Intended Setup

The web service is supposed to be run on a machine with access to a supported download handler. 


## Supported Services

These are the lists of currently supported Services.

### Download Handlers

- [MeTube](https://github.com/alexta69/metube)


### Database Setup

All database providers that are compatible with SQLAlchemy are supported. 
By default, it connects to a [MySQL](https://www.mysql.com/) database. 
This can be changed via the 'DB_DRIVER' environment variable. 
Refer to the official 
[SQLAlchemy](https://docs.sqlalchemy.org/en/14/core/engines.html) documentation.

#### Table Setup

**Artist table** with name 'artist'.

| Column        | Type    | Constraints                 | Default |
|---------------|---------|-----------------------------|---------|
| id            | Integer | Primary Key, Auto Increment | -       |
| url           | Varchar | Unique, Not Null            | -       |
| auto_download | Boolean | Not Null                    | False   |


**Album table** with name 'album'.

| Column        | Type    | Constraints                 | Default |
|---------------|---------|-----------------------------|---------|
| id            | Integer | Primary Key, Auto Increment | -       |
| url           | Varchar | Unique, Not Null            | -       |


**Song table** with name 'song'.

| Column        | Type    | Constraints                 | Default |
|---------------|---------|-----------------------------|---------|
| id            | Integer | Primary Key, Auto Increment | -       |
| url           | Varchar | Unique, Not Null            | -       |


## Usage

It is strongly recommended to run the script using the provided [Dockerfile](Dockerfile).

### Environment Setup

Example .env file.

```dotenv
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_DATABASE=music_db
DB_USER=admin
DB_PASSWORD=securepassword
DB_DRIVER=mysql+mysqlconnector

# Handler Configuration
ME_TUBE_API_URL=http://metube:8081
```

### Auto Download of Artists

To enable the automatic download of artists a recurring job needs to be run that calls 
the ["auto_download_artist.py"](src/auto_download_artists.py) 
script. The same environment setup as for the regular web service is necessary for this.

## Releases

### 0.4.0

- Improve ui with help icon
- Remove developer option for adding artist without download
- Add option to select different audio formats
- Update Table names for albums and songs
- Add option to switch driver to a Database using an environment variable
- Bugfixes
- Update Documentation

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

You are free to use, modify, and distribute this software, including for
commercial purposes, provided that any derivative work is also licensed
under GPLv3 and the source code is made available.
