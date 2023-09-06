create user customer with password 'password1234';

create schema util_sch;

grant usage on schema util_sch to customer;

create sequence user_sequence
start with 100;

create table util_sch.users (
	id serial int default nextval('user_sequence') primary key, 
	first_name varchar(64) not null,
	last_name varchar(64) not null,
	phone_num varchar(64) not null,
	constraint cnstr_phone_num unique (phone_num)
);

create sequence apartments_sequence
start with 100;

create table util_sch.apartments (
	id serial int default nextval('apartments_sequence') primary key,
	country varchar(100) not null,
	city varchar(100) not null,
	street varchar(100) not null,
	building varchar(10) not null,
	apartment varchar(10) not null,
	constraint cnstr_address unique (country, city, street, building, apartment)
);

create sequence properties_sequence
start with 100;

create table util_sch.properties (
	id serial int default nextval('properties_sequence') primary key,
	user_id integer not null,
	apart_id integer not null,
	foreign key (user_id) references util_sch.users(id),
	foreign key (apart_id) references util_sch.apartments(id),
	constraint cnstr_property unique (id, apart_id)
);

create sequence utilities_sequence
start with 100;

create table util_sch.utilities (
	id serial int default nextval('utilities_sequence') primary key,
  	util_name varchar(100) not null,
	company_name varchar(100) not null,
	start_date date not null,
	end_date date null,
	price_per_unit numeric(10,2) not null
);

create sequence bills_sequence
start with 100;

create table util_sch.bills (
	id serial int default nextval('bills_sequence') primary key,
	util_id integer not null,
	apart_id integer not null,
	pay_period date not null,
	value numeric(10,2) not null,
	pay_date date null,
	foreign key (util_id) references util_sch.utilities(id),
	foreign key (apart_id) references util_sch.apartments(id),
	constraint cntsr_bill_address unique (util_id, apart_id, pay_period)
);

--Unpaid utilities
create or replace view util_sch.unpaid_utils_vw as 
select ap.id apart_id,
	   ut.util_name,
	   ut.company_name,
	   string_agg(bl.id::text, ';') bills_id,
	   string_agg(bl.pay_period::text, ';') pay_periods,
	   string_agg((bl.value * ut.price_per_unit)::text, ';') payments
  from util_sch.users us
  join util_sch.properties pr on pr.user_id = us.id
  join util_sch.bills bl on bl.apart_id = pr.apart_id and bl.pay_date is null
  join util_sch.utilities ut on ut.id = bl.util_id
  join util_sch.apartments ap on ap.id = bl.apart_id
 group by ap.id, ut.util_name, ut.company_name;

--Paid utilities
create or replace view util_sch.paid_utils_vw as
select ap.id apart_id,
	   ut.util_name,
	   ut.company_name,
	   bl.pay_date,
	   date_trunc('day', bl.pay_date) tr_pay_date,
	   string_agg(bl.id::text, ';') bills_id,
	   string_agg(bl.pay_period::text, ';') pay_periods,
	   string_agg((bl.value * ut.price_per_unit)::text, ';') payments
  from util_sch.users us
  join util_sch.properties pr on pr.user_id = us.id
  join util_sch.bills bl on bl.apart_id = pr.apart_id and bl.pay_date is not null
  join util_sch.utilities ut on ut.id = bl.util_id
  join util_sch.apartments ap on ap.id = bl.apart_id
 group by ap.id, tr_pay_date, ut.util_name, ut.company_name;

create index idx_status on util_sch.bills (apart_id, pay_date);

grant select on util_sch.unpaid_utils_vw to customer;
grant select on util_sch.paid_utils_vw to customer;
grant select on util_sch.users to customer;
grant select on util_sch.apartments to customer;
grant select on util_sch.properties to customer;
grant select on util_sch.utilities to customer;
grant select, update on util_sch.bills to customer;