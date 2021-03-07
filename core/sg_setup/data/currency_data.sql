UPDATE res_currency SET position='before' WHERE name = 'SGD';

--Updating tax names
update account_account_tag set name = 'Sales GST 7%' where name = 'Sales Tax 7% SR';
update account_account_tag set name = 'Sales No GST' where name = 'Sales Tax 0% ZR';
update account_account_tag set name = 'Purchase GST 7%' where name = 'Purchase Tax 7% TX7';
update account_account_tag set name = 'Purchase No GST' where name = 'Purchase Tax 0% ZP';

update account_tax set name = 'Sales GST 7%', description = 'Sales GST' where name = 'Sales Tax 7% SR';
update account_tax set name = 'Sales No GST', description = 'Sales No GST' where name = 'Sales Tax 0% ZR';
update account_tax set name = 'Purchase GST 7%', description = 'Purchase GST'  where name = 'Purchase Tax 7% TX7';
update account_tax set name = 'Purchase No GST', description = 'Purchase No GST' where name = 'Purchase Tax 0% ZP';