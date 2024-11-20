

drop table if exists clean.most_recent_bmi_biopsy_cohort;

create table clean.most_recent_bmi_biopsy_cohort as (
    select 
        ht.entity_id,
        ht.as_of_date,
        ht.measure_date as height_date,
        ht.days_since_measurement as days_since_ht,
        ht.value as height,
        wt.measure_date as weight_date,
        wt.days_since_measurement as days_since_wt,
        wt.value as weight,
        round(703 * (wt.value / (ht.value * ht.value))::numeric, 2) as bmi,
        case when ht.measure_date = wt.measure_date 
        then true else false
        end as measurements_same_day,
        abs(ht.measure_date - wt.measure_date) as gap_between_tests
    from clean.most_recent_vitals_biopsy_cohort ht left join clean.most_recent_vitals_biopsy_cohort wt 
        on ht.entity_id = wt.entity_id 
        and ht.as_of_date = wt.as_of_date 
        and wt.measure_type = 'weight'
    where ht.measure_type = 'height'
);

create index on clean.most_recent_bmi_biopsy_cohort(entity_id);
create index on clean.most_recent_bmi_biopsy_cohort(as_of_date);
create index on clean.most_recent_bmi_biopsy_cohort(days_since_ht);
create index on clean.most_recent_bmi_biopsy_cohort(days_since_wt);
create index on clean.most_recent_bmi_biopsy_cohort(gap_between_tests);
