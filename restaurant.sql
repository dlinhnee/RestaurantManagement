DROP DATABASE IF EXISTS RestaurantManagement;
CREATE DATABASE RestaurantManagement;
USE RestaurantManagement;

-- Employees table
CREATE TABLE employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    position VARCHAR(50) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    hire_date DATE
);

-- Customers table
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    address VARCHAR(255),
    email VARCHAR(100),
    tier VARCHAR(50) DEFAULT 'Standard',
    points INT DEFAULT 0,
    join_date DATE DEFAULT (CURRENT_DATE)
);

-- Tables table
CREATE TABLE tables (
    table_id INT PRIMARY KEY AUTO_INCREMENT,
    table_number INT NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'Available',
    capacity INT NOT NULL
);

-- Categories table
CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

-- Menu_items table
CREATE TABLE menu_items (
    dish_id INT PRIMARY KEY AUTO_INCREMENT,
    category_id INT,
    dish_name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2),
    is_available TINYINT(1) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- Reservations table
CREATE TABLE reservations (
    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NULL, 
    reservation_time DATETIME NOT NULL,
    guest_count INT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
);
-- Reservation_detail table
CREATE TABLE reservation_detail (
    reservation_id INT NOT NULL,
    table_id INT NOT NULL,
    PRIMARY KEY (reservation_id, table_id), 
    -- If a reservation is deleted, automatically clean up its table assignments
    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id) ON DELETE CASCADE,
    FOREIGN KEY (table_id) REFERENCES tables(table_id) ON DELETE CASCADE
);

-- Invoice table
CREATE TABLE invoices (
    invoice_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NULL,  
    employee_id INT NULL,  
    table_id INT NULL,     
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    payment_date DATETIME,
    order_type VARCHAR(20) NOT NULL,
    shipping_address VARCHAR(255),
    delivery_status VARCHAR(50),
    shipping_fee DECIMAL(10,2) DEFAULT 0.00,
    -- Using SET NULL for FKs so financial/sales history remains intact even if a customer or employee leaves
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (table_id) REFERENCES tables(table_id) ON DELETE SET NULL
);

-- Invoice_details table
CREATE TABLE invoice_details (
    detail_id INT PRIMARY KEY AUTO_INCREMENT,
    invoice_id INT NOT NULL,
    dish_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_subtotal DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    FOREIGN KEY (dish_id) REFERENCES menu_items(dish_id) ON DELETE CASCADE
);

-- Insert sample data

INSERT INTO categories (category_name) VALUES 
('Main Course'), ('Dessert'), ('Drink'), ('Appetizer'), 
('Soup'), ('Salad'), ('Seafood'), ('Steak'), ('Noodles'), ('Pizza');

INSERT INTO customers (name, phone, address, email, tier, points, join_date) VALUES
('Nguyen Ha An', '0901234567', '123 Le Loi, Ha Noi', 'a@gmail.com', 'Gold', 150, '2023-01-10'),
('Tran Thi Hang', '0912345678', '456 Tran Hung Dao, Hai Phong', 'b@gmail.com', 'Standard', 20, '2025-02-15'),
('Le Tung Duong', '0923456789', '789 Nguyen Hue, Ha Noi', 'c@gmail.com', 'Platinum', 300, '2024-03-20'),
('Pham Bao Ngoc', '0934567890', '101 Hai Ba Trung, Ha Noi', 'd@gmail.com', 'Standard', 50, '2022-04-05'),
('Hoang Khanh Vu', '0945678901', '202 Le Duan, Hung Yen', 'e@gmail.com', 'Gold', 120, '2025-05-12'),
('Nguyen Khanh Ly', '0956789012', '303 Truong Chinh, Ha Noi', 'f@gmail.com', 'Standard', 10, '2025-06-18'),
('Nguyen Thu Minh', '0967890123', '40 Nguyen Tat To, Ha Noi', 'g@gmail.com', 'Standard', 40, '2024-07-22'),
('Cai Bao Ngan', '0978901234', '505 Hoang Hoa Tham, Ha Noi', 'h@gmail.com', 'Platinum', 500, '2025-08-30'),
('Vu Dieu Linh', '0989012345', '312 Hong Gai, Quang Ninh', 'i@gmail.com', 'Gold', 180, '2024-09-14'),
('Le Ngoc Linh Nhi', '0903123456', '70 Hoang Dao Thuy, Ha Noi', 'k@gmail.com', 'Standard', 5, '2024-10-01');

INSERT INTO tables (table_number, status, capacity) VALUES
(1, 'Available', 2), (2, 'Available', 2), (3, 'Available', 4), 
(4, 'Reserved', 4), (5, 'Available', 4), (6, 'Occupied', 6), 
(7, 'Available', 6), (8, 'Reserved', 8), (9, 'Available', 8), 
(10, 'Available', 10);

INSERT INTO employees (full_name, position, username, password, hire_date) VALUES 
('Nguyen Van Anh', 'admin', 'admin', SHA2('123456', 256), '2026-01-01'),
('Tran Thu Ngan', 'cashier', 'cashier1', SHA2('123456', 256), '2026-02-15'),
('Le Ha An', 'waiter', 'waiter1', SHA2('123456', 256), '2026-03-10'),
('Pham Thanh Hai', 'waiter', 'waiter2', SHA2('123456', 256), '2026-04-05'),
('Hoang Gia An', 'admin', 'admin2', SHA2('123456', 256), '2026-05-16');


