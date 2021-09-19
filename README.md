# How-to

## Pre-requisites (Mac)
- [python 3.8](https://www.laptopmag.com/how-to/install-python-on-macos)
- python virtualenv
```
pip install virtualenv
```

Setup:
Go to the root folder of this repo, on the command line
```
cd options-trader
```

Create separate virtualenv and activate it
```
virtualenv -p python3.8 options-trader
source options-trader/bin/activate
```

Install requirements
```
pip install -r requirements.txt
cp sample_config.json config.json
```

To trigger the runner (only this command is required from next time onwards; after logging into Zerodha in Chrome)
```
python run.py
```
