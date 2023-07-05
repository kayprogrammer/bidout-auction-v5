# BidOut Auction V5 (WORK IN PROGRESS)

![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/ninja.png?raw=true)


#### DJANGO DOCS: [Documentation](https://docs.djangoproject.com/en/4.2/)
#### DJANGO NINJA DOCS: [Documentation](https://django-ninja.rest-framework.com/)

#### PG ADMIN: [Documentation](https://pgadmin.org) 


## How to run locally

* Download this repo or run: 
```bash
    $ git clone git@github.com:kayprogrammer/bidout-auction-v5.git
```

#### In the root directory:
- Install all dependencies
```bash
    $ pip install -r requirements.txt
```
- Create an `.env` file and copy the contents from the `.env.example` to the file and set the respective values. A postgres database can be created with PG ADMIN or psql

- Run Locally
```bash
    $ python manage.py migrate 
```
```bash
    $ uvicorn bidout_auction_v5.asgi:application --reload
```

- Run With Docker
```bash
    $ docker-compose up --build -d --remove-orphans
```
OR
```bash
    $ make build
```

- Test Coverage
```bash
    $ pytest --disable-warnings -vv
```
OR
```bash
    $ make test
```

## Docs
#### Live Url: [BidOut Docs (Not ready yet!)](https://bidout-drf-ninja-api.cleverapps.io/) 
#### Swagger: [Documentation](https://swagger.io/docs/)
<!-- #### React Live Url: [BidOut Auction](https://bidout3.netlify.app)  -->


![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/display1.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/display2.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/display3.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/display4.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/display5.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/display6.png?raw=true)

![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/display7.png?raw=true)

## ADMIN PAGE
![alt text](https://github.com/kayprogrammer/bidout-auction-v5/blob/main/display/admin.png?raw=true)