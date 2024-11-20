

drop table if exists clean.most_recent_bmi;

create table clean.most_recent_bmi as (
    select 
        ht.entity_id,
        ht.as_of_date,
        ht.measure_date as height_date,
        ht.days_since_measurement as days_since_ht,
        ht.value as height,
        wt.measure_date as weight_date,
        wt.days_since_measurement as days_since_wt,
        wt.value as weight,
        case when ht.value !=0 then round(703 * (wt.value / (ht.value * ht.value))::numeric, 2) else null end as bmi,
        case when 
        ht.measure_date = wt.measure_date 
        then true else false
        end as measurements_same_day,
        abs(ht.measure_date - wt.measure_date) as gap_between_tests
    from clean.most_recent_vitals ht left join clean.most_recent_vitals wt 
        on ht.entity_id = wt.entity_id 
        and ht.as_of_date = wt.as_of_date 
        and wt.measure_type = 'weight'
    where ht.measure_type = 'height'
);

create index on clean.most_recent_bmi(entity_id);
create index on clean.most_recent_bmi(as_of_date);
create index on clean.most_recent_bmi(days_since_ht);
create index on clean.most_recent_bmi(days_since_wt);
create index on clean.most_recent_bmi(gap_between_tests);
