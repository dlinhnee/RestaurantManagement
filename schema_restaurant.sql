-- 1. KHỞI TẠO DATABASE
DROP DATABASE IF EXISTS RestaurantManagement;
CREATE DATABASE RestaurantManagement;
USE RestaurantManagement;

-- 1. Bảng Nhân viên
CREATE TABLE employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(100) NOT NULL,
    position VARCHAR(50) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    hire_date DATE
);

-- 2. Bảng Khách hàng (Đã gộp thông tin Thẻ thành viên)
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(15),
    address VARCHAR(255),
    email VARCHAR(100),
    tier VARCHAR(50) DEFAULT 'Standard',
    points INT DEFAULT 0,
    join_date DATE
);

-- 3. Bảng Bàn ăn
CREATE TABLE tables (
    table_id INT PRIMARY KEY AUTO_INCREMENT,
    table_number INT NOT NULL UNIQUE,
    status VARCHAR(50) DEFAULT 'Available',
    capacity INT NOT NULL
);

-- 4. Bảng Danh mục món ăn
CREATE TABLE categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

---

### PHẦN 2: TẠO CÁC BẢNG PHỤ THUỘC (Chứa khóa ngoại)

-- 5. Bảng Món ăn
CREATE TABLE menu_items (
    dish_id INT PRIMARY KEY AUTO_INCREMENT,
    category_id INT,
    dish_name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    cost_price DECIMAL(10,2),
    is_available TINYINT(1) DEFAULT 1,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- 6. Bảng Đặt bàn
CREATE TABLE reservations (
    reservation_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    table_id INT NOT NULL,
    reservation_time DATETIME NOT NULL,
    guest_count INT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (table_id) REFERENCES tables(table_id) ON DELETE CASCADE
);

-- 7. Bảng Hóa đơn (Đã gộp thông tin Giao hàng)
CREATE TABLE invoices (
    invoice_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    employee_id INT,
    table_id INT,
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    payment_date DATETIME,
    order_type VARCHAR(20) NOT NULL,
    shipping_address VARCHAR(255),
    delivery_status VARCHAR(50),
    shipping_fee DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL,
    FOREIGN KEY (table_id) REFERENCES tables(table_id) ON DELETE SET NULL
);

-- 8. Bảng Chi tiết Hóa đơn (Bảng trung gian giải quyết quan hệ M:N)
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

-- 3. CHÈN DỮ LIỆU MẪU (DML)

INSERT INTO categories (category_name) VALUES ('Main Course'), ('Dessert'), ('Drink'), ('Appetizer');

INSERT INTO customers (name, phone, address) VALUES 
('Nguyễn Văn An', '0912345678', 'Hà Nội'),
('Trần Thị Bình', '0987654321', 'TP.HCM'),
('Lê Hoàng Nam', '0905123456', 'Đà Nẵng'),
('Phạm Minh Đức', '0933445566', 'Cần Thơ'),
('Hoàng Lan Anh', '0911223344', 'Hải Phòng'),
('Vũ Quốc Việt', '0944556677', 'Nam Định'),
('Đặng Thu Thảo', '0977889900', 'Huế'),
('Bùi Xuân Huấn', '0922334455', 'Lào Cai'),
('Ngô Bảo Châu', '0966778899', 'Hưng Yên'),
('Trịnh Công Sơn', '0955667788', 'Đà Lạt');

INSERT INTO tables (table_number, status, capacity) VALUES 
(101, 'Available', 4), (102, 'Reserved', 2), (103, 'Available', 6), 
(201, 'Available', 4), (202, 'Reserved', 4), (203, 'Available', 2),
(301, 'Available', 8), (302, 'Available', 4), (303, 'Available', 4), (401, 'Available', 10);

INSERT INTO menu_items (dish_name, price, category_id) VALUES 
('Lẩu Thái Hải sản', 749000, 1),
('Lẩu bò', 55000, 1),
('Lẩu gà', 50000, 1),
('Lẩu nấm', 350000, 1),
('Gà Nướng Mật Ong', 180000, 1),
('Gỏi Cuốn Tôm Thịt', 149000, 4),
('Trà Đào Cam Sả', 45000, 3),
('Bia', 35000, 3),
('Nước Ép Hoa Quả', 30000, 3),
('Matcha latte', 65000, 3);

-- 4. TRIGGER & PROCEDURE
DELIMITER //
CREATE TRIGGER after_reservation_insert
AFTER INSERT ON reservations
FOR EACH ROW
BEGIN
    UPDATE tables SET status = 'Reserved' WHERE table_id = NEW.table_id;
END //
DELIMITER ;

DELIMITER //
CREATE PROCEDURE CalculateInvoiceTotal(IN inv_id INT)
BEGIN
    UPDATE invoices 
    SET total_amount = (SELECT SUM(line_subtotal) FROM invoice_details WHERE invoice_id = inv_id) + shipping_fee
    WHERE invoice_id = inv_id;
END //
DELIMITER ;

CREATE VIEW View_TopSellingDishes AS
SELECT m.dish_name, SUM(id.quantity) as total_sold
FROM menu_items m
JOIN invoice_details id ON m.dish_id = id.dish_id
GROUP BY m.dish_name
ORDER BY total_sold DESC;

-- 5. SECURITY
CREATE ROLE IF NOT EXISTS 'staff_role';
GRANT SELECT, INSERT, UPDATE ON RestaurantManagement.* TO 'staff_role';
-- CREATE USER 'linh_staff'@'localhost' IDENTIFIED BY 'Linh123456'; -- Chỉ chạy dòng này nếu user chưa tồn tại
-- GRANT 'staff_role' TO 'linh_staff'@'localhost';