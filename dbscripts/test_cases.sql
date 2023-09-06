insert into util_sch.users (id, first_name, last_name, phone_num)
values 
(1, 'First_Name_1', 'Second_Name_1', '+000000000000'),
(2, 'First_Name_2', 'Second_Name_2', '+000000000001'),
(3, 'First_Name_3', 'Second_Name_3', '+000000000002');

insert into util_sch.apartments (id, country, city, street, building, apartment)
values
(1, 'Country_1', 'City_1', 'Street_1', '110', '10'),
(2, 'Country_1', 'City_1', 'Street_2', '100', '14'),
(3, 'Country_1', 'City_2', 'Street_3', '217', '18');

insert into util_sch.properties (user_id, apart_id)
values
(1, 1),
(2, 2),
(3, 3);

insert into util_sch.utilities (id, util_name, company_name, start_date, end_date, price_per_unit)
values
(1, 'Util_1', 'Company_1', '2023-01-01', null, 3.50),
(2, 'Util_2', 'Company_2', '2023-01-01', null, 0.25),
(3, 'Util_3', 'Company_3', '2023-01-01', null, 1.20);

insert into util_sch.bills (id, util_id, apart_id, pay_period, value, pay_date)
values
(1, 1, 1, '2023-01-01', 50.00, '2023-01-22 09:05:24'),
(2, 2, 1, '2023-01-01', 30.00, '2023-01-23 10:05:24'),
(3, 3, 1, '2023-01-01', 25.00, '2023-01-23 10:05:24'),
(4, 1, 1, '2023-02-01', 55.00, '2023-02-18 11:05:24'),
(5, 2, 1, '2023-02-01', 32.00, '2023-01-23 10:05:24'),
(6, 3, 1, '2023-02-01', 27.00, '2023-03-18 12:05:24'),
(7, 1, 1, '2023-03-01', 60.00, '2023-01-22 09:05:24'),
(8, 2, 1, '2023-03-01', 35.00, '2023-04-01 13:05:24'),
(9, 3, 1, '2023-03-01', 30.00, '2023-03-18 12:05:24'),
(10, 1, 1, '2023-04-01', 65.00, null),
(11, 2, 1, '2023-04-01', 73.00, null),
(12, 3, 1, '2023-04-01', 37.00, null),
(13, 1, 1, '2023-05-01', 40.00, null),
(14, 2, 1, '2023-05-01', 91.00, null),
(15, 3, 1, '2023-05-01', 30.00, null);