# musicapi

This project is intended to automatically handle the download of music from supported download handlers and
store the url to the downloaded songs and albums in a database, 
thus preventing them from being downloaded multiple times.
You can also download all albums and eps of an artist by  providing the link to that artist. 
When toggling download future albums of an artist all future albums of that  artist will be downloaded as well.
To enable this feature you have to run a reoccurring job on the machine that calls  the "auto_download_artist.py" 
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

- [MySQL](https://www.mysql.com/)

## CLI Usage

Assuming the script is located in /app:

#### Web Interface

```bash
python3 -m pip install -r ./src/requirements.txt
python3 ./src/webui.py
```

It is strongly recommended to run the script via the Dockerfile.


#### Auto Download of Artists

TODO


## License

This project is licensed under the GNU General Public License v3.0 (GPLv3).

You are free to use, modify, and distribute this software, including for
commercial purposes, provided that any derivative work is also licensed
under GPLv3 and the source code is made available.
