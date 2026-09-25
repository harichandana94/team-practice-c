# Shiva - RDS Integration

Version: V1
Owner: Shiva

## Responsibility

Connect the Team Practice C Streamlit application
to Amazon RDS PostgreSQL.

## Current State

Streamlit → SQLite

## Target State

Streamlit → PostgreSQL → Amazon RDS

## Required Information From Chandra

- DB_HOST
- DB_PORT
- DB_NAME
- DB_USER
- DB_PASSWORD

## Status

- [x] Shiva branch created
- [x] PostgreSQL dependency prepared
- [x] Environment variable template created
- [ ] RDS information received from Chandra
- [ ] Application connected to RDS
- [ ] Registration tested
- [ ] Login tested
- [ ] Data confirmed in RDS