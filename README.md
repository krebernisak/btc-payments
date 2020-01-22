# btc_payments

Implement a Python REST web service that provides the functionality to create BTC transactions

## Development

### Install dependencies

Install dependencies into your environment by running the following in the terminal:

```bash
$ pip install -r ./btc_api/requirements/dev.txt
```

This will install dependencies for development environment including black formatter and flake8 linter (excluded in prod).

### Run development server

Start Flask development server (in debug mode) by running the following in the terminal:

```bash
$ cd btc_api/src
$ env FLASK_APP=app.py FLASK_DEBUG=1 flask run
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
-d '{"source_address": "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh", "min_confirmations": 7}'
```

Here is another example with multiline JSON:

```bash
$ curl -i -X POST http://localhost/payment_transactions \
-H "Content-Type: application/json" \
--data-binary @- << EOF
{
    "source_address": "1Po1oWkD2LmodfkBYiAktwh76vkF93LKnh",
    "outputs": {
        "3EktnHQD7RiAE6uzMj2ZifT9YgRrkSgzQX": 1000
    },
    "min_confirmations": 7,
    "fee_kb": 1024,
    "strategy": "greedy_max_secure"
}
EOF
```

Testnet is also supported:

```bash
$ curl -i -X POST http://localhost/payment_transactions \
-H "Content-Type: application/json" \
--data-binary @- << EOF
{
    "source_address": "mipcBbFg9gMiCh81Kj8tqqdgoZub1ZJRfn",
    "outputs": {
        "2MzQwSSnBHWHqSAqtTVQ6v47XtaisrJa1Vc": 1000
    },
    "min_confirmations": 7,
    "fee_kb": 1024,
    "strategy": "greedy_max_secure",
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
