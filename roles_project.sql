USE RestaurantManagement;

-- BƯỚC 1: TẠO CÁC NHÓM QUYỀN (ROLES)
CREATE ROLE IF NOT EXISTS 'admin_role';
CREATE ROLE IF NOT EXISTS 'cashier_role';
CREATE ROLE IF NOT EXISTS 'waiter_role';

-- BƯỚC 2: GÁN QUYỀN CHO TỪNG ROLE TRÊN DATABASE RestaurantManagement
-- 2.1. Quản lý (Admin): Toàn quyền
GRANT ALL PRIVILEGES ON RestaurantManagement.* TO 'admin_role';

-- 2.2. Thu ngân (Cashier): Quản lý hóa đơn, khách hàng, xem thực đơn và bàn
GRANT SELECT, INSERT, UPDATE ON RestaurantManagement.invoices TO 'cashier_role';
GRANT SELECT, INSERT, UPDATE ON RestaurantManagement.invoice_details TO 'cashier_role';
GRANT SELECT, INSERT, UPDATE ON RestaurantManagement.customers TO 'cashier_role';
GRANT SELECT ON RestaurantManagement.tables TO 'cashier_role';
GRANT SELECT ON RestaurantManagement.menu_items TO 'cashier_role';
-- Cho phép Thu ngân chạy Procedure tính tổng tiền hóa đơn của nhóm bạn
GRANT EXECUTE ON PROCEDURE RestaurantManagement.CalculateInvoiceTotal TO 'cashier_role';

-- 2.3. Bồi bàn (Waiter): Quản lý đặt bàn, xem bàn và thực đơn
GRANT SELECT ON RestaurantManagement.menu_items TO 'waiter_role';
GRANT SELECT, UPDATE ON RestaurantManagement.tables TO 'waiter_role';
GRANT SELECT, INSERT, UPDATE ON RestaurantManagement.reservations TO 'waiter_role';
GRANT SELECT, INSERT, UPDATE ON RestaurantManagement.reservation_detail TO 'waiter_role';

-- BƯỚC 3: TẠO TÀI KHOẢN NGƯỜI DÙNG VÀ GÁN VÀO ROLE TƯƠNG ỨNG
CREATE USER IF NOT EXISTS 'admin_user'@'localhost' IDENTIFIED BY 'AdminPass123!';
CREATE USER IF NOT EXISTS 'cashier_user'@'localhost' IDENTIFIED BY 'CashierPass123!';
CREATE USER IF NOT EXISTS 'waiter_user'@'localhost' IDENTIFIED BY 'WaiterPass123!';

GRANT 'admin_role' TO 'admin_user'@'localhost';
GRANT 'cashier_role' TO 'cashier_user'@'localhost';
GRANT 'waiter_role' TO 'waiter_user'@'localhost';

-- Kích hoạt quyền
FLUSH PRIVILEGES;



-- kịch bản A
-- Bắt đầu giao dịch thanh toán
START TRANSACTION;

-- Bước 1: Tạo hóa đơn mới
INSERT INTO invoices (customer_id, employee_id, table_id, total_amount, payment_date, order_type, shipping_fee) 
VALUES (1, 2, 5, 0.00, NOW(), 'Dine-in', 0.00);

SET @new_invoice_id = LAST_INSERT_ID();

-- Bước 2: Thêm chi tiết hóa đơn
-- Mẹo: Để (quantity * unit_price) giúp SQL tự tính subtotal, tránh nhầm lẫn con số
INSERT INTO invoice_details (invoice_id, dish_id, quantity, unit_price, line_subtotal) 
VALUES 
    (@new_invoice_id, 3, 2, 150000.00, 2 * 150000.00),
    (@new_invoice_id, 7, 1, 200000.00, 1 * 200000.00);

-- Bước 3: Cập nhật tổng tiền (Sử dụng Procedure của nhóm)
CALL CalculateInvoiceTotal(@new_invoice_id);
UPDATE tables SET status = 'Available' WHERE table_id = 5;

COMMIT;

-- kịch bản B
START TRANSACTION;

-- Bước 1: Tạo mã đặt bàn cho Khách ID=1, đi 6 người
INSERT INTO reservations (customer_id, reservation_time, guest_count)
VALUES (1, '2026-05-15 19:00:00', 6);

-- Lấy ID của mã đặt bàn vừa tạo
SET @new_res_id = LAST_INSERT_ID();

-- Bước 2: Khách đi đông nên ghép 2 Bàn ID=3 và ID=4
-- LƯU Ý: Ngay khi chạy 2 lệnh INSERT này, Trigger 'after_reservation_table_insert'
-- của bạn sẽ tự động kích hoạt và cập nhật bảng 'tables' thành 'Reserved'!
INSERT INTO reservation_detail (reservation_id, table_id) VALUES (@new_res_id, 3);
INSERT INTO reservation_detail (reservation_id, table_id) VALUES (@new_res_id, 4);

-- Lưu giao dịch vĩnh viễn
COMMIT;