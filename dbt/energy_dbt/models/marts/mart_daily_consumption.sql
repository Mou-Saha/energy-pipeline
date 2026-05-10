with staged as (
    select * from {{ ref('stg_energy_consumption') }}
),

daily_agg as (
    select
        measured_date,
        country_code,
        round(avg(consumption_mw)::numeric, 2) as avg_consumption_mw,
        round(max(consumption_mw)::numeric, 2) as peak_consumption_mw,
        round(min(consumption_mw)::numeric, 2) as min_consumption_mw,
        round(sum(consumption_mw)::numeric, 2) as total_consumption_mw,
        count(*) as hourly_readings
    from staged
    group by measured_date, country_code
)

select * from daily_agg