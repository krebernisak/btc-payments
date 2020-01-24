# btc_payments

This project implements a Python REST web service that provides the functionality to create unsigned BTC transactions using multiple coin selection strategies.

## Development

### Install dependencies

Install dependencies into your environment by running the following in the terminal:

```bash
$ pip install -r ./btc_api/requirements/dev.txt
```

This will install dependencies for development environment including black formatter and flake8 linter (excluded in prod).

### Run tests

```bash
$ python -m unittest discover btc_api
```

### Run development server

Start Flask development server (in debug mode) by running the following in the terminal:

```bash
$ cd btc_api/app
$ env FLASK_APP=app.py FLASK_DEBUG=1 python -m flask run
```

### Install the hooks

Install the git hooks defined in the pre-commit file by running the following in the terminal:

```bash
$ pre-commit install
```

## Production deployment

The production environment scales Python Flask App using [Gunicorn](https://gunicorn.org/) application server and [NGINX](https://www.nginx.com/) web server using multiple Containers with Docker Compose.

### Docker Compose

```bash
$ docker-compose up --build --detach
```

## Testing

We can test the endpoint using `curl` via POST sending JSON payload (just remember to set correct Content-Type header):

```bash
$ curl -i -X POST http://localhost/payment_transactions \
-H "Content-Type: application/json" \
-d '{"source_address": "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh", "outputs": {"17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem": 20000}, "min_confirmations": 7}'
```

NGINX optimizes JSON response so to get the pretty printed JSON response drop the `-i` flag and pipe the `curl` result to a formatter like `json_pp`:

```bash
$ curl -X POST http://localhost/payment_transactions \
-H "Content-Type: application/json" \
-d '{"source_address": "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh", "outputs": {"17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem": 20000}, "min_confirmations": 7}' \
| json_pp
```

Here is another example with multiline JSON input:

```bash
$ curl -i -X POST http://localhost/payment_transactions \
-H "Content-Type: application/json" \
--data-binary @- << EOF
{
    "source_address": "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh",
    "outputs": {
        "3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX": 10000,
        "17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem": 20000
    },
    "min_confirmations": 7,
    "fee_kb": 1024,
    "strategy": "greedy_max_secure"
}
EOF
```

Or another one using different a strategy (please use on of [greedy_max_secure|greedy_max_coins|greedy_min_coins|greedy_random]):

```bash
$ curl -i -X POST http://localhost/payment_transactions \
-H "Content-Type: application/json" \
--data-binary @- << EOF
{
    "source_address": "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh",
    "outputs": {
        "3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX": 10000,
        "17VZNX1SN5NtKa8UQFxwQbFeFc3iqRYhem": 20000
    },
    "min_confirmations": 7,
    "fee_kb": 1024,
    "strategy": "greedy_min_coins"
}
EOF
```

Testnet is also supported but make sure to use testnet addresses:

```bash
$ curl -i -X POST http://localhost/payment_transactions \
-H "Content-Type: application/json" \
--data-binary @- << EOF
{
    "source_address": "mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn",
    "outputs": {
        "2MzQwSSnBHWHqSAqtTVQ6v47XtaisrJa1Vc": 10000
    },
    "min_confirmations": 7,
    "fee_kb": 1024,
    "strategy": "greedy_random",
    "testnet": true
}
EOF
```

### Decode Transaction

If you have access to a `bitcoind` node you can use `bitcoin-cli` to decode raw transaction:

```bash
$ bitcoin-cli decoderawtransaction "..."
```

Or you can use an convenient online service like [Decode Raw Transaction - BlockCypher](https://live.blockcypher.com/btc/decodetx/).
