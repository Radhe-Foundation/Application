-- Fix SECURITY DEFINER Views - Compact Version
DROP VIEW IF EXISTS public.employees_safe;
DROP VIEW IF EXISTS public.users_safe;

CREATE VIEW public.employees_safe AS
SELECT id, employee_code, user_id, company_id, first_name, last_name, date_of_birth, gender, email, phone, department_id, position_id, date_of_joining, is_active, created_at, employment_type, employment_status, address, city, state, pincode, emergency_contact_name, emergency_phone, emergency_relation, bank_name, ifsc_code, branch_name, basic_salary, allowance, deduction
FROM public.employees;

COMMENT ON VIEW public.employees_safe IS 'Safe employee view without account_number';

CREATE VIEW public.users_safe AS
SELECT id, username, email, role_id, status, created_at, last_seen, is_online, last_login, last_ip
FROM public.users;

COMMENT ON VIEW public.users_safe IS 'Safe user view without session_token';

GRANT SELECT ON public.employees_safe TO authenticated;
GRANT SELECT ON public.users_safe TO authenticated;

SELECT viewname FROM pg_views WHERE schemaname = 'public' AND viewname IN ('employees_safe', 'users_safe');

