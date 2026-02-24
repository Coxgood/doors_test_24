-- Таблица: users
CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            first_name TEXT,
            last_name TEXT,
            phone TEXT,
            role TEXT,
            passport_data TEXT,
            verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

-- Таблица: sqlite_sequence
CREATE TABLE sqlite_sequence(name,seq);

-- Таблица: apartments
CREATE TABLE apartments (
            apartment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            installed_by INTEGER,
            rooms_count INTEGER DEFAULT 1,
            bed_count INTEGER DEFAULT 1,
            tariff_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, latitude REAL, longitude REAL, cadastral_number TEXT, country TEXT DEFAULT 'Россия', city TEXT, district TEXT, street TEXT, building TEXT, postal_code TEXT,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (installed_by) REFERENCES users(id)
        );

-- Таблица: bookings
CREATE TABLE bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_number TEXT UNIQUE,
            apartment_id INTEGER NOT NULL,
            guest_id INTEGER,
            guest_name TEXT,
            guest_phone TEXT,
            created_by INTEGER,
            checkin_date TIMESTAMP NOT NULL,
            checkout_date TIMESTAMP NOT NULL,
            qr_code TEXT UNIQUE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, access_type TEXT DEFAULT 'rent',
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id),
            FOREIGN KEY (guest_id) REFERENCES guests(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

-- Таблица: guests
CREATE TABLE guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            phone TEXT UNIQUE,
            passport_data TEXT,
            email TEXT,
            total_bookings INTEGER DEFAULT 0,
            last_booking TIMESTAMP,
            marketing_consent BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        , type TEXT DEFAULT 'guest', manager_id INTEGER, owner_id INTEGER);

-- Таблица: invites
CREATE TABLE invites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            created_by INTEGER NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            used_by INTEGER,
            used_at TIMESTAMP,
            is_used BOOLEAN DEFAULT 0,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (used_by) REFERENCES users(id)
        );

-- Таблица: bind_tokens
CREATE TABLE bind_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            owner_id INTEGER NOT NULL,
            esp32_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            FOREIGN KEY (owner_id) REFERENCES users(telegram_id)
        );

-- Таблица: action_logs
CREATE TABLE action_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action_type TEXT NOT NULL,
            apartment_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (apartment_id) REFERENCES apartments(apartment_id)
        );

-- Таблица: assignments
CREATE TABLE assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

-- Таблица: tariffs
CREATE TABLE tariffs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            type TEXT DEFAULT 'subscription',
            price_monthly DECIMAL(10,2) DEFAULT 0,
            commission_rate DECIMAL(5,2) DEFAULT 0,
            max_doors INTEGER DEFAULT 999,
            max_managers INTEGER DEFAULT 999,
            cleaning_enabled BOOLEAN DEFAULT 1,
            reports_enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

-- Таблица: transactions
CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            amount DECIMAL(10,2),
            balance_after DECIMAL(10,2),
            type TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        );

-- Таблица: settings
CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

-- Таблица: qr_codes
CREATE TABLE qr_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            door_id INTEGER,
            issued_by INTEGER,
            issued_to TEXT,
            valid_from TIMESTAMP,
            valid_until TIMESTAMP,
            is_used BOOLEAN DEFAULT 0,
            used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (door_id) REFERENCES "devices_old"(door_id),
            FOREIGN KEY (issued_by) REFERENCES users(id)
        );

-- Таблица: scan_logs
CREATE TABLE scan_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            qr_code TEXT NOT NULL,
            door_id INTEGER,
            success BOOLEAN NOT NULL,
            scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_time_ms INTEGER,
            wifi_rssi INTEGER,
            battery_level INTEGER,
            firmware_version TEXT,
            error_message TEXT,
            FOREIGN KEY (door_id) REFERENCES "devices_old"(door_id)
        );

-- Таблица: devices
CREATE TABLE devices (
            device_id INTEGER PRIMARY KEY,
            owner_id INTEGER NOT NULL,
            installed_by INTEGER NOT NULL,
            esp32_id TEXT UNIQUE NOT NULL,
            esp32_ip TEXT,
            last_seen TIMESTAMP,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

-- Таблица: tasks
CREATE TABLE tasks (
            id INTEGER PRIMARY KEY,
            created_by INTEGER NOT NULL,
            apartment_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            assigned_to INTEGER,
            description TEXT,
            scheduled_date DATE,
            result TEXT,
            report TEXT,
            photos TEXT,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );

