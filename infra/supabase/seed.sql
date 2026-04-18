INSERT INTO tenants (id, name, abn, gst_registered, financial_year_start, timezone, basiq_user_id)
VALUES (
  'a1b2c3d4-0000-0000-0000-000000000001',
  'Coastal Trades Pty Ltd',
  '51824753556',
  TRUE,
  7,
  'Australia/Sydney',
  NULL
);

INSERT INTO accounts (tenant_id, code, name, account_type, gst_code, is_system, formance_address) VALUES
('a1b2c3d4-0000-0000-0000-000000000001','1000','ANZ Business Cheque','asset','N-T',TRUE,'assets:bank:anz_cheque'),
('a1b2c3d4-0000-0000-0000-000000000001','1010','ANZ Business Savings','asset','N-T',TRUE,'assets:bank:anz_savings'),
('a1b2c3d4-0000-0000-0000-000000000001','1100','Trade Debtors','asset','N-T',TRUE,'assets:receivables:trade'),
('a1b2c3d4-0000-0000-0000-000000000001','1200','GST Receivable','asset','N-T',TRUE,'assets:tax:gst_receivable'),
('a1b2c3d4-0000-0000-0000-000000000001','1300','Prepayments','asset','N-T',FALSE,'assets:prepayments'),
('a1b2c3d4-0000-0000-0000-000000000001','2000','Trade Creditors','liability','N-T',TRUE,'liabilities:payables:trade'),
('a1b2c3d4-0000-0000-0000-000000000001','2100','GST Collected','liability','N-T',TRUE,'liabilities:tax:gst_collected'),
('a1b2c3d4-0000-0000-0000-000000000001','2110','GST Payable','liability','N-T',TRUE,'liabilities:tax:gst_payable'),
('a1b2c3d4-0000-0000-0000-000000000001','2200','PAYG Withholding Payable','liability','N-T',FALSE,'liabilities:tax:payg'),
('a1b2c3d4-0000-0000-0000-000000000001','2300','Superannuation Payable','liability','N-T',FALSE,'liabilities:super'),
('a1b2c3d4-0000-0000-0000-000000000001','3000','Retained Earnings','equity','N-T',TRUE,'equity:retained'),
('a1b2c3d4-0000-0000-0000-000000000001','3100','Owner Drawings','equity','N-T',FALSE,'equity:drawings'),
('a1b2c3d4-0000-0000-0000-000000000001','4000','Plumbing Services Revenue','revenue','G1',TRUE,'revenue:services:plumbing'),
('a1b2c3d4-0000-0000-0000-000000000001','4010','Emergency Call-Out Revenue','revenue','G1',FALSE,'revenue:services:callout'),
('a1b2c3d4-0000-0000-0000-000000000001','4020','Parts & Materials Revenue','revenue','G1',FALSE,'revenue:parts'),
('a1b2c3d4-0000-0000-0000-000000000001','4900','Interest Income','revenue','N-T',FALSE,'revenue:interest'),
('a1b2c3d4-0000-0000-0000-000000000001','5000','Plumbing Materials & Parts','expense','G11',FALSE,'expenses:cogs:materials'),
('a1b2c3d4-0000-0000-0000-000000000001','5010','Subcontractor Labour','expense','G11',FALSE,'expenses:cogs:subcontractors'),
('a1b2c3d4-0000-0000-0000-000000000001','6000','Fuel & Vehicle','expense','G11',FALSE,'expenses:vehicle:fuel'),
('a1b2c3d4-0000-0000-0000-000000000001','6010','Vehicle Registration & Insurance','expense','G11',FALSE,'expenses:vehicle:insurance'),
('a1b2c3d4-0000-0000-0000-000000000001','6020','Tools & Equipment','expense','G11',FALSE,'expenses:tools'),
('a1b2c3d4-0000-0000-0000-000000000001','6100','Electricity','expense','G11',FALSE,'expenses:utilities:electricity'),
('a1b2c3d4-0000-0000-0000-000000000001','6110','Mobile & Internet','expense','G11',FALSE,'expenses:utilities:mobile'),
('a1b2c3d4-0000-0000-0000-000000000001','6200','Software Subscriptions','expense','G11',FALSE,'expenses:software'),
('a1b2c3d4-0000-0000-0000-000000000001','6300','Advertising & Marketing','expense','G11',FALSE,'expenses:marketing'),
('a1b2c3d4-0000-0000-0000-000000000001','6400','Accounting & Legal','expense','G11',FALSE,'expenses:professional'),
('a1b2c3d4-0000-0000-0000-000000000001','6500','Bank Fees & Charges','expense','G11',FALSE,'expenses:bank'),
('a1b2c3d4-0000-0000-0000-000000000001','6600','Superannuation Expense','expense','N-T',FALSE,'expenses:super'),
('a1b2c3d4-0000-0000-0000-000000000001','6700','Wages & Salaries','expense','N-T',FALSE,'expenses:wages'),
('a1b2c3d4-0000-0000-0000-000000000001','6800','ATO Payments','expense','N-T',FALSE,'expenses:tax:ato');

INSERT INTO bank_connections (id, tenant_id, basiq_connection_id, institution_name, account_name, account_number, account_type, sync_status)
VALUES 
('b1b2c3d4-0000-0000-0000-000000000001', 'a1b2c3d4-0000-0000-0000-000000000001', 'conn-anz-cheque', 'ANZ', 'Business Everyday', '****4521', 'transaction', 'active'),
('b1b2c3d4-0000-0000-0000-000000000002', 'a1b2c3d4-0000-0000-0000-000000000001', 'conn-anz-savings', 'ANZ', 'Business Savings', '****7834', 'savings', 'active');