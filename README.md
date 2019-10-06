![Python3](https://img.shields.io/badge/python-3.5%2B-green "Python3")

## What's this?

If you have a domain name in Alibaba cloud and you want to use its DNS service as DDNS,
then you can use this script *aliddns.py* to update your public IP to Ali's DNS service.

*aliddns.py* is a pure python3 script and only uses built-in modules.

## How to Use?

### Prerequisites

- A domain name in Ali cloud
- A pubilc IP addr

### Installation

    curl -O https://raw.githubusercontent.com/hlin/aliddns/master/aliddns.py
    chmod +x aliddns.py

### Usage

    ./aliddns.py -h

### Example

    export ALIDDNS_ACCESSKEYID=<Your Ali cloud AccessKey ID>
    export ALIDDNS_SECRET=<Your Ali cloud Access secret>

    # Update the IP for main domain example.com
    ./aliddns.py example.com @

    # Update the IP for sub domain abc.example.com
    ./aliddns.py example.com abc
