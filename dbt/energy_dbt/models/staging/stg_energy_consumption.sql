with source as (
    select
        utc_timestamp,
        country,
        consumption_mw,
        loaded_at
    from raw.energy_consumption
    where consumption_mw is not null
),

renamed as (
    select
        utc_timestamp as measured_at,
        country as country_code,
        consumption_mw,
        date_trunc('day', utc_timestamp) as measured_date,
        extract(hour from utc_timestamp) as hour_of_day,
        loaded_at
    from source
)

select * from renamed