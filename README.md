# Tally

Tally is an application designed to help you manage recurring bills and forecast your future bank account balance. With Tally, you can track upcoming payments, visualize your cash flow, and plan ahead with confidence.

## Getting Started with Docker Compose

Tally uses Docker Compose to simplify running all required services. Follow the steps below to get started:

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- [Docker Compose](https://docs.docker.com/compose/install/) installed

### Starting the Services

Start the services with:

```sh
docker-compose up
```

This command will build and start all necessary containers for Tally.

Access the application by opening your browser and navigating to [http://localhost:8000](http://localhost:8000) (or the port specified in your `docker-compose.yml`).

### Stopping the Services

To stop the services, press `Ctrl+C` in the terminal where Docker Compose is running, then run:

```sh
docker-compose down
```

## Configuration

You can customize environment variables and service settings in the `docker-compose.yml` file as needed.

## Support

For questions or issues, please open an issue on the [GitHub repository](https://github.com/yourusername/tally/issues).