INSERT INTO employees (full_name, position, username, password, hire_date) VALUES 
('Ha Quang Huy', 'cashier', 'cashier2', SHA2('123456', 256), '2026-05-16');


INSERT INTO menu_items (category_id, dish_name, price, cost_price, is_available) VALUES
(1, 'Grilled Chicken Sandwich', 75000, 35000, 1),
(1, 'Beef Burger with Fries', 95000, 45000, 1),
(9, 'Beef Noodle Soup', 70000, 25000, 1),
(9, 'Seafood Pad Thai', 100000, 40000, 1),
(10, 'Pepperoni Pizza', 240000, 60000, 1),
(6, 'Grilled Chicken Salad', 65000, 30000, 1),
(5, 'Tomato Basil Soup', 45000, 20000, 1),
(4, 'Fried Dumplings', 50000, 25000, 1),
(3, 'Iced Peach Tea', 40000, 10000, 1),
(2, 'Fresh Fruit Bowl', 70000, 15000, 1);

INSERT INTO reservations (customer_id, reservation_time, guest_count) VALUES
(1, '2026-05-20 18:30:00', 2),
(2, '2026-05-21 19:00:00', 4),
(3, '2026-05-22 20:00:00', 6),
(4, '2026-05-23 18:00:00', 2),
(5, '2026-05-24 19:30:00', 8),
(6, '2026-05-25 18:45:00', 4),
(7, '2026-05-26 19:15:00', 2),
(8, '2026-05-27 20:30:00', 6),
(9, '2026-05-28 18:00:00', 4),
(10, '2026-05-29 19:00:00', 2);

INSERT INTO reservation_detail (reservation_id, table_id) VALUES
(1, 1), (2, 3), (3, 6), (4, 2), (5, 8), 
(6, 4), (7, 5), (8, 7), (9, 9), (10, 10);

INSERT INTO invoices (customer_id, employee_id, table_id, total_amount, payment_date, order_type, delivery_status) VALUES 
(1, 2, 1, 150000, '2026-05-01 11:30:00', 'Dine-in', 'Delivered'), 
(2, 2, 3, 190000, '2026-05-4 12:15:00', 'Dine-in', 'Delivered'), 
(3, 3, 6, 300000, '2026-05-8 18:00:00', 'Dine-in', 'Delivered'), 
(4, 3, NULL, 360000, '2026-05-10 19:30:00', 'Takeaway', 'Shipped'), 
(5, 4, 8, 600000, '2026-05-10 11:45:00', 'Dine-in', 'Delivered'), 
(6, 4, 4, 380000, '2026-05-11 13:00:00', 'Dine-in', 'Delivered'), 
(7, 2, NULL, 225000, '2026-05-11 19:15:00', 'Delivery', 'Shipped'), 
(8, 2, 7, 450000, '2026-05-12 12:30:00', 'Dine-in', 'Delivered'), 
(9, 1, 9, 500000, '2026-05-12 18:45:00', 'Dine-in', 'Delivered'), 
(10, 1, 10, 50000, '2026-05-12 20:00:00', 'Dine-in', 'Delivered');

INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) VALUES
(1, 1, 2, 75000, 150000),      
(2, 2, 2, 95000, 190000),      
(3, 1, 4, 75000, 300000),      
(4, 3, 5, 70000, 350000),      
(4, 4, 1, 100000, 100000),      
(5, 1, 8, 75000, 600000),     
(6, 2, 4, 95000, 380000),     
(7, 7, 5, 45000, 225000),      
(8, 1, 6, 75000, 450000),     
(9, 8, 10, 50000, 500000),    
(10, 9, 2, 40000, 80000);      

-- Trigger and procedure
USE RestaurantManagement;
DROP TRIGGER IF EXISTS after_reservation_insert;
DELIMITER //

CREATE TRIGGER after_reservation_table_insert
AFTER INSERT ON reservation_detail
FOR EACH ROW
BEGIN
    -- Automatically flip table status to 'Reserved' when assigned to a booking
    UPDATE tables 
    SET status = 'Reserved' 
    WHERE table_id = NEW.table_id;
    
DROP FUNCTION IF EXISTS CalculateLoyaltyPoints;

DELIMITER //
CREATE FUNCTION CalculateLoyaltyPoints(total_amount DECIMAL(10,2))
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE points INT;
    SET points = FLOOR(total_amount / 1000); -- Every 1,000 VND spent equals 1 loyalty point
    RETURN points;
END //
DELIMITER ;
DELIMITER ;

CREATE VIEW View_TopSellingDishes AS
SELECT m.dish_name, SUM(id.quantity) as total_sold
FROM menu_items m
JOIN invoice_details id ON m.dish_id = id.dish_id
GROUP BY m.dish_name
ORDER BY total_sold DESC;

-- Security
CREATE ROLE IF NOT EXISTS 'staff_role';
GRANT SELECT, INSERT, UPDATE ON RestaurantManagement.* TO 'staff_role';


-- Optimize menu item name searches
-- Added B-Tree index on dish_name to speed up front-end search/auto-complete dropdowns
CREATE INDEX idx_dish_name ON menu_items(dish_name);

-- Optimized search for table reservations by date and time
-- Added index on reservation_time since filtering bookings by date range is a high-frequency query
CREATE INDEX idx_reservation_time ON reservations(reservation_time);


