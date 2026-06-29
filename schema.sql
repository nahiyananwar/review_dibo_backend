-- Review Dibo API - PostgreSQL schema
-- Generated from the SQLAlchemy models (app/modules/*/models.py).
-- Apply with: psql -d review_dibo -f schema.sql   (or just run `python seed.py`).

CREATE TABLE products (
	id SERIAL NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	image_url VARCHAR(1024), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_products_id ON products (id);
CREATE INDEX ix_products_title ON products (title);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255), 
	is_admin BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_users_id ON users (id);
CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE reviews (
	id SERIAL NOT NULL, 
	product_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	rating INTEGER NOT NULL, 
	comment TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_reviews_rating_range CHECK (rating >= 1 AND rating <= 5), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX ix_reviews_user_id ON reviews (user_id);
CREATE INDEX ix_reviews_product_id ON reviews (product_id);
CREATE INDEX ix_reviews_id ON reviews (id);
