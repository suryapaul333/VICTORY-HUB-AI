-- PostgreSQL schema for AI Student Performance System
-- Render can create these tables automatically via app.py.
-- This file is provided for reference/manual setup.

CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE,
  phone TEXT UNIQUE,
  password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS semester_subjects (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  branch TEXT NOT NULL,
  year TEXT NOT NULL,
  semester TEXT NOT NULL,
  subject_names TEXT NOT NULL,
  UNIQUE(user_id, branch, year, semester)
);

CREATE TABLE IF NOT EXISTS predictions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT, name TEXT, year TEXT, semester TEXT, branch TEXT,
  attendance DOUBLE PRECISION, subject_names TEXT, subject_marks TEXT,
  assignment_marks TEXT, internal_marks TEXT, study_hours DOUBLE PRECISION,
  prediction TEXT, score DOUBLE PRECISION,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS custom_subjects (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT, branch TEXT, year TEXT, semester TEXT, subjects TEXT,
  UNIQUE(user_id, branch, year, semester)
);
