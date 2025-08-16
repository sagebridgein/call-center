#!/bin/bash

echo "Stopping all services..."
docker-compose down
docker-compose --env-file variables.env up
echo "Removing volumes to start fresh..."
docker-compose down -v

echo "Starting services in order..."
docker-compose up -d postgres rabbitmq

echo "Waiting for database and message queue to be ready..."
sleep 10

echo "Starting auth service..."
docker-compose up -d auth

echo "Waiting for auth service to be ready..."
sleep 15

echo "Starting other services..."
docker-compose up -d confd provd sysconfd webhookd dird

echo "Waiting for services to be ready..."
sleep 10

echo "Starting remaining services..."
docker-compose up -d

echo "Waiting for all services to be ready..."
sleep 20

echo "Running bootstrap..."
docker-compose up bootstrap

echo "Services should now be ready!"
echo "Access the UI at: https://localhost:8443"
echo "Default credentials: admin / secret"
