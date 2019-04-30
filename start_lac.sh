#! /bin/bash

sudo docker run -it -p 18080:18080 -v $PWD:/paddle -w /paddle/lac/build paddle:dev python m.py
