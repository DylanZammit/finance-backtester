# Backtester
## Introduction

This framework allows easy implementation of backtesting strategies in finance. The framework takes into consideration the following.
- Transaction costs (ex. 2% of traded assets)
- Risk scaling  (ex. 20% annualized risk)
- Risk scaling with cross-correlations (using covariance matrix)
- Minimises round trades

A working version can be found [here](http://dylanzammit.pythonanywhere.com/).

## Usage
A strategy class needs to inherit from the generic `Strat` class. The only method that _needs_ to be defined in this strategy class is the `signal` method. This is the "brains" of the model and should output a "signal", i.e. buy, sell a certain amount. An example implementation is given by. 

    class LongOnly(Strat):

        @property
        @cache
        def signal(self):
            return self.prices.div(self.prices)

The above example outputs a signal of 1 throughout, meaning that one should always **buy one unit of risk**. This does **not** mean that one share is bought and never sold. Since we are risk-scaling, an increase in volatility might mean that we sell shares in order to achieve a constant level of risk in our portfolio.

## Setup
A `.yaml` file can be set up as a configuration file for the strategies. An example config file is

    common:
       capital: 100_000
       risk: 0.1
       tc_cost: 0.02
       start: '2013-01-01'
    
    models:
        MyStrat1:
            strat: LongOnly
            param1: val1
        MyStrat2:
            strat: LongOnly
            param1: valX
            param2: valY
In order to run the backtested strategy, you can call the `simulator.py` script with the following example parameters.

    python simulator.py -d path/to/data.csv -t TIK1,TIK2

## Hosting
In order to locally host the dashboard you can build the image as specificed in the `Dockerfile` by running

`docker build --tag findash .`

Then you can run the docker container command given by

`docker run -it -p 8050:8050 -d --name findash findash`

## Images

![findash](https://github.com/DylanZammit/finance-backtester/blob/master/README_img/fin_dashboard.jpeg)
