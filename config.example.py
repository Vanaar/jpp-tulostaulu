import os

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'mysql://<username>:<password>@127.0.0.1:3306/jpp-tulostaulu?charset=utf8mb4&binary_prefix=true'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Secret key for sessions
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'

    # Activate debug mode
    # DEBUG_LEVEL = 1 näytä kaikki debug-viestit
    # DEBUG_LEVEL = 2 näytä vain info ja korkeammat viestit
    # DEBUG_LEVEL = 3 näytä vain varoitus ja korkeammat viestit
    # DEBUG_LEVEL = 4 näytä vain virheviestit
    DEBUG = True
    DEBUG_LEVEL = 1
    
    #Chromium
    #Poista kommentti, jos käytät chromedriveria ja sen polku pitää asettaa erikseen
    #Vaaditaan erityisesti Linux-ympäristössä
    
    #CHROMIUM_CUSTOM_CONFIG = True
    #CHROMIUM_PATH = '/usr/lib/chromium-browser/chromedriver'
    
    #Kauanko selenium odottaa sivun sisällön päivittymistä, ennen kuin jatkaa parsimista
    #default 1 sekunti
    PAGE_LOAD_WAIT = 1