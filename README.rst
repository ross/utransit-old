utransit
########

Proof-of-concept/API demo for a universal multi-region transit data api
including scheduling and real-time data.

If you would like to test out a server that may or may not be up/accessible at
any given time you can visit http://demo.xormedia.com/api/ and log in with the
username demo and the password demo566.

If you would like to run your own instance the following should get you
started.

===============
Getting Started
===============

    git clone https://github.com/ross/utransit.git
    cd utransit
    virtualenv env
    source env/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt

    # create a new file, creds.py, and open it in your editor, adding the
    # folowing line to it
    API_KEY_ONE_BUS_AWAY_SEA = '<your-sea-api-key>'
    # talk a look at the API_KEY variable in www/settings/base.py for other
    # possible providers/values

    export ENV=dev
    ./manage.py syncdb
    ./manage.py runserver

Open http://localhost:8000/adm/ in your browser and sign in with the admin
account your created during the syncdb step. Note that the workflow for a lot
of this could be automated, but hasn't been (yet.)

Go to the Region section and add a new region.
    
    id sea
    name Seattle Area
    sign SEA

Then go to the Agency section and add a new agency.

    region, select SEA from the drop down
    id sea:1
    name Metro Transit
    sign METRO
    provider, select OneBusAwaySea
    ...


    ./manage.py shell

    from www.clients import sync_agency
    from www.info.models import Agency

    sync_agency(Agency.objects.get(pk='sea:1')
    # a bunch of debug logging will fly by as the agencies data is synced

Open http://localhost:8000/api/ in your browser and log in using your admin
account. You should now see your region and after clicking it your agency, etc.

