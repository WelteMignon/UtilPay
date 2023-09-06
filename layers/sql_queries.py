class SqlQueriesEnum:
    hist_utils = """with rnk_periods 
                      as (select pu.*,
                                 dense_rank() over (partition by pu.tr_pay_date order by pu.tr_pay_date desc) as pay_rank_down,
                                 dense_rank() over (partition by pu.tr_pay_date order by pu.tr_pay_date asc) as pay_rank_up
                            from util_sch.paid_utils_vw pu
                          where ((%(date_up)s is not null and pu.tr_pay_date > to_date(%(date_up)s, 'yyyy-mm-dd'))
                                  or (%(date_down)s is not null and pu.tr_pay_date < to_date(%(date_down)s, 'yyyy-mm-dd')))
                             and pu.apart_id = %(apart_id)s)
                  select to_char(rp.tr_pay_date, 'yyyy-mm-dd'),
                         rp.util_name,
                         rp.company_name,
                         rp.pay_periods,
                         rp.payments
                    from rnk_periods rp
                   where ((%(date_up)s is not null and rp.pay_rank_up <= 3)
                          or (%(date_down)s is not null and rp.pay_rank_down <= 3));"""
    pay_utils = """update util_sch.bills
                      set pay_date = to_date(%s, 'yyyy-mm-dd')
                    where pay_date is null
                      and id = %s;"""