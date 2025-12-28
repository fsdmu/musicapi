# musicapi

This project is intended to automatically handle the download of music from supported download handlers and
store the url to the downloaded songs and albums in a database, 
thus preventing them from being downloaded multiple times.
You can also download all albums and eps of an artist by  providing the link to that artist. 
When toggling download future albums of an artist all future albums of that  artist will be downloaded as well.
To enable this feature you have to run a reoccurring job on the machine that calls the "auto_download_artist.py" 
script periodically. 

The exact behavior could differ by handler to handler.


## Intended Setup

The webui service is supposed to be run on a machine with access to a supported download handler. 


## Supported Services

These are the lists of currently supported Services.

### Download Handlers

- [MeTube](https://github.com/alexta69/metube)


### Database Connections

All database providers that are compatible with SQLAlchemy can be implemented very easily without any issues.

#### [MySQL](https://www.mysql.com/)


**Database Setup**

- Artist table
  - 'artist' as tablename
  - 'id' Column as an Integer primary key with auto increment
  - 'url' Column as Varchar and a Unique constraint
  - 'auto_download' as Boolean which defaults to false

- Album table
  - 'album' as tablename
  - 'id' Column as an Integer primary key with auto increment
  - 'url' Column as Varchar and a Unique constraint

- Song table
  - 'song' as tablename
  - 'id' Column as an Integer primary key with auto increment
  - 'url' Column as Varchar and a Unique constraint

## Usage

It is strongly recommended to run the script via the Dockerfile.

### Environment Setup

- Database information
  - "DB_URL"
  - "DB_PORT"
  - "DB_DATABASE"
- Username and password for an account with 'SELECT', 'INSERT', 'UPDATE' and 
    'DELETE' permissions 
    - "DB_USER"
    - "DB_PASSWORD"
- MeTube information
  - "ME_TUBE_API_URL"


### Auto Download of Artists

To enable the automatic download of artists a reoccurring job needs to be run that calls the "auto_download_artist.py" 
script. The same environment setup as for the regular web service is necessary for this.

## Releases

### 0.4.0

- Improve ui with help icon
- Remove developer option for adding artist without download
- Add option to select different audio formats
- Update Table names for albums and songs
- Bugfixes
- Update Documentation

## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

You are free to use, modify, and distribute this software, including for
commercial purposes, provided that any derivative work is also licensed
under GPLv3 and the source code is made available.
