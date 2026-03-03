-- Структура базы данных doors_db
-- Создано: 2026-03-03 15:47:33.406826

CREATE TABLE action_logs (id integer NOT NULL, user_id bigint, action_type text NOT NULL, apartment_id bigint, details text, created_at timestamp with time zone);


CREATE TABLE apartments (apartment_id integer NOT NULL, owner_id bigint, address text, installed_by bigint, rooms_count bigint, bed_count bigint, tariff_id bigint, created_at timestamp with time zone, latitude real, longitude real, cadastral_number text, country text, city text, district text, street text, building text, postal_code text, apartment text, timezone text, wifi_ssid text, wifi_password text, status text, registered_by integer, registered_at timestamp without time zone);


CREATE TABLE assignments (id integer NOT NULL, owner_id bigint NOT NULL, user_id bigint NOT NULL, role text NOT NULL, assigned_at timestamp with time zone);


CREATE TABLE bind_tokens (id integer NOT NULL, token text NOT NULL, owner_id bigint NOT NULL, esp32_id text, created_at timestamp with time zone, expires_at timestamp with time zone NOT NULL, used boolean);


CREATE TABLE bookings (id integer NOT NULL, booking_number text, apartment_id bigint, guest_id bigint, guest_name text, guest_phone text, created_by bigint, checkin_date timestamp with time zone, checkout_date timestamp with time zone, qr_code text, status text, created_at timestamp with time zone, access_type text);


CREATE TABLE device_commands (id integer NOT NULL, device_id bigint NOT NULL, command text NOT NULL, payload jsonb, status text, created_at timestamp with time zone, sent_at timestamp with time zone, completed_at timestamp with time zone);


CREATE TABLE device_logs (id integer NOT NULL, device_id bigint NOT NULL, event_type text NOT NULL, data jsonb, battery_level integer, wifi_rssi integer, local_time timestamp with time zone, created_at timestamp with time zone);


CREATE TABLE devices (device_id integer NOT NULL, owner_id bigint NOT NULL, installed_by bigint NOT NULL, esp32_id text NOT NULL, esp32_ip text, last_seen timestamp with time zone, is_active boolean, firmware_version text, battery_level integer, created_at timestamp with time zone);


CREATE TABLE guests (id integer NOT NULL, first_name text, last_name text, phone text, passport_data text, email text, total_bookings bigint, last_booking timestamp with time zone, marketing_consent boolean, created_at timestamp with time zone, type text, manager_id bigint, owner_id bigint);


CREATE TABLE invites (id integer NOT NULL, code text, created_by bigint, role text, created_at timestamp with time zone, expires_at timestamp with time zone, used_by bigint, used_at timestamp with time zone, is_used boolean);


CREATE TABLE qr_codes (id integer NOT NULL, code text NOT NULL, device_id bigint, booking_id bigint, purpose text NOT NULL, valid_from timestamp with time zone NOT NULL, valid_until timestamp with time zone NOT NULL, is_active boolean, created_at timestamp with time zone);


CREATE TABLE scan_logs (id integer NOT NULL, device_id bigint NOT NULL, qr_code text NOT NULL, success boolean NOT NULL, scanned_at timestamp with time zone, battery_level integer, wifi_rssi integer, error_message text);


CREATE TABLE settings (key text NOT NULL, value text, description text, updated_at timestamp with time zone);


CREATE TABLE tariffs (id integer NOT NULL, name text, type text, price_monthly numeric, commission_rate numeric, max_doors integer, max_managers integer, cleaning_enabled boolean, reports_enabled boolean, created_at timestamp with time zone);


CREATE TABLE tasks (id integer NOT NULL, created_by integer NOT NULL, apartment_id integer NOT NULL, booking_id integer, type text NOT NULL, status text, assigned_to integer, description text, scheduled_date date, result text, report text, photos text, completed_at timestamp with time zone, created_at timestamp with time zone, updated_at timestamp with time zone);


CREATE TABLE transactions (id integer NOT NULL, owner_id bigint NOT NULL, amount numeric, balance_after numeric, type text, description text, created_at timestamp with time zone);


CREATE TABLE users (id integer NOT NULL, telegram_id bigint, first_name text, last_name text, phone text, role text, passport_data text, verified boolean, created_at timestamp with time zone, timezone text, created_by integer);


