"""
-- WeatherGPT PostgreSQL schema (SQLAlchemy also creates these on startup)

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  phone VARCHAR(20) UNIQUE,
  email VARCHAR(255) UNIQUE,
  role VARCHAR(32) NOT NULL,
  preferred_language VARCHAR(8) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE locations (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  district VARCHAR(120),
  state VARCHAR(120),
  country VARCHAR(80) DEFAULT 'India',
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL
);

CREATE TABLE user_locations (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  location_id INTEGER REFERENCES locations(id),
  is_primary BOOLEAN DEFAULT TRUE,
  UNIQUE (user_id, location_id)
);

CREATE TABLE weather_observations (
  id SERIAL PRIMARY KEY,
  location_id INTEGER REFERENCES locations(id),
  timestamp TIMESTAMP NOT NULL,
  temperature DOUBLE PRECISION,
  humidity DOUBLE PRECISION,
  rainfall DOUBLE PRECISION,
  wind_speed DOUBLE PRECISION,
  wind_direction DOUBLE PRECISION,
  pressure DOUBLE PRECISION,
  source VARCHAR(80) NOT NULL,
  is_demo BOOLEAN DEFAULT FALSE
);

CREATE TABLE forecasts (
  id SERIAL PRIMARY KEY,
  location_id INTEGER REFERENCES locations(id),
  forecast_time TIMESTAMP NOT NULL,
  temperature DOUBLE PRECISION,
  rain_probability DOUBLE PRECISION,
  rainfall DOUBLE PRECISION,
  humidity DOUBLE PRECISION,
  wind_speed DOUBLE PRECISION,
  source VARCHAR(80) NOT NULL,
  model_name VARCHAR(80),
  is_demo BOOLEAN DEFAULT FALSE
);

CREATE TABLE historical_weather (
  id SERIAL PRIMARY KEY,
  location_id INTEGER REFERENCES locations(id),
  date DATE NOT NULL,
  temperature DOUBLE PRECISION,
  rainfall DOUBLE PRECISION,
  humidity DOUBLE PRECISION,
  wind_speed DOUBLE PRECISION,
  source VARCHAR(80) NOT NULL,
  is_demo BOOLEAN DEFAULT FALSE
);

CREATE TABLE alerts (
  id SERIAL PRIMARY KEY,
  alert_type VARCHAR(80) NOT NULL,
  severity VARCHAR(40) NOT NULL,
  title VARCHAR(255) NOT NULL,
  description TEXT NOT NULL,
  affected_location VARCHAR(200) NOT NULL,
  district VARCHAR(120),
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  source VARCHAR(120) NOT NULL,
  cyclone_path JSON,
  warning_zones JSON,
  is_demo BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE chat_history (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  question TEXT NOT NULL,
  intent VARCHAR(80) NOT NULL,
  retrieved_data JSON,
  response TEXT NOT NULL,
  language VARCHAR(8) NOT NULL,
  grounded BOOLEAN DEFAULT TRUE,
  used_llm BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE advisories (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  advisory_type VARCHAR(80) NOT NULL,
  input_data JSON,
  response TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE notifications (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  alert_id INTEGER REFERENCES alerts(id),
  message TEXT NOT NULL,
  status VARCHAR(16) NOT NULL,
  created_at TIMESTAMP NOT NULL
);
"""
